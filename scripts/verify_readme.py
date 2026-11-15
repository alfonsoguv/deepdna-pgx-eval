#!/usr/bin/env python3
"""Recompute every figure in README.md and check that the README states it.
Usage: python3 -I scripts/verify_readme.py [repo_root]

Each figure is recomputed from results.tsv (plus cases.tsv, manual_review.tsv, category_adjustments.tsv, the data files
and, for the statements about tool output, the transcripts) and the exact sentence fragment or table row is looked up
in README.md. Then every number left in the README that no check accounts for is listed; the run fails if any remains.
Numbers that do not come from the results (dates, doses quoted from guideline text, identifiers) are in STATIC."""
import csv, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
E = common.root(sys.argv)
R = list(csv.DictReader(open(E + '/results.tsv'), delimiter='\t'))
CASES = {c['id']: c for c in common.cases(E)}
README = re.sub(r'\s+', ' ', open(E + '/README.md').read())
checks = []          # (description, fragment expected in the README)
def claim(desc, fragment): checks.append((desc, fragment))

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)
def ci(k, n):
    p, lo, hi = wilson(k, n); return f'{100*p:.0f}%; {100*lo:.0f}–{100*hi:.0f}'
def pct(k, n): return f'{100*k/n:.0f}'
def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n)
ok = lambda r: r['action_correct'] == 'True'
yes = lambda r, k: r[k] == 'True'
def sel(model=None, arm=None, covered=None):
    return [r for r in R if (model is None or r['model'] == model) and (arm is None or r['arm'] == arm)
            and (covered is None or r['covered'] == covered)]
idx = {(r['model'], r['arm'], r['id']): r for r in R}
def serious(rs): return sum(int(r['serious_error']) for r in rs if r['expected'] != 'OTHER')
def assessable(rs): return sum(r['expected'] != 'OTHER' for r in rs)
def paired(model, x, y, covered=None):
    ids = [r['id'] for r in sel(model, x, covered)]
    b = sum(ok(idx[model, x, i]) and not ok(idx[model, y, i]) for i in ids)
    c = sum(ok(idx[model, y, i]) and not ok(idx[model, x, i]) for i in ids)
    return b, c, mcnemar(b, c)
def K(model, arm, covered=None): return sum(ok(r) for r in sel(model, arm, covered))
def N(model, arm, covered=None): return len(sel(model, arm, covered))

# ---------- sizes ----------
n_cases, n_cov, n_unc = len(CASES), sum(c['covered_by_deepdna'] == 'yes' for c in CASES.values()), sum(c['covered_by_deepdna'] == 'no' for c in CASES.values())
sub = [c for c in CASES.values() if c['opus_subsample'] == 'yes']
sub_cov = sum(c['covered_by_deepdna'] == 'yes' for c in sub)
n_pgxqa = sum(1 for _ in open(E + '/data/pgxqa/drug_guidelines_for_pheno_queries.txt')) - 1
groups = {c['genes'] for c in CASES.values() if c['covered_by_deepdna'] == 'yes'}
adj = list(csv.DictReader(open(E + '/category_adjustments.tsv'), delimiter='\t'))
assert len(adj) == sum(c['expected_category'] != c['expected_category_pgxqa'] for c in CASES.values())
assert {a['id']: a['new_category'] for a in adj} == {'c04': 'NORMAL', 'c14': 'OTHER', 'c35': 'OTHER', 'c50': 'AVOID'}
unc_hlab = sum(c['genes'] == 'HLA-B' for c in CASES.values() if c['covered_by_deepdna'] == 'no')
assert all(r['answered'] == '1' and r['graded'] == '1' for r in R)
assert {r['model']: r['model_id'] for r in R} == {'sonnet': 'claude-sonnet-5-5', 'haiku': 'claude-haiku-5-5', 'opus': 'claude-opus-5-5'}
claim('cases', f'answering {n_cases} pharmacogenomics questions')
claim('answers', f'transcripts of all {len(R)} answers')
claim('cases', f'{n_cases} questions taken from PGxQA')
claim('PGxQA rows', f'({n_pgxqa:,} questions generated')
claim('covered cases, gene groups', f'{n_cov} cases on pairs that DeepDNA covers ({len(groups)} gene groups:')
claim('uncovered cases', f'and {n_unc} on pairs it does NOT cover (HLA-B ×{unc_hlab},')
claim('adjusted categories', f'the category of {len(adj)} cases was corrected')
claim('models', f'on all {n_cases} cases; `opus` (claude-opus-5-5) on a fixed subsample of {len(sub)} ({sub_cov} covered + {len(sub)-sub_cov} uncovered)')
claim('answers', f'{len(R)} answers generated and {sum(r["graded"]=="1" for r in R)} graded')
claim('summary sizes', f'On the {n_cov} cases about drug–gene pairs')
claim('summary sizes', f'On the {n_unc} cases about pairs DeepDNA does not cover')
claim('summary sizes', f'{n_cov} of the {n_cases} cases were chosen inside')
claim('limitation 1', f'{n_cov} covered and {n_unc} uncovered cases per model; {len(sub)} in opus')
claim('limitation 6', f'{n_cov} of {n_cases} cases are pairs it covers')
claim('scope', f'outside the {n_cases} cases')
claim('files', f'One row per answer ({len(R)} rows)')
claim('files', f'The {n_cases} cases: question')
claim('files', f'The {len(adj)} categories corrected by hand')
claim('run size', f'(about {len(R)} + {len(R)} calls')
claim('limitation 5', f'({len(adj)} corrected by hand before the run')

