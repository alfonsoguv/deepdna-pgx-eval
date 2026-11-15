#!/usr/bin/env python3
"""Select the evaluation cases from PGxQA (MIT), deterministically (fixed seed).
Usage: python3 -I scripts/select_cases.py [repo_root]
The expected answer and its category come ONLY from PGxQA (which took them from the CPIC database).
data/deepdna_coverage.tsv is used only to flag whether the drug-gene pair is in DeepDNA."""
import csv, os, random, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
E = common.root(sys.argv)
SEED = 20261115
rows = list(csv.DictReader(open(E + '/data/pgxqa/drug_guidelines_for_pheno_queries.txt'), delimiter='\t'))
cov = {(r['gene'], r['drug']) for r in csv.DictReader(open(E + '/data/deepdna_coverage.tsv'), delimiter='\t')}

def cat(r):
    c = r['concurring_recommendation']
    if c.startswith('Avoid'): return 'AVOID'
    if c.startswith('Take'): return 'ADJUST'
    if c.startswith('Proceed'): return 'NORMAL'
    raise ValueError(c)

def covered(r):
    return all((g, r['drug']) in cov for g in r['genes'].split(';'))
def uncovered(r):  # no gene of the case has that drug in DeepDNA
    return not any((g, r['drug']) in cov for g in r['genes'].split(';'))

# quotas per gene group (defined before seeing any result)
COVERED_QUOTAS = [('CYP2D6', 9), ('CYP2C19', 8), ('CYP2D6;CYP2C19', 4), ('CYP2C9', 5), ('CYP2C9;SLCO1B1', 2),
                  ('SLCO1B1', 5), ('G6PD', 4), ('DPYD', 3), ('TPMT;NUDT15', 4), ('CYP3A5', 2), ('UGT1A1', 2)]
UNCOVERED_QUOTAS = [('HLA-B', 3), ('HLA-A;HLA-B', 1), ('MT-RNR1', 1), ('RYR1;CACNA1S', 1), ('CFTR', 1),
                    ('CYP2B6', 1), ('CYP2D6', 1), ('G6PD', 1)]
ORDER = ['AVOID', 'ADJUST', 'NORMAL']

def pick(pool, n, rng):
    """Spread across categories (rotating) and avoid repeating a drug while unused drugs remain."""
    by = collections.defaultdict(list)
    for r in pool: by[cat(r)].append(r)
    for v in by.values(): rng.shuffle(v)
    out, used, i, guard = [], collections.Counter(), 0, 0
    while len(out) < n and guard < 10000:
        guard += 1
        c = ORDER[i % 3]; i += 1
        cand = [r for r in by[c] if r not in out]
        if not cand: continue
        m = min(used[r['drug']] for r in cand)
        r = next(r for r in cand if used[r['drug']] == m)
        out.append(r); used[r['drug']] += 1
    return out

rng = random.Random(SEED)
sel = []
for genes, n in COVERED_QUOTAS:
    pool = [r for r in rows if r['genes'] == genes and covered(r)]
    sel += [('yes', r) for r in pick(pool, n, rng)]
for genes, n in UNCOVERED_QUOTAS:
    pool = [r for r in rows if r['genes'] == genes and uncovered(r) and r['drug'] not in ('phenytoin', 'fosphenytoin')]
    sel += [('no', r) for r in pick(pool, n, rng)]

# category adjustments made by hand BEFORE running anything (see category_adjustments.tsv); the CPIC text is never changed, only added to
adj = {r['id']: r for r in csv.DictReader(open(E + '/category_adjustments.tsv'), delimiter='\t')}
# opus subsample: 12 covered + 3 uncovered, same seed
ids = [(f'c{i:02d}', c) for i, (c, r) in enumerate(sel, 1)]
rng2 = random.Random(SEED + 1)
sub = set(rng2.sample([i for i, c in ids if c == 'yes'], 12) + rng2.sample([i for i, c in ids if c == 'no'], 3))
with open(E + '/cases.tsv', 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(['id', 'covered_by_deepdna', 'opus_subsample', 'genes', 'drug', 'question', 'expected_category',
                'expected_category_pgxqa', 'expected_text', 'source'])
    for i, (c, r) in enumerate(sel, 1):
        cid = f'c{i:02d}'; a = adj.get(cid)
        text = r['answer'] + ((' || ' + a['added_text']) if a and a['added_text'] else '')
        w.writerow([cid, c, 'yes' if cid in sub else 'no', r['genes'], r['drug'], r['question'],
                    a['new_category'] if a else cat(r), cat(r), text,
                    'PGxQA drug_guidelines_for_pheno_queries.txt (MIT; recommendation from the CPIC database)'])
print(len(sel), 'cases;', collections.Counter((c, cat(r)) for c, r in sel))
