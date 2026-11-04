"""Build v5.html (introspection scaffolds on the v2/v3 report turns) from ../v5/results/v5.json."""
import json, os, html, datetime
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.join(HERE, '..', 'v5')
E = html.escape
CSS = open(os.path.join(HERE, 'style.css')).read()
R = json.load(open(os.path.join(V5, 'results', 'v5.json')))
SC = json.load(open(os.path.join(V5, 'stimuli', 'scaffolds.json')))
NAV = [('index.html', 'Results (v2)'), ('protocol.html', 'Protocol v2'), ('v3.html', 'v3: Natural swap'), ('v4.html', 'v4: Cued hold'), ('v5.html', 'v5: Scaffolds')]
FR = ['original', 'accurate', 'vague', 'poetic']
DOCS = ['none', 'pro', 'lipsum', 'poetic', 'ellipses']
FNAME = dict(original='Original wording', accurate='Accurate', vague='Vague', poetic='Poetic')
DNAME = dict(none='No document', pro='Pro-Introspection', lipsum='Lipsum', poetic='Poetic doc', ellipses='Ellipses')
LOG = json.load(open(os.path.join(V5, 'results', 'log.json')))
V3, V2 = R['v3'], R['v2']


def nav(cur):
    return '<nav class="tabs" aria-label="Pages">' + ''.join(f'<a href="{h}"' + (' aria-current="page"' if h == cur else '') + f'>{t}</a>' for h, t in NAV) + '</nav>'


SUBCSS = ('.muted{color:var(--ink-3);font-size:.9em}pre.q{white-space:pre-wrap;font-family:var(--sans);font-size:14px;background:var(--panel);'
          'border:1px solid var(--rule);border-radius:4px;padding:10px 12px;margin:4px 0 14px;overflow-x:auto}'
          'td.hl{background:color-mix(in srgb,var(--accent) 12%,transparent);font-weight:600}td.na{color:var(--ink-3)}'
          'details.doc{margin:6px 0 12px}details.doc summary{cursor:pointer;font-family:var(--sans);font-size:14px;color:var(--ink-2)}')


def table(head, rows, cls='', cap=None, note=None):
    h = ''.join(f'<th>{x}</th>' for x in head)
    b = ''.join('<tr>' + ''.join(x if str(x).startswith('<td') else f'<td>{x}</td>' for x in r) + '</tr>' for r in rows)
    return ('<div class="table-wrap">' + (f'<p class="table-cap">{cap}</p>' if cap else '') + f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'
            + (f'<p class="table-note">{note}</p>' if note else '') + '</div>')


def grid(fn, cap, note=None):
    rows = []
    for f in FR:
        r = [f'<b>{FNAME[f]}</b>']
        for d in DOCS:
            c = f'{f}|{d}'
            if c not in SC['cells']:
                r.append('<td class="na">—</td>'); continue
            v = fn(c)
            r.append(f'<td class="hl">{v}</td>' if c in SC['primary'] else v)
        rows.append(r)
    return table([''] + [DNAME[d] for d in DOCS], rows, 'num', cap=cap, note=note)


pp = lambda x: f'{100 * x:+.1f}'
pc = lambda k, n: f'{100 * k / n:.0f}%' if n else '—'


def ci(b, scale=100, f='+.1f'):
    return f"{scale * b['mean']:{f}} <span class='muted'>[{scale * b['lo']:{f}}, {scale * b['hi']:{f}}]</span>"