# ---------- covered table ----------
LAB = {'A': 'A no tools', 'B': 'B DeepDNA', 'C': 'C web search'}
for m in common.MODELS:
    for a in common.ARMS:
        rs = sel(m, a, 'yes'); n = len(rs); k = sum(ok(r) for r in rs)
        claim(f'covered table {m} {a}', f"| {m} | {LAB[a]} | {n} | {k} ({ci(k, n)}) | {serious(rs)}/{assessable(rs)} | {sum(r['answer_action']=='NO_ANSWER' for r in rs)} |")
p = lambda m, a, cov=None: pct(K(m, a, cov), N(m, a, cov))
_sp = paired('sonnet', 'A', 'B', 'yes')[2]; _hp = paired('haiku', 'A', 'B', 'yes')[2]
claim('headline A→B', f"(Sonnet {p('sonnet','A','yes')}% → {p('sonnet','B','yes')}%, paired exact McNemar p = {_sp:.3f}, not significant at 0.05; Haiku {p('haiku','A','yes')}% → {p('haiku','B','yes')}%, p = {_hp:.3f}; neither corrected for multiple comparisons)")
claim('not concluded B vs C', f"(sonnet {p('sonnet','B','yes')}% vs {p('sonnet','C','yes')}%, p = {paired('sonnet','C','B','yes')[2]:.2f}; haiku {p('haiku','B','yes')}% vs {p('haiku','C','yes')}%, p = {paired('haiku','C','B','yes')[2]:.2f})")
claim('headline C', f"than with web search ({p('sonnet','C','yes')}% and {p('haiku','C','yes')}%)")
claim('headline A→B (closing)', f"({p('sonnet','A','yes')} → {p('sonnet','B','yes')}% and {p('haiku','A','yes')} → {p('haiku','B','yes')}%)")
sb, sc, sp = paired('sonnet', 'A', 'B', 'yes'); hb, hc, hp = paired('haiku', 'A', 'B', 'yes')
claim('McNemar A vs B', f'on the same {n_cov} cases (exact McNemar, not corrected for multiple comparisons): sonnet A→B, {sc} cases become correct and {sb} become incorrect (p = {sp:.3f}); haiku A→B, {hc} and {hb} (p = {hp:.3f})')
claim('McNemar B vs C', f"(sonnet p = {paired('sonnet','C','B','yes')[2]:.2f}; haiku p = {paired('haiku','C','B','yes')[2]:.2f})")
ob, oc, _ = paired('opus', 'A', 'B', 'yes')
assert (ob, oc) == (1, 0) and paired('opus', 'A', 'C', 'yes')[:2] == (0, 0)
claim('opus covered', f"In opus ({N('opus','A','yes')} cases) there is nothing to distinguish; the only change is one case that B makes worse")
claim('opus covered', f"opus got {K('opus','A','yes')}/{N('opus','A','yes')} with no tool and {K('opus','B','yes')}/{N('opus','B','yes')} with DeepDNA")
hw = [50 * (wilson(K(m, a, 'yes'), n_cov)[2] - wilson(K(m, a, 'yes'), n_cov)[1]) for m in ('sonnet', 'haiku') for a in common.ARMS]
claim('interval half-widths', f'(roughly ±{min(hw):.0f} to ±{max(hw):.0f} points for the {n_cov}-case cells of sonnet and haiku)')

