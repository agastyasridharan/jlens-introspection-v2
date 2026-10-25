"""Build index.html from data/results.json (written by the analysis stages)."""
import json, html, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(HERE, 'style.css')).read()
R = json.load(open(os.path.join(HERE, 'data/results.json')))
CAT = {'grocery': 'Groceries', 'animal': 'Animals', 'country': 'Countries'}


def pill(s):
    return {'done': '<span class="pill done">done</span>', 'running': '<span class="pill partial">running</span>',
            'todo': '<span class="pill todo">not started</span>', 'skip': '<span class="pill todo">not run (by design)</span>'}[s]


def table(head, rows, cls='', cap=None, note=None):
    h = ''.join(f'<th>{x}</th>' for x in head)
    b = ''.join('<tr>' + ''.join(f'<td>{x}</td>' for x in r) + '</tr>' for r in rows)
    out = '<div class="table-wrap">' + (f'<p class="table-cap">{cap}</p>' if cap else '')
    out += f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'
    out += (f'<p class="table-note">{note}</p>' if note else '') + '</div>'
    return out


def figure(fid, title, legend, note, caption, data_table=None):
    leg = ''.join(f'<span><i style="border-color:{c};border-top-width:{w}px"></i>{n}</span>' for n, c, w in legend)
    tv = f'<details class="tv"><summary>Data table</summary>{data_table}</details>' if data_table else ''
    return (f'<figure class="wide" id="fig-{fid}"><div class="fig-panel"><div class="fig-top"><div class="fig-title">{title}</div>'
            f'<div class="legend" aria-hidden="true">{leg}</div></div><div id="chart-{fid}" class="chart" role="img" aria-label="{html.escape(title)}"></div>'
            f'<div class="fig-note">{note}</div></div><figcaption>{caption}</figcaption>{tv}</figure>')