def sections():
    out, toc, n = [], [], [0]
    def h2(i, t):
        n[0] += 1; toc.append((i, t)); out.append(f'<h2 id="{i}"><span class="num">{n[0]}</span>{t}</h2>')
    h2('design', 'Design')
    out.append('<p>v5 changes only the report turn of the frozen v2 and v3 experiments. It borrows the two prompt factors of Pearson-Vogel et al. (2026, '
               '<a href="https://arxiv.org/abs/2602.20031">arXiv 2602.20031</a>, Appendix B): a <b>framing</b> (how the experimenter describes what they do, and how the question is worded) and an '
               '<b>info document</b> placed before the question. The earlier processing (v3 request and answer, with the frozen swap or control edit; v2 hold phase and copy) is the same as in the original runs, '
               'so a change in reports can only come from how the report reads that state.</p>'
               '<p>Report turn: <code>[framing intro]</code>, blank line, <code>[document]</code>, blank line, <code>[question] [ending]</code>. Context prediction ("another instance of this model…") gets the same intro and document. '
               f'Cells: {len(SC["cells"])} (4 framings × 4 documents, plus Ellipses under the two primary cells). Primary cells, fixed in advance from the paper: '
               '<b>Accurate × Pro-Introspection</b> (its headline improvement) and <b>Vague × Lipsum</b> (its best cell), each against Original × No document.</p>')
    ex = next(iter(SC['questions']['v3_self'].items()))
    rows = [[FNAME[f], E(SC['intros'][f] or '—'), E(SC['questions']['v3_self'][f].format(X='{X}', cat='{category}')), E(SC['questions']['v2_self'][f].format(cat='{category}'))] for f in FR]
    out.append(table(['Framing', 'Intro', 'v3 question', 'v2 question'], rows, 'text', cap='Framings',
                     note='Vague and Poetic intros are the paper&#8217;s verbatim. Accurate is rewritten to describe our lens readout and edits (the paper&#8217;s describes concept injection). '
                          'The paper&#8217;s Wrong framing (weight finetuning) was frozen but dropped from the run for time.'))
    tc = SC['token_counts']
    out.append(f'<p>Documents (Qwen3.6 tokens): Pro-Introspection {tc["pro"]} (Janus&#8217;s K/V paragraph plus the Lindsey 2025 abstract), Lipsum {tc["lipsum"]} (matched), Ellipses {tc["ellipses"]} (matched), Poetic {tc["poetic"]}. '
               'Texts are the paper&#8217;s Appendix B.3 verbatim.</p>')
    out.append('<details class="doc"><summary>Pro-Introspection document (from arXiv 2602.20031, Appendix B.3)</summary><pre class="q">' + E(SC['docs']['pro']) + '</pre></details>')

    h2('primary', 'Primary tests')
    P = R['primary']
    rows = []
    for name, p, h in zip(P['tests'], P['p'], P['holm']):
        kind, cell = name.split(' ')[0], name.split(' ')[-1]
        if kind == 'v3':
            c = V3['cells'][cell]; fc = c['follow_counts']
            est = f"{ci(c['follow'])} pp <span class='muted'>({fc['swap']} vs {fc['control']} of {V3['n_pairs']})</span>"
        else:
            c = V2['cells'][cell]
            est = f"{ci(c['adv_vs_base'])} pp"
        f, d = cell.split('|')
        fp = lambda x: '&lt;0.001' if x < 1e-3 else f'{x:.2g}'
        rows.append(['v3 report-follow (C under swap − control)' if kind == 'v3' else 'v2 self advantage, minus baseline', f'{FNAME[f]} × {DNAME[d]}', est, fp(p), fp(h)])
    out.append(table(['Test', 'Cell', 'Estimate [95% CI]', 'p', 'Holm p'], rows, 'num', cap='Four pre-specified primary tests',
                     note='v3: exact McNemar over situations where both swap and control keep the answer. v2: per-trial (self match − context match) in the cell minus the same in the baseline cell, bootstrap.'))

    h2('v3', 'v3: does the report follow the swap?')
    out.append(f'<p>{V3["n"]} eligible v3 situations. Under bf16, the swap keeps the answer in {V3["valid"]["swap"]} and the control in {V3["valid"]["control"]}; both in <b>{V3["n_pairs"]}</b> (the report-follow set). '
               f'The bf16 model regenerates the original fp32 answer exactly in {V3["bf16_matches_original"]} of {V3["n"]}; the original answer is teacher-forced in every condition.</p>')
    out.append(grid(lambda c: f"{pp(V3['cells'][c]['follow']['mean'])} <span class='muted'>({V3['cells'][c]['follow_counts']['swap']}/{V3['cells'][c]['follow_counts']['control']})</span>",
                    'Report-follow: share naming C under swap minus control, pp (counts swap/control)',
                    note=f'n = {V3["n_pairs"]} paired situations per cell. Highlighted: primary cells.'))
    out.append(grid(lambda c: f"{V3['cells'][c]['B_retention']['swap']}/{V3['cells'][c]['B_retention']['control']}", 'B-retention: reports naming B, swap/control'))
    out.append(grid(lambda c: f"{pc(V3['cells'][c]['agree_B']['self'], V3['n'])} / {pc(V3['cells'][c]['agree_B']['context'], V3['n'])}",
                    'No edit: report names B (the top lens competitor), self / context prediction',
                    note='Context prediction: a fresh conversation quoting the request and answer, asking about "another instance of this model", with the same intro and document.'))
    out.append(grid(lambda c: f"{pc(V3['cells'][c]['labels_self']['Truncated'], V3['n'])} / {pc(V3['cells'][c]['labels_self']['Abstention'], V3['n'])}",
                    'No edit, self-report: truncated at 16 tokens / abstained (free naming 1)'))
    rows = [[f"{FNAME[c.split('|')[0]]} × {DNAME[c.split('|')[1]]}", pc(V3['cells'][c]['abstain_free2']['self'], V3['n']), pc(V3['cells'][c]['abstain_free2']['context'], V3['n'])]
            for c in SC['extra_cells'] if 'abstain_free2' in V3['cells'][c]]
    out.append(table(['Cell', 'Self abstains', 'Context abstains'], rows, 'num', cap='"…or NONE if you cannot identify one": abstention, self vs context prediction'))
    lat = dict(blocks=list(range(40, 63)), series=[dict(name=f"{FNAME[c.split('|')[0]]} × {DNAME[c.split('|')[1]]}", y=V3['cells'][c]['latent']) for c in SC['extra_cells']])
    out.append('<figure><div class="fig-frame"><div id="chart-latent" class="chart" role="img" aria-label="Latent report-follow by block"></div>'
               '<div class="fig-note">J++ lens log p(C) − log p(B) at the report&#8217;s first generated token, swap minus control, mean over paired situations.</div></div>'
               '<figcaption><b>Figure 1.</b> Latent report-follow by block: whether the report position carries the swap internally, as in the paper&#8217;s logit-lens analysis.</figcaption></figure>')
    out.append('<script>window.LATFIG = ' + json.dumps(lat) + ';</script>')

    h2('v2', 'v2: self-report vs context prediction')
    out.append(f'<p>{V2["n"]} v2 main trials (seeded sample), {V2["n_eligible"]} eligible under the frozen v2 rule (reference item in the lens top 10). Free naming condition 2. '
               f'The bf16 model reproduces the original copy in {V2["bf16_matches_original"]} of {V2["n"]}; the original copy is teacher-forced.</p>')
    N2 = V2['n_eligible']
    out.append(grid(lambda c: f"{pc(V2['cells'][c]['agree']['self'], N2)} / {pc(V2['cells'][c]['agree']['context'], N2)}", 'Report matches the lens reference item: self / context prediction'))
    out.append(grid(lambda c: ci(V2['cells'][c]['adv_vs_base']), 'Self advantage (self − context), minus the baseline cell&#8217;s, pp [95% CI]'))
    out.append(grid(lambda c: f"{pc(V2['cells'][c]['labels_self']['Abstention'], N2)} / {pc(V2['cells'][c]['labels_ctx']['Abstention'], N2)}", 'Abstained without being offered NONE: self / context'))
    S = V2['swap']
    rows = []
    for c in SC['extra_cells']:
        x = S['cells'][c]
        rows.append([f"{FNAME[c.split('|')[0]]} × {DNAME[c.split('|')[1]]}"] + [f"{x[k]['A']} / {x[k]['B']}" for k in ('none0', 'swap1', 'control1', 'swap2', 'control2')])
    out.append(table(['Cell', 'No edit', 'Swap α1', 'Control α1', 'Swap α2', 'Control α2'], rows, 'num',
                     cap=f'v2 hold-phase swap (A → B at block 54): reports naming A / naming B, of {S["n"]}',
                     note='The copy is teacher-forced with the edit active; validity (edited greedy = copy at every step) is reported in the JSON.'))

    h2('reading', 'Reading')
    out.append(R.get('reading', ''))
    h2('amend', 'Deviations from the draft protocol')
    out.append('<ul>' + ''.join(f'<li>{E(a)}</li>' for a in R['scaffolds']['amendments']) + '</ul>')
    h2('log', 'Log')
    out.append('<ol class="log">' + ''.join(f'<li><time>{e["t"]}</time><div class="entry"><p>{e["text"]}</p></div></li>' for e in reversed(LOG)) + '</ol>')
    return '\n'.join(out), toc