# ---------- uncovered table ----------
claim('uncovered header', f"(n = {n_unc}; opus n = {N('opus','A','no')})")
for m in ('sonnet', 'haiku'):
    for a in common.ARMS:
        rs = sel(m, a, 'no'); n = len(rs); k = sum(ok(r) for r in rs)
        cell = f'{k}/{n}' + (f' ({ci(k, n)})' if (m, a) == ('haiku', 'B') else '')
        states = f"{sum(yes(r,'states_no_record') for r in rs)}/{n}" if a == 'B' else '—'
        claim(f'uncovered table {m} {a}', f"| {m} | {a} | {cell} | {states} | {sum(yes(r,'abstains') for r in rs)} | {serious(rs)} |")
o = {a: sel('opus', a, 'no') for a in common.ARMS}
claim('uncovered table opus', '| opus | A / B / C | ' + ' · '.join(f'{sum(ok(r) for r in o[a])}/{len(o[a])}' for a in common.ARMS)
      + f" | B: {sum(yes(r,'states_no_record') for r in o['B'])}/{len(o['B'])} | {sum(yes(r,'abstains') for a in o for r in o[a])} | {sum(serious(o[a]) for a in o)} |")
hA, hB = K('haiku', 'A', 'no'), K('haiku', 'B', 'no')
claim('haiku uncovered', f'{hA}/{n_unc} correct with no tools, {hB}/{n_unc} with DeepDNA')
lost = [r['id'] for r in sel('haiku', 'A', 'no') if ok(r) and not ok(idx['haiku', 'B', r['id']])]
gained = [r['id'] for r in sel('haiku', 'A', 'no') if not ok(r) and ok(idx['haiku', 'B', r['id']])]
assert all(idx['haiku', 'B', i]['answer_action'] == 'NO_ANSWER' for i in lost)
assert sorted(CASES[i]['drug'] for i in lost) == ['carbamazepine', 'ivacaftor', 'oxcarbazepine', 'paromomycin']
_ab = paired('haiku', 'A', 'B', 'no'); _cb = paired('haiku', 'C', 'B', 'no')
claim('haiku uncovered', f'(A {hA}/{n_unc} → B {hB}/{n_unc}; {len(lost)} cases go from correct to no answer, none the other way; exact McNemar p = {_ab[2]:.3f})')
claim('haiku uncovered vs web', f"(C {K('haiku','C','no')}/{n_unc} → B {hB}/{n_unc}; {_cb[0]} cases correct only with web search, none the other way; p = {_cb[2]:.3f}, not corrected for multiple comparisons)")
assert _cb[1] == 0 and _ab[1] == 0 and _ab[0] == len(lost)
claim('haiku all vs web (sizes)', f'Over all {n_cases} cases the difference')
claim('haiku uncovered vs web (size)', f'on the same {n_unc} cases')
claim('haiku all vs web', f"on those {n_unc} alone it is (p = {_cb[2]:.3f}, uncorrected)")
assert not gained
h_abst = sum(yes(r, 'abstains') for r in sel('haiku', 'B', 'no'))
claim('haiku abstains', f'haiku in {h_abst} of {n_unc} gives no recommendation')
# transcripts of arm B on uncovered cases: the tool never returned a record
unc_B = [(r['model'], r['id']) for r in sel(None, 'B', 'no')]
for m, i in unc_B:
    t = common.read_transcript(E, m, 'B', i)
    for c in t['tool_calls']:
        res = c['result']
        if c['name'] == 'lookup_drug_gene': assert c['is_error'] and (res.startswith('Unknown gene') or res.startswith('No guidance curated')), (m, i)
        elif c['name'] == 'check_medications': assert json.loads(res)['with_curated_records'] == [], (m, i)
        elif c['name'] == 'lookup_variant': assert c['is_error'], (m, i)
        else: raise AssertionError((m, i, c['name']))
    assert any(c['name'] == 'lookup_drug_gene' for c in t['tool_calls'])
