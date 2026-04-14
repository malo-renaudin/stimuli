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


_FIELD_HINTS_BY_FRAME = {
    "education": ["education"],
    "workplace": ["workplace"],
    "transport": ["transport"],
    "culture": ["culture"],
}

_OBJECT_HINTS = {
    "education": {"un examen", "un test", "un exercice", "un article", "un roman"},
    "workplace": {"un dossier", "un email", "un projet", "une commande"},
    "transport": {"un bus", "un taxi", "un train", "un trajet", "une option"},
    "culture": {"un roman", "un article", "un café", "un jus"},
}


def _object_naturalness_score(frame, verb, object_dp):
    """Heuristic score used to prefer plausible verb-object choices in each frame."""
    score = 1
    frame_id = frame["id"]
    verb_lemma = verb["lemma"]

    # Favor earlier, curated objects in each verb list.
    frame_choices = frame.get("objects_by_verb", {}).get(verb_lemma, [])
    if object_dp in frame_choices:
        score += max(0, len(frame_choices) - frame_choices.index(object_dp))
    else:
        global_choices = OBJECTS_BY_VERB.get(verb_lemma, [])
        if object_dp in global_choices:
            score += max(0, len(global_choices) - global_choices.index(object_dp))

    # Add a small semantic bonus when object and frame domain match.
    for hint, tags in _FIELD_HINTS_BY_FRAME.items():
        if hint in frame_id and object_dp in _OBJECT_HINTS[tags[0]]:
            score += 3
            break

    return score


def pick_object_for_frame(frame, verb, rng):
    frame_choices = frame.get("objects_by_verb", {}).get(verb["lemma"])
    if not frame_choices:
        frame_choices = OBJECTS_BY_VERB.get(verb["lemma"])
    if not frame_choices:
        raise RuntimeError(f"No compatible objects configured for verb: {verb['lemma']}")

    scored = [(obj, _object_naturalness_score(frame, verb, obj)) for obj in frame_choices]
    top_score = max(score for _, score in scored)
    top_objects = [obj for obj, score in scored if score == top_score]
    # Keep deterministic variation across seeds while rejecting low-plausibility choices.
    return rng.choice(top_objects)


def build_lemma_index(items):
    return {item["singular"]: item for item in items}


def _split_lemmas_by_number(lemmas):
    """Create disjoint singular/plural lemma inventories by deterministic split."""
    singular = set(lemmas[::2])
    plural = set(lemmas[1::2])
    return {"singular": singular, "plural": plural}


_SUBJECT_LEMMAS_BY_NUMBER = {
    "m": _split_lemmas_by_number([noun["singular"] for noun in SUBJECT_NOUNS_MASC]),
    "f": _split_lemmas_by_number([noun["singular"] for noun in SUBJECT_NOUNS_FEM]),
}

_PP_LEMMAS_BY_NUMBER = {
    "m": _split_lemmas_by_number([noun["singular"] for noun in PP_NOUNS_MASC]),
    "f": _split_lemmas_by_number([noun["singular"] for noun in PP_NOUNS_FEM]),
}

_PLURAL_DISFAVORED_PP_LEMMAS = {"institut", "établissement", "entrée", "office"}


def _frame_subject_lemmas(frame, gender, number, number_specific_lexicons):
    lemmas = list(frame["subject"][gender])
    if not number_specific_lexicons:
        return lemmas
    allowed = _SUBJECT_LEMMAS_BY_NUMBER[gender][number]
    filtered = [lemma for lemma in lemmas if lemma in allowed]
    return filtered if filtered else lemmas


def _frame_slot_options(frame, slot_key, gender, number, number_specific_lexicons):
    options = list(frame[slot_key][gender])
    if not number_specific_lexicons:
        return options
    allowed = _PP_LEMMAS_BY_NUMBER[gender][number]
    filtered = [option for option in options if option["lemma"] in allowed]
    if number == "plural":
        preferred = [option for option in filtered if option["lemma"] not in _PLURAL_DISFAVORED_PP_LEMMAS]
        if preferred:
            return preferred
    return filtered if filtered else options


def candidate_verbs_for_frame(frame, verb_type):
    allowed = set(frame["lexical_verbs"])
    if verb_type == "copula":
        return [COPULA]
    if verb_type == "lexical_2":
        return [verb for verb in SECOND_GROUP_VERBS if verb["lemma"] in allowed]
    return [verb for verb in THIRD_GROUP_VERBS if verb["lemma"] in allowed]


def frame_slot_candidates(frame, slot_key, gender, noun_index, preposition, number, number_specific_lexicons):
    candidates = []
    for option in _frame_slot_options(frame, slot_key, gender, number, number_specific_lexicons):
        noun = noun_index[option["lemma"]]
        allowed_prepositions = set(option["prepositions"])
        allowed_prepositions &= set(compatible_prepositions(noun, number))
        if preposition in allowed_prepositions:
            candidates.append(noun)
    return candidates


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
    number_specific_lexicons,
    rng,
):
    pp1_index = pp_index_m if pp1_gender == "m" else pp_index_f
    pp2_index = pp_index_m if pp2_gender == "m" else pp_index_f

    pp1_pool = frame_slot_candidates(
        frame,
        "pp1_options",
        pp1_gender,
        pp1_index,
        pp1_preposition,
        pp1_number,
        number_specific_lexicons,
    )
    pp2_pool = frame_slot_candidates(
        frame,
        "pp2_options",
        pp2_gender,
        pp2_index,
        pp2_preposition,
        pp2_number,
        number_specific_lexicons,
    )

    if not pp1_pool or not pp2_pool:
        return None, None

    pp1 = rng.choice(pp1_pool)
    pp2_candidates = [candidate for candidate in pp2_pool if candidate["singular"] != pp1["singular"]]
    if not pp2_candidates:
        return None, None
    return pp1, rng.choice(pp2_candidates)


