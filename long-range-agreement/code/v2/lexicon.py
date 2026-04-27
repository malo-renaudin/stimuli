from itertools import permutations, product


def _entry(noun, gender, number, **extra):
    return {"noun": noun, "gender": gender, "number": number, **extra}


SUBJECTS = [
    _entry("autrice", "f", "singular", vp="lit un livre", vp_violation="lisent un livre", no_probe="L'autrice regarde-t-elle un film ?"),
    _entry("auteurs", "m", "plural", vp="sont pensifs", vp_violation="est pensifs", no_probe ="Les auteurs sont-ils agités ?"),
    _entry("étudiant", "m", "singular", vp="apprend une leçon", vp_violation="apprennent une leçon", no_probe="L'étudiant est-il en train de faire du sport ?"),
    _entry("étudiantes", "f", "plural", vp="sont attentives", vp_violation="est attentive", no_probe ="Les étudiantes sont-elles distraites ?"),
    _entry("ouvrière", "f", "singular", vp="est fatiguée", vp_violation="sont fatiguée", no_probe = "L'ouvrière est-elle en forme ?"),
    _entry("ouvriers", "m", "plural", vp="finissent de travailler", vp_violation="finit de travailler", no_probe = " Les ouvriers commencent-ils à travailler ?"),
    _entry("usager", "m", "singular", vp="est en retard", vp_violation="sont en retard", no_probe = "L'usager est-il en avance ?"),
    _entry("usagères", "f", "plural", vp="prennent l'autoroute", vp_violation="prend l'autoroute", no_probe = "Les usagères sont-elles à vélo ?"),
]

PLACES = [
    # _entry("atelier", "m", "singular", "culture"),
    # _entry("université", "f", "singular", "culture"),
    _entry("amphithéâtre", "m", "singular"),
    _entry("école", "f", "singular"),
    _entry("usine", "f", "singular"),
    _entry("entrepôt", "m", "singular"),
    _entry("abri", "m", "singular"),
    _entry("avenue", "f", "singular"),
    _entry("immeubles", "m", "plural"),
    _entry("escaliers", "m", "plural"),
    _entry("installations", "f", "plural"),
    _entry("habitations", "f", "plural"),
    _entry("infrastructures", "f", "plural"),
    _entry("affiches", "f", "plural"),
]

PREPOSITIONS = [
    {"label": "devant", "words": 2, "opposite": "derrière"},
    {"label": "derrière", "words": 2, "opposite": "devant"},
    {"label": "près de", "words": 2, "opposite": "loin de"},
    {"label": "à côté de", "words": 3, "opposite": "loin de"},
    {"label": "loin de", "words": 3, "opposite": "près de"},
    {"label": "en face de", "words": 3, "opposite": "derrière"},
    {"label": "à gauche de", "words": 3, "opposite": "à droite de"},
    {"label": "à droite de", "words": 3, "opposite": "à gauche de"},
]


def preposition_opposites(prepositions=PREPOSITIONS):
    labels = {prep["label"] for prep in prepositions}
    opposites = {}
    for prep in prepositions:
        label = prep["label"]
        opposite = prep.get("opposite", "")
        opposites[label] = opposite if opposite in labels else ""
    return opposites


def starts_with_vowel(word):
    return word[:1].lower() in "aeiouyàâéèêîïôùûü"


def _np(entry):
    noun = entry["noun"]
    if entry["number"] == "plural":
        return f"les {noun}"
    if starts_with_vowel(noun):
        return f"l'{noun}"
    return f"{'le' if entry['gender'] == 'm' else 'la'} {noun}"


def _subject(entry):
    noun = entry["noun"]
    return f"Les {noun}" if entry["number"] == "plural" else f"L'{noun}"


def _pp(preposition, entry):
    label = preposition["label"]
    noun = entry["noun"]
    if label.endswith("de"):
        if entry["number"] == "plural":
            return f"{label}s {noun}"
        if starts_with_vowel(noun):
            return f"{label} l'{noun}"
        article = "du" if entry["gender"] == "m" else "de la"
        return f"{label[:-2]}{article} {noun}"
    return f"{label} {_np(entry)}"


def preposition_pairs(total_words=5, prepositions=PREPOSITIONS):
    return [pair for pair in product(prepositions, repeat=2) if pair[0]["words"] + pair[1]["words"] == total_words]


def build_lexicon(total_prep_words=5):
    rows = []
    opposite_map = preposition_opposites()
    for subject in SUBJECTS:
        for place1, place2 in permutations(PLACES, 2):
            for prep1, prep2 in preposition_pairs(total_prep_words):
                rows.append(
                    {
                        "subject": _subject(subject),
                        "subject_noun": subject["noun"],
                        "subject_gender": subject["gender"],
                        "subject_number": subject["number"],
                        "verb_phrase": subject["vp"],
                        "verb_phrase_violation": subject.get("vp_violation"),
                        "subject_no_probe": subject.get("no_probe", ""),
                        "pp1_prep": prep1["label"],
                        "pp1_opposite_prep": opposite_map.get(prep1["label"], ""),
                        "pp1": _pp(prep1, place1),
                        "pp1_noun": place1["noun"],
                        "pp1_gender": place1["gender"],
                        "pp1_number": place1["number"],
                        "pp2_prep": prep2["label"],
                        "pp2_opposite_prep": opposite_map.get(prep2["label"], ""),
                        "pp2": _pp(prep2, place2),
                        "pp2_noun": place2["noun"],
                        "pp2_gender": place2["gender"],
                        "pp2_number": place2["number"],
                        "pp_word_budget": total_prep_words,
                    }
                )
    return rows