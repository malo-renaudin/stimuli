#!/usr/bin/env python3

import argparse
from pathlib import Path

from v2.generator import generate_stimuli, write_stimuli


def parse_args():
    parser = argparse.ArgumentParser(description="Generate stimuli from the compact v2 lexicon.")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--prep-word-budget", type=int, default=5)
    parser.add_argument(
        "--with-vp-violations",
        dest="with_vp_violations",
        action="store_true",
        default=True,
        help="Include ungrammatical items using lexicon-provided vp_violation forms (default: on).",
    )
    parser.add_argument(
        "--without-vp-violations",
        dest="with_vp_violations",
        action="store_false",
        help="Generate only grammatical items.",
    )
    parser.add_argument("--output", type=Path, default=Path("run_lists/v2_stimuli.csv"))
    parser.add_argument("--format", choices=["csv", "tsv"], default="csv")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = generate_stimuli(
        seed=args.seed,
        total_prep_words=args.prep_word_budget,
        include_vp_violations=args.with_vp_violations,
    )
    output = args.output if args.output.suffix else args.output.with_suffix(f".{args.format}")
    write_stimuli(rows, output, "\t" if args.format == "tsv" else ",")
    print(f"Generated {len(rows)} stimuli")
    print(f"Saved to {output}")


if __name__ == "__main__":
    main()