def generate_lexical_combos_for_run(run_id, rng, number_specific_lexicons=False):
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
            subject_number = spec["pattern"]["subject_number"]
            pp1_number = spec["pattern"]["pp1_number"]
            pp2_number = spec["pattern"]["pp2_number"]

            subject_gender = seq_subject[idx]
            pp1_gender = seq_pp1[idx]
            pp2_gender = seq_pp2[idx]

            candidates = []
            for frame in SCENARIO_FRAMES:
                subject_lemmas = _frame_subject_lemmas(
                    frame,
                    subject_gender,
                    subject_number,
                    number_specific_lexicons,
                )
                subject_pool = [
                    subject_index_m[l] if subject_gender == "m" else subject_index_f[l]
                    for l in subject_lemmas
                ]
                if not subject_pool:
                    continue

                verb_pool = candidate_verbs_for_frame(frame, verb_type)
                if not verb_pool:
                    continue

                pair_candidates = frame.get("preposition_pairs")
                if not pair_candidates:
                    continue

                frame_candidates = []
                pair_candidates = list(pair_candidates)
                rng.shuffle(pair_candidates)
                for pp1_preposition, pp2_preposition in pair_candidates:
                    if pp1_preposition == "chez" and pp2_preposition == "chez":
                        continue
                    if pp1_preposition == "chez" and pp2_preposition == "dans":
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
                        number_specific_lexicons,
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
            if pp1_preposition == "chez" and pp2_preposition == "dans":
                break

            object_dp = None
            if verb["type"] != "copula":
                object_dp = pick_object_for_frame(frame, verb, rng)

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


# Natural French PP ordering: enclosure/container prepositions (dans, chez) naturally
# precede deictic (devant, derrière) and proximal/relational ones (près de, loin de).
# Lower rank = preferred earlier in the sentence.
_PP_ORDER_RANK = {
    "dans": 0,
    "chez": 0,
    "vers": 1,
    "devant": 2,
    "derrière": 2,
    "à gauche de": 3,
    "à droite de": 3,
    "en face de": 3,
    "près de": 4,
    "à côté de": 4,
    "loin de": 5,
}


def _should_swap_pp_order(prep1, prep2):
    """Return True when pp1 should appear after pp2 for natural French ordering."""
    return _PP_ORDER_RANK.get(prep1, 3) > _PP_ORDER_RANK.get(prep2, 3)


def _render_sentence(structure, subject_dp, pp1_str, pp2_str, verb_form, tail_word):
    if structure == "long":
        return f"{subject_dp} {pp1_str} {pp2_str} {verb_form} {tail_word}."
    if structure == "medium":
        return f"{pp1_str.capitalize()}, {lower_initial(subject_dp)} {pp2_str} {verb_form} {tail_word}."
    return f"{pp1_str.capitalize()}, {pp2_str}, {lower_initial(subject_dp)} {verb_form} {tail_word}."


def _pp_order_score(first_prep, second_prep):
    """Higher is better for natural PP order under fixed templates."""
    first_rank = _PP_ORDER_RANK.get(first_prep, 3)
    second_rank = _PP_ORDER_RANK.get(second_prep, 3)

    score = 0
    if first_rank < second_rank:
        score += 4
    elif first_rank == second_rank:
        score += 1
    else:
        score -= 4

    if first_prep in {"dans", "chez"} and second_prep not in {"dans", "chez"}:
        score += 2
    if second_prep in {"près de", "à côté de", "loin de"}:
        score += 1
    if first_prep == second_prep:
        score -= 2

    return score


def make_sentence(combo, structure):
    subject_dp = make_subject_dp(combo["subject"], combo["subject_number"])
    pp1_base = make_pp(combo["pp1_preposition"], combo["pp1"], combo["pp1_number"])
    pp2_base = make_pp(combo["pp2_preposition"], combo["pp2"], combo["pp2_number"])

    verb_form = expected_verb_form(combo["verb"], combo["subject_number"], combo["grammaticality"])
    expected_verb = combo["verb"]["singular"] if combo["subject_number"] == "singular" else combo["verb"]["plural"]

    if combo["verb"]["type"] == "copula":
        tail_word = adjective_form(combo["adjective"], combo["subject"]["gender"], combo["subject_number"])
    else:
        tail_word = combo["object_dp"]

    # Rerank only two fixed-template candidates: original PP order vs swapped order.
    # This keeps experimental templates unchanged while selecting the more natural surface form.
    keep_order_sentence = _render_sentence(structure, subject_dp, pp1_base, pp2_base, verb_form, tail_word)
    swap_order_sentence = _render_sentence(structure, subject_dp, pp2_base, pp1_base, verb_form, tail_word)

    keep_score = _pp_order_score(combo["pp1_preposition"], combo["pp2_preposition"])
    swap_score = _pp_order_score(combo["pp2_preposition"], combo["pp1_preposition"])

    # Keep the old deterministic behavior as an additional tie-break preference.
    if _should_swap_pp_order(combo["pp1_preposition"], combo["pp2_preposition"]):
        swap_score += 1

    sentence = swap_order_sentence if swap_score > keep_score else keep_order_sentence

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


def generate_trials(seed, use_number_specific_lexicons=False):
    rng = random.Random(seed)
    all_trials = []

    for run_id in range(1, RUN_COUNT + 1):
        combos = generate_lexical_combos_for_run(
            run_id,
            rng,
            number_specific_lexicons=use_number_specific_lexicons,
        )
        run_trials = []
        for combo in combos:
            for structure in STRUCTURES:
                run_trials.append(make_sentence(combo, structure))
        rng.shuffle(run_trials)
        all_trials.extend(run_trials)

    return all_trials
