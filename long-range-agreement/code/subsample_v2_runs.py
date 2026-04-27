#!/usr/bin/env python3

import argparse
import itertools
import random
import sys
from pathlib import Path

import pandas as pd
from wordfreq import zipf_frequency


RUN_COUNT = 6
TRIALS_PER_RUN = 48
STRUCTURES = ("short", "medium", "long")
GRAMMATICALITIES = ("grammatical", "violation")
NUMBERS = ("singular", "plural")
GENDERS = ("masculine", "feminine")

KEY_COLUMNS = [
    "Structure",
    "VP_Grammaticality",
    "Subject_Number",
    "PP1_Number",
    "PP2_Number",
]

BALANCE_METRICS = [
    "Verb_Zipf_Frequency",
    "Verb_Length",
    "Subject_Zipf_Frequency",
    "Subject_Length",
    "Noun_Zipf_Frequency",
    "Noun_Length",
]

PROBE_TARGET_PP = "pp_scene"
PROBE_TARGET_SUBJECT = "subject_state"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Subsample v2 stimuli into 6 balanced runs (48 trials each) with "
            "vocabulary-heavy sampling and Zipf/length balancing controls."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("run_lists/v2_stimuli.csv"),
        help="Input stimuli CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("run_lists/v2_subsampled_runs.csv"),
        help="Output subsampled CSV.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=13,
        help="Random seed.",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=60,
        help="Number of randomized search attempts.",
    )
    parser.add_argument(
        "--candidate-sample-size",
        type=int,
        default=64,
        help="Number of candidates probed per condition cell pick.",
    )
    parser.add_argument(
        "--allow-number-gender-dependence",
        action="store_true",
        help=(
            "Disable the subject-number/subject-gender independence constraint. "
            "By default, each (structure, grammaticality, subject number) block "
            "must include 2 masculine and 2 feminine subjects."
        ),
    )
    return parser.parse_args()


def _letters(text):
    return sum(1 for char in str(text) if char.isalpha())


def _norm_label(text):
    return str(text).strip().lower()


def _norm_gender(text):
    label = _norm_label(text)
    mapping = {
        "m": "masculine",
        "masculine": "masculine",
        "f": "feminine",
        "feminine": "feminine",
    }
    return mapping.get(label, label)


def _require_columns(df, columns):
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required columns: {', '.join(missing)}")


def _prepare_dataframe(df):
    required = [
        "Stimulus_ID",
        "Structure",
        "VP_Grammaticality",
        "Noun_Congruency",
        "Subject_Lemma",
        "Subject_Gender",
        "Subject_Number",
        "PP1_Lemma",
        "PP1_Number",
        "PP2_Lemma",
        "PP2_Number",
        "PP1_Preposition",
        "PP2_Preposition",
        "Verb_Phrase",
    ]
    _require_columns(df, required)

    out = df.copy()
    out["Structure"] = out["Structure"].map(_norm_label)
    out["VP_Grammaticality"] = out["VP_Grammaticality"].map(_norm_label)
    out["Subject_Gender"] = out["Subject_Gender"].map(_norm_gender)
    out["Subject_Number"] = out["Subject_Number"].map(_norm_label)
    out["PP1_Number"] = out["PP1_Number"].map(_norm_label)
    out["PP2_Number"] = out["PP2_Number"].map(_norm_label)

    if "Verb_Lemma" not in out.columns:
        out["Verb_Lemma"] = out["Verb_Phrase"].astype(str).str.split().str[0]

    if "Subject_Zipf_Frequency" not in out.columns:
        out["Subject_Zipf_Frequency"] = out["Subject_Lemma"].astype(str).str.lower().map(
            lambda word: zipf_frequency(word, "fr")
        )
    if "Subject_Length" not in out.columns:
        out["Subject_Length"] = out["Subject_Lemma"].map(_letters)

    if "Verb_Zipf_Frequency" not in out.columns:
        out["Verb_Zipf_Frequency"] = out["Verb_Lemma"].astype(str).str.lower().map(
            lambda word: zipf_frequency(word, "fr")
        )
    if "Verb_Length" not in out.columns:
        out["Verb_Length"] = out["Verb_Lemma"].map(_letters)

    pp1_zipf = out["PP1_Lemma"].astype(str).str.lower().map(lambda word: zipf_frequency(word, "fr"))
    pp2_zipf = out["PP2_Lemma"].astype(str).str.lower().map(lambda word: zipf_frequency(word, "fr"))
    out["Noun_Zipf_Frequency"] = (pp1_zipf + pp2_zipf) / 2.0

    pp1_len = out["PP1_Lemma"].map(_letters)
    pp2_len = out["PP2_Lemma"].map(_letters)
    out["Noun_Length"] = (pp1_len + pp2_len) / 2.0

    return out


