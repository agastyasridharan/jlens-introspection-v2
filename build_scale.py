"""Build scale.html: Experiment 1 across Qwen3.6-27B, Qwen3.5-122B-A10B and DeepSeek-V4-Flash (2026-11-26)."""
import json, os, html, datetime
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
E = html.escape
import build_exp1 as B

MODELS = [
    dict(key='q27', name='Qwen3.6-27B', short='27B', res=os.path.join(ROOT, 'results'), color='#8a7d6d',
         params='27B dense', layers=64, target=63, recall10='55.2%', precision='fp32, 1 GPU', cap=54),
    dict(key='q122', name='Qwen3.5-122B-A10B', short='122B-A10B', res=os.path.join(ROOT, 'scale', 'q122', 'results'), color='#235fa6',
         params='122B MoE, 10B active', layers=48, target=47, recall10='48.4%', precision='bf16, 2 GPUs', cap=40),
    dict(key='dsv4', name='DeepSeek-V4-Flash', short='V4-Flash', res=os.path.join(ROOT, 'scale', 'dsv4', 'results'), color='#b0702a',
         params='284B MoE, 13B active', layers=43, target=42, recall10='61.4%', precision='bf16 (dequantized FP8/FP4), 5 GPUs', cap=36),
]
MODELS = [m for m in MODELS if os.path.exists(os.path.join(m['res'], 'exp1_measures.json'))]
for m in MODELS:
    m['M'] = json.load(open(os.path.join(m['res'], 'exp1_measures.json')))
    m['D'] = json.load(open(os.path.join(m['res'], 'exp1_design.json')))
    m['P'] = json.load(open(os.path.join(m['res'], 'prelim.json')))
    m['RB'] = m['D']['readout_block']
TXT = json.load(open(os.path.join(ROOT, 'results', 'scale_text.json'))) if os.path.exists(os.path.join(ROOT, 'results', 'scale_text.json')) else {}
LOG = json.load(open(os.path.join(ROOT, 'results', 'scale_log.json'))) if os.path.exists(os.path.join(ROOT, 'results', 'scale_log.json')) else []
NAV = B.NAV
FREE = B.FREE
CH = {}
table, fig = B.table, B.fig
bm, pv, f1 = B.bm, B.pv, B.f1


def nav(cur):
    return '<nav class="tabs" aria-label="Pages">' + ''.join(f'<a href="{h}"' + (' aria-current="page"' if h == cur else '') + f'>{t}</a>' for h, t in NAV) + '</nav>'


def g(d, *ks, default=None):
    for k in ks:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def pctci(d):
    return '—' if not d else f'{d["pct"]:.1f}% <span class="muted">[{d["lo"]:.1f}, {d["hi"]:.1f}]</span>'


def alpha_note(p):
    """Other α levels, where a model ran them (27B: 0.25 and 0.5 on all trials, see exp1.html; 122B: 0.5 on its first trials)."""
    out = []
    for m in MODELS:
        for a in m['M']['alphas']:
            if a == 1.0:
                continue
            sw_, nr_ = g(m['M'], 'swap', f'{p}/{p}_swap_{a}'), g(m['M'], 'swap', f'{p}/{p}_nonref_{a}')
            out.append(f'{m["short"]} α = {a:g} ({sw_["valid"]} trials): swap &#916; free {sw_["2_unspecified"]["delta"]["mean"]:+.2f}, '
                       f'non-reference swap on its own pair {nr_["2_unspecified"]["delta_DC"]["mean"]:+.2f}, recognition &#916; {sw_["recog"]["delta"]["mean"]:+.3f}')
    return ('Other α levels: ' + '; '.join(out) + '. ') if out else ''


