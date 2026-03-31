import random

from fr_experiment.config import LEXICAL_COMBOS_PER_RUN, RUN_COUNT, STRUCTURES
from fr_experiment.language import (
    adjective_form,
    compatible_prepositions,
    expected_verb_form,
    lower_initial,
    make_pp,
    make_subject_dp,
)
from fr_experiment.lexicon import (
    ADJECTIVES,
    COPULA,
    OBJECTS_BY_VERB,
    PP_NOUNS_FEM,
    PP_NOUNS_MASC,
    SCENARIO_FRAMES,
    SECOND_GROUP_VERBS,
    SUBJECT_NOUNS_FEM,
    SUBJECT_NOUNS_MASC,
    THIRD_GROUP_VERBS,
)


def all_number_patterns():
    patterns = []
    for subject_number in ["singular", "plural"]:
        for pp1_number in ["singular", "plural"]:
            for pp2_number in ["singular", "plural"]:
                patterns.append(
                    {
                        "subject_number": subject_number,
                        "pp1_number": pp1_number,
                        "pp2_number": pp2_number,
                    }
                )
    return patterns


def sample_nouns_by_gender(sequence, pool_masc, pool_fem, rng):
    need_m = sequence.count("m")
    need_f = sequence.count("f")
    if need_m > len(pool_masc) or need_f > len(pool_fem):
        raise RuntimeError("Not enough noun inventory to satisfy gender constraints.")

    sampled_m = rng.sample(pool_masc, need_m)
    sampled_f = rng.sample(pool_fem, need_f)

    picked = []
    for gender in sequence:
        if gender == "m":
            picked.append(sampled_m.pop())
        else:
            picked.append(sampled_f.pop())
    return picked


def pick_object_for_verb(verb, rng):
    choices = OBJECTS_BY_VERB.get(verb["lemma"])
    if not choices:
        raise RuntimeError(f"No compatible objects configured for verb: {verb['lemma']}")
    return rng.choice(choices)


def build_lemma_index(items):
    return {item["singular"]: item for item in items}


def candidate_verbs_for_frame(frame, verb_type):
    allowed = set(frame["lexical_verbs"])
    if verb_type == "copula":
        return [COPULA]
    if verb_type == "lexical_2":
        return [verb for verb in SECOND_GROUP_VERBS if verb["lemma"] in allowed]
    return [verb for verb in THIRD_GROUP_VERBS if verb["lemma"] in allowed]


def pick_from_lemma_pool(lemmas, gender, index_m, index_f, rng):
    pool = [index_m[l] if gender == "m" else index_f[l] for l in lemmas]
    if not pool:
        return None
    return rng.choice(pool)


def pick_distinct_frame_places(frame, pp1_gender, pp2_gender, pp_index_m, pp_index_f, rng):
    pp1 = pick_from_lemma_pool(frame["pp1"][pp1_gender], pp1_gender, pp_index_m, pp_index_f, rng)
    pp2_pool = [pp_index_m[l] if pp2_gender == "m" else pp_index_f[l] for l in frame["pp2"][pp2_gender]]
    if pp1 is None or not pp2_pool:
        return None, None
    pp2_candidates = [candidate for candidate in pp2_pool if candidate["singular"] != pp1["singular"]]
    if not pp2_candidates:
        return None, None
    return pp1, rng.choice(pp2_candidates)


def pick_distinct_frame_places_with_prepositions(
    frame,
    pp1_gender,
    pp2_gender,
    pp_index_m,
    pp_index_f,
    pp1_preposition,
    pp2_preposition,
    pp1_number,
    pp2_number,
    rng,
):
    if pp1_gender == "m":
        pp1_pool = [pp_index_m[l] for l in frame["pp1"][pp1_gender]]
    else:
        pp1_pool = [pp_index_f[l] for l in frame["pp1"][pp1_gender]]

    if pp2_gender == "m":
        pp2_pool = [pp_index_m[l] for l in frame["pp2"][pp2_gender]]
    else:
        pp2_pool = [pp_index_f[l] for l in frame["pp2"][pp2_gender]]

    pp1_pool = [
        noun
        for noun in pp1_pool
        if pp1_preposition in compatible_prepositions(noun, pp1_number)
    ]
    pp2_pool = [
        noun
        for noun in pp2_pool
        if pp2_preposition in compatible_prepositions(noun, pp2_number)
    ]

    if not pp1_pool or not pp2_pool:
        return None, None

    pp1 = rng.choice(pp1_pool)
    pp2_candidates = [candidate for candidate in pp2_pool if candidate["singular"] != pp1["singular"]]
    if not pp2_candidates:
        return None, None
    return pp1, rng.choice(pp2_candidates)


