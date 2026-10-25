"""Build v3.html (protocol v3 results tab) from ../v3/results/*.json."""
import json, html, os
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'v3', 'results')
E = html.escape
CSS = open(os.path.join(HERE, 'style.css')).read()
load = lambda n: json.load(open(os.path.join(RES, n))) if os.path.exists(os.path.join(RES, n)) else None
S, LOG, P, J = load('state.json'), load('log.json'), load('prelim.json'), load('judge_validation.json')
CAT = {'instrument': 'Instruments', 'grocery': 'Groceries', 'animal': 'Animals', 'country': 'Countries'}
COL = {'instrument': '#7a4fa3', 'grocery': '#b0702a', 'animal': '#2f8a57', 'country': '#235fa6'}
NAV = [('index.html', 'Results (v2)'), ('protocol.html', 'Protocol v2'), ('v3.html', 'v3: Natural swap')]


def nav(cur):
    return '<nav class="tabs" aria-label="Pages">' + ''.join(f'<a href="{h}"' + (' aria-current="page"' if h == cur else '') + f'>{t}</a>' for h, t in NAV) + '</nav>'


def subnav(cur):
    items = [('v3.html', 'Results'), ('v3-protocol.html', 'Protocol v3')]
    return '<nav class="subtabs" aria-label="v3 pages">' + ''.join(f'<a href="{h}"' + (' aria-current="page"' if h == cur else '') + f'>{t}</a>' for h, t in items) + '</nav>'


SUBCSS = ('.subtabs{display:flex;gap:18px;font-family:var(--sans);font-size:14px;margin:-12px 0 20px}'
          '.subtabs a{color:var(--ink-2);text-decoration:none;padding:2px 0}.subtabs a[aria-current="page"]{color:var(--ink);font-weight:600;'
          'border-bottom:2px solid var(--accent)}.subtabs a:hover{color:var(--accent)}')


def pill(s):
    return {'done': '<span class="pill done">done</span>', 'running': '<span class="pill partial">running</span>',
            'todo': '<span class="pill todo">not started</span>'}[s]


def table(head, rows, cls='', cap=None, note=None):
    h = ''.join(f'<th>{x}</th>' for x in head)
    b = ''.join('<tr>' + ''.join(f'<td>{x}</td>' for x in r) + '</tr>' for r in rows)
    return ('<div class="table-wrap">' + (f'<p class="table-cap">{cap}</p>' if cap else '') + f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'
            + (f'<p class="table-note">{note}</p>' if note else '') + '</div>')


