"""Build exp1.html (Experiment 1 from the 'Introspection experiments' write-up, 2026-11-26) from ../results/exp1_measures.json."""
import json, os, html, datetime
from zoneinfo import ZoneInfo
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'results')
E = html.escape
CSS = open(os.path.join(HERE, 'style.css')).read()
M = json.load(open(os.path.join(RES, 'exp1_measures.json')))
DES = json.load(open(os.path.join(RES, 'exp1_design.json')))
TXT = json.load(open(os.path.join(RES, 'exp1_text.json'))) if os.path.exists(os.path.join(RES, 'exp1_text.json')) else {}
LOG = json.load(open(os.path.join(RES, 'exp1_log.json'))) if os.path.exists(os.path.join(RES, 'exp1_log.json')) else []
NAV = [('index.html', 'Results (v2)'), ('protocol.html', 'Protocol v2'), ('v3.html', 'v3: Natural swap'), ('v4.html', 'v4: Cued hold'), ('v5.html', 'v5: Scaffolds'),
       ('exp1.html', 'Experiment 1'), ('scale.html', 'Exp 1 scaling')]
CATS = ['grocery', 'animal', 'country']
CN = dict(grocery='Groceries', animal='Animals', country='Countries', all='All')
FREE = [('1_permitted', 'Abstention permitted'), ('2_unspecified', 'Abstention unspecified'), ('3_prohibited', 'Abstention prohibited')]
PN = dict(sw='Strongest–weakest', sm='Strongest–median')
KN = dict(swap='Swap A ↔ B', nonref='Non-reference swap', random='Matched random perturbation')
KC = dict(swap='#235fa6', nonref='#b0702a', random='#8a7d6d')
AL = M['alphas']
SUBCSS = ('.muted{color:var(--ink-3);font-size:.9em}pre.q{white-space:pre-wrap;font-family:var(--sans);font-size:14px;background:var(--panel);'
          'border:1px solid var(--rule);border-radius:4px;padding:10px 12px;margin:4px 0 14px;overflow-x:auto}'
          '.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px 18px}.mini-title{font-family:var(--sans);font-size:13.5px;font-weight:600;color:var(--ink-2);margin:6px 0 0}'
          '.chart.small{height:250px}')


def nav(cur):
    return '<nav class="tabs" aria-label="Pages">' + ''.join(f'<a href="{h}"' + (' aria-current="page"' if h == cur else '') + f'>{t}</a>' for h, t in NAV) + '</nav>'


def table(head, rows, cls='', cap=None, note=None):
    h = ''.join(f'<th>{x}</th>' for x in head)
    b = ''.join('<tr>' + ''.join(f'<td>{x}</td>' for x in r) + '</tr>' for r in rows)
    return ('<div class="table-wrap">' + (f'<p class="table-cap">{cap}</p>' if cap else '') + f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'
            + (f'<p class="table-note">{note}</p>' if note else '') + '</div>')


def fig(fid, title, note, caption, cls='chart', legend=None):
    leg = ''.join(f'<span><i style="border-color:{c};border-top-width:6px"></i>{n}</span>' for n, c in (legend or []))
    return (f'<figure class="wide" id="fig-{fid}"><div class="fig-panel"><div class="fig-top"><div class="fig-title">{title}</div><div class="legend" aria-hidden="true">{leg}</div></div>'
            f'<div id="chart-{fid}" class="{cls}" role="img" aria-label="{E(title)}"></div><div class="fig-note">{note}</div></div><figcaption>{caption}</figcaption></figure>')


f1 = lambda x: '—' if x is None else f'{x:.1f}'
pct = lambda d: f'{d["pct"]:.1f}% <span class="muted">[{d["lo"]:.1f}, {d["hi"]:.1f}]</span>'
bm = lambda d, n=2: '—' if d.get('mean') is None else f'{d["mean"]:+.{n}f} <span class="muted">[{d["lo"]:+.{n}f}, {d["hi"]:+.{n}f}]</span>'
pv = lambda p: '—' if p is None else ('&lt;0.001' if p < 0.001 else f'{p:.3f}')
CH = {}