def _cell_space():
    return list(itertools.product(STRUCTURES, GRAMMATICALITIES, NUMBERS, NUMBERS, NUMBERS))


def _build_pools(df, cells):
    pools = {}
    for cell in cells:
        structure, grammaticality, subject_number, pp1_number, pp2_number = cell
        subset = df[
            (df["Structure"] == structure)
            & (df["VP_Grammaticality"] == grammaticality)
            & (df["Subject_Number"] == subject_number)
            & (df["PP1_Number"] == pp1_number)
            & (df["PP2_Number"] == pp2_number)
        ]
        pools[cell] = subset.index.tolist()
    return pools


def _validate_pool_capacity(pools, run_count):
    too_small = [cell for cell, indices in pools.items() if len(indices) < run_count]
    if too_small:
        details = "; ".join([f"{cell}: {len(pools[cell])}" for cell in too_small[:8]])
        raise RuntimeError(
            "Not enough candidates to sample without replacement for all runs. "
            f"Examples: {details}"
        )


def _validate_number_gender_feasibility(df, enforce_independence):
    if not enforce_independence:
        return

    observed = (
        df[["Subject_Number", "Subject_Gender"]]
        .drop_duplicates()
        .groupby("Subject_Number")["Subject_Gender"]
        .apply(set)
        .to_dict()
    )

    missing = []
    for subject_number in NUMBERS:
        seen = observed.get(subject_number, set())
        missing_genders = [gender for gender in GENDERS if gender not in seen]
        if missing_genders:
            missing.append((subject_number, missing_genders, sorted(seen)))

    if missing:
        details = "; ".join(
            [
                (
                    f"subject_number={subject_number}, missing={','.join(missing_genders)}, "
                    f"observed={','.join(seen) if seen else 'none'}"
                )
                for subject_number, missing_genders, seen in missing
            ]
        )
        raise RuntimeError(
            "Cannot enforce subject-number/subject-gender independence with current input data. "
            f"Details: {details}. "
            "Add both masculine and feminine subjects for each subject number in the lexicon, "
            "or rerun with --allow-number-gender-dependence."
        )


def _row_tokens(row):
    return {
        f"subj:{row.Subject_Lemma}",
        f"verb:{row.Verb_Lemma}",
        f"ppnoun:{row.PP1_Lemma}",
        f"ppnoun:{row.PP2_Lemma}",
        f"prep:{row.PP1_Preposition}",
        f"prep:{row.PP2_Preposition}",
    }


def _token_rarity(df):
    token_counts = {}
    for row in df.itertuples(index=False):
        for token in _row_tokens(row):
            token_counts[token] = token_counts.get(token, 0) + 1
    return {token: 1.0 / count for token, count in token_counts.items()}


