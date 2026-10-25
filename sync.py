"""Assemble data/results.json from the analysis stage outputs, then build index.html."""
import json, os, glob, datetime, subprocess, html
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, 'results')
E = html.escape
CATN = {'grocery': 'Groceries', 'animal': 'Animals', 'country': 'Countries'}


def now():
    return datetime.datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M ET')


def load(name):
    p = os.path.join(RES, name)
    return json.load(open(p)) if os.path.exists(p) else None


state = load('state.json') or {}
log = load('log.json') or []
R = dict(tag='Updating live', updated=now(), log=log,
         thanks='Qwen3.6-27B is asked to silently choose a grocery item, animal, or country for a setting and keep it in mind while copying a neutral sentence. '
                'We read the J++ lens at every copied token, then ask the model (in separate branches) which item it was keeping in mind. '
                'Design: <a href="protocol.html">protocol v2</a>. Step 8 (the causal swap) is deliberately not run here.',
         summary_tag=state.get('summary_tag', 'Summary so far'), summary=state.get('summary', []),
         status=state.get('status', []), appendix=state.get('appendix', []), charts={})

R['judge_html'] = state.get('judge_html')
hold = load('hold.json')
if hold:
    R['hold'] = hold
pre = load('prelim.json')
if pre:
    R['prelim'] = pre
    R['charts']['curve'] = pre['chart']
main = load('main.json')
if main:
    R['main'] = main
    R['charts'].update(main.get('charts', {}))

json.dump(R, open(os.path.join(HERE, 'data/results.json'), 'w'), indent=1, ensure_ascii=False)
subprocess.run(['python3', os.path.join(HERE, 'build.py')], check=True)
