#!/usr/bin/env python3

import argparse
import random
from pathlib import Path

from fr_experiment.config import DEFAULT_OUTPUT, LEXICAL_COMBOS_PER_RUN, RUN_COUNT, STRUCTURES
from fr_experiment.generator import generate_trials
from fr_experiment.validation import assign_delays, validate_trials
from fr_experiment.writer import write_run_list


def parse_args():
    parser = argparse.ArgumentParser(description="Generate constrained French run lists for agreement experiment.")
    parser.add_argument("--seed", type=int, default=13, help="Random seed for reproducibility.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output file path.")
    parser.add_argument("--format", choices=["csv", "tsv"], default="csv", help="Output delimiter format.")
    return parser.parse_args()


def main():
    args = parse_args()

    trials = generate_trials(args.seed)
    assign_delays(trials, random.Random(args.seed + 1000))
    validate_trials(trials)

    delimiter = "," if args.format == "csv" else "\t"
    output_path = args.output
    if output_path.suffix == "":
        output_path = output_path.with_suffix(f".{args.format}")

    write_run_list(trials, output_path, delimiter)

    print(f"Runs: {RUN_COUNT}")
    print(f"Lexical combinations per run: {LEXICAL_COMBOS_PER_RUN}")
    print(f"Structures per combination: {len(STRUCTURES)}")
    print(f"Experimental trials per run: {LEXICAL_COMBOS_PER_RUN * len(STRUCTURES)}")
    print(f"Total trials: {len(trials)}")
    print(f"Saved run list to {output_path}")


if __name__ == "__main__":
    main()