def _pick_candidate(
    pool,
    used_indices,
    df,
    used_tokens,
    run_tokens,
    rarity,
    rng,
    sample_size,
    cell,
    run_gender_counts,
    enforce_independence,
):
    if not pool:
        return None

    # Sampling directly from the pool is much faster than rebuilding full
    # availability lists every time. We only need a handful of unused rows.
    sample_cap = min(len(pool), max(sample_size * 3, sample_size))
    probe = []
    for idx in rng.sample(pool, sample_cap):
        if idx not in used_indices:
            probe.append(idx)
            if len(probe) >= sample_size:
                break

    if not probe:
        for idx in pool:
            if idx in used_indices:
                continue
            if enforce_independence:
                structure, grammaticality, subject_number, _, _ = cell
                row = df.loc[idx]
                gender_key = (
                    structure,
                    grammaticality,
                    subject_number,
                    row["Subject_Gender"],
                )
                if run_gender_counts.get(gender_key, 0) >= 2:
                    continue
            probe.append(idx)
            break

    if not probe:
        return None

    best_idx = None
    best_score = None

    for idx in probe:
        row = df.loc[idx]
        if enforce_independence:
            structure, grammaticality, subject_number, _, _ = cell
            gender_key = (
                structure,
                grammaticality,
                subject_number,
                row["Subject_Gender"],
            )
            if run_gender_counts.get(gender_key, 0) >= 2:
                continue

        tokens = _row_tokens(row)

        global_novelty = sum(1 for token in tokens if token not in used_tokens)
        run_novelty = sum(1 for token in tokens if token not in run_tokens)
        rarity_bonus = sum(rarity.get(token, 0.0) for token in tokens if token not in used_tokens)

        score = 6.0 * global_novelty + 3.0 * run_novelty + 2.0 * rarity_bonus + rng.random()

        if best_score is None or score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def _construct_solution(df, pools, cells, rarity, rng, sample_size, enforce_independence):
    used_indices = set()
    used_tokens = set()
    run_assignments = []

    for _run_id in range(1, RUN_COUNT + 1):
        run_tokens = set()
        run_indices = []
        run_gender_counts = {}

        cell_order = list(cells)
        rng.shuffle(cell_order)

        for cell in cell_order:
            picked = _pick_candidate(
                pools[cell],
                used_indices,
                df,
                used_tokens,
                run_tokens,
                rarity,
                rng,
                sample_size,
                cell,
                run_gender_counts,
                enforce_independence,
            )
            if picked is None:
                return None

            used_indices.add(picked)
            run_indices.append(picked)

            picked_tokens = _row_tokens(df.loc[picked])
            used_tokens.update(picked_tokens)
            run_tokens.update(picked_tokens)

            if enforce_independence:
                structure, grammaticality, subject_number, _, _ = cell
                row = df.loc[picked]
                gender_key = (
                    structure,
                    grammaticality,
                    subject_number,
                    row["Subject_Gender"],
                )
                run_gender_counts[gender_key] = run_gender_counts.get(gender_key, 0) + 1

        rng.shuffle(run_indices)
        run_assignments.append(run_indices)

    return run_assignments


def _materialize(df, run_assignments):
    rows = []
    for run_id, indices in enumerate(run_assignments, start=1):
        run_df = df.loc[indices].copy()
        run_df.insert(0, "Run", run_id)
        run_df.insert(1, "Trial_In_Run", range(1, len(run_df) + 1))
        rows.append(run_df)
    return pd.concat(rows, ignore_index=True)


def _diversity_score(selected, source):
    source_subjects = set(source["Subject_Lemma"])
    source_verbs = set(source["Verb_Lemma"])
    source_nouns = set(source["PP1_Lemma"]).union(set(source["PP2_Lemma"]))
    source_preps = set(source["PP1_Preposition"]).union(set(source["PP2_Preposition"]))

    selected_subjects = set(selected["Subject_Lemma"])
    selected_verbs = set(selected["Verb_Lemma"])
    selected_nouns = set(selected["PP1_Lemma"]).union(set(selected["PP2_Lemma"]))
    selected_preps = set(selected["PP1_Preposition"]).union(set(selected["PP2_Preposition"]))

    subject_ratio = len(selected_subjects) / max(1, len(source_subjects))
    verb_ratio = len(selected_verbs) / max(1, len(source_verbs))
    noun_ratio = len(selected_nouns) / max(1, len(source_nouns))
    prep_ratio = len(selected_preps) / max(1, len(source_preps))

    # Noun coverage is weighted highest because there are many noun combinations.
    return (1.0 * subject_ratio + 1.0 * verb_ratio + 2.0 * noun_ratio + 1.0 * prep_ratio) / 5.0


