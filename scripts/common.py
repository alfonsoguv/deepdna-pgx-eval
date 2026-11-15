"""Shared helpers: cases, experiment cells, label mapping, and readers for raw and sanitized transcripts."""
import csv, json, os, re

MODELS = ['sonnet', 'haiku', 'opus']
ARMS = ['A', 'B', 'C']   # A no tools · B DeepDNA MCP server only · C WebSearch only
ARM_DESCRIPTION = {'A': 'no tools', 'B': 'DeepDNA MCP server only', 'C': 'web search only'}
SYSTEM_PROMPT = 'You are a helpful assistant.'

# The judge prompt (prompts/judge_prompt.txt) was written with Spanish category labels and Spanish JSON keys,
# and it is kept exactly as it was run. Everything published in this repository uses the English names below.
LABEL_EN = {'EVITAR': 'AVOID', 'AJUSTAR': 'ADJUST', 'NORMAL': 'NORMAL', 'OTRA': 'OTHER', 'SIN_RESPUESTA': 'NO_ANSWER',
            'CPIC': 'CPIC', 'DPWG': 'DPWG', 'AMBAS': 'BOTH', 'NINGUNA': 'NONE'}
LABEL_JUDGE = {'AVOID': 'EVITAR', 'ADJUST': 'AJUSTAR', 'NORMAL': 'NORMAL', 'OTHER': 'OTRA'}
JUDGE_KEYS = {'accion_respuesta': 'answer_action', 'accion_correcta': 'action_correct', 'cita_guia': 'guideline_cited',
              'cita_correcta': 'citation_correct', 'cita_sospechosa': 'citation_suspect',
              'declara_sin_registro': 'states_no_record', 'se_abstiene': 'abstains', 'nota': 'note_es'}

def root(argv):
    """Repository root: first command-line argument, or the parent of scripts/."""
    return argv[1] if len(argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def raw_dir(E):
    """Where raw `claude -p` output is written. Never published: it holds machine and session metadata."""
    return os.environ.get('PGX_EVAL_RAW', E + '/raw')

def cases(E):
    return list(csv.DictReader(open(E + '/cases.tsv'), delimiter='\t'))

def cells(E):
    """(model, arm, case) for the whole evaluation; opus only on its subsample."""
    for m in MODELS:
        for c in cases(E):
            if m == 'opus' and c['opus_subsample'] != 'yes': continue
            for arm in ARMS:
                yield m, arm, c

def question_prompt(E, case):
    return open(E + '/prompts/question_prompt.txt').read().replace('{question}', case['question'])

def read_raw(path):
    """Parse one raw stream-json file. Returns the final text, the tool calls (with their results) and the model id.
    Only these fields are read; everything else in the stream is ignored."""
    out = {'ok': False, 'text': '', 'calls': [], 'model': None, 'web_search_requests': 0, 'exists': os.path.exists(path)}
    if not out['exists']: return out
    by_id = {}
    for line in open(path):
        try: d = json.loads(line)
        except Exception: continue
        t = d.get('type')
        if t == 'system' and d.get('subtype') == 'init':
            out['model'] = d.get('model')
        elif t == 'assistant':
            for c in d['message'].get('content', []):
                if c.get('type') in ('tool_use', 'server_tool_use'):
                    call = {'name': c['name'].split('__')[-1], 'arguments': c.get('input'), 'result': None, 'is_error': False}
                    out['calls'].append(call); by_id[c.get('id')] = call
        elif t == 'user':
            content = d['message'].get('content', [])
            if not isinstance(content, list): continue
            for c in content:
                if not (isinstance(c, dict) and c.get('type') == 'tool_result'): continue
                call = by_id.get(c.get('tool_use_id'))
                if call is None: continue
                call['is_error'] = bool(c.get('is_error'))
                x = c.get('content')
                if isinstance(x, list): x = ' '.join(str(i.get('text', '')) if isinstance(i, dict) else str(i) for i in x)
                if call['name'] == 'WebSearch':
                    # Third-party page content is not republished: keep only the titles and URLs of the hits.
                    call['result'] = {'links': web_links(d.get('tool_use_result'), str(x)), 'content_omitted': True}
                else:
                    call['result'] = str(x)
        elif t == 'result':
            out['text'] = d.get('result') or ''
            out['ok'] = (not d.get('is_error')) and d.get('subtype') == 'success' and bool(out['text'].strip())
            out['web_search_requests'] = sum(v.get('webSearchRequests', 0) for v in (d.get('modelUsage') or {}).values())
    return out

def web_links(structured, text):
    links = []
    if isinstance(structured, dict):
        for r in structured.get('results', []):
            if isinstance(r, dict):
                links += [{'title': i.get('title'), 'url': i.get('url')} for i in r.get('content', []) if isinstance(i, dict)]
    else:
        for m in re.finditer(r'^Links: (\[.*\])$', text, re.M):
            try: links += [{'title': i.get('title'), 'url': i.get('url')} for i in json.loads(m.group(1))]
            except Exception: pass
    return links

def json_from(text):
    """Extract the JSON object from the judge's reply."""
    m = re.search(r'\{.*\}', text, re.S)
    if not m: return None
    s = re.sub(r'//[^\n"]*$', '', m.group(0), flags=re.M)
    try: return json.loads(s)
    except Exception: return None

def transcript_path(E, model, arm, case_id):
    return f'{E}/transcripts/{model}/{arm}/{case_id}.json'

def read_transcript(E, model, arm, case_id):
    p = transcript_path(E, model, arm, case_id)
    return json.load(open(p)) if os.path.exists(p) else None
