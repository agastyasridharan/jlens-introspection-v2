"""Build v4.html (cued single-token hold) from ../v4/results/pilot.json and pilot_explore.json."""
import json, os, html, datetime
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'v4', 'results')
E = html.escape
CSS = open(os.path.join(HERE, 'style.css')).read()
load = lambda n: json.load(open(os.path.join(RES, n))) if os.path.exists(os.path.join(RES, n)) else None
P, X = load('pilot.json'), load('pilot_explore.json')
DESIGN = json.load(open(os.path.join(HERE, '..', 'v4', 'stimuli', 'pilot_design.json')))
CAT = {'grocery': 'Groceries', 'animal': 'Animals', 'country': 'Countries'}
NAV = [('index.html', 'Results (v2)'), ('protocol.html', 'Protocol v2'), ('v3.html', 'v3: Natural swap'), ('v4.html', 'v4: Cued hold'), ('v5.html', 'v5: Scaffolds')]
LOG = [
    dict(t='2026-11-03 19:21 ET', text='Protocol v4 written and pilot criteria frozen before generation. Cue words frozen (<code>v4/stimuli/cues.json</code>): 3 per carrier, all single tokens in context.'),
    dict(t='2026-11-03 19:24 ET', text='Pilot generation done on 6 H200s: 72 of 72 copies exact, and token-for-token identical to the v2 hold-all copies of the same situations.'),
    dict(t='2026-11-03 19:29 ET', text='Judge labels for new lens tokens (frozen v2 prompts and cache, merge_main synonym map). Primary measures computed: both go criteria fail. Exploratory profile of the token before the cue added.'),
]


def nav(cur):
    return '<nav class="tabs" aria-label="Pages">' + ''.join(f'<a href="{h}"' + (' aria-current="page"' if h == cur else '') + f'>{t}</a>' for h, t in NAV) + '</nav>'


def subnav(cur):
    items = [('v4.html', 'Results'), ('v4-protocol.html', 'Protocol v4')]
    return '<nav class="subtabs" aria-label="v4 pages">' + ''.join(f'<a href="{h}"' + (' aria-current="page"' if h == cur else '') + f'>{t}</a>' for h, t in items) + '</nav>'


SUBCSS = ('.subtabs{display:flex;gap:18px;font-family:var(--sans);font-size:14px;margin:-12px 0 20px}'
          '.subtabs a{color:var(--ink-2);text-decoration:none;padding:2px 0}.subtabs a[aria-current="page"]{color:var(--ink);font-weight:600;'
          'border-bottom:2px solid var(--accent)}.subtabs a:hover{color:var(--accent)}'
          '.muted{color:var(--ink-3);font-size:.9em}pre.q{white-space:pre-wrap;font-family:var(--sans);font-size:14px;background:var(--panel);'
          'border:1px solid var(--rule);border-radius:4px;padding:10px 12px;margin:4px 0 14px;overflow-x:auto}')


def table(head, rows, cls='', cap=None, note=None):
    h = ''.join(f'<th>{x}</th>' for x in head)
    b = ''.join('<tr>' + ''.join(f'<td>{x}</td>' for x in r) + '</tr>' for r in rows)
    return ('<div class="table-wrap">' + (f'<p class="table-cap">{cap}</p>' if cap else '') + f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'
            + (f'<p class="table-note">{note}</p>' if note else '') + '</div>')


ci = lambda b, f='+.2f': f"{b['mean']:{f}} <span class='muted'>[{b['lo']:{f}}, {b['hi']:{f}}]</span>"
pct = lambda x: f'{100 * x:.0f}%'
G, XG = P['groups'], X['groups']
GS = list(CAT) + ['all']
NAME = dict(CAT, all='All')