def _balance_penalty(selected):
    eps = 1e-9
    penalties = []

    for metric in BALANCE_METRICS:
        if metric not in selected.columns:
            continue

        scale = float(selected[metric].std(ddof=0)) + eps

        cell_means = selected.groupby(["Structure", "VP_Grammaticality", "Noun_Congruency"])[metric].mean()
        penalties.append(float(cell_means.std(ddof=0)) / scale)

        for factor in ["Structure", "VP_Grammaticality", "Noun_Congruency"]:
            level_means = selected.groupby(factor)[metric].mean()
            penalties.append(float(level_means.std(ddof=0)) / scale)

    if not penalties:
        return 0.0
    return sum(penalties) / len(penalties)


def _score_solution(selected, source):
    diversity = _diversity_score(selected, source)
    penalty = _balance_penalty(selected)
    # Diversity is the priority; balance is a control constraint.
    score = 8.0 * diversity - 1.0 * penalty
    return score, diversity, penalty


def _sample_exact(indices, k, rng, label):
    if len(indices) < k:
        raise RuntimeError(f"Not enough rows to sample {k} items for {label}; got {len(indices)}")
    return rng.sample(indices, k)


def _pick_absent_pp_lemma(row, all_pp_lemmas, rng):
    present = {str(row["PP1_Lemma"]), str(row["PP2_Lemma"])}
    candidates = [lemma for lemma in all_pp_lemmas if lemma not in present]
    if not candidates:
        raise RuntimeError("Could not build a PP-scene NO probe: no distractor PP lemma available.")
    return rng.choice(candidates)


def _starts_with_vowel(word):
    return str(word)[:1].lower() in "aeiouyàâéèêîïôùûü"


def _pluralize_noun(noun, gender):
    """Simple French pluralization: most nouns add -s, some special cases handled."""
    noun_str = str(noun)
    # Most French nouns just add -s
    if noun_str.endswith(('s', 'x', 'z')):
        return noun_str  # Already plural-marked
    if noun_str.endswith('al'):
        return noun_str[:-2] + 'aux'  # e.g., animal -> animaux
    if noun_str.endswith('eau'):
        return noun_str + 'x'  # e.g., bureau -> bureaux
    return noun_str + 's'


def _article_np(gender, number, lemma):
    """Returns article for an NP (handles spacing)."""
    lemma_str = str(lemma)
    if number == "plural":
        return "les "
    if _starts_with_vowel(lemma_str):
        return "l'"
    return "la " if gender == "feminine" else "le "


def _subject_pronoun(gender, number):
    """Returns pronoun for subject verb inversion (elle/il/elles/ils)."""
    if number == "singular":
        return "elle" if gender == "feminine" else "il"
    return "elles" if gender == "feminine" else "ils"


def _subject_probe_text(subject_lemma, subject_gender, subject_number, verb_head, verb_phrase, probe_continuation=""):
    """Generate subject-state probe: 'l'autrice lit-elle un livre ?'"""
    article = _article_np(subject_gender, subject_number, subject_lemma)
    subject_np = f"{article}{subject_lemma}"
    pronoun = _subject_pronoun(subject_gender, subject_number)
    verb_inverted = f"{verb_head}-{pronoun}"
    
    continuation = str(probe_continuation).strip()
    if not continuation:
        # Backward-compatible fallback: derive continuation from Verb_Phrase.
        continuation = str(verb_phrase)[len(str(verb_head)):].lstrip()

    if continuation:
        return f"{subject_np} {verb_inverted} {continuation} ?"
    return f"{subject_np} {verb_inverted} ?"


