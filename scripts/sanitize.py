#!/usr/bin/env python3
"""Turn the raw `claude -p` stream-json output into the minimal transcripts that are published.
Usage: python3 -I scripts/sanitize.py [repo_root]

The raw stream starts with a start-up message describing the machine it ran on (working directory, session
identifiers, installed tools, plugins, skills, agents, servers, account details) and carries identifiers and usage
metadata on every event. None of that is copied. This script builds each transcript from a fixed list of fields:
case id, model, arm, prompt, tool calls (name, arguments, result), final answer and the judge's grade.
For web search calls only the titles and URLs of the hits are kept, not the text returned with them.
The model's intermediate reasoning blocks are not kept either."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
E = common.root(sys.argv)
RAW = common.raw_dir(E)

n = 0
for m, arm, c in common.cells(E):
    r = common.read_raw(f"{RAW}/answers/{m}/{arm}/{c['id']}.jsonl")
    if not r['exists']: continue   # cell not run (e.g. arm C skipped)
    j = common.json_from(common.read_raw(f"{RAW}/grading/{m}/{arm}/{c['id']}.jsonl")['text']) if r['ok'] else None
    judge = None
    if j is not None:
        judge = {'model': 'sonnet'}
        for k_raw, k in common.JUDGE_KEYS.items():
            v = j.get(k_raw, '')
            judge[k] = common.LABEL_EN.get(v, v) if k in ('answer_action', 'guideline_cited') else v
    t = {'case_id': c['id'], 'model': m, 'model_id': r['model'], 'arm': arm, 'arm_description': common.ARM_DESCRIPTION[arm],
         'system_prompt': common.SYSTEM_PROMPT, 'prompt': common.question_prompt(E, c), 'answered': r['ok'],
         'tool_calls': r['calls'], 'web_search_requests': r['web_search_requests'], 'final_answer': r['text'], 'judge': judge}
    p = common.transcript_path(E, m, arm, c['id'])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        json.dump(t, f, ensure_ascii=False, indent=1); f.write('\n')
    n += 1
print(n, 'transcripts written')