def sections():
    out, toc = [], []

    def h2(i, t):
        toc.append((i, t)); out.append(f'<h2 id="{i}"><span class="num">{len(toc)}</span>{t}</h2>')

    # ---------------- setup ----------------
    h2('setup', 'Models and what changed')
    out.append(TXT.get('setup', ''))
    rows = []
    for m in MODELS:
        M, D = m['M'], m['D']
        nd = sum('pairings' in t for t in D['trials'])
        curve = m['P']['chart']['mean']
        cnt = {a: g(M, 'swap', f'sw/sw_swap_{a}', 'valid', default=0) for a in M['alphas']}
        if len(set(cnt.values())) > 1:
            m['alpha_note'] = '; '.join(f'{a:g} <span class="muted">({cnt[a]} trials)</span>' for a in sorted(M['alphas'], reverse=True))
        rows.append([f'<b>{m["name"]}</b><br><span class="muted">{m["params"]}; {m["precision"]}</span>', m['recall10'],
                     f'{m["RB"]} of {m["target"]} <span class="muted">({m["RB"] / m["target"]:.2f}; searched 0–{m["cap"]})</span>',
                     f'{curve[m["RB"]]:.2f}', f'{M["repro"]["same_hold"]} / {M["n"]}', f'{nd}', m.get('alpha_note') or ', '.join(f'{a:g}' for a in M['alphas'])])
    out.append(table(['Model', 'Lens recall@10', 'Readout block (relative depth)', 'Items / position at readout',
                      'Trials in (c): copy reproduced / run', 'Trials in (d)', 'α in (d)'], rows, cls='num',
                     note='Lens recall@10 is from the koayon/jpp-lenses model card. The block search is capped at the same relative depth as the 27B&#8217;s 0–54 of 63. '
                          '&#8220;Copy reproduced&#8221;: the unedited copy regenerated in the Exp1 run equals, token for token, the stage-A copy the design was built from.'))
    # block curves
    CH['curves'] = dict(kind='curves', ytitle='Distinct category items per copied position', xtitle='Relative depth (block / final block)',
                        series=[dict(name=m['short'], color=m['color'], x=[b / m['target'] for b in m['P']['chart']['blocks']], y=m['P']['chart']['mean'],
                                     mark=m['RB'] / m['target'], marky=m['P']['chart']['mean'][m['RB']]) for m in MODELS])
    out.append(fig('curves', 'Category items in the lens top 100 during the copy', '24 preliminary situations; filled marker = chosen readout block',
                   TXT.get('curves_caption', '<b>Figure 1.</b> The block-selection curve of the appendix, for each model, on a common depth axis.'),
                   legend=[(m['short'], m['color']) for m in MODELS]))

    # ---------------- (c) free recall ----------------
    h2('free', '(c) Free recall')
    out.append(TXT.get('free_reading', ''))
    groups = [n for _, n in FREE]
    CH['free'] = dict(kind='gbars', groups=groups, ytitle='Names the reference item', suffix='%',
                      series=[dict(name=m['short'], color=m['color'], y=[g(m['M'], 'free', f'{k}/all', 'pct') for k, _ in FREE],
                                   lo=[g(m['M'], 'free', f'{k}/all', 'lo') for k, _ in FREE], hi=[g(m['M'], 'free', f'{k}/all', 'hi') for k, _ in FREE],
                                   chance=[g(m['M'], 'free', f'{k}/all', 'perm') for k, _ in FREE]) for m in MODELS])
    out.append(fig('free', 'Free recall: share of replies naming the reference item', 'All 480 trials per model; 95% Wilson intervals; dash = scored against other trials&#8217; reference items',
                   TXT.get('free_caption', '<b>Figure 2.</b>'), legend=[(m['short'], m['color']) for m in MODELS]))
    rows = []
    for k, n in FREE:
        for m in MODELS:
            d = g(m['M'], 'free', f'{k}/all')
            rows.append([n if m is MODELS[0] else '', m['short'], pctci(d), f1(d['perm']), f1(d['abstain']), f1(d['deny']), f1(d['trunc'] - d['deny']), f1(d['notitem'])])
    out.append(table(['Condition', 'Model', 'Names reference', 'Other trials&#8217; reference', 'Abstains (NONE)', 'Denies holding an item', 'Other cut-off reply', 'Not an item'], rows, cls='num',
                     note='Percent of all trials. &#8220;Abstains&#8221; and &#8220;Not an item&#8221; are the judge&#8217;s labels. Replies that hit the 16-token cap are not judged and count as not naming an item; '
                          'those that open with &#8220;I cannot&#8221;, &#8220;I did not&#8221;, &#8220;I don&#8217;t&#8221; or &#8220;As an AI&#8221; are counted as denials (a pattern match; every such reply we read says the model did not, or as an AI could not, keep an item in mind).'))

    # ---------------- recognition ----------------
    h2('recog', '(c) Multiple-choice recognition')
    out.append(TXT.get('recog_reading', ''))
    menus = [('strict_required', 'Strict'), ('loose_required', 'Loose'), ('strict_abstain', 'Strict, U allowed'), ('loose_abstain', 'Loose, U allowed')]
    CH['recog'] = dict(kind='gbars', groups=[n for _, n in menus], ytitle='Picks the reference item', suffix='%', chance25=True,
                       series=[dict(name=m['short'], color=m['color'], y=[g(m['M'], 'recog', f'{k}/all', 'pct') for k, _ in menus],
                                    lo=[g(m['M'], 'recog', f'{k}/all', 'lo') for k, _ in menus], hi=[g(m['M'], 'recog', f'{k}/all', 'hi') for k, _ in menus]) for m in MODELS])
    out.append(fig('recog', 'Recognition: share of trials picking the reference item', '480 trials per model; chance is 25% (dotted)',
                   TXT.get('recog_caption', '<b>Figure 3.</b>'), legend=[(m['short'], m['color']) for m in MODELS]))
    rows = []
    for m in MODELS:
        P = m['M']['pairs']
        rows.append([m['short']] + [f'{P[x]["all"]["slope"]:.2f} <span class="muted">(SE {P[x]["all"]["se"]:.2f})</span>' for x in ('strict', 'loose')]
                    + [f'{g(m["M"], "recog", f"{x}_abstain/all", "abstain", default=0)}' for x in ('strict', 'loose')]
                    + [f'{sum(t.get("filled", 0) > 0 for t in m["D"]["trials"])}'])
    out.append(table(['Model', 'Slope, strict (nats per score unit)', 'Slope, loose', 'U answers, strict', 'U answers, loose', 'Trials with filled options'], rows, cls='num',
                     note='Slope of log P(i) &#8722; log P(j) (answer letters) on s<sub>i</sub> &#8722; s<sub>j</sub> over all option pairs, answer required, SEs clustered by trial. '
                          'Scores are on each model&#8217;s own lens scale, so slopes compare direction and significance more than size. '
                          'Trials with fewer than four candidates get options filled from the category pool.'))

    # ---------------- (d) swap ----------------
    h2('swap', '(d) Swapping J-space coordinates')
    out.append(TXT.get('swap_reading', ''))
    kinds = [('swap', 'Swap A ↔ B'), ('nonref', 'Non-reference swap'), ('random', 'Random')]
    for p in ('sw', 'sm'):
        groups = [m['short'] for m in MODELS]
        CH[f'delta_{p}'] = dict(kind='gbars', groups=groups, ytitle='Δ log P(B) − log P(A), nats', suffix='', zero=True,
                                series=[dict(name=n, color=B.KC[k], y=[g(m['M'], 'swap', f'{p}/{p}_{k}_1.0', '2_unspecified', 'delta', 'mean') for m in MODELS],
                                             lo=[g(m['M'], 'swap', f'{p}/{p}_{k}_1.0', '2_unspecified', 'delta', 'lo') for m in MODELS],
                                             hi=[g(m['M'], 'swap', f'{p}/{p}_{k}_1.0', '2_unspecified', 'delta', 'hi') for m in MODELS]) for k, n in kinds]
                                + [dict(name='Non-reference swap, its own pair (Δ D vs C)', color='#d9b48a',
                                        y=[g(m['M'], 'swap', f'{p}/{p}_nonref_1.0', '2_unspecified', 'delta_DC', 'mean') for m in MODELS],
                                        lo=[g(m['M'], 'swap', f'{p}/{p}_nonref_1.0', '2_unspecified', 'delta_DC', 'lo') for m in MODELS],
                                        hi=[g(m['M'], 'swap', f'{p}/{p}_nonref_1.0', '2_unspecified', 'delta_DC', 'hi') for m in MODELS])])
        out.append(fig(f'delta_{p}', f'Free recall, {B.PN[p].lower()} pairing, α = 1: change in the B-vs-A name margin',
                       'Abstention unspecified; teacher-forced name log-probabilities; 95% bootstrap intervals over trials',
                       TXT.get(f'delta_{p}_caption', ''), legend=[(n, B.KC[k]) for k, n in kinds] + [('Non-ref., own pair', '#d9b48a')]))
    # main table
    for p in ('sw', 'sm'):
        rows = []
        for m in MODELS:
            S = m['M']['swap']
            for a in [1.0]:
                for k, n in kinds:
                    s = S.get(f'{p}/{p}_{k}_{a}')
                    if not s:
                        continue
                    u = S[f'{p}/unedited']
                    rows.append([m['short'] if k == 'swap' else '', n, f'{100 * s["rel"]:.1f}%',
                                 f'{u["2_unspecified"]["A"]:.1f} → {s["2_unspecified"]["A"]:.1f}',
                                 f'{u["3_prohibited"]["A"]:.1f} → {s["3_prohibited"]["A"]:.1f}',
                                 f'{s["3_prohibited"]["B"]:.1f}', f'{s["3_prohibited"]["changed"]:.1f}',
                                 bm(s['2_unspecified']['delta']), bm(s['2_unspecified']['delta_DC']), bm(s['recog']['delta'], 3),
                                 f'{s["recog"]["changed"]:.1f}', bm(s['dsBA'])])
        out.append(table(['Model', 'Edit', 'Edit / residual', 'Names A, unspec. (%)', 'Names A, prohib. (%)', 'Names B, prohib. (%)', 'Changed, prohib. (%)',
                          'Δ free (B vs A)', 'Δ free (D vs C)', 'Δ recognition', 'Recog. changed (%)', 'Δs<sub>B,A</sub>'], rows, cls='num',
                         cap=f'{B.PN[p]} pairing, α = 1', note=alpha_note(p) + f'Trials with (d): {", ".join(f"{m["short"]} {m["M"]["swap"][f"{p}/unedited"]["valid"]}" for m in MODELS)}. '
                         'Names A: unedited → edited. &#916; free uses abstention unspecified; recognition is the pairing&#8217;s four-option question.'))
    rows = []
    for m in MODELS:
        for p in ('sw', 'sm'):
            sw_ = g(m['M'], 'swap', f'{p}/{p}_swap_1.0', '2_unspecified', 'delta')
            nr_ = g(m['M'], 'swap', f'{p}/{p}_nonref_1.0', '2_unspecified', 'delta_DC')
            sp_ = g(m['M'], 'specific', f'{p}/1.0/2_unspecified')
            rows.append([m['short'] if p == 'sw' else '', B.PN[p], bm(sw_), bm(nr_), bm(sp_), f'{sp_["n"]}'])
    out.append(table(['Model', 'Pairing', 'Swap A ↔ B: shift of B vs A', 'Non-reference swap C ↔ D: shift of D vs C', 'Difference (paired by trial)', 'Trials'], rows, cls='num',
                     cap='Is the reference item special? Each edit&#8217;s shift of its own pair, α = 1, abstention unspecified (nats; 95% bootstrap CI)',
                     note='If the model&#8217;s report drew on the reference item in a privileged way, swapping A with B should move the report more than swapping two other items matched for lens-score gap and size of edit. A positive difference would mean it does.'))
    out.append(TXT.get('swap_more', ''))
    # paired tests vs controls at alpha 1
    rows = []
    for m in MODELS:
        for p in ('sw', 'sm'):
            for ctrl in ('nonref', 'random'):
                c2 = g(m['M'], 'compare', f'{p}/1.0/{ctrl}/2_unspecified') or {}
                c3 = g(m['M'], 'compare', f'{p}/1.0/{ctrl}/3_prohibited') or {}
                cr = g(m['M'], 'compare', f'{p}/1.0/{ctrl}/recog') or {}
                rows.append([m['short'] if (p == 'sw' and ctrl == 'nonref') else '', B.PN[p] if ctrl == 'nonref' else '', B.KN[ctrl],
                             f'{c3["A"]["diff"]["mean"]:+.1f} <span class="muted">(p {pv(c3["A"]["p"])})</span>' if c3 else '—',
                             f'{c3["changed"]["diff"]["mean"]:+.1f} <span class="muted">(p {pv(c3["changed"]["p"])})</span>' if c3 else '—',
                             bm(c2.get('delta', {})) if c2 else '—', bm(cr.get('delta', {}), 3) if cr else '—'])
    out.append(table(['Model', 'Pairing', 'Control', 'Names A, swap − control (pp, prohib.)', 'Changed, swap − control (pp, prohib.)', 'Δ free, swap − control', 'Δ recog., swap − control'],
                     rows, cls='num', cap='Swap against each control at α = 1 (paired by trial; McNemar p for proportions, bootstrap 95% CI for Δ)'))
    rows = []
    for m in MODELS:
        R = m['M']['reg']
        for k, n in (('2_unspecified', 'Free recall'), ('recog', 'Recognition')):
            r = R.get(f'{k}/swap/both')
            rows.append([m['short'] if k == '2_unspecified' else '', n, f'{r["slope"]:.3f}' if r else '—', f'{r["se"]:.3f}' if r and r['se'] is not None else '—',
                         f'{r["r"]:.2f}' if r else '—', f'{r["clusters"]}' if r else '—'])
    out.append(table(['Model', 'Report', 'Slope of Δ on Δs<sub>B,A</sub>', 'SE', 'r', 'Trials'], rows, cls='num',
                     cap='Does the report change track the lens-score change? (swap conditions, both pairings)',
                     note='&#916;s is read at the edited block, so part of it is the edit itself.'))
    out.append(TXT.get('ds_reading', ''))

    # ---------------- examples ----------------
    h2('examples', 'What the models say')
    out.append(TXT.get('examples', ''))
    rows = []
    for m in MODELS:
        for e in m['M']['examples'][:TXT.get('n_examples', 4)]:
            rows.append([m['short'], E(e['setting']), f'{E(e["A"])} → {E(e["B"])} <span class="muted">({e["pairing"]})</span>', E(e['unedited']), E(e['swap']), E(e['nonref']), E(e['random'])])
    out.append(table(['Model', 'Setting', 'A → B', 'Unedited', 'Swap', 'Non-ref. swap', 'Random'], rows,
                     cap='Free recall (abstention unspecified) in trials where the α = 1 swap changed the reply',
                     note='Counts of such trials: ' + ', '.join(f'{m["short"]} {m["M"]["n_examples"]}' for m in MODELS) + '. Replies are cut at 16 tokens.'))
    h2('choices', 'Porting choices and deviations')
    out.append(TXT.get('choices', ''))
    if LOG:
        h2('log', 'Log')
        out.append('<ol class="log">' + ''.join(f'<li><time>{e["t"]}</time><div class="entry"><p>{e["text"]}</p></div></li>' for e in reversed(LOG)) + '</ol>')
    return '\n'.join(out), toc