SUMMARY = [
    f"<b>Pre-registered result: no-go.</b> At the copied cue word, cueing does not raise lens item content: cue effect {G['all']['cue_effect']['mean']:+.2f} items "
    f"(95% CI {G['all']['cue_effect']['lo']:+.2f} to {G['all']['cue_effect']['hi']:+.2f}, 24 situations), and the cue word is the peak in {pct(G['all']['peak'])} of trials (chance {pct(G['all']['chance'])}). "
    "Both frozen criteria fail, so the main and swap stages were not run.",
    f"<b>The content moves one token earlier.</b> At the token <em>before</em> the cue (the position where the model is about to write the cue word), cueing adds "
    f"{X['offsets']['-1']['mean']:+.1f} items (CI {X['offsets']['-1']['lo']:+.1f} to {X['offsets']['-1']['hi']:+.1f}), and that token is the peak in {pct(XG['all']['peak_prev'])} of trials. Exploratory: this position was a listed sensitivity check, not the primary readout.",
    f"<b>It is mostly category content, not the chosen item.</b> The top lens items there are prototypes (“dog” in 13 of 24 animal trials; “apple” or “bread” in 13 of 24 grocery trials). "
    f"The model's report names the top lens item in {pct(XG['all']['report_cued_eq_top1'])} of trials. The report is among the top 5 lens items {pct(0.31)} of the time, against {pct(0.21)} for a report from another situation.",
    f"<b>The same content appears when the instruction itself names the cue.</b> At the opening quote before the cue word in the instruction (“…the word \"”), there are {XG['all']['prompt_quote']:.1f} items on average, against {XG['all']['count_prev']:.1f} at the copied token before the cue. "
    "This suggests the effect is tied to the cue string, not to a held choice.",
]