def sections():
    S = []
    toc = []
    cnt = [0]
    def h2(id_, num, text):
        if num != '':
            cnt[0] += 1; num = str(cnt[0])
        toc.append((id_, text)); S.append(f'<h2 id="{id_}"><span class="num">{num}</span>{text}</h2>')

    h2('status', '1', 'Status')
    S.append(table(['Step', 'What', 'Status'], [[s['step'], s['what'], pill(s['status'])] for s in R['status']], 'text'))

    hp = R.get('hold')
    if hp:
        h2('hold', '2', 'Hold phase: copy validity')
        S.append(f'<p>{hp["text"]}</p>')
        S.append(table(['Trials', 'Run', 'Valid copies', 'Terminated'], hp['rows'], cap='<b>Copy validity.</b> Valid = reply, whitespace stripped, equals the carrier, then end of turn.'))
        if hp.get('examples'):
            S.append(table(['Trial', 'Setting', 'Free naming (condition 2)'], hp['examples'], 'text',
                           cap='<b>Examples.</b> First two preliminary trials per category; raw model answers.'))

    if R.get('judge_html'):
        h2('judge', '0', 'LLM judge: validation (step 0)')
        S.append(R['judge_html'])

    pr = R.get('prelim')
    if pr:
        h2('readout', '3', 'Readout block (preliminary trials)')
        S.append(f'<p>{pr["block_text"]}</p>')
        rows = [[str(L)] + [f'{v[c]:.2f}' for c in ('grocery', 'animal', 'country')] + [f'{v["mean"]:.2f}'] for L, v in pr['curve'].items()]
        S.append(figure('curve', 'Distinct category items in the lens top 100, per copied position',
                        [('Groceries', '#b0702a', 2.5), ('Animals', '#2f8a57', 2.5), ('Countries', '#235fa6', 2.5), ('Mean', '#2a2318', 2.5)],
                        'Judge-labeled Items (step 0a). Averaged over copied positions, then the 8 preliminary trials per category, then categories. Blocks 0–54.',
                        pr['curve_caption'], table(['Block', 'Groceries', 'Animals', 'Countries', 'Mean'], rows)))
        h2('eligibility', '4', 'Eligibility cutoff K')
        S.append(f'<p>{pr["k_text"]}</p>')
        S.append(table(['K'] + [CAT[c] for c in ('grocery', 'animal', 'country')] + ['Meets 6/8 in every category'], pr['k_rows'],
                       cap='<b>Eligible preliminary trials by K</b> (of 8 per category), at the readout block.'))
        S.append(table(['Trial', 'Setting', 'Lens reference item', 'Best rank', 'Margin', 'Lens top items (corrected score)', 'Free naming (cond. 2)'],
                       pr['trial_rows'], 'text', cap='<b>Preliminary trials at the readout block.</b> Best rank = best rank of a reference-item token over copied positions (1 = top).'))
        if pr.get('stop_text'):
            S.append(f'<div class="answer warn"><span class="answer-tag">Stopping rule</span><p>{pr["stop_text"]}</p></div>')

    mn = R.get('main')
    if mn:
        h2('main', '5', 'Main experiment: does the report match the lens?')
        S.append(mn['intro'])
        S.append(figure('agree', 'Free naming: report matches the lens reference item',
                        [('Cond. 1: abstention allowed', '#cfc4b4', 6), ('Cond. 2: not mentioned (primary)', '#235fa6', 6), ('Cond. 3: answer required', '#b0702a', 6)],
                        mn['agree_note'], mn['agree_caption'], mn.get('agree_table')))
        S.append(mn['beta_html'])
        S.append(figure('recog', 'Recognition: share choosing the lens reference item (chance 25%)',
                        [('Answer required', '#235fa6', 6), ('Abstention allowed', '#b0702a', 6)],
                        mn['recog_note'], mn['recog_caption'], mn.get('recog_table')))
        h2('secondary', '6', 'Secondary analyses')
        S.append(mn['secondary_html'])
        if mn.get('perblock'):
            S.append(figure('perblock', 'Free-naming agreement (condition 2) when the reference item is read at each block',
                            [('All valid trials', '#235fa6', 2.5), ('Eligible at that block', '#b0702a', 2.5)],
                            mn['perblock_note'], mn['perblock_caption'], mn.get('perblock_table')))
        if mn.get('examples_html'):
            S.append(mn['examples_html'])

    sw = R.get('swap')
    if sw:
        h2('stability', '7', 'Is the lens readout stable across copied positions?')
        S.append(sw['stab']['html'])
        S.append(figure('stab', 'Condition-2 agreement by readout stability', [('Agreement', '#235fa6', 6)], sw['stab']['note'], sw['stab']['caption']))
        S.append(sw['stab']['tables'])
        x = sw['swap']
        h2('swap', '8', 'Causal swap test (step 8)')
        S.append(x['intro']); S.append(x['answer'])
        S.append(figure('swap', 'Free-naming report after editing the hold phase',
                        [('Names A', '#235fa6', 6), ('Names B', '#b0702a', 6), ('Differs from no-edit report', '#2f8a57', 6)], x['chart_note'], x['chart_caption']))
        S.append(x['cond_table']); S.append(x['comp_table']); S.append(x['coord_table']); S.append(x['examples'])
        S.append('<h3>Disclosures</h3>' + x['disclosures'])

    h2('log', '9', 'Log')
    S.append('<ol class="log">' + ''.join(f'<li><time>{e["t"]}</time><div class="entry"><p>{e["text"]}</p></div></li>' for e in reversed(R['log'])) + '</ol>')
    h2('appendix', '', 'Appendix')
    for a in R['appendix']:
        S.append(f'<details class="app"><summary>{a["title"]}</summary><div>{a["html"]}</div></details>')
    return '\n'.join(S), toc


body, toc = sections()
toc_html = '<nav class="toc"><div class="toc-head">Contents</div><ul>' + ''.join(f'<li><a href="#{i}">{t}</a></li>' for i, t in toc) + '</ul></nav>'
summary = ''.join(f'<li>{b}</li>' for b in R['summary'])
page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Introspection v2: Results</title>
<meta name="description" content="Protocol v2 on Qwen3.6-27B: does the model's report of an item it held in mind while copying agree with the J++ lens readout?">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="page">
{toc_html}
<main>
<header>
  <nav class="tabs" aria-label="Pages"><a href="./" aria-current="page">Results</a><a href="protocol.html">Protocol v2</a></nav>
  <p class="crumbs"><b>J-lens introspection</b> · Protocol v2</p>
  <h1>Introspection v2: Results</h1>
  <p class="byline">Qwen3.6-27B · J++ lens · October 2026 <span class="tag">{R["tag"]}</span></p>
  <p class="thanks">{R["thanks"]}</p>
  <details class="toc-mobile"><summary>Contents</summary>{toc_html}</details>
</header>
<div class="answer">
  <span class="answer-tag">{R["summary_tag"]}</span>
  <ul>{summary}</ul>
</div>
{body}
<p class="footer">Data: <code>data/results.json</code>. Last updated {R["updated"]}. </p>
</main>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<script>
const R = {json.dumps(R.get("charts", {}))};
{open(os.path.join(HERE, "charts.js")).read()}
</script>
</body>
</html>
'''
open(os.path.join(HERE, 'index.html'), 'w').write(page)
print('wrote index.html', len(page))
