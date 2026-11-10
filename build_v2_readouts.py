"""Export the v2 (copy-and-hold) per-trial readout dashboard data to v2-readouts/data/.
index.json: one row per main trial (id, category, setting, reference item, flags).
s/{id}.json: prompt + copied tokens, J++ top-20 at blocks 40-54 for every copied token and the assistant-start token,
top-100 item ranks per position and block, the frozen reference (corrected score, eligibility), the three free reports,
recognition, the swap stage (120 situations) and the v5 scaffold reports (bf16)."""
import json, os, sys, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(IN, 'code')]
import analysis as A
import stage_main as M
OUT = os.path.join(HERE, 'v2-readouts', 'data'); os.makedirs(os.path.join(OUT, 's'), exist_ok=True)
BLOCKS = list(range(40, 55)); TOP = 20
L = M.labels()
V = A.V
REP = M.reports
SC = json.load(open(os.path.join(IN, 'v5', 'stimuli', 'scaffolds.json')))
rows = M.trial_table(L)


def item_of(L, c, tok):
    try:
        return L.item(c, tok)
    except KeyError:  # token never labeled (outside the labeled top-N)
        return None


def lab(c, text, hit):
    if hit: return dict(label='Truncated')
    if text not in REP.get(c, {}): return dict(label='Unlabeled')
    it, lb = M.report_item(L, c, text)
    return dict(label=lb, item=it) if it else dict(label=lb)


def tag(r, A_, B_):
    it = r.get('item')
    return 'A' if it and it == A_ else 'B' if it and it == B_ else None


def recog(entries, opts_key='options'):
    out = []
    for e in entries:
        a = M.parse_letter(e['text'], e['mode'])
        pick = e[opts_key][M.LETTERS.index(a)] if a and a in M.LETTERS else ('abstain' if a == 'U' else None)
        out.append(dict(order=e['order'], mode=e['mode'], options=e[opts_key], text=e['text'], pick=pick))
    return out