def sections():
    out, toc = [], []
    def h2(i, t):
        toc.append((i, t)); out.append(f'<h2 id="{i}"><span class="num">{len(toc)}</span>{t}</h2>')

    rp = M['repro']
    nr = sorted(t['n_ranked'] for t in DES['trials'])
    ex = DES['trials'][0]
    # ---------------- setup ----------------
    h2('setup', 'Setup: what was reused and what was rerun')
    out.append(TXT.get('setup', ''))
    out.append('<p><b>(a) Hold.</b> 480 situations (160 per category) with 12 carrier sentences. The model is asked to silently choose an item suitable for the setting and keep it in mind while copying the sentence:</p>'
               f'<pre class="q">{E(ex["prompt"])}</pre>'
               '<p><b>(b) Reference item.</b> At block 54, at every copied token, each category item scores its best J++ log-probability among its tokens in the top 100 (or the rank-100 log-probability if absent). '
               'Scores are averaged over the copied tokens, and the same quantity from a copy with no hold instruction (same sentence) is subtracted. The reference item is the item with the highest corrected score. '
               f'Items are those the frozen LLM judge labels as category items among the lens tokens. Median {nr[len(nr) // 2]} candidate items per trial (range {nr[0]}–{nr[-1]}). There is no eligibility cutoff: all {M["n"]} trials are analysed.</p>'
               f'<p><b>Readout block.</b> On the 24 preliminary situations, the average number of distinct category items in the top 100 per copied position peaks at block 54 (the last block searched), as in v2.</p>')
    out.append(table(['Check', 'Result'], [
        ['Hold copies regenerated on RunPod, identical to v2 token for token', f'{rp["same_hold"]} / {rp["n"]}'],
        ['Copied positions whose block-54 top 100 (ids and order) equals v2&#8217;s stored readout', f'{rp["top100_positions_identical"]:,} / {rp["positions"]:,}'],
        ['Preliminary holds identical (used for σ<sub>m</sub>)', f'{rp["prelim_same_hold"]} / {rp["prelim_n"]}'],
        ['Valid copies (reply = sentence, then end of turn)', '480 / 480']], cap='<b>Reproduction of steps (a) and (b).</b>'))

    # ---------------- (c) free recall ----------------
    h2('free', '(c) Free recall')
    q = DES['trials'][0]['free']
    out.append('<p>From the post-copy state, each question is asked in its own branch:</p>' + ''.join(f'<pre class="q">{E(q[k])}</pre>' for k, _ in FREE))
    F = M['free']
    series = [dict(name=n, y=[F[f'{k}/{c}']['pct'] for c in CATS + ['all']], lo=[F[f'{k}/{c}']['lo'] for c in CATS + ['all']],
                   hi=[F[f'{k}/{c}']['hi'] for c in CATS + ['all']], color=col) for (k, n), col in zip(FREE, ('#cfc4b4', '#235fa6', '#b0702a'))]
    CH['free'] = dict(kind='bars', groups=[CN[c] for c in CATS + ['all']], series=series, ymax=60, ytitle='Names the reference item',
                      chance=[F[f'2_unspecified/{c}']['perm'] for c in CATS + ['all']])
    f2 = F['2_unspecified/all']
    out.append(fig('free', 'Free recall: the reply names the reference item', 'Wilson 95% CIs. Dotted marks: the same replies scored against other same-category trials&#8217; reference items (abstention unspecified).',
                   TXT.get('free_caption', f'<b>Figure 1.</b> Abstention unspecified: {f2["pct"]:.1f}% of replies name the reference item, against {f2["perm"]:.1f}% when scored against other trials&#8217; reference items.'),
                   legend=[(s['name'], s['color']) for s in series]))
    rows = [[n, CN[c], pct(F[f'{k}/{c}']), f'{F[f"{k}/{c}"]["perm"]:.1f}%', f'{F[f"{k}/{c}"]["abstain"]:.1f}%', f'{F[f"{k}/{c}"]["notitem"]:.1f}%', f'{F[f"{k}/{c}"]["trunc"]:.1f}%']
            for k, n in FREE for c in CATS + ['all']]
    out.append(table(['Condition', 'Category', 'Names reference item', 'Scored against other trials', 'Abstains', 'Not a category item', 'Truncated (16 tokens)'], rows,
                     cap='<b>Free recall by condition and category.</b>'))

    # ---------------- recognition ----------------
    h2('recog', '(c) Multiple-choice recognition')
    rq = DES['trials'][0]['recog']
    out.append('<p>Same question, four options, one random order per trial. <b>Strict</b>: the four highest-scoring items. <b>Loose</b>: the highest, the lowest, and two drawn uniformly from ranks 2 to n−1. '
               'Answer required (primary), and a variant that allows “U”. Example (loose, answer required):</p>' + f'<pre class="q">{E(rq["loose_required"]["question"])}</pre>')
    Rg = M['recog']
    names = [('strict_required', 'Strict, answer required', '#235fa6'), ('strict_abstain', 'Strict, U allowed', '#9fb8d9'),
             ('loose_required', 'Loose, answer required', '#b0702a'), ('loose_abstain', 'Loose, U allowed', '#dcc0a0')]
    CH['recog'] = dict(kind='bars', groups=[CN[c] for c in CATS + ['all']], ymax=100, ytitle='Picks the reference item', chance25=True,
                       series=[dict(name=n, color=col, y=[Rg[f'{k}/{c}']['pct'] for c in CATS + ['all']], lo=[Rg[f'{k}/{c}']['lo'] for c in CATS + ['all']],
                                    hi=[Rg[f'{k}/{c}']['hi'] for c in CATS + ['all']]) for k, n, col in names])
    sr, lr = Rg['strict_required/all'], Rg['loose_required/all']
    out.append(fig('recog', 'Recognition: share picking the reference item (chance 25%)', 'Wilson 95% CIs. Dotted line: chance.',
                   TXT.get('recog_caption', f'<b>Figure 2.</b> Strict: {sr["pct"]:.1f}%; loose: {lr["pct"]:.1f}% (answer required).'), legend=[(n, c) for _, n, c in names]))
    rows = []
    for k, n, _ in names:
        for c in CATS + ['all']:
            d = Rg[f'{k}/{c}']; t = d['tiers']
            tiers = (f'{t.get("top", 0)} / {t.get("middle", 0)} / {t.get("bottom", 0)}' if k.startswith('loose') else ' / '.join(str(t.get(str(i), 0)) for i in range(1, 5)))
            rows.append([n, CN[c], pct(d), tiers, f'{d["abstain"]}', f'{d["invalid"]}'])
    out.append(table(['Menu', 'Category', 'Picks reference item', 'Picks by option (strict: ranks 1/2/3/4; loose: top/middle/bottom)', 'U', 'Invalid'], rows,
                     cap='<b>Recognition by menu, mode and category</b> (counts of trials).'))
    # pairwise regression
    P = M['pairs']
    out.append('<h3 id="pairs">Do larger lens-score differences give larger answer preferences?</h3>'
               '<p>For each pair of options i, j in a trial, we regress log P(i) − log P(j) (answer-letter probabilities, answer required) on s<sub>i</sub> − s<sub>j</sub> '
               '(baseline-corrected lens scores), with standard errors clustered by trial. Each trial gives six pairs, oriented by option letter.</p>')
    rows = [[m.capitalize(), CN[c], f'{P[m][c]["slope"]:+.3f}', ('—' if P[m][c]['se'] is None else f'{P[m][c]["se"]:.3f}'), pv(P[m][c]['p']), f'{P[m][c]["r"]:.3f}' if P[m][c]['r'] is not None else '—', P[m][c]['n'], P[m][c]['clusters']]
            for m in ('strict', 'loose') for c in CATS + ['all'] if c in P[m]]
    out.append(table(['Menu', 'Category', 'Slope (nats per unit score)', 'Cluster SE', 'p', 'r', 'Pairs', 'Trials'], rows, cap='<b>Pairwise regression.</b>'))
    for m in ('strict', 'loose'):
        pts = np.array([p[:2] for p in P[m]['points']], float)
        if len(pts):
            q_ = np.quantile(pts[:, 0], np.linspace(0, 1, 13)); xb, yb, eb = [], [], []
            for a, b in zip(q_[:-1], q_[1:]):
                s = pts[(pts[:, 0] >= a) & (pts[:, 0] <= b)]
                if len(s): xb.append(float(s[:, 0].mean())); yb.append(float(s[:, 1].mean())); eb.append(float(1.96 * s[:, 1].std() / np.sqrt(len(s))))
            CH[f'pairs_{m}'] = dict(kind='scatter', x=xb, y=yb, e=eb, slope=P[m]['all']['slope'], intercept=P[m]['all']['intercept'],
                                    xtitle='s<sub>i</sub> − s<sub>j</sub> (lens score difference)', ytitle='log P(i) − log P(j) (nats)')
    out.append('<div class="grid2">' + ''.join(f'<div><p class="mini-title">{m.capitalize()} menu</p><div id="chart-pairs_{m}" class="chart small"></div></div>' for m in ('strict', 'loose')) + '</div>'
               '<p class="table-note">Points: pairs binned into 12 quantile bins of the score difference; mean ± 1.96 SE (not clustered). Line: the clustered OLS fit on all pairs.</p>')
    out.append(TXT.get('recog_reading', ''))

    # ---------------- (d) swap ----------------
    h2('swap', '(d) Causal test: swapping J-space coordinates')
    mt = M['match']
    out.append(TXT.get('swap_method', ''))
    out.append(table(['Pairing', 'Median rank of B', 'Median ranks of C, D', 'Median g<sub>AB</sub> / g<sub>CD</sub>', 'Median m<sub>AB</sub> / m<sub>CD</sub>', 'Median match distance', 'Median cos(d<sub>A</sub>, d<sub>B</sub>)'],
                     [[PN[p], f'{mt[p]["B_rank"]:.0f}', f'{mt[p]["CD_ranks"][0]:.0f}, {mt[p]["CD_ranks"][1]:.0f}', f'{mt[p]["g_AB"]:.2f} / {mt[p]["g_CD"]:.2f}',
                       f'{mt[p]["m_AB"]:.2f} / {mt[p]["m_CD"]:.2f}', f'{mt[p]["dist"]:.2f}', f'{mt[p]["cos_AB"]:.2f}'] for p in ('sw', 'sm')],
                     cap='<b>Swap pairs and the matched non-reference pairs.</b> g: absolute difference of corrected lens scores. m: RMS over copied tokens of the α = 1 perturbation norm, in the unedited run. '
                         f'σ<sub>g</sub> = {M["sigma_g"]:.3f}, σ<sub>m</sub> = {M["sigma_m"]["sigma_m"]:.3f} (all candidate pairs in the 24 preliminary situations, {M["sigma_m"]["n_pairs"]:,} pairs).'))
    S = M['swap']
    xs = [0.0] + AL
    for p in ('sw', 'sm'):
        def line(metric, sub=None):
            sr = []
            for k in ('swap', 'nonref', 'random'):
                y, lo, hi = [], [], []
                for a in xs:
                    d = S[f'{p}/unedited'] if a == 0 else S[f'{p}/{p}_{k}_{a}']
                    v = d[sub] if sub else d
                    v = v[metric] if metric in v else None
                    if isinstance(v, dict):
                        y.append(v['mean']); lo.append(v['lo']); hi.append(v['hi'])
                    else:
                        y.append(v); lo.append(v); hi.append(v)
                sr.append(dict(name=KN[k], color=KC[k], y=y, lo=lo, hi=hi))
            return sr
        panels = [('A', '2_unspecified', 'Names A (%)'), ('B', '2_unspecified', 'Names B (%)'), ('changed', '2_unspecified', 'Answer changed (%)'),
                  ('delta', '2_unspecified', 'Δ free recall (nats)'), ('delta', 'recog', 'Δ recognition (nats)'), ('dsBA', None, 'Δs<sub>B,A</sub> lens margin')]
        for i, (m, sub, t) in enumerate(panels):
            CH[f'sw_{p}_{i}'] = dict(kind='lines', x=xs, series=line(m, sub), ytitle=t)
        out.append(f'<h3 id="swap-{p}">{PN[p]} pair</h3><div class="legend">' + ''.join(f'<span><i style="border-color:{KC[k]};border-top-width:6px"></i>{KN[k]}</span>' for k in KC) + '</div>'
                   '<div class="grid2">' + ''.join(f'<div><p class="mini-title">{t}</p><div id="chart-sw_{p}_{i}" class="chart small"></div></div>' for i, (_, _, t) in enumerate(panels)) + '</div>'
                   '<p class="table-note">x: α (0 = unedited). Free recall: abstention unspecified. Δ = [log P(B) − log P(A)]<sub>edited</sub> − [same]<sub>unedited</sub>; bands are 95% bootstrap CIs over trials.</p>')
        out.append(TXT.get(f'swap_caption_{p}', ''))
    # condition table
    rows = []
    for p in ('sw', 'sm'):
        for a in [0.0] + AL:
            for k in (['unedited'] if a == 0 else ['swap', 'nonref', 'random']):
                d = S[f'{p}/unedited'] if a == 0 else S[f'{p}/{p}_{k}_{a}']
                f, r = d['2_unspecified'], d['recog']
                rows.append([PN[p], 'Unedited' if a == 0 else f'{KN[k]}, α = {a:g}', f'{d["valid"]}/{d["n"]}', f'{100 * d["rel"]:.2f}%',
                             f'{f["A"]:.1f}%', f'{f["B"]:.1f}%', '—' if a == 0 else f'{f["changed"]:.1f}%', '—' if a == 0 else bm(f['delta']),
                             f'{r["A"]:.1f}%', f'{r["B"]:.1f}%', '—' if a == 0 else f'{r["changed"]:.1f}%', '—' if a == 0 else bm(r['delta'], 3), '—' if a == 0 else bm(d['dsBA'])])
    out.append(table(['Pairing', 'Condition', 'Copy identical', 'Edit / ‖h‖', 'Free: names A', 'Free: names B', 'Free: changed', 'Free: Δ (nats)', 'Recog: A', 'Recog: B', 'Recog: changed', 'Recog: Δ (nats)', 'Δs<sub>B,A</sub>'],
                     rows, cap='<b>All conditions</b> (free recall: abstention unspecified; recognition: A, B and two other candidates, answer required).'))
    # other free conditions
    rows = []
    for p in ('sw', 'sm'):
        for k_, n_ in FREE:
            r_ = [PN[p], n_, f'{S[f"{p}/unedited"][k_]["A"]:.1f}%']
            for a in AL:
                s_, c1, c2 = S[f'{p}/{p}_swap_{a}'][k_], S[f'{p}/{p}_nonref_{a}'][k_], S[f'{p}/{p}_random_{a}'][k_]
                r_.append(f'{s_["A"]:.1f} / {c1["A"]:.1f} / {c2["A"]:.1f} · B {s_["B"]:.1f} / {c1["B"]:.1f} / {c2["B"]:.1f}')
            rows.append(r_)
    out.append(table(['Pairing', 'Free-recall condition', 'Unedited: names A'] + [f'α = {a:g}: names A, swap / non-ref / random · names B' for a in AL], rows,
                     cap='<b>Measures 1 and 2 in all three free-recall conditions</b> (% of valid trials).'))
    # paired comparisons
    C = M['compare']
    rows = []
    for p in ('sw', 'sm'):
        for a in AL:
            for ctrl in ('nonref', 'random'):
                for k_, n_ in (('2_unspecified', 'Free recall'), ('recog', 'Recognition')):
                    e = C[f'{p}/{a}/{ctrl}/{k_}']
                    rows.append([PN[p], f'{a:g}', KN[ctrl], n_, f'{e["A"]["swap"]:.1f} vs {e["A"]["ctrl"]:.1f} (p {pv(e["A"]["p"])})', f'{e["B"]["swap"]:.1f} vs {e["B"]["ctrl"]:.1f} (p {pv(e["B"]["p"])})',
                                 f'{e["changed"]["swap"]:.1f} vs {e["changed"]["ctrl"]:.1f} (p {pv(e["changed"]["p"])})', bm(e['delta'], 3) + f' <span class="muted">swap larger in {e["delta"]["swap_gt"]:.0f}%</span>'])
    out.append(table(['Pairing', 'α', 'Control', 'Report', 'Names A: swap vs control (McNemar p)', 'Names B', 'Changed', 'Δ swap − Δ control (nats) [95% CI]'], rows,
                     cap='<b>Swap vs each control, paired by trial.</b>'))
    # decomposition and casing variants
    rows = []
    for p in ('sw', 'sm'):
        for a in AL:
            for k in ('swap', 'nonref', 'random'):
                f = S[f'{p}/{p}_{k}_{a}']['2_unspecified']
                rows.append([PN[p], f'{KN[k]}, α = {a:g}', f'{f["dlpA"]:+.3f}', f'{f["dlpB"]:+.3f}', f'{f["dlpC"]:+.3f}', f'{f["dlpD"]:+.3f}', bm(f['delta_cap'], 3), bm(f['delta_low'], 3), bm(f['delta_end'], 3), bm(f['delta_DC'], 3)])
    out.append(table(['Pairing', 'Condition', 'Δ log P(A)', 'Δ log P(B)', 'Δ log P(C)', 'Δ log P(D)', 'Δ, capitalized form only', 'Δ, lowercase form only', 'Δ, name + end of turn', 'Δ for the C, D pair'], rows,
                     cap='<b>Free recall, item by item</b> (abstention unspecified; mean change from the unedited run, nats). '
                         f'Unedited medians: log P(A) {S["sw/unedited"]["2_unspecified"]["base_lpA"]:.1f}, log P(B) {S["sw/unedited"]["2_unspecified"]["base_lpB"]:.1f} (strongest–weakest), '
                         f'{S["sm/unedited"]["2_unspecified"]["base_lpB"]:.1f} (strongest–median).',
                     note='P(item) sums the capitalized and lowercase name (the model replies with a bare name, mostly capitalized). Δ for the C, D pair: [log P(D) − log P(C)] change, D the lower-ranked item.'))
    # Delta vs Delta s
    G = M['reg']
    rows = [[{'2_unspecified': 'Free recall', 'recog': 'Recognition'}[k], {'swap': 'Swap conditions', 'all': 'All edited conditions'}[s], {'sw': PN['sw'], 'sm': PN['sm'], 'both': 'Both'}[p],
             f'{G[f"{k}/{s}/{p}"]["slope"]:+.4f}', ('—' if G[f"{k}/{s}/{p}"]["se"] is None else f'{G[f"{k}/{s}/{p}"]["se"]:.4f}'), pv(G[f'{k}/{s}/{p}']['p']), f'{G[f"{k}/{s}/{p}"]["r"]:.2f}' if G[f'{k}/{s}/{p}']['r'] is not None else '—',
             G[f'{k}/{s}/{p}']['n']] for k in ('2_unspecified', 'recog') for s in ('swap', 'all') for p in ('sw', 'sm', 'both')]
    out.append('<h3 id="dsreg">Does a larger change in the lens margin give a larger change in the report?</h3>'
               '<p>Δs<sub>B,A</sub> = (s<sub>B</sub> − s<sub>A</sub>)<sub>edited</sub> − (s<sub>B</sub> − s<sub>A</sub>)<sub>unedited</sub>, with s the lens score (same scoring as step b) read from the edited block-54 output. '
               'We regress the report margin change Δ<sub>B,A</sub> on Δs<sub>B,A</sub>, clustering by trial.</p>')
    out.append(table(['Report', 'Conditions', 'Pairing', 'Slope', 'Cluster SE', 'p', 'r', 'n'], rows, cap='<b>Δ on Δs.</b>'))
    out.append(TXT.get('ds_reading', ''))
    ex_rows = [[E(x['id']), PN[x['pairing']], E(x['A']), E(x['B']), E(x['unedited'] or ''), E(x['swap'] or ''), E(x['nonref'] or ''), E(x['random'] or '')] for x in M['examples'][:20]]
    out.append(table(['Trial', 'Pairing', 'A', 'B', 'Unedited', 'Swap α = 1', 'Non-reference α = 1', 'Random α = 1'], ex_rows, 'text',
                     cap=f'<b>Free-recall replies that changed under the α = 1 swap</b> ({M["n_examples"]} trial × pairing cases; first 20, raw replies, abstention unspecified).'))
    h2('choices', 'Operational choices and deviations')
    out.append(TXT.get('choices', ''))
    if LOG:
        h2('log', 'Log')
        out.append('<ol class="log">' + ''.join(f'<li><time>{e["t"]}</time><div class="entry"><p>{e["text"]}</p></div></li>' for e in reversed(LOG)) + '</ol>')
    return '\n'.join(out), toc