claim('uncovered B transcripts', f'Checked in the {len(unc_B)} raw arm B transcripts')
claim('uncovered B transcripts (rubric note is in rubric.md)', 'the tool returned "unknown gene" or "no guidance for that pair" in all of them')

# ---------- all cases, serious errors ----------
for m in common.MODELS:
    claim(f'all-cases table {m}', f"| {m} (n = {N(m,'A')}) | " + ' | '.join(f"{K(m,a)} ({ci(K(m,a), N(m,a))})" for a in common.ARMS) + ' |')
S = {a: [r for r in sel(None, a) if r['serious_error'] == '1'] for a in common.ARMS}
claim('serious errors', f"({assessable(sel(None,'A'))} assessable answers per arm): A {len(S['A'])}, B {len(S['B'])}, C {len(S['C'])}")
assert assessable(sel(None, 'A')) == assessable(sel(None, 'B')) == assessable(sel(None, 'C'))
assert {(r['model'], r['id']) for r in S['B']} == {('sonnet', 'c02'), ('haiku', 'c02')}
claim('serious errors B', f"The {len(S['B'])} in B are the same case (c02) in sonnet and haiku")
to_normal = [r for r in S['A'] if r['answer_action'] == 'NORMAL']; to_avoid = [r for r in S['A'] if r['answer_action'] != 'NORMAL']
assert {(r['model'], r['drug'], r['answer_action']) for r in to_avoid} == {('haiku', 'venlafaxine', 'AVOID'), ('haiku', 'hydrocodone', 'AVOID')}
assert {r['drug'] for r in to_normal} == {'fluvastatin', 'pravastatin', 'simvastatin', 'voriconazole', 'atazanavir', 'desipramine', 'doxepin',
                                         'paroxetine', 'citalopram', 'dexlansoprazole', 'tenoxicam', 'tacrolimus', 'ondansetron'}
claim('serious errors A', f"Of the {len(S['A'])} in A, {len(to_normal)} are \"normal use\"")
claim('serious errors A', f'and {len(to_avoid)} are "avoid" where there is no recommendation')
sA = serious(sel('sonnet', 'A', 'yes')) + serious(sel('haiku', 'A', 'yes')); sB = serious(sel('sonnet', 'B', 'yes')) + serious(sel('haiku', 'B', 'yes'))
claim('serious errors covered', f'({sA} → {sB} between the two)')
claim('haiku all cases', f"web search ({p('haiku','C')}%) came out above DeepDNA ({p('haiku','B')}%)")
claim('haiku all cases', f"not significant (p = {paired('haiku','C','B')[2]:.2f})")
assert K('haiku', 'C') > K('haiku', 'B') and K('sonnet', 'B', 'yes') > K('sonnet', 'C', 'yes') and K('haiku', 'B', 'yes') == K('haiku', 'C', 'yes')

