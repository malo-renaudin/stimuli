from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT = ROOT / "run_lists" / "french_run_list.csv"

RUN_COUNT = 6
LEXICAL_COMBOS_PER_RUN = 16
STRUCTURES = ["short", "medium", "long"]
DELAY_OPTIONS_MS = [1000, 1250, 1500, 1750, 2000]

PREPOSITIONS = ["chez", "dans", "à côté de", "près de", "devant", "derrière", "à gauche de", "à droite de", "en face de", "loin de"]
