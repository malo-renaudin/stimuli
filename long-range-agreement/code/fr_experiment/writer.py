import csv


def write_run_list(trials, output_path, delimiter):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "Trial_ID",
                "Run_ID",
                "Lexical_Combo_ID",
                "Condition_Code",
                "Structure",
                "Grammaticality",
                "Sentence_String",
                "Is_Filler",
                "Expected_Verb",
                "Verb_Form",
                "Verb_Lemma",
                "Verb_Type",
                "Subject_Lemma",
                "Subject_Gender",
                "Subject_Number",
                "PP1_Lemma",
                "PP1_Gender",
                "PP1_Number",
                "PP1_Preposition",
                "PP2_Lemma",
                "PP2_Gender",
                "PP2_Number",
                "PP2_Preposition",
                "Delayed_Repetition",
                "Delay_ms",
                "Go_Beep",
                "Audio_Normalization_Note",
            ],
            delimiter=delimiter,
        )
        writer.writeheader()
        for index, trial in enumerate(trials, start=1):
            row = dict(trial)
            row["Trial_ID"] = f"T{index:03d}"
            writer.writerow(row)
