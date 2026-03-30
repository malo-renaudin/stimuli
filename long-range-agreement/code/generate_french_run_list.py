#!/usr/bin/env python3

import argparse
import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "stimuli" / "french_run_list.csv"


DELAY_OPTIONS_MS = [1000, 1250, 1500, 1750, 2000]


EXPERIMENTAL_BASES = [
    {
        "base_id": "B01",
        "gender": "Masc",
        "subject": {"singular": "ami", "plural": "amis", "gender": "m"},
        "pp1": {"singular": "jardin", "plural": "jardins", "gender": "m"},
        "pp2": {"singular": "village", "plural": "villages", "gender": "m"},
        "adjective": {"m_sg": "heureux", "m_pl": "heureux", "f_sg": "heureuse", "f_pl": "heureuses"},
        "verb_pair": {"singular": "est", "plural": "sont"},
    },
    {
        "base_id": "B02",
        "gender": "Masc",
        "subject": {"singular": "étudiant", "plural": "étudiants", "gender": "m"},
        "pp1": {"singular": "musicien", "plural": "musiciens", "gender": "m"},
        "pp2": {"singular": "maison", "plural": "maisons", "gender": "f"},
        "adjective": {"m_sg": "calme", "m_pl": "calmes", "f_sg": "calme", "f_pl": "calmes"},
        "verb_pair": {"singular": "finit", "plural": "finissent"},
    },
    {
        "base_id": "B03",
        "gender": "Masc",
        "subject": {"singular": "artiste", "plural": "artistes", "gender": "m"},
        "pp1": {"singular": "professeur", "plural": "professeurs", "gender": "m"},
        "pp2": {"singular": "école", "plural": "écoles", "gender": "f"},
        "adjective": {"m_sg": "content", "m_pl": "contents", "f_sg": "contente", "f_pl": "contentes"},
        "verb_pair": {"singular": "est", "plural": "sont"},
    },
    {
        "base_id": "B04",
        "gender": "Masc",
        "subject": {"singular": "infirmier", "plural": "infirmiers", "gender": "m"},
        "pp1": {"singular": "atelier", "plural": "ateliers", "gender": "m"},
        "pp2": {"singular": "usine", "plural": "usines", "gender": "f"},
        "adjective": {"m_sg": "fatigué", "m_pl": "fatigués", "f_sg": "fatiguée", "f_pl": "fatiguées"},
        "verb_pair": {"singular": "finit", "plural": "finissent"},
    },
    {
        "base_id": "B05",
        "gender": "Fem",
        "subject": {"singular": "amie", "plural": "amies", "gender": "f"},
        "pp1": {"singular": "jardin", "plural": "jardins", "gender": "m"},
        "pp2": {"singular": "ville", "plural": "villes", "gender": "f"},
        "adjective": {"m_sg": "heureux", "m_pl": "heureux", "f_sg": "heureuse", "f_pl": "heureuses"},
        "verb_pair": {"singular": "est", "plural": "sont"},
    },
    {
        "base_id": "B06",
        "gender": "Fem",
        "subject": {"singular": "étudiante", "plural": "étudiantes", "gender": "f"},
        "pp1": {"singular": "verger", "plural": "vergers", "gender": "m"},
        "pp2": {"singular": "route", "plural": "routes", "gender": "f"},
        "adjective": {"m_sg": "fier", "m_pl": "fiers", "f_sg": "fière", "f_pl": "fières"},
        "verb_pair": {"singular": "finit", "plural": "finissent"},
    },
    {
        "base_id": "B07",
        "gender": "Fem",
        "subject": {"singular": "amatrice", "plural": "amatrices", "gender": "f"},
        "pp1": {"singular": "campus", "plural": "campus", "gender": "m"},
        "pp2": {"singular": "bibliothèque", "plural": "bibliothèques", "gender": "f"},
        "adjective": {"m_sg": "préoccupé", "m_pl": "préoccupés", "f_sg": "préoccupée", "f_pl": "préoccupées"},
        "verb_pair": {"singular": "est", "plural": "sont"},
    },
    {
        "base_id": "B08",
        "gender": "Fem",
        "subject": {"singular": "infirmière", "plural": "infirmières", "gender": "f"},
        "pp1": {"singular": "quartier", "plural": "quartiers", "gender": "m"},
        "pp2": {"singular": "avenue", "plural": "avenues", "gender": "f"},
        "adjective": {"m_sg": "sérieux", "m_pl": "sérieux", "f_sg": "sérieuse", "f_pl": "sérieuses"},
        "verb_pair": {"singular": "finit", "plural": "finissent"},
    },
]