def _pp_probe_text(pp2_noun, pp2_gender, pp2_number, pp1_prep, pp1_noun, pp1_gender, pp1_number):
    """Generate PP-scene probe: 'est-ce que les escaliers sont devant l'école ?'"""
    article2 = _article_np(pp2_gender, pp2_number, pp2_noun)
    
    # Pluralize noun if needed
    noun2 = pp2_noun if pp2_number == "singular" else _pluralize_noun(pp2_noun, pp2_gender)
    np2 = f"{article2}{noun2}"
    
    estre = "sont" if pp2_number == "plural" else "est"
    noun1 = pp1_noun if pp1_number == "singular" else _pluralize_noun(pp1_noun, pp1_gender)

    if str(pp1_prep).endswith("de"):
        if pp1_number == "plural":
            pp1_with_prep = f"{pp1_prep}s {noun1}"
        elif _starts_with_vowel(pp1_noun):
            pp1_with_prep = f"{pp1_prep} l'{noun1}"
        else:
            article1 = "du" if pp1_gender == "masculine" else "de la"
            pp1_with_prep = f"{pp1_prep[:-2]}{article1} {noun1}"
    else:
        article1 = _article_np(pp1_gender, pp1_number, pp1_noun)
        np1 = f"{article1}{noun1}"
        pp1_with_prep = f"{pp1_prep} {np1}"
    
    return f"est-ce que {np2} {estre} {pp1_with_prep} ?"


def _get_opposite_gender_subject(gender):
    """Helper to flip gender."""
    return "feminine" if gender == "masculine" else "masculine"


def _normalize_question(text):
    question = str(text).strip()
    if not question:
        return ""
    if not question.endswith("?"):
        question = f"{question} ?"
    return question