SWAP = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(IN, 'data', 'swap', '*.json'))}
index = []
for tid in sorted(t for t in M.recs if t.startswith('m-')):
    rec = M.recs[tid]; c = rec['category']; r = rows[tid]
    ids, lp, n = A.lens(tid)
    npz = np.load(os.path.join(IN, 'data', 'lens', f'{tid}.npz'))
    positions = [int(p) for p in npz['positions']]
    strings, sidx, items = [], {}, {}

    def S(tok):
        s = V[tok]
        if s not in sidx: sidx[s] = len(strings); strings.append(s)
        return sidx[s]
    lensd, ranks = [], []
    for j in range(len(positions)):
        per, rk = [], []
        for b in BLOCKS:
            row = []
            for q in range(TOP):
                tok = int(ids[b, j, q]); it = item_of(L, c, tok)
                if it: items[S(tok)] = it
                row.append([S(tok), round(float(lp[b, j, q]), 2)])
            per.append(row)
            im = {}
            for q in range(ids.shape[2]):
                it = item_of(L, c, int(ids[b, j, q]))
                if it and it not in im: im[it] = q + 1
            rk.append([im, {}])
        lensd.append(per); ranks.append(rk)
    sw = SWAP.get(tid)
    A_, B_ = (sw['A'], sw['B']) if sw else (r['ref'], None)
    reps = {}
    for k in M.COND:
        f = rec['free'][k]; x = dict(question=f['question'], text=f['text'], **lab(c, f['text'], f['hit_token_limit']))
        x['tag'] = tag(x, A_, B_); reps[k] = x
    out = dict(id=tid, category=c, scenario=rec['setting'], prompt_text=rec['prompt'], answer=rec['generation']['text'],
               prompt_tokens=[V[t] for t in rec['initial_ids']], answer_tokens=[V[t] for t in rec['generation']['token_ids']],
               site=rec['assistant_start'], positions=positions, n_copied=int(n), blocks=BLOCKS, readout_block=M.RB, K=M.K,
               strings=strings, items={str(k): v for k, v in items.items()}, lens=lensd, ranks=ranks, rank_depth=int(ids.shape[2]),
               valid=rec['valid'], carrier=rec['carrier'],
               design=dict(ref=r['ref'], A=A_, B=B_, ranked=r['ranked'][:10], scores=[round(s, 3) for s in r['scores'][:10]],
                           margin=r['margin'], best_rank=(r['best_rank'] + 1) if r['best_rank'] is not None else None,
                           eligible=r['eligible']),
               reports=reps)
    rp = os.path.join(IN, 'data', 'recog', f'{tid}.json')
    if os.path.exists(rp): out['recog'] = recog(json.load(open(rp))['recognition'])
    if sw:
        res = []
        for x in sw['results']:
            f = x['reports']['free']; e = dict(text=f['text'], **lab(c, f['text'], len(f['token_ids']) >= 16)); e['tag'] = tag(e, A_, B_)
            ed = x.get('edits') or []
            res.append(dict(mode=x['mode'], alpha=x['alpha'], valid=x['same_copy'], free=e, recog=recog(x['reports'].get('recog', [])),
                            rel=float(np.mean([q['rel'] for q in ed])) if ed else None,
                            c_before=ed[0]['c_before'] if ed else None, c_after=ed[0]['c_after'] if ed else None))
        out['swap'] = dict(A=A_, B=B_, cos_AB=sw['cos_AB'], results=res)
    v5 = {}
    p5 = os.path.join(IN, 'v5', 'data', 'v2', f'{tid}.json')
    if os.path.exists(p5):
        x5 = json.load(open(p5)); cells = {}
        for cell in SC['cells']:
            e = {}
            for side in ('self', 'context'):
                for q in ('2', '1'):
                    v = x5[side].get(f'{cell}#{q}')
                    if v:
                        y = dict(text=v['text'], **lab(c, v['text'], v['hit'])); y['tag'] = tag(y, A_, B_); e[f'{side}{q}'] = y
            cells[cell] = e
        v5['hold'] = dict(valid=x5['same_copy'], cells=cells)
    p5 = os.path.join(IN, 'v5', 'data', 'v2swap', f'{tid}.json')
    if os.path.exists(p5):
        x5 = json.load(open(p5)); res = []
        for x in x5['results']:
            e = {}
            for cell, v in x['reports'].items():
                y = dict(text=v['text'], **lab(c, v['text'], v['hit'])); y['tag'] = tag(y, A_, B_); e[cell] = y
            res.append(dict(mode=x['mode'], alpha=x['alpha'], valid=x['same_copy'], reports=e))
        v5['swap'] = res
    if v5: out['v5'] = v5
    json.dump(out, open(os.path.join(OUT, 's', f'{tid}.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    f2 = reps['2_not_mentioned']
    index.append(dict(id=tid, category=c, scenario=rec['setting'], valid=rec['valid'], eligible=bool(r['eligible'] and rec['valid']),
                      ref=r['ref'], match2=bool(r['rep']['2_not_mentioned']['match']), report2=f2.get('item') or f2['label'],
                      swap=bool(sw), swap_tag=(next((y['free']['tag'] for y in out['swap']['results'] if y['mode'] == 'swap' and y['alpha'] == 2), None) if sw else None),
                      v5=('v5' in out)))
cells = [dict(id=c, label=c.replace('|', ' × ')) for c in SC['cells']]
json.dump(dict(situations=index, cells=cells, blocks=BLOCKS, readout_block=M.RB, K=M.K), open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False)
print(len(index), 'trials;', sum(r['eligible'] for r in index), 'eligible;', sum(r['match2'] and r['eligible'] for r in index), 'cond-2 matches;',
      sum(r['swap'] for r in index), 'swap;', sum(r['v5'] for r in index), 'v5')
