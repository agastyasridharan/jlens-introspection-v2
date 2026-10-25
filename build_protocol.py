"""Render ../protocol-v2.md as protocol.html and ../protocol-v3.md as v3.html in the site style."""
import os, re
from markdown_it import MarkdownIt
HERE = os.path.dirname(os.path.abspath(__file__))
NAV = [('./', 'Results (v2)'), ('protocol.html', 'Protocol v2'), ('v3.html', 'v3: Natural swap')]


def nav(cur):
    return '<nav class="tabs" aria-label="Pages">' + ''.join(f'<a href="{h}"' + (' aria-current="page"' if h == cur else '') + f'>{t}</a>' for h, t in NAV) + '</nav>'


def render(src, out, title, crumb, h1, tag, intro=''):
    md = open(os.path.join(HERE, '..', src)).read()
    body = MarkdownIt('commonmark').enable('table').render(md)
    body = re.sub(r'<h1>.*?</h1>', '', body, count=1)
    body = body.replace('<table>', '<div class="table-wrap"><table class="text">').replace('</table>', '</table></div>')
    body = body.replace('<blockquote>', '<div class="answer"><span class="answer-tag">Prompt</span>').replace('</blockquote>', '</div>')
    css = open(os.path.join(HERE, 'style.css')).read()
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>{css}</style></head><body><div class="page" style="padding-left:0"><main>
<header>
  {nav(out)}
  <p class="crumbs"><b>J-lens introspection</b> · {crumb}</p>
  <h1>{h1}</h1>
  <p class="byline">Qwen3.6-27B · J++ lens · October 2026 <span class="tag">{tag}</span></p>
  {intro}
</header>
{body}
</main></div></body></html>'''
    open(os.path.join(HERE, out), 'w').write(page)
    print('ok', out, len(page))


render('protocol-v2.md', 'protocol.html', 'Introspection v2: Protocol', 'Protocol v2', 'Introspection v2: Procedures', 'Frozen design')
render('protocol-v3.md', 'v3.html', 'Introspection v3: Natural Swap', 'Protocol v3', 'Introspection v3: Natural-recommendation swap',
       'Draft design · not run',
       '<p class="thanks">A new experiment: no hold instruction. The model answers a natural recommendation request, then reports which <em>other</em> items were strongly represented. The primary test swaps two such competitors without changing the answer. '
       'Results will be reported on this tab once runs begin.</p>')