# ---------- citation, tool use ----------
cit = [100 * sum(yes(r, 'citation_correct') for r in sel(m, a)) / N(m, a) for m in common.MODELS for a in common.ARMS]
claim('citation range', f'({min(cit):.0f}–{max(cit):.0f}% depending on the cell)')
hb_unc = sel('haiku', 'B', 'no')
claim('citation haiku B uncovered', f"({sum(yes(r,'citation_correct') for r in hb_unc)}/{len(hb_unc)}, because it abstains)")
used = lambda m, a: sum(int(r['n_tool_calls']) > 0 for r in sel(m, a))
assert used('sonnet', 'B') == N('sonnet', 'B') == used('haiku', 'B') == N('haiku', 'B') and used('opus', 'B') == N('opus', 'B')
claim('tool use B', f"B: {used('sonnet','B')}/{N('sonnet','B')} answers from sonnet and from haiku and {used('opus','B')}/{N('opus','B')} from opus called DeepDNA")
means = [sum(int(r['n_tool_calls']) for r in sel(m, 'B')) / N(m, 'B') for m in common.MODELS]
claim('tool use B', f'(mean {min(means):.1f}–{max(means):.1f} calls')
assert all('lookup_drug_gene' in r['tools_called'] for r in sel(None, 'B'))
assert used('haiku', 'C') == N('haiku', 'C') and used('opus', 'C') == N('opus', 'C')
claim('tool use C', f"sonnet searched in {used('sonnet','C')}/{N('sonnet','C')} and answered from memory in {N('sonnet','C')-used('sonnet','C')},")
claim('limitation 7', f"({used('sonnet','B')}/{N('sonnet','B')})")
claim('limitation 8', f"sonnet did not search in {N('sonnet','C')-used('sonnet','C')} of {N('sonnet','C')}")

# ---------- examples ----------
for i in ('c10', 'c47', 'c28', 'c30', 'c05'):
    assert not ok(idx['sonnet', 'A', i]) and ok(idx['sonnet', 'B', i]) and idx['sonnet', 'A', i]['answer_action'] == 'NORMAL', i
for m in ('sonnet', 'haiku'):
    r = idx[m, 'B', 'c02']; assert r['expected'] == 'ADJUST' and r['answer_action'] == 'NORMAL' and r['serious_error'] == '1'
assert ok(idx['sonnet', 'A', 'c02'])
assert 'the usual titration' in common.read_transcript(E, 'sonnet', 'B', 'c02')['tool_calls'][0]['result']
noans = lambda m: [r['id'] for r in sel(m, 'B', 'yes') if r['answer_action'] == 'NO_ANSWER']
hn, sn = noans('haiku'), noans('sonnet')
assert hn == ['c08', 'c12', 'c24', 'c28', 'c31', 'c43', 'c46'] and sn == ['c15', 'c43']
claim('no answer with DeepDNA', f'haiku gave no recommendation in {len(hn)} covered cases (c08 paroxetine in an intermediate metabolizer, c12, c24, c28, c31, c43, c46) and sonnet in {len(sn)} (c15, c43)')
h_was_ok = sum(ok(idx['haiku', 'A', i]) for i in hn); assert all(ok(idx['sonnet', 'A', i]) for i in sn)
claim('no answer with DeepDNA', f"in {h_was_ok} of haiku's {len(hn)} and in sonnet's {len(sn)}, the same model with no tool had been right")
assert all(not ok(idx[m, 'B', 'c43']) for m in common.MODELS) and [r['id'] for r in sel('opus') if not ok(r)] == ['c43']
r = idx['haiku', 'B', 'c27']; assert r['expected'] == 'AVOID' and r['answer_action'] == 'ADJUST'
texts = [(m, i, c['result']) for (m, a, i) in idx if a == 'B' for c in common.read_transcript(E, m, 'B', i)['tool_calls']]
assert any('84 curated drug–gene pairs across 16 genes' in t for _, _, t in texts)
known = next(t for _, _, t in texts if t.startswith('Unknown gene'))
n_known = len(known.split('Known genes:')[1].strip(' .').split(', '))
cov_rows = list(csv.DictReader(open(E + '/data/deepdna_coverage.tsv'), delimiter='\t'))
cov_genes = {r['gene'] for r in cov_rows}
assert 'HFE' not in cov_genes and 'HFE' in known
said16 = sum(('16 genes' in t['final_answer'] or '16 curated genes' in t['final_answer'])
             for t in (common.read_transcript(E, 'haiku', 'B', r['id']) for r in sel('haiku', 'B')))
claim('server wording', f'`check_medications` says "84 curated drug–gene pairs across 16 genes" while `lookup_drug_gene` lists {n_known} known genes; haiku repeated "16 genes" in {said16} answers')
claim('server wording', f'the local coverage list has {len(cov_rows)} pairs over {len(cov_genes)} genes, and the {n_known}th known gene, HFE,')
claim('limitation 6', f'outside coverage ({n_known} genes)')