def sections():
    out, toc, n = [], [], [0]
    def h2(i, t):
        n[0] += 1; toc.append((i, t)); out.append(f'<h2 id="{i}"><span class="num">{n[0]}</span>{t}</h2>')
    t0 = next(t for t in DESIGN['trials'] if t['id'] == 'p-grocery-000-early')
    h2('design', 'Design')
    out.append('<p>The v2 copy-and-hold prompt, with one added sentence that pins the hold to a named word of the sentence. '
               '24 v2 preliminary situations (8 per category, same settings and carriers as v2) × 3 cue words (early, middle, late) = 72 trials. '
               'Greedy decoding, thinking disabled; the J++ lens top 100 at every block and every position from the user message to the end of the copy.</p>'
               f'<p class="muted">Example prompt (p-grocery-000-early):</p><pre class="q">{E(t0["prompt"])}</pre>'
               f'<p class="muted">Report questions, each in its own branch after the copy:</p><pre class="q">{E(t0["questions"]["cued"])}\n{E(t0["questions"]["v2_cond2"])}</pre>'
               '<p>Main measure, at readout block 54 (frozen from v2): M(p), the number of distinct judge-labeled items in the lens top 100 at position p. '
               'The <b>cue effect</b> compares one word with itself: M at word w when w is the cue, minus the mean M at the same word when one of the other two words is the cue (same setting and carrier). '
               '<b>Go criterion (frozen):</b> pooled cue effect with bootstrap 95% lower bound above 0, and cue word the peak in at least 30% of trials.</p>')
    h2('primary', 'Pre-registered result: the cue word')
    rows = [[NAME[g], ci(G[g]['cue_effect']), f"{G[g]['count_cue']:.2f}", f"{G[g]['count_v2_same']:.2f}", pct(G[g]['peak']), pct(G[g]['chance']), pct(G[g]['eligible'])] for g in GS]
    out.append(table(['', 'Cue effect (items)', 'Items at cue', 'v2 hold-all, same word', 'Peak at cue', 'Chance', 'Eligible'], rows, 'num',
                     cap='Block 54, at the copied cue token (n = 24 situations, 72 trials)',
                     note='All 72 copies are exact and identical, token for token, to v2&#8217;s hold-all copies. Eligible means the reference item (top corrected item at the cue token) is in the lens top 10 there. '
                          f'Go check: lower bound above 0 — <b>{"yes" if P["go"]["cue_effect_lb_pos"] else "no"}</b>; peak ≥ 30% — <b>{"yes" if P["go"]["peak_ge_30"] else "no"}</b>.'))
    out.append(f'<p>The copied cue word carries almost no item content whether or not it is cued (under one item in the top 100), much as in v2. The pilot fails both criteria, so per protocol v4 the main and swap stages are not run.</p>')
    h2('offset', 'Exploratory: where the content goes')
    out.append('<p>The same cue-effect comparison, at each position relative to the cue word. Offset −1 is the token before the cue: the position whose output is the cue word. '
               'This was listed in the protocol as a position-sensitivity check, so it is reported here as exploratory.</p>')
    offs = [int(k) for k in X['offsets']]
    fig = dict(x=[('cue' if d == 0 else f'{d:+d}') for d in offs], y=[X['offsets'][str(d)]['mean'] for d in offs],
               lo=[X['offsets'][str(d)]['lo'] for d in offs], hi=[X['offsets'][str(d)]['hi'] for d in offs])
    curve = dict(blocks=[int(b) for b in P['curve']], cue=list(P['curve'].values()), prev=list(X['curve_prev'].values()))
    out.append('<figure><div class="fig-frame"><div id="chart-offset" class="chart" role="img" aria-label="Cue effect by offset from the cue word"></div>'
               '<div class="fig-note">Items in the lens top 100 at block 54: cued minus cued-elsewhere, same word. 95% bootstrap CI over 24 situations.</div></div>'
               '<figcaption><b>Figure 1.</b> Cueing a word raises item content on the two tokens before it, peaking right before it. The cue word itself (0) and the words after it lose content.</figcaption></figure>')
    out.append('<figure><div class="fig-frame"><div id="chart-curve" class="chart" role="img" aria-label="Cue effect by block"></div>'
               '<div class="fig-note">Same comparison at every second block. Blue: token before the cue. Grey: the cue word.</div></div>'
               '<figcaption><b>Figure 2.</b> The effect at the token before the cue appears at block 50–52 and is largest at block 54, the frozen v2 readout block.</figcaption></figure>')
    out.append('<script>window.OFFFIG = ' + json.dumps(fig) + '; window.CURVEFIG = ' + json.dumps(curve) + ';</script>')
    rows = [[NAME[g], f"{XG[g]['count_prev']:.1f}", f"{XG[g]['count_other']:.1f}", f"{XG[g]['v2_prev']:.1f}", pct(XG[g]['peak_prev']), pct(XG[g]['eligible']),
             f"{XG[g]['prompt_quote']:.1f}", f"{XG[g]['prompt_sentence_prev']:.1f}"] for g in GS]
    out.append(table(['', 'Cued', 'Other words', 'v2 hold-all', 'Peak', 'Eligible', 'Instruction quote', 'Sentence line'], rows, 'num',
                     cap='Items in the lens top 100 at block 54, token before the cue (72 trials)',
                     note='Other words: mean over the other copied tokens of the same trial. v2 hold-all: same position, v2 instruction (hold over the whole copy). '
                          'Instruction quote: the opening quote before the cue word inside the instruction. Sentence line: the token before the cue in the prompt&#8217;s copy of the sentence.'))
    h2('content', 'Exploratory: what the content is')
    rows = [[NAME[g], pct(XG[g]['report_cued_eq_top1']), pct(XG[g]['report_v2_eq_top1']), pct(XG[g]['report_cued_in_top10'])] for g in GS]
    out.append(table(['', 'Cued report = top lens item', 'v2-question report = top lens item', 'Cued report in lens top 10'], rows, 'num',
                     cap='Token before the cue, block 54',
                     note=f'Top lens item: the highest-ranked judge-labeled item. The cued and v2-question reports name the same item in {pct(G["all"]["cued_vs_v2_report_same"])} of trials.'))
    out.append('<p>The lens content is dominated by category prototypes that recur across settings, and the reports mostly name a setting-appropriate item that is not the top lens item. '
               'Shuffle check (same category, other situation): the report is among the top 5 lens items in 31% of matched trials against 21% shuffled, so the content is only weakly specific to the situation. '
               'Within a situation, the top lens item agrees across the three cue variants in 22% of pairs, against 16% across situations.</p>')
    pick = ['p-grocery-003-early', 'p-grocery-002-mid', 'p-animal-000-late', 'p-animal-002-early', 'p-country-000-early', 'p-country-001-mid']
    R = {x['id']: x for x in X['rows']}
    sets = {t['id']: t['setting'] for t in DESIGN['trials']}
    rows = [[f"{E(sets[i])}<br><span class='muted'>{R[i]['category']}</span>", f"“{E(R[i]['cue'])}” <span class='muted'>after “{E((R[i]['prev_token'] or '').strip())}”</span>",
             str(R[i]['count_prev']), E(', '.join(R[i]['top_items'][:4])), E(str(R[i]['report_cued']))] for i in pick if i in R]
    out.append(table(['Setting', 'Cue', 'Items', 'Top lens items (token before cue)', 'Cued report'], rows, 'text', cap='Examples'))
    h2('decision', 'Decision')
    out.append('<p>Per the frozen rule, v4 stops at the pilot. The instruction does not put the chosen item at the cue word. It does make category content appear just before the cue word is written, '
               'and also where the instruction quotes the cue. That content is mostly generic, and the reports do not track it. '
               'A swap at the token before the cue would edit content the report does not appear to read, so a follow-up there would need its own pre-registered protocol and a case for why the report should depend on it.</p>')
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
<title>Introspection v4: Results</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>{CSS}{SUBCSS}</style>
</head>
<body>
<div class="page">
{toc_html}
<main>
<header>
  {nav('v4.html')}
  {subnav('v4.html')}
  <p class="crumbs"><b>J-lens introspection</b> · Protocol v4</p>
  <h1>Introspection v4: Cued single-token hold</h1>
  <p class="byline">Qwen3.6-27B · J++ lens · November 2026 <span class="tag">Pilot done · no-go</span></p>
  <p class="thanks">The v2 copy-and-hold task, with the hold pinned to one named word: “Think about the item you chose only while you write the word &quot;painting&quot;.” If the lens showed the item at that word,
  a swap there would test whether the report reads that moment. Design: <a href="v4-protocol.html">protocol v4</a>.</p>
  <details class="toc-mobile"><summary>Contents</summary>{toc_html}</details>