JS2 = r'''
function render2() {
  for (const [id, F] of Object.entries(window.CH)) {
    const el = document.getElementById("chart-" + id); if (!el) continue;
    if (F.kind === "gbars") {
      const tr = F.series.map(s => ({type:"bar", name:s.name, x:F.groups, y:s.y, marker:{color:s.color, line:{color:"#fffdf9", width:2}},
        error_y:{type:"data", symmetric:false, array:s.hi.map((h,i)=>h==null?0:h-s.y[i]), arrayminus:s.lo.map((l,i)=>l==null?0:s.y[i]-l), color:"#8a7d6d", thickness:1.2, width:3},
        hovertemplate:"%{x}: %{y:.2f}"+F.suffix+"<extra>"+s.name+"</extra>"}));
      const shapes = F.chance25 ? [{type:"line", xref:"paper", x0:0, x1:1, y0:25, y1:25, line:{color:"#8a7d6d", width:1, dash:"dot"}}] : [];
      const lay = Object.assign(base(330), {barmode:"group", bargap:0.22, bargroupgap:0.06, shapes, xaxis:ax({type:"category"}),
        yaxis:gax({ticksuffix:F.suffix, title:tt(F.ytitle), showline:false, ticks:"", zeroline:!!F.zero, zerolinecolor:"#8a7d6d"})});
      Plotly.react(el, tr, lay, CFG).then(() => {
        if (!F.series[0].chance) return;
        // chance dashes, one per bar: offset each series inside its group
        const n = F.series.length, w = (1 - 0.22) / n;
        const sh = shapes.slice();
        F.series.forEach((s, j) => s.chance.forEach((c, i) => { if (c == null) return;
          const x0 = i - (1 - 0.22) / 2 + j * w + w * 0.15, x1 = x0 + w * 0.7;
          sh.push({type:"line", xref:"x", x0, x1, y0:c, y1:c, line:{color:"#2a2318", width:2}}); }));
        Plotly.relayout(el, {shapes: sh});
      });
    } else if (F.kind === "curves") {
      const tr = [];
      F.series.forEach(s => {
        tr.push({type:"scatter", mode:"lines", name:s.name, x:s.x, y:s.y, line:{color:s.color, width:2}, hovertemplate:"%{x:.2f}: %{y:.2f}<extra>"+s.name+"</extra>"});
        tr.push({type:"scatter", mode:"markers", x:[s.mark], y:[s.marky], marker:{color:s.color, size:10, line:{color:"#fffdf9", width:1.5}}, hoverinfo:"skip"});
      });
      Plotly.react(el, tr, Object.assign(base(320), {xaxis:gax({range:[0,1], title:tt(F.xtitle)}), yaxis:gax({title:tt(F.ytitle), rangemode:"tozero"})}), CFG);
    }
  }
}
render2(); window.addEventListener("resize", () => { clearTimeout(window.t2); window.t2 = setTimeout(render2, 150); });
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
<title>Experiment 1 scaling</title>
<meta name="description" content="Experiment 1 (J-space recall and coordinate swaps) on Qwen3.6-27B, Qwen3.5-122B-A10B and DeepSeek-V4-Flash.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>{B.CSS}{B.SUBCSS}</style>
</head>
<body>
<div class="page">
{toc_html}
<main>
<header>
  {nav('scale.html')}
  <p class="crumbs"><b>J-lens introspection</b> · Experiment 1 scaling</p>
  <h1>Experiment 1 across three models</h1>
  <p class="byline">Qwen3.6-27B · Qwen3.5-122B-A10B · DeepSeek-V4-Flash · J++ lenses · November 2026 <span class="tag">{TXT.get('tag', 'Running')}</span></p>
  <p class="thanks">The same 480 situations, questions and analysis as <a href="exp1.html">Experiment 1</a>, on two larger models with published J++ lenses.</p>
  <details class="toc-mobile"><summary>Contents</summary>{toc_html}</details>
</header>
{('<div class="answer"><span class="answer-tag">Result</span><ul>' + summary + '</ul></div>') if summary else ''}
{body}
<p class="footer">Last updated {updated}.</p>
</main>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<script>window.CH = {json.dumps(CH)};</script>
<script>{B.JS}</script>
<script>{JS2}</script>
</body>
</html>
'''
    open(os.path.join(HERE, 'scale.html'), 'w').write(page)
    print('wrote scale.html', len(page))
