# DeepDNA PGx eval: pharmacogenomics questions with and without the DeepDNA MCP server

A small comparison, run on 15 Nov 2026, of Claude models answering 58 pharmacogenomics questions from PGxQA in three arms: no tools, the DeepDNA MCP server, and web search. This repository holds the report (this file), the cases, the rubric, one result row per answer, the sanitized transcripts of all 393 answers, and the code.

DeepDNA is a personal, non-commercial project based in Spain. Its MCP server (`https://deepdna.ai/mcp`) is free, needs no key, is read-only and educational, and does not accept genotypes: an argument such as a genotype is refused and not used, stored or counted.

## Read this first

- **Who did this.** The DeepDNA project itself, which is an interested party. The evaluation was designed, run and graded, and this report was written, by an AI agent (Claude) working for the project. The automatic judge is also a Claude model. The "manual review" of a sample of answers was done by that same agent, not by a person and not by an independent reviewer. Nobody outside the project has reviewed any of it.
- **Covered pairs.** On the 48 cases about drug–gene pairs that DeepDNA covers, Sonnet and Haiku gave the guideline's action more often with DeepDNA than with no tools (Sonnet 77% → 94%, paired exact McNemar p = 0.057, not significant at 0.05; Haiku 58% → 81%, p = 0.019; neither corrected for multiple comparisons). They did NOT do better with DeepDNA than with web search (90% and 81%).
- **Outside coverage.** On the 10 cases about pairs DeepDNA does not cover, Haiku got worse with DeepDNA connected: 7/10 correct with no tools, 3/10 with DeepDNA.
- **Size.** Small n, a single run with no replicates, and 48 of the 58 cases were chosen inside DeepDNA's coverage.
- **What this does not show.** Nothing here supports any conclusion about clinical utility or about patients. See [Limitations](#limitations) and [What can NOT be concluded](#what-can-not-be-concluded).

## Question

Does an assistant (Claude models) answer questions of the form "drug + gene + phenotype → guideline recommendation" better with the DeepDNA MCP server connected than without it? A third arm, web search only, was added as a reference.

## Method

**Cases.** 58 questions taken from PGxQA (Keat et al., https://github.com/KarlKeat/PGxQA, MIT License, commit `0dfb974`), file `test_queries/drug_guidelines_for_pheno_queries.txt` (2,133 questions generated from the CPIC database). Each row carries the question, the text of the CPIC recommendation and its category (avoid / change dose / proceed as normal). The expected answer comes only from there, never from DeepDNA. The file is included unchanged in `data/pgxqa/` with its licence.

- Automatic selection with a fixed seed (`scripts/select_cases.py`), by gene quotas and rotating categories: 48 cases on pairs that DeepDNA covers (11 gene groups: CYP2D6, CYP2C19, CYP2D6+CYP2C19, CYP2C9, CYP2C9+SLCO1B1, SLCO1B1, G6PD, DPYD, TPMT+NUDT15, CYP3A5, UGT1A1) and 10 on pairs it does NOT cover (HLA-B ×3, HLA-A/HLA-B, MT-RNR1, RYR1/CACNA1S, CFTR, CYP2B6, CYP2D6–ondansetron, G6PD–mafenide). "Covered" was decided with the local list of DeepDNA pairs (`data/deepdna_coverage.tsv`), which was used only for that flag.
- Before running anything, the category of 4 cases was corrected by hand where the PGxQA label did not describe the text (`category_adjustments.tsv`, with the reason for each): c04 becomes NORMAL, c14 and c35 become OTHER (no serious-error assessment), c50 becomes AVOID by joining two rows with the same question. The CPIC text was not changed.
- The other set considered, AgenticGenomics (Corpas et al., Zenodo 10.5281/zenodo.20567743, CC BY 4.0, 110 CPIC level A cases), was not used: its small files only carry aggregate scores per case; the case definitions are inside the response JSON files (15–37 MB) and the repository zip, which were not downloaded. It is not a licence problem.

**Arms.** (A) no tools; (B) the DeepDNA MCP server only (`https://deepdna.ai/mcp`, 5 read-only tools); (C) `WebSearch` only. Files and shell were disabled in all three (`--tools`), with no other MCP servers (`--strict-mcp-config`), no user settings (`--setting-sources ""`), a minimal and identical system prompt ("You are a helpful assistant."), run from a neutral working directory whose path does not name the product. Arm C could be included because `claude -p` ran under a subscription (no API key); whether it carries an additional cost was not checked in billing.

**Models.** `sonnet` (claude-sonnet-5-5) and `haiku` (claude-haiku-5-5) on all 58 cases; `opus` (claude-opus-5-5) on a fixed subsample of 15 (12 covered + 3 uncovered). One answer per cell (no replicates).

**Prompt** (the same in all arms; `prompts/question_prompt.txt`): the PGxQA question as is, asking for the recommendation for that phenotype, its strength or level if known, and the source; "If you have tools available, use them to check before answering. If you cannot determine the answer, say so rather than guessing."

**Grading.** Rubric fixed before any answer was generated (`rubric.md`): (1) main action correct against the expected text; (2) serious error = saying "normal use" when avoid or adjust was expected, or the reverse (computed by the code); (3) citation of the CPIC/DPWG guideline; (4) on uncovered cases, whether the answer states that there is no record. Automatic judge: `claude -p --model sonnet` with no tools, which sees the question, the expected text and only the final text of the answer (not the arm or the model). The strength of the recommendation was asked for but not scored (PGxQA does not carry it). 393 answers generated and 393 graded, with no failures or retries.

Naming used below and in the files: AVOID, ADJUST, NORMAL, OTHER, NO_ANSWER. The judge was given these categories with Spanish labels and wrote its one-sentence notes in Spanish; `rubric.md` has the mapping, and the notes are published as written (`judge_note_es`).

## Results

Correct action, with 95% Wilson interval. Full tables in `results.md`; one row per answer in `results.tsv`.

### Cases DeepDNA covers

| Model | Arm | n | Correct action | Serious errors | No answer |
|---|---|---|---|---|---|
| sonnet | A no tools | 48 | 37 (77%; 63–87) | 5/46 | 0 |
| sonnet | B DeepDNA | 48 | 45 (94%; 83–98) | 1/46 | 2 |
| sonnet | C web search | 48 | 43 (90%; 78–95) | 2/46 | 0 |
| haiku | A no tools | 48 | 28 (58%; 44–71) | 11/46 | 7 |
| haiku | B DeepDNA | 48 | 39 (81%; 68–90) | 1/46 | 7 |
| haiku | C web search | 48 | 39 (81%; 68–90) | 1/46 | 5 |
| opus | A no tools | 12 | 12 (100%; 76–100) | 0/11 | 0 |
| opus | B DeepDNA | 12 | 11 (92%; 65–99) | 0/11 | 0 |
| opus | C web search | 12 | 12 (100%; 76–100) | 0/11 | 0 |

Paired comparison on the same 48 cases (exact McNemar, not corrected for multiple comparisons): sonnet A→B, 11 cases become correct and 3 become incorrect (p = 0.057); haiku A→B, 15 and 4 (p = 0.019). B versus C: no significant difference (sonnet p = 0.73; haiku p = 1.00); this sample is too small to show that the two are equivalent. In opus (12 cases) there is nothing to distinguish; the only change is one case that B makes worse.

### Cases DeepDNA does NOT cover (n = 10; opus n = 3)

| Model | Arm | Correct action | States there is no record | Abstains | Serious errors |
|---|---|---|---|---|---|
| sonnet | A | 9/10 | — | 0 | 0 |
| sonnet | B | 9/10 | 10/10 | 1 | 0 |
| sonnet | C | 9/10 | — | 1 | 0 |
| haiku | A | 7/10 | — | 1 | 1 |
| haiku | B | 3/10 (30%; 11–60) | 10/10 | 7 | 0 |
| haiku | C | 9/10 | — | 0 | 0 |
| opus | A / B / C | 3/3 · 3/3 · 3/3 | B: 3/3 | 0 | 0 |

Checked in the 23 raw arm B transcripts: the tool returned "unknown gene" or "no guidance for that pair" in all of them, and no answer attributed to DeepDNA a recommendation it did not give. The difference is in what the model does next: sonnet and opus say there is no record and answer from their own knowledge, saying so; haiku in 7 of 10 gives no recommendation, including cases it got right with no tool (HLA-B*15:02 with carbamazepine and with oxcarbazepine, MT-RNR1, CFTR). With haiku, connecting DeepDNA made the answer worse on uncovered cases (A 7/10 → B 3/10; 4 cases go from correct to no answer, none the other way; exact McNemar p = 0.125). Against web search on the same 10 cases, haiku with DeepDNA was also worse (C 9/10 → B 3/10; 6 cases correct only with web search, none the other way; p = 0.031, not corrected for multiple comparisons).

### All cases, and serious errors by arm

| Model | A | B | C |
|---|---|---|---|
| sonnet (n = 58) | 46 (79%; 67–88) | 54 (93%; 84–97) | 52 (90%; 79–95) |
| haiku (n = 58) | 35 (60%; 47–72) | 42 (72%; 60–82) | 48 (83%; 71–90) |
| opus (n = 15) | 15 (100%; 80–100) | 14 (93%; 70–99) | 15 (100%; 80–100) |

Serious errors summed over the three models (126 assessable answers per arm): A 17, B 2, C 3. The 2 in B are the same case (c02) in sonnet and haiku. Of the 17 in A, 15 are "normal use" where the guideline says avoid or adjust (statins with SLCO1B1 or CYP2C9, voriconazole, atazanavir, tricyclics, paroxetine, citalopram, dexlansoprazole, tenoxicam, tacrolimus, ondansetron) and 2 are "avoid" where there is no recommendation (venlafaxine and hydrocodone in ultrarapid metabolizers, haiku). Full list in `results.md`.

With haiku, over all cases, web search (83%) came out above DeepDNA (72%). Over all 58 cases the difference is not significant (p = 0.21), but it comes from the uncovered cases, and on those 10 alone it is (p = 0.031, uncorrected).

### Citation

Almost all answers name the CPIC guideline for the pair (84–100% depending on the cell); it does not distinguish arms, except haiku B on uncovered cases (2/10, because it abstains). The judge's "citation suspect" field is not reliable and is not used: it flagged as "looks invented" the reference Maillard et al., Clin Pharmacol Ther 2026 (PMID 41618934, the 2025 update of the thiopurine guideline) that DeepDNA returns; the agent checked on PubMed that it exists. No other citation has been verified.

### Tool use

B: 58/58 answers from sonnet and from haiku and 15/15 from opus called DeepDNA (mean 1.3–1.5 calls; almost always `lookup_drug_gene`). C: haiku and opus always searched; sonnet searched in 40/58 and answered from memory in 18, so "C" in sonnet is partly "A".

## Examples

**Correct with DeepDNA where the model alone was wrong (sonnet):** c10 voriconazole in a CYP2C19 rapid metabolizer (A: standard dose; B: alternative); c47 atazanavir in a UGT1A1 poor metabolizer (A: no need to avoid; B: consider an alternative); c28 and c30 fluvastatin and pravastatin (A: desired dose; B: 40 mg cap); c05 desipramine in an intermediate metabolizer (A: standard dose; B: reduce by 25%).

**Failures with DeepDNA:**

- c02, atomoxetine in a CYP2D6 ultrarapid metabolizer: sonnet and haiku with DeepDNA say "usual titration" (serious error under the rubric; expected ADJUST). The DeepDNA record says literally that for the other phenotypes CPIC recommends "the usual titration". Nuance: the CPIC text (40 mg/day, increase to 80 after 3 days, 100 if there is no response) resembles the drug-label regimen, and PGxQA's "change dose" label is debatable; it was not corrected before the run, so it counts as a failure. Sonnet with no tool got it right.
- Phenotypes the record does not detail (Indeterminate, increased function, two-gene combinations): DeepDNA records are a summary per pair, not the per-phenotype table. With DeepDNA, haiku gave no recommendation in 7 covered cases (c08 paroxetine in an intermediate metabolizer, c12, c24, c28, c31, c43, c46) and sonnet in 2 (c15, c43); in 4 of haiku's 7 and in sonnet's 2, the same model with no tool had been right. c43 (mercaptopurine, TPMT normal + NUDT15 indeterminate) fails with DeepDNA in all three models and is opus's only failure.
- c27, fluvastatin with CYP2C9 poor metabolizer + SLCO1B1 poor function (haiku B): it says adjust the dose; the guideline says another statin.
- An inconsistency of the server itself seen in the transcripts: `check_medications` says "84 curated drug–gene pairs across 16 genes" while `lookup_drug_gene` lists 17 known genes; haiku repeated "16 genes" in 3 answers. (Note added at publication: the local coverage list has 84 pairs over 16 genes, and the 17th known gene, HFE, has no drug pair in it, so both numbers may be accurate; the wording still led the model to miscount the gene list.)

## Agreement between the judge and the manual review

24 answers chosen with a fixed seed (8 per arm), graded by hand before seeing the judge's grade (`manual_review.tsv`): action correct 24/24 (100%; CI 86–100); action category 22/24 (92%); citation correct 23/24 (96%). The 3 disagreements do not change any correct answer or serious error. The review was done by the same AI agent that built the evaluation, and it knew which arm each answer belonged to whenever the answer named the tool.

## Limitations

1. **Size.** 48 covered and 10 uncovered cases per model; 15 in opus. The intervals are wide (roughly ±7 to ±13 points for the 48-case cells of sonnet and haiku), and the uncovered and opus cells only show direction. One answer per cell: variation between repetitions was not measured.
2. **Claude models only**, in `claude -p` with a minimal system prompt. It says nothing about ChatGPT, Gemini or Claude in other clients.
3. **Automatic judge** from the same vendor (sonnet). It agreed with the manual review on the sample, but that sample is 24 answers and the reviewer is not independent. Blinding is partial: arm B answers name the tool.
4. **Interested party.** The evaluation was designed, run and graded by an AI agent (Claude) working for the DeepDNA project, which maintains the tool under test. Selection and rubric were fixed before seeing answers and everything is reproducible, but nobody outside the project has reviewed it.
5. **The reference is PGxQA, not a clinician.** It is a snapshot of the CPIC database from 2024; some guidelines have been updated since (thiopurines, 2025) and DeepDNA cites the new one. PGxQA's categories contain errors (4 corrected by hand before the run; c02 remains debatable). Several questions use unusual phenotypes ("Indeterminate", "No Result", activity scores ≥5.0).
6. **Selection bias in favour of DeepDNA in the main table:** 48 of 58 cases are pairs it covers. In real use the share of questions outside coverage (17 genes) will be different, and there, with haiku, the result was worse than with no tool.
7. **The prompt asks the model to use the tools and not to guess.** That favours the model calling the tool (58/58) and abstaining when it does not find the phenotype. With a question lacking that instruction the result may change.
8. Arm C is not fully comparable: sonnet did not search in 18 of 58.
9. Neither the strength of the recommendation nor dose accuracy was scored; "correct action" is only the direction (avoid / adjust / normal).

## What can NOT be concluded

- That DeepDNA improves clinical decisions or patient outcomes: what was measured is whether a text matches a guideline table, for phenotypes already given.
- That DeepDNA is better than web search: on covered cases the difference was not significant (sonnet 94% vs 90%, p = 0.73; haiku 81% vs 81%, p = 1.00), and over all cases haiku did better with web search.
- That the effect holds in more capable models: opus got 12/12 with no tool and 11/12 with DeepDNA.
- That the result generalises to real user questions (natural language, no phenotype given, several drugs) or to genes and drugs outside the 58 cases.
- That the exact figures will repeat: the models are not deterministic and there were no replicates.

What the data do show, with those reservations: on covered pairs, sonnet and haiku gave the guideline's action more often with DeepDNA than with no tools (77 → 94% and 58 → 81%) and with fewer serious errors (16 → 2 between the two), by a margin similar to web search, with no significant difference between the two; and outside coverage the tool always said it had no record, but haiku stopped answering.

## Files

| Path | What it is |
|---|---|
| `cases.tsv` | The 58 cases: question, expected category and text, coverage flag, opus subsample flag |
| `category_adjustments.tsv` | The 4 categories corrected by hand before the run, with reasons |
| `rubric.md` | The grading rubric (translated) and the label mapping |
| `results.tsv` | One row per answer (393 rows) |
| `results.md` | All tables, generated by `scripts/analyze.py` |
| `manual_review_sample.tsv`, `manual_review.tsv` | The 24 sampled answers and their grades by hand |
| `transcripts/<model>/<arm>/<case>.json` | Sanitized transcript of each answer |
| `prompts/`, `config/` | The question prompt, the judge prompt, and the MCP configuration of each arm |
| `scripts/`, `run.sh` | Code |
| `data/pgxqa/` | The PGxQA file the cases come from, with its licence |
| `data/deepdna_coverage.tsv` | The list of DeepDNA pairs used only to flag cases as covered or not |

### Transcripts

`claude -p` writes a raw event stream whose first message describes the machine it ran on, and whose every event carries identifiers and usage metadata. None of that is published. `scripts/sanitize.py` builds each transcript from a fixed list of fields: case id, model, arm, system prompt, prompt, tool calls (name, arguments, result), final answer, and the judge's grade. Two things are deliberately left out besides the metadata: the text returned by web searches (only the titles and URLs of the hits are kept, because it is third-party content) and the models' intermediate reasoning blocks. In arm B the tool names are shown without the local server alias prefix.

## Reproduce

```
git clone https://github.com/alfonsoguv/deepdna-pgx-eval
cd deepdna-pgx-eval
python3 -I scripts/select_cases.py     # rebuilds cases.tsv from data/pgxqa/ (no model calls)
python3 -I scripts/analyze.py          # rebuilds results.tsv and results.md from transcripts/ (no model calls)
python3 -I scripts/verify_readme.py    # recomputes every figure in this file from results.tsv
```

`bash run.sh` performs a new run: it checks the SHA-256 of the PGxQA file, selects the cases, generates the answers, grades them, sanitizes the raw output and writes the tables (about 393 + 393 calls, close to an hour with parallelism 4). It needs Claude Code signed in, and it overwrites the published transcripts and tables with the new run.

Checked: from the files in this repository, `select_cases.py` regenerates `cases.tsv`, and `analyze.py` regenerates `results.tsv` and `results.md`, identically. The scripts published here are an English port of the ones used for the run (files, columns and labels renamed; `analyze.py` reads the sanitized transcripts instead of the raw output), and their `cases.tsv` and `results.tsv` were compared row by row with the originals. In this ported form `run_models.py` and `run.sh` have not been executed end to end, and no second full run from scratch has been made.

## Licence and attribution

Code, report and result files: MIT, copyright DeepDNA (`LICENSE`). The cases derive from PGxQA (https://github.com/KarlKeat/PGxQA, commit `0dfb974`, MIT; notice in `data/pgxqa/LICENSE`), whose recommendation texts come from CPIC guidelines (https://cpicpgx.org). This evaluation is not affiliated with or endorsed by PGxQA, CPIC or Anthropic.

Nothing in this repository is medical advice.

Contact: hello@deepdna.ai
