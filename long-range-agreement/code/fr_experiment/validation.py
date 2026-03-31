from fr_experiment.config import DELAY_OPTIONS_MS, LEXICAL_COMBOS_PER_RUN, PREPOSITIONS, RUN_COUNT, STRUCTURES
from fr_experiment.language import starts_with_vowel


def assign_delays(trials, rng):
    for trial in trials:
        trial["Delay_ms"] = rng.choice(DELAY_OPTIONS_MS)


def validate_trials(all_trials):
    run_ids = sorted({row["Run_ID"] for row in all_trials})
    if len(run_ids) != RUN_COUNT:
        raise RuntimeError(f"Expected {RUN_COUNT} runs, got {len(run_ids)}")

    for run_id in run_ids:
        run_trials = [row for row in all_trials if row["Run_ID"] == run_id]
        if len(run_trials) != LEXICAL_COMBOS_PER_RUN * len(STRUCTURES):
            raise RuntimeError(f"Run {run_id}: expected 48 trials, got {len(run_trials)}")

        short_rows = [row for row in run_trials if row["Structure"] == "short"]
        if len(short_rows) != LEXICAL_COMBOS_PER_RUN:
            raise RuntimeError(f"Run {run_id}: expected 16 lexical combos, got {len(short_rows)}")

        combo_keys = {
            (row["Subject_Lemma"], row["PP1_Lemma"], row["PP2_Lemma"], row["Verb_Lemma"])
            for row in short_rows
        }
        if len(combo_keys) != LEXICAL_COMBOS_PER_RUN:
            raise RuntimeError(f"Run {run_id}: lexical combos are not unique")

        pattern_keys = {
            (row["Subject_Number"], row["PP1_Number"], row["PP2_Number"], row["Grammaticality"])
            for row in short_rows
        }
        if len(pattern_keys) != LEXICAL_COMBOS_PER_RUN:
            raise RuntimeError(f"Run {run_id}: pattern x grammaticality coverage is incomplete")

        copula_count = sum(1 for row in short_rows if row["Verb_Type"] == "copula")
        lexical_count = sum(1 for row in short_rows if row["Verb_Type"] in {"lexical_2", "lexical_3"})
        if copula_count != 8 or lexical_count != 8:
            raise RuntimeError(f"Run {run_id}: expected 8 copula and 8 lexical combos")

        second_count = sum(1 for row in short_rows if row["Verb_Type"] == "lexical_2")
        third_count = sum(1 for row in short_rows if row["Verb_Type"] == "lexical_3")
        if second_count != 4 or third_count != 4:
            raise RuntimeError(f"Run {run_id}: expected 4 lexical_2 and 4 lexical_3 combos")

        noun_m = 0
        noun_f = 0
        for row in short_rows:
            for gender in [row["Subject_Gender"], row["PP1_Gender"], row["PP2_Gender"]]:
                if gender == "m":
                    noun_m += 1
                else:
                    noun_f += 1
        if noun_m != noun_f:
            raise RuntimeError(f"Run {run_id}: noun gender imbalance ({noun_m} m vs {noun_f} f)")

    for row in all_trials:
        if row["PP1_Preposition"] not in PREPOSITIONS or row["PP2_Preposition"] not in PREPOSITIONS:
            raise RuntimeError("Detected invalid one-word preposition.")

        for noun in [row["Subject_Lemma"], row["PP1_Lemma"], row["PP2_Lemma"]]:
            if not starts_with_vowel(noun):
                raise RuntimeError(f"Noun does not start with a vowel: {noun}")

        if row["Verb_Lemma"] == "voir":
            raise RuntimeError("Verb 'voir' is forbidden due to singular/plural homophony.")

        if row["Expected_Verb"] == row["Verb_Form"] and row["Grammaticality"] == "violation":
            raise RuntimeError("Violation trial has matching verb agreement.")

        tail = row["Sentence_String"].split(f" {row['Verb_Form']} ", maxsplit=1)[1]
        tokens = tail.rstrip(".").split()
        if row["Verb_Type"] == "copula":
            if len(tokens) != 1:
                raise RuntimeError(f"Copula sentence must have one word after verb: {row['Sentence_String']}")
        else:
            if len(tokens) != 2:
                raise RuntimeError(f"Lexical sentence must have two words after verb (COD): {row['Sentence_String']}")
