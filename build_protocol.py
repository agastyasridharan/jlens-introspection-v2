"""Render ../protocol-v2.md as protocol.html in the site style."""
import os, re
from markdown_it import MarkdownIt
HERE = os.path.dirname(os.path.abspath(__file__))
md = open(os.path.join(HERE, '..', 'protocol-v2.md')).read()
body = MarkdownIt('commonmark').enable('table').render(md)
body = re.sub(r'<h1>.*?</h1>', '', body, count=1)
body = body.replace('<table>', '<div class="table-wrap"><table class="text">').replace('</table>', '</table></div>')
body = body.replace('<blockquote>', '<div class="answer"><span class="answer-tag">Prompt</span>').replace('</blockquote>', '</div>')
css = open(os.path.join(HERE, 'style.css')).read()
page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Introspection v2: Protocol</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>{css}</style></head><body><div class="page" style="padding-left:0"><main>
<header>
  <nav class="tabs" aria-label="Pages"><a href="./">Results</a><a href="protocol.html" aria-current="page">Protocol v2</a></nav>
  <p class="crumbs"><b>J-lens introspection</b> · Protocol v2</p>
  <h1>Introspection v2: Procedures</h1>
  <p class="byline">Qwen3.6-27B · J++ lens · October 2026 <span class="tag">Frozen design</span></p>
</header>
{body}
</main></div></body></html>'''
open(os.path.join(HERE, 'protocol.html'), 'w').write(page)
print('ok', len(page))