FILLER_SUBJECTS = [
    {"singular": "Le médecin", "plural": "Les médecins"},
    {"singular": "Le voisin", "plural": "Les voisins"},
    {"singular": "La musicienne", "plural": "Les musiciennes"},
    {"singular": "La journaliste", "plural": "Les journalistes"},
    {"singular": "Le pilote", "plural": "Les pilotes"},
    {"singular": "La chercheuse", "plural": "Les chercheuses"},
]

FILLER_OBJECTS = [
    {"singular": "le roman", "plural": "les romans"},
    {"singular": "la radio", "plural": "les radios"},
    {"singular": "le dossier", "plural": "les dossiers"},
    {"singular": "la photo", "plural": "les photos"},
    {"singular": "le message", "plural": "les messages"},
    {"singular": "la lampe", "plural": "les lampes"},
]

FILLER_VERBS = [
    {"lemma": "regarder", "singular": "regarde", "plural": "regardent"},
    {"lemma": "porter", "singular": "porte", "plural": "portent"},
    {"lemma": "chercher", "singular": "cherche", "plural": "cherchent"},
    {"lemma": "trouver", "singular": "trouve", "plural": "trouvent"},
    {"lemma": "aimer", "singular": "aime", "plural": "aiment"},
    {"lemma": "suivre", "singular": "suit", "plural": "suivent"},
]


def starts_with_vowel(word):
    return word[0].lower() in {"a", "à", "â", "e", "é", "è", "ê", "i", "î", "ï", "o", "ô", "u", "ù", "û", "ü", "y"}


def make_subject_dp(noun, number):
    if number == "plural":
        return f"Les {noun['plural']}"
    return f"L'{noun['singular']}"


def lower_initial(text):
    return text[:1].lower() + text[1:]


def make_np_after_de(noun, number):
    if number == "plural":
        return f"des {noun['plural']}"

    form = noun["singular"]
    if noun["gender"] == "m":
        if starts_with_vowel(form):
            return f"de l'{form}"
        return f"du {form}"

    if starts_with_vowel(form):
        return f"de l'{form}"
    return f"de la {form}"


def make_pp(preposition, noun, number):
    return f"{preposition} {make_np_after_de(noun, number)}"


def adjective_form(base, subject_number):
    gender = base["subject"]["gender"]
    number_code = "pl" if subject_number == "plural" else "sg"
    return base["adjective"][f"{gender}_{number_code}"]


def complement_phrase(base, subject_number):
    verb = base["verb_pair"][subject_number]
    adjective = adjective_form(base, subject_number)
    if verb in {"est", "sont"}:
        return f"{verb} {adjective}"
    return verb


def condition_code(base_gender, subject_number, local_number, distance):
    sub = "SingSub" if subject_number == "singular" else "PlurSub"
    loc = "SingLoc" if local_number == "singular" else "PlurLoc"
    dist = distance.capitalize()
    return f"{base_gender}_{sub}_{loc}_{dist}"