JS = r'''
const FONT = "'Source Sans 3', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";
const CFG = {displayModeBar:false, responsive:true, scrollZoom:false};
function ax(x) { return Object.assign({showgrid:false, zeroline:false, fixedrange:true, showline:true, linecolor:"#cfc4b4", ticks:"outside", ticklen:4, tickcolor:"#cfc4b4", tickfont:{family:FONT,size:12,color:"#5e5245"}}, x); }
const gax = x => ax(Object.assign({showgrid:true, gridcolor:"#efe8dc"}, x));
const tt = t => ({text:t, font:{family:FONT,size:12,color:"#8a7d6d"}, standoff:6});
const base = (h, m) => ({font:{family:FONT,size:12,color:"#5e5245"}, paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", dragmode:false, height:h, showlegend:false, margin:m||{l:56,r:10,t:14,b:40}});
function render() {
  for (const [id, F] of Object.entries(window.CH)) {
    const el = document.getElementById("chart-" + id); if (!el) continue;
    if (F.kind === "bars") {
      const tr = F.series.map(s => ({type:"bar", name:s.name, x:F.groups, y:s.y, marker:{color:s.color, line:{color:"#fffdf9", width:2}},
        error_y:{type:"data", symmetric:false, array:s.hi.map((h,i)=>h-s.y[i]), arrayminus:s.lo.map((l,i)=>s.y[i]-l), color:"#8a7d6d", thickness:1.2, width:3},
        hovertemplate:"%{x}: %{y:.1f}%<extra>"+s.name+"</extra>"}));
      if (F.chance) tr.push({type:"scatter", mode:"markers", x:F.groups, y:F.chance, marker:{symbol:"line-ew-open", size:40, color:"#2a2318", line:{width:2}}, hovertemplate:"%{x}: %{y:.1f}%<extra>other trials</extra>"});
      const shapes = F.chance25 ? [{type:"line", xref:"paper", x0:0, x1:1, y0:25, y1:25, line:{color:"#8a7d6d", width:1, dash:"dot"}}] : [];
      Plotly.react(el, tr, Object.assign(base(330), {barmode:"group", bargap:0.25, bargroupgap:0.05, shapes, xaxis:ax({type:"category"}), yaxis:gax({range:[0,F.ymax], ticksuffix:"%", title:tt(F.ytitle), showline:false, ticks:""})}), CFG);
    } else if (F.kind === "lines") {
      const tr = [];
      F.series.forEach(s => {
        tr.push({type:"scatter", mode:"lines", x:F.x.concat(F.x.slice().reverse()), y:s.hi.concat(s.lo.slice().reverse()), fill:"toself", fillcolor:s.color+"22", line:{width:0}, hoverinfo:"skip"});
        tr.push({type:"scatter", mode:"lines+markers", name:s.name, x:F.x, y:s.y, line:{color:s.color, width:2}, marker:{size:6}, hovertemplate:"α = %{x}: %{y:.3f}<extra>"+s.name+"</extra>"});
      });
      Plotly.react(el, tr, Object.assign(base(250, {l:52,r:8,t:8,b:36}), {xaxis:ax({tickvals:F.x, title:tt("α")}), yaxis:gax({zeroline:true, zerolinecolor:"#cfc4b4", title:tt(F.ytitle)})}), CFG);
    } else if (F.kind === "scatter") {
      const lo = Math.min(...F.x), hi = Math.max(...F.x);
      Plotly.react(el, [{type:"scatter", mode:"markers", x:F.x, y:F.y, error_y:{type:"data", array:F.e, color:"#8a7d6d", thickness:1, width:2}, marker:{color:"#235fa6", size:7}, hovertemplate:"%{x:.2f}: %{y:.2f}<extra></extra>"},
                        {type:"scatter", mode:"lines", x:[lo, hi], y:[F.intercept + F.slope*lo, F.intercept + F.slope*hi], line:{color:"#b0702a", width:2}, hoverinfo:"skip"}],
        Object.assign(base(250, {l:56,r:8,t:8,b:40}), {xaxis:gax({zeroline:true, zerolinecolor:"#cfc4b4", title:tt(F.xtitle)}), yaxis:gax({zeroline:true, zerolinecolor:"#cfc4b4", title:tt(F.ytitle)})}), CFG);
    }
  }
}
let tmr; window.addEventListener("resize", () => { clearTimeout(tmr); tmr = setTimeout(render, 150); }); render();
'''