def _assign_probes(selected, rng):
    out = selected.copy()
    out["Probe"] = ""
    out["Probe_Target"] = ""
    out["Probe_Correct_Answer"] = ""

    all_pp_lemmas = sorted(set(out["PP1_Lemma"]).union(set(out["PP2_Lemma"])))
    
    # Build mapping of (number, gender) to list of subject lemmas for generating NO probes
    subject_map = {}
    for _, row in out.iterrows():
        key = (str(row["Subject_Number"]), str(row["Subject_Gender"]))
        if key not in subject_map:
            subject_map[key] = []
        subject_map[key].append(str(row["Subject_Lemma"]))
    for key in subject_map:
        subject_map[key] = list(set(subject_map[key]))

    for run_id in sorted(out["Run"].unique()):
        run_df = out[out["Run"] == run_id]

        gram_idx = run_df[run_df["VP_Grammaticality"] == "grammatical"].index.tolist()
        viol_idx = run_df[run_df["VP_Grammaticality"] == "violation"].index.tolist()

        if len(gram_idx) != 24 or len(viol_idx) != 24:
            raise RuntimeError(
                f"Run {run_id}: expected 24 grammatical and 24 violation rows, "
                f"got grammatical={len(gram_idx)}, violation={len(viol_idx)}"
            )

        gram_plural_idx = run_df[
            (run_df["VP_Grammaticality"] == "grammatical") & (run_df["Subject_Number"] == "plural")
        ].index.tolist()
        gram_singular_idx = run_df[
            (run_df["VP_Grammaticality"] == "grammatical") & (run_df["Subject_Number"] == "singular")
        ].index.tolist()

        subj_yes_idx = _sample_exact(gram_plural_idx, 6, rng, f"run {run_id} grammatical subject-state YES")
        subj_no_idx = _sample_exact(gram_singular_idx, 6, rng, f"run {run_id} grammatical subject-state NO")

        subject_idx = set(subj_yes_idx).union(set(subj_no_idx))
        gram_remaining = [idx for idx in gram_idx if idx not in subject_idx]

        pp_yes_gram_idx = _sample_exact(gram_remaining, 6, rng, f"run {run_id} grammatical pp-scene YES")
        pp_no_gram_idx = [idx for idx in gram_remaining if idx not in set(pp_yes_gram_idx)]
        if len(pp_no_gram_idx) != 6:
            raise RuntimeError(
                f"Run {run_id}: expected 6 grammatical pp-scene NO rows, got {len(pp_no_gram_idx)}"
            )

        pp_yes_viol_idx = _sample_exact(viol_idx, 12, rng, f"run {run_id} violation pp-scene YES")
        pp_no_viol_idx = [idx for idx in viol_idx if idx not in set(pp_yes_viol_idx)]
        if len(pp_no_viol_idx) != 12:
            raise RuntimeError(
                f"Run {run_id}: expected 12 violation pp-scene NO rows, got {len(pp_no_viol_idx)}"
            )

        # Generate subject YES probes: actual subject
        for idx in subj_yes_idx:
            row = out.loc[idx]
            probe_text = _subject_probe_text(
                str(row["Subject_Lemma"]),
                str(row["Subject_Gender"]),
                str(row["Subject_Number"]),
                str(row["Verb_Lemma"]),
                str(row["Verb_Phrase"]),
                str(row.get("Probe_Continuation", "")),
            )
            out.at[idx, "Probe"] = probe_text
            out.at[idx, "Probe_Target"] = PROBE_TARGET_SUBJECT
            out.at[idx, "Probe_Correct_Answer"] = "yes"

        # Generate subject NO probes: opposite gender subject
        for idx in subj_no_idx:
            row = out.loc[idx]
            explicit_no_probe = _normalize_question(row.get("Subject_No_Probe", ""))

            if explicit_no_probe:
                probe_text = explicit_no_probe
            else:
                # Backward-compatible fallback if lexicon no_probe is not provided.
                actual_gender = str(row["Subject_Gender"])
                actual_number = str(row["Subject_Number"])
                opposite_gender = _get_opposite_gender_subject(actual_gender)

                key = (actual_number, opposite_gender)
                candidates = subject_map.get(key, [])
                if not candidates:
                    raise RuntimeError(
                        f"No opposite-gender subject found for {key}; cannot generate NO probe"
                    )
                alt_subject = rng.choice(candidates)

                probe_text = _subject_probe_text(
                    alt_subject,
                    opposite_gender,
                    actual_number,
                    str(row["Verb_Lemma"]),
                    str(row["Verb_Phrase"]),
                    str(row.get("Probe_Continuation", "")),
                )
            out.at[idx, "Probe"] = probe_text
            out.at[idx, "Probe_Target"] = PROBE_TARGET_SUBJECT
            out.at[idx, "Probe_Correct_Answer"] = "no"

        # Generate PP YES probes: actual PP2
        for idx in pp_yes_gram_idx + pp_yes_viol_idx:
            row = out.loc[idx]
            probe_text = _pp_probe_text(
                str(row["PP2_Lemma"]),
                str(row["PP2_Gender"]),
                str(row["PP2_Number"]),
                str(row["PP1_Preposition"]),
                str(row["PP1_Lemma"]),
                str(row["PP1_Gender"]),
                str(row["PP1_Number"])
            )
            out.at[idx, "Probe"] = probe_text
            out.at[idx, "Probe_Target"] = PROBE_TARGET_PP
            out.at[idx, "Probe_Correct_Answer"] = "yes"

        # Generate PP NO probes: opposite preposition in PP relation
        for idx in pp_no_gram_idx + pp_no_viol_idx:
            row = out.loc[idx]
            opposite_prep = str(row.get("PP1_Opposite_Preposition", "")).strip()

            if opposite_prep and opposite_prep != str(row["PP1_Preposition"]):
                # Preferred NO probe: same nouns, opposite spatial relation.
                probe_text = _pp_probe_text(
                    str(row["PP2_Lemma"]),
                    str(row["PP2_Gender"]),
                    str(row["PP2_Number"]),
                    opposite_prep,
                    str(row["PP1_Lemma"]),
                    str(row["PP1_Gender"]),
                    str(row["PP1_Number"]),
                )
            else:
                # Robust fallback when opposite mapping is missing in lexicon.
                distractor = _pick_absent_pp_lemma(row, all_pp_lemmas, rng)
                probe_text = _pp_probe_text(
                    distractor,
                    str(row["PP2_Gender"]),
                    str(row["PP2_Number"]),
                    str(row["PP1_Preposition"]),
                    str(row["PP1_Lemma"]),
                    str(row["PP1_Gender"]),
                    str(row["PP1_Number"]),
                )
            out.at[idx, "Probe"] = probe_text
            out.at[idx, "Probe_Target"] = PROBE_TARGET_PP
            out.at[idx, "Probe_Correct_Answer"] = "no"

    return out