def sections():
    out, toc, n = [], [], [0]
    def h2(i, t, num=True):
        if num: n[0] += 1
        toc.append((i, t)); out.append(f'<h2 id="{i}"><span class="num">{n[0] if num else ""}</span>{t}</h2>')
    h2('status', 'Status')
    out.append(table(['Step', 'What', 'Status'], [[s['step'], s['what'], pill(s['status'])] for s in S['status']], 'text'))
    if P:
        T = P['trials']
        h2('generation', 'Preliminary requests and natural answers')
        nt = len(T)
        out.append(f'<p>96 preliminary requests (24 per category) and one neutral baseline request per category (“I&#8217;m planning an event.” plus the category question). '
                   'Scenarios were written by <code>gpt-5.5</code> and screened as in v2; all requests were frozen before generation. Every answer ended naturally (at most 64 tokens). '
                   'The lens is read at the assistant-start token: the final <code>\\n\\n</code> after <code>&lt;/think&gt;</code>, before any answer text.</p>')
        rows = []
        for c in CAT:
            ts = [t for t in T if t['category'] == c]
            from collections import Counter
            top = Counter(t['X'] for t in ts if t['X']).most_common(4)
            rows.append([CAT[c], str(len(ts)), str(P['no_item_answers'][c]), ', '.join(f'{E(x)} ({k})' for x, k in top),
                         f'{sum(t["X_rank"] is not None for t in ts)}/{len(ts)}', E(P['baselines'][c]['X'] or '—')])
        out.append(table(['Category', 'Situations', 'Answer names no item', 'Most common answer items', 'Answer item in lens top 100 (block 53)', 'Baseline answer'], rows,
                         cap='<b>Natural answers.</b> The answer item X is the first category item the judge finds in the answer.'))
    if J:
        h2('judge', 'Judge validation (step 0)')
        rt, ra = J['rerun']['tokens'], J['rerun']['answers']
        out.append(table(['Check', 'Result'], [
            ['200 random instrument token labels (hand-checked by Claude)', '200/200 correct'],
            ['50 random answer-item lists, all categories (hand-checked by Claude)', '50/50 correct'],
            [f'All {len(J["items"])} non-None instrument token labels (extra check)', '3 item-level problems (below); fragment labels are not used in primary analyses'],
            ['Rerun identity', f'tokens {rt[0]}/{rt[1]}, answers {ra[0]}/{ra[1]}']], 'text',
            cap='<b>Validation.</b> Groceries, animals and countries reuse the v2 token cache and prompts (validated in v2).'))
        out.append('<div class="answer warn"><span class="answer-tag">Amendments (Oct 25, 14:41 ET)</span><ul>'
                   '<li><b>“Yamaha” excluded.</b> The judge labeled this brand as an instrument; its own rerun labels it None.</li>'
                   '<li><b>qin → guqin and zheng → guzheng merged.</b> The verified merge left these Chinese short names separate from their full names, so a swap could have exchanged two names for one instrument.</li>'
                   '<li><b>Head-noun rule.</b> A competitor also counts as named when a named answer item ends with it as a separate word (piano in “digital piano”).</li>'
                   '</ul><p>None of these changes any eligibility count.</p></div>')
        lab = lambda x: f'{x["label"]}' + (f': {E(x["item"])}' if x['item'] else '')
        out.append('<details class="app"><summary>Non-None instrument token labels</summary><div>' +
                   table(['Token', 'Label'], [[f'<code>{E(json.dumps(x["token"], ensure_ascii=False))}</code>', lab(x)] for x in J['items']], 'text') + '</div></details>')
        out.append('<details class="app"><summary>Answer-item validation sample (50)</summary><div>' +
                   table(['Category', 'Answer', 'Items'], [[x['cat'], E(x['answer']), E(', '.join(x['items']) or '—')] for x in J['answers']], 'text') + '</div></details>')
    if P:
        h2('readout', 'Readout block')
        rb = P['readout_block']
        out.append(f'<p>For each block up to 54 we count distinct judge-labeled Items in the top 100 at the assistant-start token, average within category, then across the four categories. '
                   f'<b>The readout block is {rb}</b> (mean {P["curve"][str(rb)]["mean"]:.1f} items), the same block the earlier natural-recommendation pilot selected with fixed lists.</p>')
        out.append('<figure class="wide" id="fig-curve"><div class="fig-panel"><div class="fig-top"><div class="fig-title">Distinct category items in the lens top 100 at the assistant-start token</div>'
                   '<div class="legend" aria-hidden="true">' + ''.join(f'<span><i style="border-color:{COL[c]};border-top-width:2.5px"></i>{CAT[c]}</span>' for c in CAT) +
                   '<span><i style="border-color:#2a2318;border-top-width:2.5px"></i>Mean</span></div></div><div id="chart-curve" class="chart" role="img" aria-label="Items per block"></div>'
                   '<div class="fig-note">24 preliminary situations per category. Judge-labeled Items after amendments.</div></div>'
                   f'<figcaption><b>Figure 1.</b> Category content rises sharply in the last blocks; block {rb} has the most. Countries show far more items than the other categories.</figcaption></figure>')
        h2('k', 'K, category screen, and competitors')
        ks = [k for k in P['k_rows']]
        out.append(table(['K'] + [CAT[c] for c in CAT], [[k] + [f'{P["k_rows"][k][c]}/24' for c in CAT] for k in ks],
                         cap='<b>Eligible preliminary situations by K</b> (at least two competitors in the top K at block 53, answer names an item).',
                         note='K is the smallest of 10, 20, 50 with at least 12/24 instrument situations eligible; other categories are kept if at least 12/24 are eligible at that K.'))
        out.append(f'<p><b>K = {P["chosen"]["K"]}</b>, with no fallback step. <b>Kept: {", ".join(CAT[c] for c in P["kept"])}.</b> '
                   'Animals (11/24) and groceries (0/24) are dropped from the swap stage; their correlational results can still be reported. '
                   'Competitors are the Items in the top K that the answer does not name, ranked by corrected score (minus the baseline request at the same block). B is the top competitor and C the second.</p>')
        for c in CAT:
            ts = [t for t in P['trials'] if t['category'] == c]
            rows = [[t['id'].split('-')[-1], E(t['scenario']), E(t['X'] or '—'), str(t['X_rank'] or '—'),
                     ', '.join(f'{E(i)} ({s:+.2f})' for i, s, r in t['lens_top'][:5]), E(t['B'] or '—'), E(t['C'] or '—'),
                     '✓' if t['eligible'] else '✗'] for t in ts]
            op = ' open' if c in ('instrument',) else ''
            out.append(f'<details class="app"{op}><summary>{CAT[c]}: {sum(t["eligible"] for t in ts)}/24 eligible</summary><div>' +
                       table(['#', 'Scenario', 'Answer item X', 'X rank', 'Lens top items (corrected score)', 'B', 'C', 'Eligible'], rows, 'text') + '</div></details>')
    h2('log', 'Log')
    out.append('<ol class="log">' + ''.join(f'<li><time>{e["t"]}</time><div class="entry"><p>{e["text"]}</p></div></li>' for e in reversed(LOG)) + '</ol>')
    return '\n'.join(out), toc


