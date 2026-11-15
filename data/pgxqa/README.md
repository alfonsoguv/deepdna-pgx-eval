# PGxQA data used by this evaluation

Source: PGxQA, https://github.com/KarlKeat/PGxQA, commit `0dfb974a2281380abc77e9b95eca055b8997475f`, MIT License (see `LICENSE` in this directory, copied unchanged from that repository, with its copyright notice).

| File here | Path in PGxQA | Changes |
|---|---|---|
| `drug_guidelines_for_pheno_queries.txt` | `test_queries/drug_guidelines_for_pheno_queries.txt` | none (SHA-256 in `SHA256SUMS`) |
| `LICENSE` | `LICENSE` | none |

Only this one data file is included, because it is the only one the case selection reads. It holds 2,133 questions that PGxQA generated from the CPIC database, each with the CPIC recommendation text and an action category. The 58 cases in `../../cases.tsv` are rows of this file, chosen by `../../scripts/select_cases.py`; four of them had their category adjusted by hand before the run (`../../category_adjustments.tsv`).

The recommendation texts originate from CPIC (Clinical Pharmacogenetics Implementation Consortium, https://cpicpgx.org) guidelines, as recorded by PGxQA in 2024. They are a snapshot and may not match the current guidelines.

This evaluation is not affiliated with or endorsed by PGxQA or CPIC.
