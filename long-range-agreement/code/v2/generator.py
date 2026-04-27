import csv
import random

from v2.lexicon import build_lexicon

from wordfreq import zipf_frequency


def _lower_initial(text):
    return text[:1].lower() + text[1:]


def _render(structure, row):
    if structure == "short":
        return f"{row['subject']} {row['pp1']} {row['pp2']} {row['verb_phrase']}."
    if structure == "medium":
        return f"{row['pp1'].capitalize()}, {_lower_initial(row['subject'])} {row['pp2']} {row['verb_phrase']}."
    return f"{row['pp1'].capitalize()}, {row['pp2']}, {_lower_initial(row['subject'])} {row['verb_phrase']}."


def _vp_form(row, grammaticality):
    vp = row["verb_phrase"]
    if grammaticality == "grammatical":
        return vp
    explicit_violation = row.get("verb_phrase_violation")
    if explicit_violation:
        return explicit_violation
    raise RuntimeError(
        "Missing 'verb_phrase_violation' in lexicon row for ungrammatical stimulus generation."
    )


def _verb_head(verb_phrase):
    return verb_phrase.split(maxsplit=1)[0]


def _zipf_fr(text):
    return round(zipf_frequency(text.lower(), "fr"), 3)


def _letter_count(text):
    return sum(1 for char in text if char.isalpha())


def _noun_congruency(subject_number, pp1_number, pp2_number):
    number_code = {"singular": "S", "plural": "P"}
    try:
        return (
            f"{number_code[subject_number]}"
            f"{number_code[pp1_number]}"
            f"{number_code[pp2_number]}"
        )
    except KeyError as exc:
        raise RuntimeError(f"Unexpected number label in row: {exc.args[0]}") from exc


def _congruency_locus(structure, subject_number, pp1_number, pp2_number):
    if structure == "medium":
        pre_subject = "C" if pp1_number == subject_number else "I"
        between_subject_verb = "C" if pp2_number == subject_number else "I"
        return f"pre{pre_subject}_between{between_subject_verb}"
    if structure == "long":
        return "auto_long"
    return "auto_short"


def generate_stimuli(seed=13, total_prep_words=5, structures=("short", "medium", "long"), include_vp_violations=True):
    rng = random.Random(seed)
    base_rows = build_lexicon(total_prep_words)
    rng.shuffle(base_rows)
    grammaticalities = ("grammatical", "violation") if include_vp_violations else ("grammatical",)
    stimuli = []
    for index, row in enumerate(base_rows, start=1):
        for grammaticality in grammaticalities:
            vp = _vp_form(row, grammaticality)
            verb_head = _verb_head(vp)
            sentence_row = dict(row)
            sentence_row["verb_phrase"] = vp
            for structure in structures:
                stimuli.append(
                    {
                        "Stimulus_ID": f"V2_{index:03d}_{structure[0].upper()}_{grammaticality[0].upper()}",
                        "Structure": structure,
                        "VP_Grammaticality": grammaticality,
                        "Noun_Congruency": _noun_congruency(
                            row["subject_number"],
                            row["pp1_number"],
                            row["pp2_number"],
                        ),
                        "Congruency_Locus": _congruency_locus(
                            structure,
                            row["subject_number"],
                            row["pp1_number"],
                            row["pp2_number"],
                        ),
                        "Sentence_String": _render(structure, sentence_row),
                        "Subject_Lemma": row["subject_noun"],
                        "Subject_Gender": row["subject_gender"],
                        "Subject_Number": row["subject_number"],
                        "Subject_No_Probe": row.get("subject_no_probe", ""),
                        "Subject_Zipf_Frequency": _zipf_fr(row["subject_noun"]),
                        "Subject_Length": _letter_count(row["subject_noun"]),
                        "Verb_Phrase": vp,
                        "Verb_Lemma": verb_head,
                        "Verb_Zipf_Frequency": _zipf_fr(verb_head),
                        "Verb_Length": _letter_count(verb_head),
                        "PP1_Preposition": row["pp1_prep"],
                        "PP1_Opposite_Preposition": row.get("pp1_opposite_prep", ""),
                        "PP1_Preposition_Zipf_Frequency": _zipf_fr(row["pp1_prep"]),
                        "PP1_Preposition_Length": _letter_count(row["pp1_prep"]),
                        "PP1_Lemma": row["pp1_noun"],
                        "PP1_Gender": row["pp1_gender"],
                        "PP1_Number": row["pp1_number"],
                        "PP2_Preposition": row["pp2_prep"],
                        "PP2_Opposite_Preposition": row.get("pp2_opposite_prep", ""),
                        "PP2_Preposition_Zipf_Frequency": _zipf_fr(row["pp2_prep"]),
                        "PP2_Preposition_Length": _letter_count(row["pp2_prep"]),
                        "PP2_Lemma": row["pp2_noun"],
                        "PP2_Gender": row["pp2_gender"],
                        "PP2_Number": row["pp2_number"],
                        "PP_Word_Budget": row["pp_word_budget"],
                    }
                )
    return stimuli


def write_stimuli(rows, output_path, delimiter=","):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)