body, toc = sections()
toc_html = '<nav class="toc"><div class="toc-head">Contents</div><ul>' + ''.join(f'<li><a href="#{i}">{t}</a></li>' for i, t in toc) + '</ul></nav>'
curve = dict(blocks=list(range(55)), **{c: [P['curve'][str(b)][c] for b in range(55)] for c in list(CAT) + ['mean']}, chosen=P['readout_block']) if P else None
import datetime
from zoneinfo import ZoneInfo
updated = datetime.datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M ET')
page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Introspection v3: Results</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>{CSS}{SUBCSS}</style>
</head>
<body>
<div class="page">
{toc_html}
<main>
<header>
  {nav('v3.html')}
  {subnav('v3.html')}
  <p class="crumbs"><b>J-lens introspection</b> · Protocol v3</p>
  <h1>Introspection v3: Natural-recommendation swap</h1>
  <p class="byline">Qwen3.6-27B · J++ lens · October 2026 <span class="tag">{S["tag"]}</span></p>
  <p class="thanks">The model answers an ordinary recommendation request; we read the lens just before it answers, find the <em>other</em> items represented there (competitors),
  and later ask the model about them, swapping two competitors without changing its answer. Design: <a href="v3-protocol.html">protocol v3</a>.</p>
  <details class="toc-mobile"><summary>Contents</summary>{toc_html}</details>
</header>
<div class="answer"><span class="answer-tag">{S["summary_tag"]}</span><ul>{"".join(f"<li>{b}</li>" for b in S["summary"])}</ul></div>
{body}
<p class="footer">Last updated {updated}.</p>
</main>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<script>
const CURVE = {json.dumps(curve)};
const COL = {json.dumps(COL)}, NAMES = {json.dumps(CAT)};
const FONT = "'Source Sans 3', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";
function ax(x) {{ return Object.assign({{showgrid:false, zeroline:false, fixedrange:true, showline:true, linecolor:"#cfc4b4", ticks:"outside", ticklen:4, tickcolor:"#cfc4b4", tickfont:{{family:FONT,size:12,color:"#5e5245"}}}}, x); }}
function render() {{
  const el = document.getElementById("chart-curve"); if (!el || !CURVE) return;
  const tr = Object.keys(NAMES).map(c => ({{type:"scatter", mode:"lines", x:CURVE.blocks, y:CURVE[c], name:NAMES[c], line:{{color:COL[c], width:2}}, hovertemplate:"Block %{{x}}: %{{y:.1f}}<extra>"+NAMES[c]+"</extra>"}}));
  tr.push({{type:"scatter", mode:"lines", x:CURVE.blocks, y:CURVE.mean, name:"Mean", line:{{color:"#2a2318", width:2.5}}, hovertemplate:"Block %{{x}}: %{{y:.1f}}<extra>Mean</extra>"}});
  Plotly.react(el, tr, {{font:{{family:FONT,size:12.5,color:"#5e5245"}}, paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", showlegend:false, dragmode:false, height:320,
    margin:{{l:50,r:10,t:14,b:40}}, hovermode:"x unified", xaxis:ax({{title:{{text:"Block (0-based block output)",font:{{size:12,color:"#8a7d6d"}}}}, dtick:6}}),
    yaxis:ax({{showgrid:true, gridcolor:"#efe8dc", title:{{text:"Items in top 100",font:{{size:12,color:"#8a7d6d"}}}}, rangemode:"tozero"}}),
    shapes:[{{type:"line", x0:CURVE.chosen, x1:CURVE.chosen, yref:"paper", y0:0, y1:1, line:{{color:"#8a7d6d", width:1, dash:"dot"}}}}]}}, {{displayModeBar:false, responsive:true}});
}}
let t; window.addEventListener("resize", () => {{ clearTimeout(t); t = setTimeout(render, 150); }}); render();
</script>
</body>
</html>
'''
open(os.path.join(HERE, 'v3.html'), 'w').write(page)
print('wrote v3.html', len(page))