def make_experimental_sentence(base, subject_number, local_number, distance):
    expected_verb = base["verb_pair"][subject_number]
    subject_dp = make_subject_dp(base["subject"], subject_number)
    predicate = complement_phrase(base, subject_number)
    interference_type = (
        "Match" if subject_number == local_number else "Mismatch"
    )
    liaison_cue = "liaison_z" if subject_number == "plural" else "no_liaison"

    if distance == "long":
        pp1_number = "singular"
        pp2_number = local_number
        pp1 = make_pp("près", base["pp1"], pp1_number)
        pp2 = make_pp("à côté", base["pp2"], pp2_number)
        sentence = f"{subject_dp} {pp1} {pp2} {predicate}."
        local_noun_slot = "pp2"
    elif distance == "medium":
        pp1_number = local_number
        pp2_number = "singular"
        pp1 = make_pp("près", base["pp1"], pp1_number)
        pp2 = make_pp("À côté", base["pp2"], pp2_number)
        sentence = f"{pp2}, {lower_initial(subject_dp)} {pp1} {predicate}."
        local_noun_slot = "pp1"
    else:
        pp1_number = local_number
        pp2_number = "singular"
        pp1 = make_pp("près", base["pp1"], pp1_number)
        pp2 = make_pp("À côté", base["pp2"], pp2_number)
        sentence = f"{pp2}, {pp1}, {lower_initial(subject_dp)} {predicate}."
        local_noun_slot = "pp1"

    return {
        "Condition_Code": condition_code(base["gender"], subject_number, local_number, distance),
        "Sentence_String": sentence,
        "Is_Filler": False,
        "Expected_Verb": expected_verb,
        "Distance": distance,
        "Base_ID": base["base_id"],
        "Subject_Number": subject_number,
        "Local_Number": local_number,
        "Local_Noun_Slot": local_noun_slot,
        "Interference_Type": interference_type,
        "Subject_Liaison_Cue": liaison_cue,
        "Delayed_Repetition": True,
        "Delay_ms": None,
        "Go_Beep": True,
        "Audio_Normalization_Note": "Normalize pre-verb pause and verb duration across conditions.",
    }


def generate_experimental_trials():
    trials = []
    for base in EXPERIMENTAL_BASES:
        for subject_number in ["singular", "plural"]:
            for local_number in ["singular", "plural"]:
                for distance in ["long", "medium", "short"]:
                    trials.append(
                        make_experimental_sentence(base, subject_number, local_number, distance)
                    )
    return trials


def make_filler_sentence(subject, subject_number, verb, obj, negative):
    subject_dp = subject[subject_number]
    verb_form = verb[subject_number]
    object_number = "plural" if negative else "singular"
    object_dp = obj[object_number]

    if negative:
        sentence = f"{subject_dp} ne {verb_form} pas {object_dp}."
    else:
        sentence = f"{subject_dp} {verb_form} {object_dp}."

    return {
        "Condition_Code": "Filler_Neg" if negative else "Filler_SVO",
        "Sentence_String": sentence,
        "Is_Filler": True,
        "Expected_Verb": verb_form,
        "Distance": "filler",
        "Base_ID": "FILLER",
        "Subject_Number": subject_number,
        "Local_Number": "NA",
        "Local_Noun_Slot": "NA",
        "Interference_Type": "NA",
        "Subject_Liaison_Cue": "NA",
        "Delayed_Repetition": True,
        "Delay_ms": None,
        "Go_Beep": True,
        "Audio_Normalization_Note": "Use fillers to prevent structural habituation.",
    }


def generate_fillers(n_fillers, rng):
    all_fillers = []
    for subject in FILLER_SUBJECTS:
        for subject_number in ["singular", "plural"]:
            for verb in FILLER_VERBS:
                for obj in FILLER_OBJECTS:
                    for negative in [False, True]:
                        all_fillers.append(
                            make_filler_sentence(subject, subject_number, verb, obj, negative)
                        )

    rng.shuffle(all_fillers)
    return all_fillers[:n_fillers]


def violates_distance_streak(sequence, candidate):
    if candidate["Is_Filler"]:
        return False

    streak = 0
    for trial in reversed(sequence):
        if trial["Is_Filler"]:
            break
        if trial["Distance"] == candidate["Distance"]:
            streak += 1
        else:
            break
    return streak >= 3


