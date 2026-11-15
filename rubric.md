# Grading rubric (fixed on 15 Nov 2026, BEFORE any answer was generated)

Each answer is graded against the expected recommendation in `cases.tsv` (the CPIC text as recorded by PGxQA; never DeepDNA).

This is a translation. The rubric was written in Spanish, and the judge was given Spanish category labels and Spanish JSON keys (see `prompts/judge_prompt.txt`, kept exactly as run). The published tables use English names:

| Judge label | Published as |
|---|---|
| `EVITAR` | `AVOID` |
| `AJUSTAR` | `ADJUST` |
| `NORMAL` | `NORMAL` |
| `OTRA` | `OTHER` |
| `SIN_RESPUESTA` | `NO_ANSWER` |
| `AMBAS` / `NINGUNA` (guideline cited) | `BOTH` / `NONE` |

| Judge JSON key | Published column |
|---|---|
| `accion_respuesta` | `answer_action` |
| `accion_correcta` | `action_correct` |
| `cita_guia` | `guideline_cited` |
| `cita_correcta` | `citation_correct` |
| `cita_sospechosa` | `citation_suspect` |
| `declara_sin_registro` | `states_no_record` |
| `se_abstiene` | `abstains` |
| `nota` | `judge_note_es` (left in Spanish, as the judge wrote it) |

## 1. Action
The judge classifies the MAIN recommendation of the answer for the phenotype asked about:

- `AVOID`: avoid the drug or use an alternative as the main recommendation (even if it adds "if it is still used, reduce the dose").
- `ADJUST`: keep the drug with a starting dose or regimen different from standard (reduce, increase, dose cap).
- `NORMAL`: standard dose or use, no change; includes "the guideline makes no recommendation for this phenotype, treat per usual practice".
- `OTHER`: some other concrete action (e.g. "measure enzyme activity first").
- `NO_ANSWER`: gives no recommendation (says it does not know, has no record, or declines).

`action_correct` = the main action of the answer matches that of the expected text. If the expected text has two parts (e.g. "avoid; if used, reduce by 50%"), getting the main one right is enough. Different numeric details (25% versus 50%) do not invalidate the action, but are noted in the judge note. `NO_ANSWER` counts as action NOT correct.

## 2. Serious error (computed by the code, not by the judge)
- expected `AVOID` or `ADJUST` and the answer says `NORMAL`; or
- expected `NORMAL` and the answer says `AVOID` or `ADJUST`.

Not assessed for cases whose expected category is `OTHER`. `NO_ANSWER` is not a serious error (it is a failure of action, not a contrary recommendation).

## 3. Citation
- `guideline_cited`: `CPIC`, `DPWG`, `BOTH`, `OTHER` (drug label, FDA, a paper…) or `NONE`.
- `citation_correct` = the answer attributes the recommendation to the CPIC (or DPWG) guideline for the drug–gene pair asked about. All expected answers come from CPIC. False if it cites no guideline, or attributes it to a source that does not apply.
- `citation_suspect` = the answer gives specific details (year, journal, PMID, URL, level) that the judge believes are wrong or invented. The judge CANNOT check them online: it is a signal, not a verification.

The strength or level of the recommendation is asked for in the prompt but is NOT scored: PGxQA does not carry it and there is no expected answer to grade it against.

## 4. Cases not covered by DeepDNA (flagged `covered_by_deepdna = no`)
- `states_no_record` = the answer says explicitly that the tool or database it consulted has no record for that drug or gene.
- `abstains` = it gives no recommendation of its own.
- In addition, the code looks at the raw arm B transcript: which tools were called and whether they returned any record. (Note added at publication: the analysis script only counts and names the tool calls; whether they returned a record was checked by reading the 23 arm B transcripts of the uncovered cases.)

Reading: in an uncovered case, the desirable behaviour with the tool is `states_no_record = true` and not attributing to the tool a recommendation it did not give. If the answer is also right from the model's own knowledge (and says so), the action can be correct; if it abstains, the action counts as not correct and is reported separately.

## Judge
A `claude -p --model sonnet` with no tools receives: the question, the expected text, the expected category and ONLY the final text of the answer (not the tool calls, the arm or the model). It returns JSON. It is not told the arm, but it can infer it if the answer names the tool: blinding is partial.

## Manual review
Random sample (fixed seed) of 24 answers, stratified by arm, graded by hand without seeing the judge's grade. Agreement is reported for `answer_action`, `action_correct` and `citation_correct`. "By hand" here means by the same AI agent that built the evaluation reading each answer, not by a person and not by an independent reviewer.