def _validate_probe_distribution(selected):
    required_columns = ["Probe", "Probe_Target", "Probe_Correct_Answer"]
    _require_columns(selected, required_columns)

    for run_id in sorted(selected["Run"].unique()):
        run_df = selected[selected["Run"] == run_id]

        gram = run_df[run_df["VP_Grammaticality"] == "grammatical"]
        viol = run_df[run_df["VP_Grammaticality"] == "violation"]

        gram_counts = gram.groupby(["Probe_Target", "Probe_Correct_Answer"]).size().to_dict()
        viol_counts = viol.groupby(["Probe_Target", "Probe_Correct_Answer"]).size().to_dict()

        expected_gram = {
            (PROBE_TARGET_SUBJECT, "yes"): 6,
            (PROBE_TARGET_SUBJECT, "no"): 6,
            (PROBE_TARGET_PP, "yes"): 6,
            (PROBE_TARGET_PP, "no"): 6,
        }
        expected_viol = {
            (PROBE_TARGET_PP, "yes"): 12,
            (PROBE_TARGET_PP, "no"): 12,
        }

        for key, expected in expected_gram.items():
            got = gram_counts.get(key, 0)
            if got != expected:
                raise RuntimeError(
                    f"Run {run_id} grammatical probe quota mismatch for {key}: expected {expected}, got {got}"
                )

        for key, expected in expected_viol.items():
            got = viol_counts.get(key, 0)
            if got != expected:
                raise RuntimeError(
                    f"Run {run_id} violation probe quota mismatch for {key}: expected {expected}, got {got}"
                )

        unexpected_viol_subject = viol[viol["Probe_Target"] == PROBE_TARGET_SUBJECT]
        if len(unexpected_viol_subject) != 0:
            raise RuntimeError(
                f"Run {run_id}: violation rows must not use subject-state probes; got {len(unexpected_viol_subject)}"
            )


def _validate_output(selected, enforce_independence):
    if len(selected) != RUN_COUNT * TRIALS_PER_RUN:
        raise RuntimeError(f"Expected {RUN_COUNT * TRIALS_PER_RUN} trials, got {len(selected)}")

    for run_id in sorted(selected["Run"].unique()):
        run_df = selected[selected["Run"] == run_id]
        if len(run_df) != TRIALS_PER_RUN:
            raise RuntimeError(f"Run {run_id}: expected {TRIALS_PER_RUN} trials, got {len(run_df)}")

        counts = run_df.groupby("Structure").size().to_dict()
        for structure in STRUCTURES:
            if counts.get(structure, 0) != 16:
                raise RuntimeError(f"Run {run_id}: structure={structure} expected 16, got {counts.get(structure, 0)}")

        counts = run_df.groupby(["Structure", "VP_Grammaticality"]).size().to_dict()
        for structure in STRUCTURES:
            for grammaticality in GRAMMATICALITIES:
                key = (structure, grammaticality)
                if counts.get(key, 0) != 8:
                    raise RuntimeError(f"Run {run_id}: {key} expected 8, got {counts.get(key, 0)}")

        counts = run_df.groupby(["Structure", "VP_Grammaticality", "Subject_Number"]).size().to_dict()
        for structure in STRUCTURES:
            for grammaticality in GRAMMATICALITIES:
                for subject_number in NUMBERS:
                    key = (structure, grammaticality, subject_number)
                    if counts.get(key, 0) != 4:
                        raise RuntimeError(f"Run {run_id}: {key} expected 4, got {counts.get(key, 0)}")

        counts = run_df.groupby(["Structure", "VP_Grammaticality", "Subject_Number", "PP1_Number"]).size().to_dict()
        for structure in STRUCTURES:
            for grammaticality in GRAMMATICALITIES:
                for subject_number in NUMBERS:
                    for pp1_number in NUMBERS:
                        key = (structure, grammaticality, subject_number, pp1_number)
                        if counts.get(key, 0) != 2:
                            raise RuntimeError(f"Run {run_id}: {key} expected 2, got {counts.get(key, 0)}")

        counts = run_df.groupby(KEY_COLUMNS).size().to_dict()
        for key in itertools.product(STRUCTURES, GRAMMATICALITIES, NUMBERS, NUMBERS, NUMBERS):
            if counts.get(key, 0) != 1:
                raise RuntimeError(f"Run {run_id}: {key} expected 1, got {counts.get(key, 0)}")

        if enforce_independence:
            counts = run_df.groupby(["Structure", "VP_Grammaticality", "Subject_Number", "Subject_Gender"]).size().to_dict()
            for key in itertools.product(STRUCTURES, GRAMMATICALITIES, NUMBERS, GENDERS):
                if counts.get(key, 0) != 2:
                    raise RuntimeError(f"Run {run_id}: {key} expected 2, got {counts.get(key, 0)}")