# ---------- manual review ----------
man = list(csv.DictReader(open(E + '/manual_review.tsv'), delimiter='\t'))
agree = {}
for f in ('answer_action', 'action_correct', 'citation_correct'):
    agree[f] = sum((idx[x['model'], x['arm'], x['id']][f] if f == 'answer_action' else ('yes' if yes(idx[x['model'], x['arm'], x['id']], f) else 'no')) == x[f] for x in man)
per_arm = {a: sum(x['arm'] == a for x in man) for a in common.ARMS}; assert len(set(per_arm.values())) == 1
nm = len(man); dis = sum(nm - v for v in agree.values())
claim('manual review', f"{nm} answers chosen with a fixed seed ({per_arm['A']} per arm)")
claim('manual review', f"action correct {agree['action_correct']}/{nm} ({ci(agree['action_correct'], nm).replace('; ', '; CI ')}); action category {agree['answer_action']}/{nm} ({pct(agree['answer_action'], nm)}%); citation correct {agree['citation_correct']}/{nm} ({pct(agree['citation_correct'], nm)}%)")
claim('manual review', f'The {dis} disagreements do not change any correct answer or serious error')
claim('manual review', f'that sample is {nm} answers')
claim('files', f'The {nm} sampled answers')

# ---------- numbers that do not come from the results ----------
STATIC = [
    'run on 15 Nov 2026', 'commit `0dfb974`', '95% Wilson interval', 'Zenodo 10.5281/zenodo.20567743, CC BY 4.0, 110 CPIC level A cases',
    '(15–37 MB)', '5 read-only tools',  # the tool count comes from the server's tool list at run time; only 4 distinct tools were called
    '`sonnet` (claude-sonnet-5-5) and `haiku` (claude-haiku-5-5)', 'B: 40 mg cap', 'reduce by 25%',
    '(40 mg/day, increase to 80 after 3 days, 100 if there is no response)', 'Clin Pharmacol Ther 2026 (PMID 41618934, the 2025 update',
    'database from 2024', '(thiopurines, 2025)', 'activity scores ≥5.0', 'HLA-B*15:02', 'SHA-256', 'close to an hour with parallelism 4',
    'python3', 'c04 becomes NORMAL, c14 and c35 become OTHER', 'c50 becomes AVOID', 'c02 remains debatable', '- c02, atomoxetine',
    '(1) main action', '(2) serious error', '(3) citation of', '(4) on uncovered cases',   # numbering of the rubric items
    'c10 voriconazole', 'c47 atazanavir', 'c28 and c30 fluvastatin', 'c05 desipramine', 'c43 (mercaptopurine', '- c27, fluvastatin',
]
GENES = r'\b(CYP2D6|CYP2C19|CYP2C9|CYP2B6|CYP3A5|SLCO1B1|G6PD|UGT1A1|NUDT15|RYR1|CACNA1S|MT-RNR1)\b'

failed = [(d, f) for d, f in checks if f not in README]
rest = README
for _, f in checks:
    rest = rest.replace(f, ' ')
missing_static = [s for s in STATIC if s not in README]
for s in STATIC: rest = rest.replace(s, ' ')
rest = re.sub(GENES, ' ', rest)
rest = re.sub(r'^\s*\d+\. ', ' ', re.sub(r' (\d)\. \*\*', r' **', rest))   # numbering of the limitations list
left = sorted(set(re.findall(r'\S*\d\S*', rest)))
left = [x for x in left if not re.fullmatch(r'[1-9]\.', x)]

print(f'README figures checked against the data: {len(checks) - len(failed)}/{len(checks)} found as stated')
for d, f in failed: print('  NOT FOUND:', d, '->', f)
print(f'Numbers not derived from the results (dates, doses, identifiers), listed in STATIC: {len(STATIC)}' + (f'; not in README: {missing_static}' if missing_static else ''))
print(f'Numbers in README.md not accounted for by any check: {len(left)}' + (f' -> {left}' if left else ''))
sys.exit(1 if failed or left or missing_static else 0)