</header>
<div class="answer"><span class="answer-tag">Pilot result</span><ul>{"".join(f"<li>{b}</li>" for b in SUMMARY)}</ul></div>
{body}
<p class="footer">Last updated {updated}.</p>
</main>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<script>
const FONT = "'Source Sans 3', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";
function ax(x) {{ return Object.assign({{showgrid:false, zeroline:false, fixedrange:true, showline:true, linecolor:"#cfc4b4", ticks:"outside", ticklen:4, tickcolor:"#cfc4b4", tickfont:{{family:FONT,size:12,color:"#5e5245"}}}}, x); }}
const base = h => ({{font:{{family:FONT,size:12,color:"#5e5245"}}, paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", showlegend:false, dragmode:false, height:h}});
function renderOff() {{
  const el = document.getElementById("chart-offset"); const F = window.OFFFIG; if (!el || !F) return;
  const col = F.x.map(x => x === "-1" ? "#235fa6" : (x === "cue" ? "#2a2318" : "#b8ab98"));
  Plotly.react(el, [{{type:"bar", x:F.x, y:F.y, marker:{{color:col}},
    error_y:{{type:"data", symmetric:false, array:F.hi.map((h,i)=>h-F.y[i]), arrayminus:F.lo.map((l,i)=>F.y[i]-l), color:"#8a7d6d", thickness:1.2, width:4}},
    hovertemplate:"Offset %{{x}}: %{{y:+.2f}} items<extra></extra>"}}],
    Object.assign(base(300), {{bargap:0.35, margin:{{l:50,r:10,t:14,b:44}}, xaxis:ax({{type:"category", title:{{text:"Position relative to the cue word",font:{{size:12,color:"#8a7d6d"}}}}}}),
    yaxis:ax({{showgrid:true, gridcolor:"#efe8dc", title:{{text:"Cue effect (items)",font:{{size:12,color:"#8a7d6d"}}}}, zeroline:true, zerolinecolor:"#cfc4b4"}})}}), {{displayModeBar:false, responsive:true}});
}}
function renderCurve() {{
  const el = document.getElementById("chart-curve"); const F = window.CURVEFIG; if (!el || !F) return;
  const mk = (name, y, color) => ({{type:"scatter", mode:"lines", name:name, x:F.blocks, y:y, line:{{color:color, width:2}}, hovertemplate:"Block %{{x}}: %{{y:+.2f}}<extra>"+name+"</extra>"}});
  Plotly.react(el, [mk("Cue word", F.cue, "#b8ab98"), mk("Token before cue", F.prev, "#235fa6")],
    Object.assign(base(300), {{margin:{{l:50,r:10,t:14,b:44}}, hovermode:"x unified", xaxis:ax({{title:{{text:"Block",font:{{size:12,color:"#8a7d6d"}}}}, dtick:6}}),
    yaxis:ax({{showgrid:true, gridcolor:"#efe8dc", title:{{text:"Cue effect (items)",font:{{size:12,color:"#8a7d6d"}}}}, zeroline:true, zerolinecolor:"#cfc4b4"}}),
    shapes:[{{type:"line", x0:54, x1:54, yref:"paper", y0:0, y1:1, line:{{color:"#8a7d6d", width:1, dash:"dot"}}}}]}}), {{displayModeBar:false, responsive:true}});
}}
let t; window.addEventListener("resize", () => {{ clearTimeout(t); t = setTimeout(() => {{ renderOff(); renderCurve(); }}, 150); }}); renderOff(); renderCurve();
</script>
</body>
</html>
'''
    open(os.path.join(HERE, 'v4.html'), 'w').write(page)
    print('wrote v4.html', len(page))
