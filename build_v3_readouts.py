"""Export the v3 per-situation readout dashboard data to v3-readouts/data/.
index.json: one row per main situation (id, category, scenario, B, C, X, flags).
s/{id}.json: prompt + answer tokens, J++ top-20 (plus top-100 item and answer-token ranks) at blocks 40-54 for the assistant-start token and every answer token
(token strings, log-probs, judge item labels), design (competitors, corrected scores, coordinates), the v3 swap-stage
reports (fp32) and the v5 scaffold reports (bf16)."""
import json, os, sys, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(IN, 'v3', 'code'), os.path.join(IN, 'code')]
from prelim_v3 import V, lens, is_named
from dev_v3 import labels
OUT = os.path.join(HERE, 'v3-readouts', 'data'); os.makedirs(os.path.join(OUT, 's'), exist_ok=True)
BLOCKS = list(range(40, 55)); TOP = 20
L = labels()
REP = json.load(open(os.path.join(IN, 'code', 'judge_cache', 'reports.json')))
D = {t['id']: t for t in json.load(open(os.path.join(IN, 'v3', 'stimuli', 'main_design.json')))['trials']}
SKIP = json.load(open(os.path.join(IN, 'v3', 'stimuli', 'main_design.json')))['skipped']
SC = json.load(open(os.path.join(IN, 'v5', 'stimuli', 'scaffolds.json')))


def rep_item(c, text, hit, named):
    if hit: return dict(label='Truncated')
    lab = REP.get(c, {}).get(text)
    if lab is None: return dict(label='Unlabeled')
    if lab['label'] != 'Item': return dict(label=lab['label'])
    it = L.canon(c, lab['item'])
    if it is None: return dict(label='NotItem')
    return dict(label='Named' if is_named(it, named) else 'Item', item=it)


def tag(r, d):
    it = r.get('item')
    return 'C' if it == d['C'] else 'B' if it == d['B'] else 'X' if r['label'] == 'Named' else None