if __name__ == '__main__':
    body, toc = sections()
    toc_html = '<nav class="toc"><div class="toc-head">Contents</div><ul>' + ''.join(f'<li><a href="#{i}">{t}</a></li>' for i, t in toc) + '</ul></nav>'
    updated = datetime.datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M ET')
    summary = ''.join(f'<li>{b}</li>' for b in TXT.get('summary', []))
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Experiment 1: J-space recall</title>
<meta name="description" content="Experiment 1 on Qwen3.6-27B: can the model recall the contents of its J-space, and does its report causally depend on them?">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>{CSS}{SUBCSS}</style>
</head>
<body>
<div class="page">
{toc_html}
<main>
<header>
  {nav('exp1.html')}
  <p class="crumbs"><b>J-lens introspection</b> · Experiment 1</p>
  <h1>Experiment 1: Can the model recall the contents of its J-space?</h1>
  <p class="byline">Qwen3.6-27B · J++ lens · November 2026 <span class="tag">{TXT.get('tag', 'Done')}</span></p>
  <p class="thanks">Run from the “Introspection experiments” write-up: hold an item in mind while copying, read the J++ lens, ask the model what it held, then swap J-space coordinates during the copy and ask again.
  Thinking disabled, greedy decoding, fp32.</p>
  <details class="toc-mobile"><summary>Contents</summary>{toc_html}</details>
</header>
{('<div class="answer"><span class="answer-tag">Result</span><ul>' + summary + '</ul></div>') if summary else ''}
{body}
<p class="footer">Last updated {updated}.</p>
</main>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<script>window.CH = {json.dumps(CH)};</script>
<script>{JS}</script>
</body>
</html>
'''
    open(os.path.join(HERE, 'exp1.html'), 'w').write(page)
    print('wrote exp1.html', len(page))
