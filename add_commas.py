import re

import pandas as pd
#add commas after each noun in the PPs such that for all distances there is the same number of commas.
#this is to keep the length of audio stimuli constant across trials

INPUT_CSV = "run_lists/rerun_2026-04-27_opposite_probe_work_v4/v2_subsampled_runs.csv"
OUTPUT_CSV = "run_lists/rerun_2026-04-27_opposite_probe_work_v4/v2_subsampled_runs_commas.csv"

stim = pd.read_csv(INPUT_CSV)

def add_commas_after_lemmas(sentence: str, pp1_lemma: str, pp2_lemma: str) -> str:
    for lemma in [pp1_lemma, pp2_lemma]:
        if lemma:
            # Add a comma after the lemma if not already followed by punctuation
            sentence = re.sub(rf"({re.escape(lemma)})(?![,;:])", r"\1,", sentence, count=1)
    return sentence

stim["Sentence_String"] = stim.apply(
    lambda row: add_commas_after_lemmas(
        str(row["Sentence_String"]),
        str(row["PP1_Lemma"]),
        str(row["PP2_Lemma"]),
    ),
    axis=1,
)

stim.to_csv(OUTPUT_CSV, index=False)
print(f"Saved updated file: {OUTPUT_CSV}")