def main():
    args = parse_args()
    rng = random.Random(args.seed)
    enforce_independence = not args.allow_number_gender_dependence

    source = pd.read_csv(args.input)
    source = _prepare_dataframe(source)
    _validate_number_gender_feasibility(source, enforce_independence)

    cells = _cell_space()
    pools = _build_pools(source, cells)
    _validate_pool_capacity(pools, RUN_COUNT)
    rarity = _token_rarity(source)

    best = None
    interrupted = False

    try:
        for attempt in range(1, args.attempts + 1):
            attempt_rng = random.Random(rng.randint(0, 10**12))
            run_assignments = _construct_solution(
                source,
                pools,
                cells,
                rarity,
                attempt_rng,
                sample_size=args.candidate_sample_size,
                enforce_independence=enforce_independence,
            )
            if run_assignments is None:
                continue

            selected = _materialize(source, run_assignments)
            score, diversity, penalty = _score_solution(selected, source)

            if best is None or score > best["score"]:
                best = {
                    "selected": selected,
                    "score": score,
                    "diversity": diversity,
                    "penalty": penalty,
                    "attempt": attempt,
                }

            if attempt % 20 == 0:
                print(f"Attempt {attempt}/{args.attempts} complete", file=sys.stderr)
    except KeyboardInterrupt:
        interrupted = True
        print("Interrupted: writing best solution found so far.", file=sys.stderr)

    if best is None:
        raise RuntimeError("Failed to build a feasible subsample. Increase --attempts and retry.")

    selected = best["selected"].copy()
    selected = _assign_probes(selected, random.Random(args.seed + 7919))
    _validate_output(selected, enforce_independence)
    _validate_probe_distribution(selected)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(args.output, index=False)

    print(f"Saved subsample to {args.output}")
    if interrupted:
        print("Run ended early due to interrupt; output reflects best-so-far solution.")
    print(f"Best attempt: {best['attempt']}/{args.attempts}")
    print(f"Objective score: {best['score']:.4f}")
    print(f"Vocabulary coverage score: {best['diversity']:.4f}")
    print(f"Balance penalty score: {best['penalty']:.4f}")
    print(f"Number-gender independence enforced: {enforce_independence}")

    print("Unique vocabulary in selected set:")
    print(f"  subjects: {selected['Subject_Lemma'].nunique()}")
    print(f"  verbs: {selected['Verb_Lemma'].nunique()}")
    noun_unique = len(set(selected["PP1_Lemma"]).union(set(selected["PP2_Lemma"])))
    prep_unique = len(set(selected["PP1_Preposition"]).union(set(selected["PP2_Preposition"])))
    print(f"  nouns (PP1/PP2): {noun_unique}")
    print(f"  prepositions (PP1/PP2): {prep_unique}")


if __name__ == "__main__":
    main()
