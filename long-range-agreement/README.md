# Long-Range Agreement (Français)

Générateur de stimuli pour une tâche d'accord sujet-verbe en français avec deux groupes préverbaux interférents.

## Objectif expérimental

Le matériel manipule l'accord verbal sous interférence nominale en contrôlant :

- le nombre du sujet (singulier/pluriel)
- le nombre de PP1 (singulier/pluriel)
- le nombre de PP2 (singulier/pluriel)
- la grammaticalité (grammatical vs violation d'accord)
- la distance structurale au verbe (short/medium/long)

Chaque combinaison lexicale est déclinée dans les 3 structures de distance.

## Contraintes implémentées

### Plan global

- 6 runs
- 16 combinaisons lexicales par run
- 3 structures par combinaison
- 48 essais expérimentaux par run
- 288 essais expérimentaux au total
- aucun filler dans cette version (`Is_Filler=False`)

### Couverture combinatoire par run

- les 8 patrons `(Subject_Number, PP1_Number, PP2_Number)` sont présents
- chaque patron apparaît 2 fois :
  - 1 fois en `grammatical`
  - 1 fois en `violation`
- donc 16 combinaisons lexicales uniques par run

### Équilibrage verbal

Dans chaque run (sur les lignes `short`, qui indexent les 16 bases lexicales) :

- 8 phrases copule (`être`)
- 8 phrases lexicales
- parmi les lexicales :
  - 4 verbes du 2e groupe (`lexical_2`)
  - 4 verbes du 3e groupe (`lexical_3`)

### Contraintes lexicales et phonologiques

- les lemmes de sujet, PP1 et PP2 doivent commencer par une voyelle (validation stricte)
- l'adjectif post-copule est un seul mot
- le complément post-verbe lexical est exactement 2 mots (COD)

### Contraintes de structure

- 3 noms distincts dans chaque item (`subject`, `PP1`, `PP2`)
- pas de combinaison dupliquée dans un run pour la clé :
  - `(Subject_Lemma, PP1_Lemma, PP2_Lemma, Verb_Lemma)`
- équilibre de genre global dans chaque run sur les lignes `short` :
  - nombre total de noms masculins = nombre total de noms féminins

### Prépositions

Inventaire actuel :

- `chez`
- `dans`
- `à côté de`
- `près de`
- `devant`
- `derrière`
- `à gauche de`
- `à droite de`
- `en face de`
- `loin de`

Règles :

- les noms animés prennent `chez`
- les noms de lieu utilisent des options compatibles sémantiquement (`PLACE_PREPOSITION_OPTIONS`)
- en structure `long`, les prépositions statiques (`dans`, `chez`) sont placées avant les relationnelles quand les deux types coexistent

## Comment les stimuli sont créés

Pipeline principal :

1. Construire les patrons de nombres (`2 x 2 x 2 = 8`).
2. Dupliquer chaque patron en `grammatical` et `violation`.
3. Assigner un plan verbal équilibré (`8 copula + 4 lexical_2 + 4 lexical_3`).
4. Tirer des candidats via des `SCENARIO_FRAMES` (sujet/PP1/PP2 + paires de prépositions + verbes autorisés).
5. Filtrer les candidats par compatibilité prépositionnelle et distinctivité des noms.
6. Construire les 3 réalisations de structure pour chaque base lexicale :
   - `long`: `Sujet PP1 PP2 Verbe Suite`
   - `medium`: `PP1, sujet PP2 Verbe Suite`
   - `short`: `PP1, PP2, sujet Verbe Suite`
7. Mélanger les essais dans chaque run.
8. Assigner un délai de répétition (`Delay_ms`) parmi `{1000, 1250, 1500, 1750, 2000}`.
9. Valider toutes les contraintes avant export.

## Lancer le générateur

Depuis le dossier `long-range-agreement` :

```bash
python3 code/generate_french_run_list.py --seed 13 --output run_lists/french_run_list.csv
```

Options CLI :

- `--seed` : graine aléatoire pour reproductibilité
- `--output` : chemin de sortie
- `--format` : `csv` (défaut) ou `tsv`

## Colonnes exportées

Le fichier de sortie contient notamment :

- identifiants : `Trial_ID`, `Run_ID`, `Lexical_Combo_ID`, `Condition_Code`
- condition : `Structure`, `Grammaticality`
- contenu : `Sentence_String`
- verbe : `Expected_Verb`, `Verb_Form`, `Verb_Lemma`, `Verb_Type`
- sujet : `Subject_Lemma`, `Subject_Gender`, `Subject_Number`
- PP1 : `PP1_Lemma`, `PP1_Gender`, `PP1_Number`, `PP1_Preposition`
- PP2 : `PP2_Lemma`, `PP2_Gender`, `PP2_Number`, `PP2_Preposition`
- timing : `Delayed_Repetition`, `Delay_ms`, `Go_Beep`
- note audio : `Audio_Normalization_Note`

## Arborescence utile

- `code/generate_french_run_list.py` : point d'entrée CLI
- `code/fr_experiment/generator.py` : génération des combinaisons et des phrases
- `code/fr_experiment/validation.py` : validations expérimentales
- `code/fr_experiment/lexicon.py` : lexique, frames, verbes, adjectifs
- `code/fr_experiment/language.py` : réalisation morpho-syntaxique des PP/DP
- `code/fr_experiment/writer.py` : export CSV/TSV
- `run_lists/french_run_list.csv` : dernière sortie générée
