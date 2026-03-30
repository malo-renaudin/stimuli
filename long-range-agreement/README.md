# Long-Range Agreement Stimuli

This folder contains materials for the French long-range agreement experiment.

## Goal

The experiment targets agreement processing under interference from structurally local nouns. The core manipulation varies:

- subject number: singular vs plural
- local noun number: singular vs plural
- distance to the main verb: short, medium, long

This yields a `2 x 2 x 3` design over a fixed set of lexical bases.

## Design Principles

- Experimental subject nouns should be vowel-initial whenever possible so singular/plural can be identified auditorily through the presence or absence of liaison.
- Main verbs in the experimental items should use auditorily distinct singular/plural forms such as `est/sont` or `finit/finissent`.
- The local noun should be tracked explicitly because the structurally closest noun to the verb changes across distance conditions.
- Fillers should make up roughly 50% of the run list to reduce strategy and habituation.
- Delayed repetition should be used to separate comprehension from speech production.

## Recommended Contents

- `run_lists/`
  Randomized CSV or TSV files used during presentation.
- `lexical_bases/`
  Source lexical bases and condition tables.
- `audio/`
  Recorded or normalized audio stimuli.
- `notes/`
  Task notes, piloting observations, and analysis-relevant comments.
- `code/`
  Scripts used to generate stimuli or randomize trial order.

## Current Run-List Expectations

A run-list file should include at least these columns:

- `Trial_ID`
- `Condition_Code`
- `Sentence_String`
- `Is_Filler`
- `Expected_Verb`

Useful additional columns:

- `Base_ID`
- `Subject_Number`
- `Local_Number`
- `Local_Noun_Slot`
- `Interference_Type`
- `Subject_Liaison_Cue`
- `Delay_ms`
- `Go_Beep`

## Audio Notes

- Keep the pre-verb region as comparable as possible across conditions.
- Normalize pause structure before the main verb.
- If recorded speech is used, verify that plural liaison is consistently realized.
- If synthetic speech is used, verify that singular/plural verb forms remain auditorily separable.

## Status

This repository was initialized as an empty repository. This README establishes the folder for the long-range agreement stimulus set and can be expanded as files are added.