if __name__ == '__main__':
    body, toc = sections()
    toc_html = '<nav class="toc"><div class="toc-head">Contents</div><ul>' + ''.join(f'<li><a href="#{i}">{t}</a></li>' for i, t in toc) + '</ul></nav>'
    updated = datetime.datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M ET')
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Introspection v5: Scaffolds</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>{CSS}{SUBCSS}</style>
</head>
<body>
<div class="page">
{toc_html}
<main>
<header>
  {nav('v5.html')}
  <p class="crumbs"><b>J-lens introspection</b> · Protocol v5</p>
  <h1>Introspection v5: Telling the model how introspection works</h1>
  <p class="byline">Qwen3.6-27B · J++ lens · November 2026 <span class="tag">Done</span></p>
  <p class="thanks">The v2 and v3 report questions, rerun under the framings and background documents of Pearson-Vogel et al. (2026), which raised injected-concept detection in Qwen2.5-Coder-32B.
  The question: does explaining introspection make the report track the earlier state?</p>
  <details class="toc-mobile"><summary>Contents</summary>{toc_html}</details>
</header>
<div class="answer"><span class="answer-tag">Result</span><ul>{"".join(f"<li>{b}</li>" for b in R.get('summary', []))}</ul></div>
{body}
<p class="footer">Last updated {updated}.</p>
</main>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<script>
const FONT = "'Source Sans 3', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";
function ax(x) {{ return Object.assign({{showgrid:false, zeroline:false, fixedrange:true, showline:true, linecolor:"#cfc4b4", ticks:"outside", ticklen:4, tickcolor:"#cfc4b4", tickfont:{{family:FONT,size:12,color:"#5e5245"}}}}, x); }}
const base = h => ({{font:{{family:FONT,size:12,color:"#5e5245"}}, paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", dragmode:false, height:h}});
function renderLat() {{
  const el = document.getElementById("chart-latent"); const F = window.LATFIG; if (!el || !F) return;
  const cols = ["#8a7d6d", "#235fa6", "#b4531f"];
  Plotly.react(el, F.series.map((s, i) => ({{type:"scatter", mode:"lines", name:s.name, x:F.blocks, y:s.y, line:{{color:cols[i], width:2}},
    hovertemplate:"Block %{{x}}: %{{y:+.3f}}<extra>"+s.name+"</extra>"}})),
    Object.assign(base(320), {{margin:{{l:56,r:10,t:14,b:44}}, hovermode:"x unified", legend:{{orientation:"h", y:1.12, x:0}},
    xaxis:ax({{title:{{text:"Block",font:{{size:12,color:"#8a7d6d"}}}}, dtick:2}}),
    yaxis:ax({{showgrid:true, gridcolor:"#efe8dc", title:{{text:"C − B log-prob, swap − control",font:{{size:12,color:"#8a7d6d"}}}}, zeroline:true, zerolinecolor:"#cfc4b4"}})}}), {{displayModeBar:false, responsive:true}});
}}
let t; window.addEventListener("resize", () => {{ clearTimeout(t); t = setTimeout(renderLat, 150); }}); renderLat();
</script>
</body>
</html>
'''
    open(os.path.join(HERE, 'v5.html'), 'w').write(page)
    print('wrote v5.html', len(page))
