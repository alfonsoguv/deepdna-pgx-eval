#!/usr/bin/env bash
# Comparative evaluation: does an assistant answer pharmacogenomics questions better with the DeepDNA MCP server than without it?
# Usage: bash run.sh        (SKIP_C=1 bash run.sh skips the web search arm)
#
# This performs a NEW run: case selection, about 393 answers + 393 grading calls to `claude -p`, sanitizing and tables.
# It overwrites transcripts/, results.tsv and results.md with the new run. The figures in README.md describe the
# published run only. To recompute the published tables without calling any model:
#     python3 -I scripts/analyze.py && python3 -I scripts/verify_readme.py
#
# Raw `claude -p` output goes to raw/ (git-ignored: it contains machine and session metadata). Work already present in
# raw/ is not repeated; move raw/ away to start from scratch.
# Read-only against https://deepdna.ai/mcp. Requires `claude` (Claude Code) signed in, curl and python3.
set -euo pipefail
E="$(cd "$(dirname "$0")" && pwd)"
D="$E/data/pgxqa"
# neutral working directory: the path does not name the product
export PGX_EVAL_WORKDIR="${PGX_EVAL_WORKDIR:-${TMPDIR:-/tmp}/pgx-eval-neutral}"
mkdir -p "$D" "$PGX_EVAL_WORKDIR"
# PGxQA (MIT), pinned to the commit of 15 Nov 2026. Data files only; nothing from that repository is executed.
# Both files are already in data/pgxqa/; they are downloaded only if missing.
BASE="https://raw.githubusercontent.com/KarlKeat/PGxQA/0dfb974a2281380abc77e9b95eca055b8997475f"
[[ -s "$D/LICENSE" ]] || curl -fsS -A "research-script/1.0" -o "$D/LICENSE" "$BASE/LICENSE"
[[ -s "$D/drug_guidelines_for_pheno_queries.txt" ]] || curl -fsS -A "research-script/1.0" -o "$D/drug_guidelines_for_pheno_queries.txt" "$BASE/test_queries/drug_guidelines_for_pheno_queries.txt"
(cd "$D" && shasum -a 256 -c SHA256SUMS)
cd "$PGX_EVAL_WORKDIR"
python3 -I "$E/scripts/select_cases.py" "$E"
python3 -I "$E/scripts/run_models.py" "$E" generate
python3 -I "$E/scripts/run_models.py" "$E" grade
python3 -I "$E/scripts/sanitize.py" "$E"
python3 -I "$E/scripts/analyze.py" "$E" > /dev/null
echo "Tables: $E/results.md · one row per answer: $E/results.tsv · transcripts: $E/transcripts/"
