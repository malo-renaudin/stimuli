from fr_experiment.config import PREPOSITIONS


DANS_PREFERRED_LEMMAS = {"auditorium", "allée"}
AT_DISALLOWED_LEMMAS = {"aire", "appartement", "abri"}

PLACE_PREPOSITION_OPTIONS = {
    "aéroport": ["dans", "près de", "devant"],
    "atelier": ["dans", "à côté de"],
    "appartement": ["dans", "près de"],
    "immeuble": ["dans", "à côté de"],
    "étage": ["dans"],
    "espace": ["dans", "loin de"],
    "établissement": ["devant"],
    "observatoire": ["dans"],
    "amphithéâtre": ["dans", "près de", "devant"],
    "entrepôt": ["dans", "à côté de", "loin de"],
    "institut": ["à gauche de"],
    "auditorium": ["dans", "derrière"],
    "office": ["à côté de"],
    "abri": ["dans", "près de"],
    "îlot": ["en face de"],
    "avenue": ["devant"],
    "école": ["devant", "à droite de"],
    "usine": ["dans", "près de"],
    "île": ["dans"],
    "entrée": ["devant"],
    "allée": ["dans", "à côté de"],
    "impasse": ["dans", "à côté de"],
    "agence": ["dans"],
    "église": ["dans", "derrière"],
    "université": ["à gauche de"],
    "oasis": ["dans"],
    "enceinte": ["dans"],
    "auberge": ["dans"],
    "arène": ["dans", "devant"],
}


def starts_with_vowel(word):
    return word[:1].lower() in {
        "a",
        "e",
        "i",
        "o",
        "u",
        "y",
        "à",
        "â",
        "é",
        "è",
        "ê",
        "î",
        "ï",
        "ô",
        "ù",
        "û",
        "ü",
    }


def lower_initial(text):
    return text[:1].lower() + text[1:]


def make_subject_dp(noun, number):
    if number == "plural":
        return f"Les {noun['plural']}"
    return f"L'{noun['singular']}"


def adjective_form(adjective_lexeme, subject_gender, subject_number):
    number_code = "pl" if subject_number == "plural" else "sg"
    return adjective_lexeme[f"{subject_gender}_{number_code}"]


def expected_verb_form(verb, subject_number, grammaticality):
    if grammaticality == "grammatical":
        return verb["singular"] if subject_number == "singular" else verb["plural"]
    return verb["plural"] if subject_number == "singular" else verb["singular"]


def compatible_prepositions(noun, number):
    if noun["semantic"] == "animate":
        return ["chez"]

    options = PLACE_PREPOSITION_OPTIONS.get(noun["singular"], ["dans"])
    if noun["singular"] in DANS_PREFERRED_LEMMAS:
        return ["dans"]
    return options


def determiner_for(noun, number):
    if number == "plural":
        return "les"
    if starts_with_vowel(noun["singular"]):
        return "l'"
    return "le" if noun["gender"] == "m" else "la"


def compose_np(determiner, noun, number):
    form = noun["plural"] if number == "plural" else noun["singular"]
    if determiner == "l'":
        return f"l'{form}"
    return f"{determiner} {form}"


def make_pp(preposition, noun, number):
    if preposition not in PREPOSITIONS:
        raise RuntimeError(f"Unsupported preposition: {preposition}")

    singular = noun["singular"]
    plural = noun["plural"]
    gender = noun["gender"]

    if preposition == "de":
        if number == "plural":
            return f"des {plural}"
        if starts_with_vowel(singular):
            return f"de l'{singular}"
        return f"du {singular}" if gender == "m" else f"de la {singular}"

    if preposition == "dans":
        if number == "plural":
            return f"dans les {plural}"
        if starts_with_vowel(singular):
            return f"dans l'{singular}"
        return f"dans le {singular}" if gender == "m" else f"dans la {singular}"

    if preposition == "vers":
        if number == "plural":
            return f"vers les {plural}"
        if starts_with_vowel(singular):
            return f"vers l'{singular}"
        return f"vers le {singular}" if gender == "m" else f"vers la {singular}"

    if preposition == "chez":
        if number == "plural":
            return f"chez les {plural}"
        if starts_with_vowel(singular):
            return f"chez l'{singular}"
        return f"chez le {singular}" if gender == "m" else f"chez la {singular}"

    if preposition == "à côté de":
        if number == "plural":
            return f"à côté des {plural}"
        if starts_with_vowel(singular):
            return f"à côté de l'{singular}"
        return f"à côté du {singular}" if gender == "m" else f"à côté de la {singular}"

    if preposition == "près de":
        if number == "plural":
            return f"près des {plural}"
        if starts_with_vowel(singular):
            return f"près de l'{singular}"
        return f"près du {singular}" if gender == "m" else f"près de la {singular}"

    if preposition == "devant":
        if number == "plural":
            return f"devant les {plural}"
        if starts_with_vowel(singular):
            return f"devant l'{singular}"
        return f"devant le {singular}" if gender == "m" else f"devant la {singular}"

    if preposition == "derrière":
        if number == "plural":
            return f"derrière les {plural}"
        if starts_with_vowel(singular):
            return f"derrière l'{singular}"
        return f"derrière le {singular}" if gender == "m" else f"derrière la {singular}"

    if preposition == "à gauche de":
        if number == "plural":
            return f"à gauche des {plural}"
        if starts_with_vowel(singular):
            return f"à gauche de l'{singular}"
        return f"à gauche du {singular}" if gender == "m" else f"à gauche de la {singular}"

    if preposition == "à droite de":
        if number == "plural":
            return f"à droite des {plural}"
        if starts_with_vowel(singular):
            return f"à droite de l'{singular}"
        return f"à droite du {singular}" if gender == "m" else f"à droite de la {singular}"

    if preposition == "en face de":
        if number == "plural":
            return f"en face des {plural}"
        if starts_with_vowel(singular):
            return f"en face de l'{singular}"
        return f"en face du {singular}" if gender == "m" else f"en face de la {singular}"

    if preposition == "loin de":
        if number == "plural":
            return f"loin des {plural}"
        if starts_with_vowel(singular):
            return f"loin de l'{singular}"
        return f"loin du {singular}" if gender == "m" else f"loin de la {singular}"

    raise RuntimeError(f"Unhandled preposition: {preposition}")