def randomize_experimentals(experimentals, rng, max_attempts=5000):
    for _ in range(max_attempts):
        shuffled = experimentals[:]
        rng.shuffle(shuffled)
        ok = True
        streak = 1
        for prev, curr in zip(shuffled, shuffled[1:]):
            if prev["Distance"] == curr["Distance"]:
                streak += 1
                if streak > 3:
                    ok = False
                    break
            else:
                streak = 1
        if ok:
            return shuffled
    raise RuntimeError("Could not randomize experimental trials without long distance streaks.")


def interleave_trials(experimentals, fillers, rng):
    exp_queue = experimentals[:]
    filler_queue = fillers[:]
    run_list = []

    while exp_queue or filler_queue:
        choices = []
        if exp_queue and not violates_distance_streak(run_list, exp_queue[0]):
            choices.append("exp")
        if filler_queue:
            choices.append("filler")

        if not choices:
            filler = filler_queue.pop(0)
            run_list.append(filler)
            continue

        if len(choices) == 2:
            total_remaining = len(exp_queue) + len(filler_queue)
            choose_exp = rng.random() < (len(exp_queue) / total_remaining)
            choice = "exp" if choose_exp else "filler"
        else:
            choice = choices[0]

        if choice == "exp":
            run_list.append(exp_queue.pop(0))
        else:
            run_list.append(filler_queue.pop(0))

    return run_list


def assign_delays(trials, rng):
    for trial in trials:
        trial["Delay_ms"] = rng.choice(DELAY_OPTIONS_MS)
    return trials


def write_run_list(trials, output_path, delimiter):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "Trial_ID",
                "Condition_Code",
                "Sentence_String",
                "Is_Filler",
                "Expected_Verb",
                "Base_ID",
                "Subject_Number",
                "Local_Number",
                "Local_Noun_Slot",
                "Interference_Type",
                "Subject_Liaison_Cue",
                "Delayed_Repetition",
                "Delay_ms",
                "Go_Beep",
                "Audio_Normalization_Note",
            ],
            delimiter=delimiter,
        )
        writer.writeheader()
        for index, trial in enumerate(trials, start=1):
            writer.writerow(
                {
                    "Trial_ID": f"T{index:03d}",
                    "Condition_Code": trial["Condition_Code"],
                    "Sentence_String": trial["Sentence_String"],
                    "Is_Filler": trial["Is_Filler"],
                    "Expected_Verb": trial["Expected_Verb"],
                    "Base_ID": trial["Base_ID"],
                    "Subject_Number": trial["Subject_Number"],
                    "Local_Number": trial["Local_Number"],
                    "Local_Noun_Slot": trial["Local_Noun_Slot"],
                    "Interference_Type": trial["Interference_Type"],
                    "Subject_Liaison_Cue": trial["Subject_Liaison_Cue"],
                    "Delayed_Repetition": trial["Delayed_Repetition"],
                    "Delay_ms": trial["Delay_ms"],
                    "Go_Beep": trial["Go_Beep"],
                    "Audio_Normalization_Note": trial["Audio_Normalization_Note"],
                }
            )


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a randomized French run list.")
    parser.add_argument("--seed", type=int, default=13, help="Random seed for reproducibility.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output file path.",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "tsv"],
        default="csv",
        help="Output delimiter format.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rng = random.Random(args.seed)

    experimentals = generate_experimental_trials()
    fillers = generate_fillers(len(experimentals), rng)

    experimentals = randomize_experimentals(experimentals, rng)
    run_list = interleave_trials(experimentals, fillers, rng)
    run_list = assign_delays(run_list, rng)

    delimiter = "," if args.format == "csv" else "\t"
    output_path = args.output
    if output_path.suffix == "":
        output_path = output_path.with_suffix(f".{args.format}")

    write_run_list(run_list, output_path, delimiter)

    print(f"Experimental trials: {len(experimentals)}")
    print(f"Filler trials: {len(fillers)}")
    print(f"Total trials: {len(run_list)}")
    print(f"Saved run list to {output_path}")


if __name__ == "__main__":
    main()