index = []
for f in sorted(glob.glob(os.path.join(IN, 'v3', 'data', 'main', 'records', '*.json'))):
    rec = json.load(open(f)); tid = rec['id']; c = rec['category']
    ids, lp = lens(tid)  # [block, pos, rank]
    npz = np.load(os.path.join(IN, 'v3', 'data', 'main', 'lens', f'{tid}.npz'))
    layers = list(npz['layers']); positions = [int(p) for p in npz['positions']]
    strings, sidx = [], {}

    def S(tok):
        s = V[tok]
        if s not in sidx: sidx[s] = len(strings); strings.append(s)
        return sidx[s]
    items = {}
    lensd, ranks = [], []
    apos = {}
    for k, t in enumerate(rec['generation']['token_ids']):
        apos.setdefault(int(t), []).append(str(len(rec['initial_ids']) + k))
    for j, p in enumerate(positions):
        per = []
        for b in BLOCKS:
            bi = layers.index(b)
            row = []
            for r in range(TOP):
                tok = int(ids[bi, j, r]); it = L.item(c, tok)
                if it: items[S(tok)] = it
                row.append([S(tok), round(float(lp[bi, j, r]), 2)])
            per.append(row)
        lensd.append(per)
        rk = []
        for b in BLOCKS:
            bi = layers.index(b); im, tm = {}, {}
            for r in range(ids.shape[2]):
                tok = int(ids[bi, j, r]); it = L.item(c, tok)
                if it and it not in im: im[it] = r + 1
                for a in apos.get(tok, ()):
                    tm.setdefault(a, r + 1)
            rk.append([im, tm])
        ranks.append(rk)
    prompt = [V[t] for t in rec['initial_ids']]
    gen = rec['generated_tokens']
    out = dict(id=tid, category=c, scenario=rec['scenario'], prompt_text=rec['prompt'], answer=rec['generation']['text'],
               prompt_tokens=prompt, answer_tokens=gen, site=rec['site'], positions=positions, blocks=BLOCKS, strings=strings,
               items={str(k): v for k, v in items.items()}, lens=lensd, ranks=ranks, rank_depth=int(ids.shape[2]))
    d = D.get(tid)
    row = dict(id=tid, category=c, scenario=rec['scenario'], eligible=d is not None, skipped=SKIP.get(tid))
    if d:
        out['design'] = {k: d[k] for k in ('X', 'named', 'competitors', 'corr', 'B', 'C', 'tok_B_str', 'tok_C_str', 'rank_B', 'rank_C',
                                           'margin_BC', 'X_rank', 'stable_rb1', 'stable_rb2', 'c_site', 'reoriented', 'options')}
        sw = json.load(open(os.path.join(IN, 'v3', 'data', 'main', 'swapstage', f'{tid}.json')))
        conds = {}
        for m, x in sw['conditions'].items():
            reps = {}
            for k, v in x.get('reports', {}).items():
                q = v['question']; t = v['text']
                if k.startswith('rec_'):
                    reps[k] = dict(question=q, text=t)
                else:
                    ri = rep_item(c, t, v['hit_token_limit'], d['named']); reps[k] = dict(question=q, text=t, **ri, tag=tag(ri, d))
            conds[m] = dict(valid=x['same_answer'], answer=x['answer'], delta=x['mcheck']['delta'], rankB=x['mcheck']['rankB'], rankC=x['mcheck']['rankC'],
                            top1=x['mcheck']['top1'], rel=x.get('edits', {}).get('rel'), c_before=(x.get('edits', {}).get('c_before') or [None])[0],
                            c_after=(x.get('edits', {}).get('c_after') or [None])[0], reports=reps)
        late = {m: dict(text=v['text'], **rep_item(c, v['text'], v['hit_token_limit'], d['named'])) for m, v in sw['late'].items()}
        for v in late.values(): v['tag'] = tag(v, d)
        ctx = {}
        for k, v in sw['context'].items():
            if k.startswith('ctx_rec_'): ctx[k] = dict(question=v['question'], text=v['text'])
            else:
                ri = rep_item(c, v['text'], v['hit_token_limit'], d['named']); ctx[k] = dict(question=v['question'], text=v['text'], **ri, tag=tag(ri, d))
        third = {m: dict(text=v['ctx_free1']['text'], **rep_item(c, v['ctx_free1']['text'], v['ctx_free1']['hit_token_limit'], d['named'])) for m, v in sw['third'].items()}
        for v in third.values(): v['tag'] = tag(v, d)
        out['v3'] = dict(conditions=conds, late=late, context=ctx, third=third)
        p5 = os.path.join(IN, 'v5', 'data', 'v3', f'{tid}.json')
        if os.path.exists(p5):
            x5 = json.load(open(p5)); cells = {}
            for cell in SC['cells']:
                e = {}
                for m in ('none', 'swap', 'control'):
                    r = x5['conditions'][m].get('reports', {}).get(f'{cell}#free1')
                    if r:
                        ri = rep_item(c, r['text'], r['hit'], d['named']); e[m] = dict(text=r['text'], **ri, tag=tag(ri, d))
                r = x5['context'].get(f'{cell}#free1')
                if r:
                    ri = rep_item(c, r['text'], r['hit'], d['named']); e['context'] = dict(text=r['text'], **ri, tag=tag(ri, d))
                cells[cell] = e
            out['v5'] = dict(valid={m: x5['conditions'][m]['same_answer'] for m in x5['conditions']}, cells=cells)
        C = conds
        row.update(B=d['B'], C=d['C'], X=d['X'], valid_pair=C['swap']['valid'] and C['control']['valid'],
                   flip=C['swap']['valid'] and C['swap']['delta'] > 0 and C['none']['delta'] <= 0,
                   swap_free1=C['swap']['reports'].get('free1', {}).get('tag'), control_free1=C['control']['reports'].get('free1', {}).get('tag'),
                   none_free1=C['none']['reports'].get('free1', {}).get('tag'))
    json.dump(out, open(os.path.join(OUT, 's', f'{tid}.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    index.append(row)
cells = [dict(id=c, label=c.replace('|', ' × ')) for c in SC['cells']]
json.dump(dict(situations=index, cells=cells, blocks=BLOCKS, readout_block=53, K=10), open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False)
print(len(index), 'situations;', sum(r['eligible'] for r in index), 'eligible')
