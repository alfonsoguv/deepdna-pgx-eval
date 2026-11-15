#!/usr/bin/env python3
"""Launch `claude -p` to generate answers or to grade them. Usage:
   python3 -I scripts/run_models.py <repo_root> generate|grade
Parallelism 4, one retry per failure, raw output under raw/answers/ and raw/grading/ (not published; see
scripts/sanitize.py). Work that is already there is not repeated."""
import os, subprocess, sys, tempfile, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

E, PHASE = sys.argv[1], sys.argv[2]
RAW = common.raw_dir(E)
# neutral working directory: its path does not contain the product name
NEUTRAL = os.environ.get('PGX_EVAL_WORKDIR', os.path.join(tempfile.gettempdir(), 'pgx-eval-neutral'))
os.makedirs(NEUTRAL, exist_ok=True)
ENV = {k: v for k, v in os.environ.items() if k not in ('CLAUDECODE', 'CLAUDE_CODE_ENTRYPOINT')}
BASE = ['--system-prompt', common.SYSTEM_PROMPT, '--strict-mcp-config', '--setting-sources', '', '--no-session-persistence',
        '--output-format', 'stream-json', '--verbose']
ARM_FLAGS = {  # files and shell disabled in all three: --tools leaves only what is named
    'A': ['--tools', '', '--mcp-config', E + '/config/mcp_empty.json'],
    'B': ['--tools', '', '--mcp-config', E + '/config/mcp.json', '--allowedTools', 'mcp__pgx'],
    'C': ['--tools', 'WebSearch', '--allowedTools', 'WebSearch', '--mcp-config', E + '/config/mcp_empty.json'],
}

def claude(prompt, model, extra, out_path, valid):
    if os.path.exists(out_path) and valid(out_path): return 'cached'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    for attempt in (1, 2):
        try:
            with open(out_path + '.tmp', 'w') as f, open(out_path + '.err', 'w') as e:
                subprocess.run(['claude', '-p', prompt, '--model', model] + BASE + extra, cwd=NEUTRAL, env=ENV,
                               stdin=subprocess.DEVNULL, stdout=f, stderr=e, timeout=420)
        except subprocess.TimeoutExpired:
            pass
        if valid(out_path + '.tmp'):
            os.replace(out_path + '.tmp', out_path); return 'ok' if attempt == 1 else 'ok_retry'
        os.replace(out_path + '.tmp', out_path + f'.failed{attempt}')
    return 'FAILED'

def generate(job):
    m, arm, c = job
    return job, claude(common.question_prompt(E, c), m, ARM_FLAGS[arm], f"{RAW}/answers/{m}/{arm}/{c['id']}.jsonl",
                       lambda f: common.read_raw(f)['ok'])

def grade(job):
    m, arm, c = job
    r = common.read_raw(f"{RAW}/answers/{m}/{arm}/{c['id']}.jsonl")
    if not r['ok']: return job, 'no_answer_to_grade'
    # the judge sees the question, the expected text and category, and ONLY the final answer text (not the arm, model or tool calls)
    p = open(E + '/prompts/judge_prompt.txt').read().format(
        question=c['question'], expected_text=c['expected_text'],
        expected_category=common.LABEL_JUDGE[c['expected_category']], answer=r['text'])
    return job, claude(p, 'sonnet', ARM_FLAGS['A'], f"{RAW}/grading/{m}/{arm}/{c['id']}.jsonl",
                       lambda f: common.json_from(common.read_raw(f)['text']) is not None)

jobs = list(common.cells(E))
if PHASE == 'generate' and os.environ.get('SKIP_C'): jobs = [j for j in jobs if j[1] != 'C']
fn = generate if PHASE == 'generate' else grade
n = {}
with cf.ThreadPoolExecutor(4) as ex:
    for (m, arm, c), st in ex.map(fn, jobs):
        n[st] = n.get(st, 0) + 1
        if st not in ('ok', 'cached'): print(f'{st}: {m}/{arm}/{c["id"]}', file=sys.stderr, flush=True)
print(PHASE, len(jobs), 'jobs:', n)