def pick_preposition_pair(frame, rng):
    preposition_pairs = frame.get("preposition_pairs")
    if preposition_pairs:
        return rng.choice(preposition_pairs)

    pp1_preposition = rng.choice(frame["pp1_prepositions"])
    pp2_candidates = [prep for prep in frame["pp2_prepositions"] if prep != pp1_preposition]
    pp2_preposition = rng.choice(pp2_candidates or frame["pp2_prepositions"])
    return pp1_preposition, pp2_preposition


def generate_lexical_combos_for_run(run_id, rng):
    subject_index_m = build_lemma_index(SUBJECT_NOUNS_MASC)
    subject_index_f = build_lemma_index(SUBJECT_NOUNS_FEM)
    pp_index_m = build_lemma_index(PP_NOUNS_MASC)
    pp_index_f = build_lemma_index(PP_NOUNS_FEM)

    patterns = all_number_patterns()
    rng.shuffle(patterns)

    specs = []
    for pattern in patterns:
        specs.append({"pattern": pattern, "grammaticality": "grammatical"})
        specs.append({"pattern": pattern, "grammaticality": "violation"})
    rng.shuffle(specs)

    seq_subject = ["m"] * (LEXICAL_COMBOS_PER_RUN // 2) + ["f"] * (LEXICAL_COMBOS_PER_RUN // 2)
    seq_pp1 = ["m"] * (LEXICAL_COMBOS_PER_RUN // 2) + ["f"] * (LEXICAL_COMBOS_PER_RUN // 2)
    seq_pp2 = ["m"] * (LEXICAL_COMBOS_PER_RUN // 2) + ["f"] * (LEXICAL_COMBOS_PER_RUN // 2)
    rng.shuffle(seq_subject)
    rng.shuffle(seq_pp1)
    rng.shuffle(seq_pp2)

    # 50/50 copula vs lexical inside each run, with lexical split 2nd/3rd group.
    verb_type_plan = ["copula"] * 8 + ["lexical_2"] * 4 + ["lexical_3"] * 4
    rng.shuffle(verb_type_plan)

    for _ in range(2000):
        combos = []
        seen = set()

        for idx, spec in enumerate(specs):
            verb_type = verb_type_plan[idx]
            pp1_number = spec["pattern"]["pp1_number"]
            pp2_number = spec["pattern"]["pp2_number"]

            subject_gender = seq_subject[idx]
            pp1_gender = seq_pp1[idx]
            pp2_gender = seq_pp2[idx]

            candidates = []
            for frame in SCENARIO_FRAMES:
                subject_pool = [
                    subject_index_m[l] if subject_gender == "m" else subject_index_f[l]
                    for l in frame["subject"][subject_gender]
                ]
                if not subject_pool:
                    continue

                verb_pool = candidate_verbs_for_frame(frame, verb_type)
                if not verb_pool:
                    continue

                pair_candidates = frame.get("preposition_pairs")
                if not pair_candidates:
                    pair_candidates = [
                        (prep1, prep2)
                        for prep1 in frame["pp1_prepositions"]
                        for prep2 in frame["pp2_prepositions"]
                    ]

                frame_candidates = []
                rng.shuffle(pair_candidates)
                for pp1_preposition, pp2_preposition in pair_candidates:
                    if pp1_preposition == "chez" and pp2_preposition == "chez":
                        continue

                    pp1, pp2 = pick_distinct_frame_places_with_prepositions(
                        frame,
                        pp1_gender,
                        pp2_gender,
                        pp_index_m,
                        pp_index_f,
                        pp1_preposition,
                        pp2_preposition,
                        pp1_number,
                        pp2_number,
                        rng,
                    )
                    if pp1 is None or pp2 is None:
                        continue

                    frame_candidates.append((frame, subject_pool, verb_pool, pp1, pp2, pp1_preposition, pp2_preposition))

                candidates.extend(frame_candidates)

            if not candidates:
                break

            frame, subject_pool, verb_pool, pp1, pp2, pp1_preposition, pp2_preposition = rng.choice(candidates)
            subject = rng.choice(subject_pool)
            verb = rng.choice(verb_pool)

            if pp1_preposition == "chez" and pp2_preposition == "chez":
                break

            object_dp = None
            if verb["type"] != "copula":
                object_dp = pick_object_for_verb(verb, rng)

            if len({subject["singular"], pp1["singular"], pp2["singular"]}) < 3:
                break

            key = (subject["singular"], pp1["singular"], pp2["singular"], verb["lemma"])
            if key in seen:
                break
            seen.add(key)

            combos.append(
                {
                    "run_id": run_id,
                    "lexical_combo_id": f"R{run_id}_C{idx + 1:02d}",
                    "subject": subject,
                    "pp1": pp1,
                    "pp2": pp2,
                    "verb": verb,
                    "adjective": rng.choice(ADJECTIVES),
                    "object_dp": object_dp,
                    "grammaticality": spec["grammaticality"],
                    "subject_number": spec["pattern"]["subject_number"],
                    "pp1_number": pp1_number,
                    "pp2_number": pp2_number,
                    "pp1_preposition": pp1_preposition,
                    "pp2_preposition": pp2_preposition,
                }
            )

        if len(combos) == LEXICAL_COMBOS_PER_RUN:
            return combos

    raise RuntimeError(f"Unable to build lexical combos for run {run_id}.")


def is_static_preposition(prep):
    """Prepositions that indicate location (statique)."""
    return prep in {"dans", "à", "vers", "chez"}


def make_sentence(combo, structure):
    subject_dp = make_subject_dp(combo["subject"], combo["subject_number"])
    pp1 = make_pp(combo["pp1_preposition"], combo["pp1"], combo["pp1_number"])
    pp2 = make_pp(combo["pp2_preposition"], combo["pp2"], combo["pp2_number"])

    verb_form = expected_verb_form(combo["verb"], combo["subject_number"], combo["grammaticality"])
    expected_verb = combo["verb"]["singular"] if combo["subject_number"] == "singular" else combo["verb"]["plural"]

    if combo["verb"]["type"] == "copula":
        tail_word = adjective_form(combo["adjective"], combo["subject"]["gender"], combo["subject_number"])
    else:
        tail_word = combo["object_dp"]

    if structure == "long":
        # For long structure, prefer static prepositions (dans, à, etc.) before relational ones (devant, à côté de, etc.)
        pp1_is_static = is_static_preposition(combo["pp1_preposition"])
        pp2_is_static = is_static_preposition(combo["pp2_preposition"])
        
        # If pp2 is static and pp1 is relational, swap them for more natural word order
        if pp2_is_static and not pp1_is_static:
            pp1, pp2 = pp2, pp1
        
        sentence = f"{subject_dp} {pp1} {pp2} {verb_form} {tail_word}."
    elif structure == "medium":
        sentence = f"{pp1.capitalize()}, {lower_initial(subject_dp)} {pp2} {verb_form} {tail_word}."
    else:
        sentence = f"{pp1.capitalize()}, {pp2}, {lower_initial(subject_dp)} {verb_form} {tail_word}."

    return {
        "Run_ID": combo["run_id"],
        "Lexical_Combo_ID": combo["lexical_combo_id"],
        "Condition_Code": (
            f"R{combo['run_id']}_"
            f"{combo['grammaticality']}_"
            f"S{combo['subject_number'][0].upper()}"
            f"P1{combo['pp1_number'][0].upper()}"
            f"P2{combo['pp2_number'][0].upper()}_"
            f"{structure}"
        ),
        "Structure": structure,
        "Grammaticality": combo["grammaticality"],
        "Sentence_String": sentence,
        "Is_Filler": False,
        "Expected_Verb": expected_verb,
        "Verb_Form": verb_form,
        "Verb_Lemma": combo["verb"]["lemma"],
        "Verb_Type": combo["verb"]["type"],
        "Subject_Lemma": combo["subject"]["singular"],
        "Subject_Gender": combo["subject"]["gender"],
        "Subject_Number": combo["subject_number"],
        "PP1_Lemma": combo["pp1"]["singular"],
        "PP1_Gender": combo["pp1"]["gender"],
        "PP1_Number": combo["pp1_number"],
        "PP1_Preposition": combo["pp1_preposition"],
        "PP2_Lemma": combo["pp2"]["singular"],
        "PP2_Gender": combo["pp2"]["gender"],
        "PP2_Number": combo["pp2_number"],
        "PP2_Preposition": combo["pp2_preposition"],
        "Delayed_Repetition": True,
        "Delay_ms": None,
        "Go_Beep": True,
        "Audio_Normalization_Note": "Normalize pre-verb pause and verb duration across conditions.",
    }


def generate_trials(seed):
    rng = random.Random(seed)
    all_trials = []

    for run_id in range(1, RUN_COUNT + 1):
        combos = generate_lexical_combos_for_run(run_id, rng)
        run_trials = []
        for combo in combos:
            for structure in STRUCTURES:
                run_trials.append(make_sentence(combo, structure))
        rng.shuffle(run_trials)
        all_trials.extend(run_trials)

    return all_trials
