"""Build v3.html (protocol v3 results tab) from ../v3/results/*.json."""
import json, html, os
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'v3', 'results')
E = html.escape
CSS = open(os.path.join(HERE, 'style.css')).read()
load = lambda n: json.load(open(os.path.join(RES, n))) if os.path.exists(os.path.join(RES, n)) else None
S, LOG, P, J, DV = load('state.json'), load('log.json'), load('prelim.json'), load('judge_validation.json'), load('dev.json')
MN, RV = load('main.json'), load('report_validation.json')
DOSE_NOTE = (load('dose_checks.json') or {}).get('note_html')
DOSECAP = (load('dose_checks.json') or {}).get('caption', '')
DOSE = {a: x for a, x in ((1, load('main_a1.json')), (2, load('main_a2.json')), (4, MN)) if x}
MD = json.load(open(os.path.join(HERE, '..', 'v3', 'stimuli', 'main_design.json'))) if MN else None
SETN = {'rb': 'block 53', 'band': 'blocks 48–53', 'site': 'assistant-start token', 'last5': 'last 5 prompt tokens'}
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
          'border-bottom:2px solid var(--accent)}.subtabs a:hover{color:var(--accent)}'
          '.muted{color:var(--ink-3);font-size:.9em}pre.q{white-space:pre-wrap;font-family:var(--sans);font-size:14px;background:var(--panel);'
          'border:1px solid var(--rule);border-radius:4px;padding:10px 12px;margin:4px 0 14px;overflow-x:auto}')


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
    if DV:
        h2('dev', 'Development: edit setting and manipulation check (step 6)')
        ch = DV['chosen']; ci = DV['criterion']
        out.append(f'<p>{DV["n"]} new development situations (30 instruments, 15 countries; disjoint from the preliminary and future main situations), with the frozen block 53 and K = 10. '
                   'For each situation and grid setting we edit the prompt forward pass (swap, or a norm-matched random control), then (a) regenerate the answer to check it is unchanged, and '
                   '(b) feed the original answer back in word for word and read, at the token where the answer item&#8217;s name begins, <b>Δ = log p(C) − log p(B)</b> '
                   '(each item&#8217;s best judge-labeled single-token form). <b>Edit-shift</b> = Δ under swap − Δ under control. No reports were collected.</p>')
        out.append('<div class="answer"><span class="answer-tag">Step 6 result</span><ul>'
                   f'<li><b>Chosen setting: {SETN[ch[0]]}, {SETN[ch[1]]}, α = {ch[2]}</b> (largest median edit-shift among settings with at least 80% of instrument answers unchanged).</li>'
                   f'<li><b>Criterion met for both categories:</b> edit-shift positive in {100*ci["instrument"]["pos"]:.0f}% of instrument situations (mean {ci["instrument"]["mean"]:+.2f} nats [{ci["instrument"]["lo"]:+.2f}, {ci["instrument"]["hi"]:+.2f}]) '
                   f'and {100*ci["country"]["pos"]:.0f}% of country situations ({ci["country"]["mean"]:+.2f} [{ci["country"]["lo"]:+.2f}, {ci["country"]["hi"]:+.2f}]); the protocol requires at least 75% and a lower bound above 0.</li>'
                   '<li><b>The instrument effect is small.</b> B leads C by a median of 7.7 nats at the name position; the swap moves this by a median of 0.31 nats, and C never overtakes B (0/30). '
                   'For countries the gap is a median 0.84 nats and C overtakes B in 20% of situations.</li>'
                   '<li><b>Where the effect comes from:</b> editing block 53 alone barely moves the output (median shift 0.005–0.02 nats at the assistant-start token). Editing earlier blocks of the band and five prompt tokens rather than one gives most of the effect.</li></ul></div>')
        keys = [tuple(k) for k in DV['settings']]
        lab = lambda k: f'{"53" if k[0]=="rb" else "48–53"} · {"start" if k[1]=="site" else "last 5"} · α{k[2]}'
        fig = dict(groups=[lab(k) for k in keys], series=[dict(name=CAT[c], color=COL[c], y=[DV['summary'][f'{c}|{k[0]}|{k[1]}|{k[2]}']['mean'] for k in keys],
                   lo=[DV['summary'][f'{c}|{k[0]}|{k[1]}|{k[2]}']['lo'] for k in keys], hi=[DV['summary'][f'{c}|{k[0]}|{k[1]}|{k[2]}']['hi'] for k in keys]) for c in ('instrument', 'country')])
        out.append('<figure class="wide" id="fig-dev"><div class="fig-panel"><div class="fig-top"><div class="fig-title">Edit-shift by grid setting (mean, nats)</div>'
                   '<div class="legend" aria-hidden="true">' + ''.join(f'<span><i style="border-color:{COL[c]};border-top-width:6px"></i>{CAT[c]}</span>' for c in ('instrument', 'country')) +
                   '</div></div><div id="chart-dev" class="chart" role="img" aria-label="Edit-shift by setting"></div>'
                   '<div class="fig-note">Blocks · positions · α. Bootstrap 95% intervals over situations (5,000 resamples). Δ in nats.</div></div>'
                   f'<figcaption><b>Figure 2.</b> Shifts grow with α, with five edited prompt tokens rather than one, and with the band rather than block 53 alone.</figcaption></figure>')
        out.append('<script>window.DEVFIG = ' + json.dumps(fig) + ';</script>')
        for c in ('instrument', 'country'):
            rows = []
            for k in keys:
                v = DV['summary'][f'{c}|{k[0]}|{k[1]}|{k[2]}']
                mark = ' <b>(chosen)</b>' if list(k) == ch else ''
                rows.append([SETN[k[0]], SETN[k[1]], str(k[2]) + mark, f'{100*v["valid_swap"]:.0f}% / {100*v["valid_control"]:.0f}%', f'{v["median"]:+.3f}',
                             f'{v["mean"]:+.3f} [{v["lo"]:+.3f}, {v["hi"]:+.3f}]', f'{100*v["pos"]:.0f}%', f'{100*v["flip"]:.0f}%', f'{100*v["rel"]:.1f}%'])
            out.append(table(['Blocks', 'Positions', 'α', 'Answer unchanged (swap / control)', 'Median edit-shift', 'Mean [95% CI]', 'Shift > 0', 'C overtakes B', 'Edit / ‖h‖'], rows,
                             cap=f'<b>{CAT[c]}</b> ({sum(1 for x in DV["situations"].values() if x["category"]==c)} situations).'))
        out.append('<div class="answer warn"><span class="answer-tag">Amendments and implementation notes (Oct 25)</span><ul>'
                   '<li><b>Band edits use unedited coordinates.</b> Re-applying the swap at each block of a band re-swaps coordinates already changed one block earlier (they cancel at α = 1 and blow up at α ≥ 2). '
                   'Each band block is therefore set to the swapped values from the unedited pass at that block. For a single block this is the ordinary J++ swap.</li>'
                   f'<li><b>B and C are ordered by coordinate.</b> The two top competitors by corrected score are kept, but B is now the one with the larger unedited coordinate at block 53 and the assistant-start token, so the swap lowers B and raises C. '
                   f'This relabels {DV["reoriented"]["instrument"]}/30 instrument and {DV["reoriented"]["country"]}/15 country pairs. The swap itself is symmetric, so no run depends on the labels.</li>'
                   '<li><b>Answer validity</b> is token-for-token identity; most changed answers keep the same item with different wording.</li></ul></div>')
        rows = []
        for i, v in DV['situations'].items():
            p = DV['per'][f'{i}|{ch[0]}|{ch[1]}|{ch[2]}']
            rows.append([i.split('-', 1)[1], E(v['X']), E(v['B']), E(v['C']), f'{-v["none_delta"]:+.2f}', f'{p["shift"]:+.2f}', '✓' if p['valid_swap'] else E((p['swap_answer'] or '')[:60])])
        out.append('<details class="app"><summary>Per-situation results at the chosen setting</summary><div>' +
                   table(['Situation', 'Answer item X', 'B', 'C', 'log p(B) − log p(C), no edit', 'Edit-shift', 'Answer under swap'], rows, 'text') + '</div></details>')

    if MN:
        from collections import Counter
        G = MN['groups']; R = MN['rows']; Dm = {t['id']: t for t in MD['trials']}
        pct = lambda a, b: f'{a}/{b} ({100*a/b:.0f}%)' if b else '—'
        ci = lambda v: f'{100*v["diff"]:+.1f} pp [{100*v["lo"]:+.1f}, {100*v["hi"]:+.1f}]'
        h2('main', 'Main situations (step 7)')
        out.append('<p>320 new requests (160 per kept category), written and screened like the earlier sets, disjoint from them, and frozen before generation. '
                   'Every answer ended naturally; the prompt-only replay matched the full-sequence readout to within 9.2e-5. Eligibility used the frozen block 53 and K = 10, '
                   'and B/C were ordered by unedited coordinate (B larger, so the swap lowers B and raises C). All eligible situations entered the swap stage.</p>')
        rows = []
        for c in ('instrument', 'country'):
            ts = [t for t in MD['trials'] if t['category'] == c]
            sk = Counter(v for k, v in MD['skipped'].items() if k.startswith(f'm-{c}-'))
            rows.append([CAT[c], f'{len(ts)}/160', ', '.join(f'{E(k)} ({v})' for k, v in sk.items()) or '—',
                         ', '.join(f'{E(x)} ({k})' for x, k in Counter(t['X'] for t in ts).most_common(4)),
                         ', '.join(f'{E(a)}/{E(b)} ({k})' for (a, b), k in Counter(tuple(sorted((t['B'], t['C']))) for t in ts).most_common(4)),
                         str(sum(t['reoriented'] for t in ts)), str(sum(t['filled'] for t in ts))])
        out.append(table(['Category', 'Eligible', 'Not eligible', 'Most common answers X', 'Most common B/C pairs', 'Pairs relabeled by coordinate', 'Menu options filled at random'], rows, 'text'))
        h2('swap', 'Swap stage: reports (steps 8–10)')
        a = G['all']
        out.append('<p>For each eligible situation we build four prompt states at the frozen setting (blocks 48–53, last five prompt tokens, α = 4): <b>no edit</b>, <b>swap</b> (B↔C), '
                   '<b>control</b> (norm-matched random direction orthogonal to B and C) and <b>injection</b> (raise C only). The model regenerates its answer from each state; '
                   'only states whose answer is token-for-token identical are kept. From each kept state, in separate branches with the answer in context, we ask the competitor question '
                   '(free naming, recognition in two menu orders), the second-choice question and, for no edit, the remaining question variants. Two further conditions use swap and control only: '
                   'the <b>late edit</b> (no prompt edit; the same edit at every token of the appended competitor question) and <b>edited third-person prediction</b> '
                   '(another-instance prediction with the edit at the last five tokens of the quoted request). “Follow” means the report names C.</p>')
        out.append('<div class="answer"><span class="answer-tag">Steps 8–10 result</span><ul>'
                   f'<li><b>Primary outcome, report-follow: {ci(a["report_follow"])}.</b> The self-report named C in {a["report_follow"]["swap"]} of {a["report_follow"]["n"]} situations under the swap and {a["report_follow"]["control"]} under the control (exact McNemar p = {a["report_follow"]["p"]:.2g}). '
                   f'Instruments {G["instrument"]["report_follow"]["swap"]} vs {G["instrument"]["report_follow"]["control"]} of {G["instrument"]["report_follow"]["n"]}; countries {G["country"]["report_follow"]["swap"]} vs {G["country"]["report_follow"]["control"]} of {G["country"]["report_follow"]["n"]}.</li>'
                   '<li><b>Reports are essentially unchanged by the prompt edit.</b> 225/233 swap and 219/222 control free-naming reports are identical, character for character, to the no-edit report; the first recognition order is identical in 232/233 and 222/222. '
                   'Recognition, second choice, injection and edited third-person prediction show no difference between swap and control.</li>'
                   f'<li><b>The late edit moves reports strongly: {ci(a["late_follow"])}</b> ({a["late_follow"]["swap"]} vs {a["late_follow"]["control"]} of {a["late_follow"]["n"]}). '
                   f'The timing contrast (early − late) is {100*a["timing_contrast"]["diff"]:+.0f} pp [{100*a["timing_contrast"]["lo"]:+.0f}, {100*a["timing_contrast"]["hi"]:+.0f}]. The lens directions for B and C do steer the report when they are present at the question.</li>'
                   '<li><b>Reading (pre-registered table):</b> edit-shift holds, report does not follow → the report does not read this answer-time state. '
                   'Because even the random control barely reaches the report, this is a statement about edits small enough to keep the answer unchanged; it does not exclude effects of larger edits.</li></ul></div>')
        meas = [('Self-report (free naming)', 'report_follow'), ('Second choice', 'second_choice'), ('Injection vs control', 'injection'),
                ('Edited third-person', 'third_follow'), ('Late edit', 'late_follow')]
        fig = dict(groups=[m for m, _ in meas], swap=[100 * a[k]['swap'] / a[k]['n'] for _, k in meas], control=[100 * a[k]['control'] / a[k]['n'] for _, k in meas],
                   n=[a[k]['n'] for _, k in meas])
        out.append('<figure class="wide" id="fig-main"><div class="fig-panel"><div class="fig-top"><div class="fig-title">Share of reports naming C (both categories)</div>'
                   '<div class="legend" aria-hidden="true"><span><i style="border-color:#235fa6;border-top-width:6px"></i>Swap (or injection)</span><span><i style="border-color:#b8ab98;border-top-width:6px"></i>Control</span></div></div>'
                   '<div id="chart-main" class="chart" role="img" aria-label="Share naming C by condition"></div>'
                   '<div class="fig-note">Paired situations valid under both conditions (n = 184; injection n = 195). The late edit needs no validity check; it uses the same 184 situations.</div></div>'
                   '<figcaption><b>Figure 3.</b> Only the late edit, placed on the question tokens, makes the report name C. Edits to the state before the answer leave every report measure flat.</figcaption></figure>')
        out.append('<script>window.MAINFIG = ' + json.dumps(fig) + ';</script>')
        rows = []
        for lab, k in [('Report-follow (primary)', 'report_follow'), ('B-retention (names B)', 'B_retention'), ('Second-choice follow', 'second_choice'), ('Injection follow', 'injection'),
                       ('Late-edit follow', 'late_follow'), ('Edited third-person follow', 'third_follow')]:
            rows.append([lab] + [f'{G[c][k]["swap"]} vs {G[c][k]["control"]} / {G[c][k]["n"]}<br><span class="muted">{ci(G[c][k])}, p = {G[c][k]["p"]:.2g}</span>' for c in ('instrument', 'country', 'all')])
        for lab, k in [('Second-choice contrast (report − second choice)', 'second_choice_contrast'), ('Timing contrast (early − late)', 'timing_contrast'), ('Self vs other (report − third-person)', 'self_vs_other')]:
            rows.append([lab] + [f'{100*G[c][k]["diff"]:+.1f} pp [{100*G[c][k]["lo"]:+.1f}, {100*G[c][k]["hi"]:+.1f}]' for c in ('instrument', 'country', 'all')])
        for lab, key in [('Recognition: chose C', 'C'), ('Recognition: chose B', 'B')]:
            rows.append([lab] + [f'{G[c]["recognition"]["swap"][key]} vs {G[c]["recognition"]["control"][key]} / {G[c]["recognition"]["swap"]["n"]} answers' for c in ('instrument', 'country', 'all')])
        rows.append(['Follow among flipped situations (C overtakes B)'] + [f'{G[c]["report_follow_flipped"]["swap_C"]}/{G[c]["report_follow_flipped"]["n"]}' for c in ('instrument', 'country', 'all')])
        rows.append(['Report-follow, stable top competitor (block 52 = 53)'] + [f'{G[c]["by_stability"]["True"]["swap"]} vs {G[c]["by_stability"]["True"]["control"]} / {G[c]["by_stability"]["True"]["n"]}' for c in ('instrument', 'country', 'all')])
        out.append(table(['Measure (swap vs control)', 'Instruments', 'Countries', 'Both'], rows, 'text', cap='<b>Primary and secondary outcomes.</b> Counts are situations (recognition: answers over two menu orders). Intervals: paired bootstrap over situations (10,000). p: exact McNemar.'))
        rows = []
        for c in ('instrument', 'country', 'all'):
            e = G[c]['edit_shift']; v = G[c]['validity']
            rows.append([CAT.get(c, 'Both'), f'{e["mean"]:+.2f} [{e["lo"]:+.2f}, {e["hi"]:+.2f}]', f'{e["median"]:+.2f}', f'{100*e["pos"]:.0f}%', f'{100*e["flip"]:.0f}%', f'{e["inject_shift"]:+.2f}'] +
                        [pct(v[m]['valid'], v[m]['n']) for m in ('swap', 'control', 'inject')])
        out.append(table(['Category', 'Edit-shift mean [95% CI]', 'Median', 'Shift > 0', 'C overtakes B', 'Injection shift (median)', 'Answer unchanged: swap', 'control', 'injection'], rows,
                         cap='<b>Manipulation check and validity on the main set.</b> Edit-shift as in step 6 (nats, at the token where the answer&#8217;s item name begins).',
                         note='The country share with a positive shift (73%) is just below the 75% development threshold; its lower bound stays above 0.'))
        rows = []
        for m in ('none', 'swap', 'control', 'inject'):
            mx = a['report_mix'][m]
            rows.append([m, str(mx['n']), str(mx['Item']), str(mx['B']), str(mx['C']), str(mx['Named']), str(mx['Abstention']), str(mx['NotItem'] + mx['Truncated'])])
        out.append(table(['State', 'Valid', 'Names an item', 'Names B', 'Names C', 'Names X / a named item', 'Abstains', 'Other'], rows,
                         cap='<b>What the competitor question returns</b> (free naming, condition 1, both categories). Most reports name a common item that is neither B nor C (instruments: guitar, piano; countries: France, China).'))
        h2('corr', 'Without an edit: self-report vs another-instance prediction')
        rows = []
        for c in ('instrument', 'country', 'all'):
            k = G[c]['correlational']; n0 = k['agree_top_free1']['n']
            rows.append([CAT.get(c, 'Both'), f'{k["agree_top_free1"]["self"]} vs {k["agree_top_free1"]["context"]} / {n0}', f'{k["agree_top_free3"]["self"]} vs {k["agree_top_free3"]["context"]}',
                         f'{k["agree_top_free2"]["self"]} vs {k["agree_top_free2"]["context"]}', f'{k["recog_req"]["self"]} vs {k["recog_req"]["context"]} / {k["recog_req"]["n"]}',
                         f'{k["recog_req"]["self_rank"]:.2f} vs {k["recog_req"]["context_rank"]:.2f}',
                         f'{k["beta_L"]["self"]["beta"]:+.2f}±{k["beta_L"]["self"]["se"]:.2f} vs {k["beta_L"]["context"]["beta"]:+.2f}±{k["beta_L"]["context"]["se"]:.2f}', pct(k['anchor_X']['X'], n0)])
        out.append(table(['Category', 'Free naming = top competitor (cond. 1)', 'Cond. 3 (must name)', 'Cond. 2 (may abstain)', 'Recognition = top competitor', 'Mean menu rank of choice', 'β_L (self vs context)', 'Anchor question returns X'], rows,
                         cap='<b>Correlational outcomes</b> (no-edit state; self vs context prediction). “Top competitor” is the highest corrected score among competitors.',
                         note='When abstention is allowed (condition 2), the model abstains about itself in 295/307 situations and about another instance in 159/307. Self-report has no advantage on any agreement measure.'))
        if RV:
            out.append(f'<p class="table-note">Judge report labels for instruments (new category): all {RV["n"]} distinct main-stage report strings hand-checked, {RV["correct"]}/{RV["n"]} correct (the error: “bell” labeled not-an-item); rerun identity {RV["rerun_identical"]}/{RV["n"]}. '
                       'Country report labels were validated in v2. Reports such as “acoustic guitar” are kept distinct from “guitar”; matching on the head noun would change 5 reports and no swap-vs-control count.</p>')
        t0 = MD['trials'][0]
        out.append('<details class="app"><summary>Exact questions (one instrument situation)</summary><div>' + ''.join(
            f'<p><b>{E(k)}</b></p><pre class="q">{E(v)}</pre>' for k, v in [('Competitor question, free naming 1', t0['self_q']['free1']), ('Recognition, answer required', t0['self_q']['rec_req_0']),
                                                                                ('Second choice', t0['self_q']['second']), ('Anchor', t0['self_q']['anchor']), ('Context prediction (recognition, abstention allowed)', t0['context_q']['ctx_rec_abs_0'])]) + '</div></details>')
        rows = []
        for t, r in R.items():
            sh = lambda m: E(r[m].get('free1') or '—') if r[m]['valid'] else '<span class="muted">answer changed</span>'
            rows.append([t.split('-', 1)[1], E(r['X']), E(r['B']), E(r['C']), sh('none'), sh('swap'), sh('control'), E(r['late_swap'] or '—'), E(r['late_control'] or '—'), E(r['context'].get('free1') or '—')])
        rows.sort(key=lambda x: x[0])
        out.append('<details class="app"><summary>Per-situation reports (free naming 1)</summary><div>' +
                   table(['Situation', 'X', 'B', 'C', 'No edit', 'Swap', 'Control', 'Late swap', 'Late control', 'Other instance'], rows, 'text') + '</div></details>')

    if MN and len(DOSE) > 1:
        h2('dose', 'Dose: α = 1, 2, 4 on the main set')
        out.append('<p>Pre-specified secondary analysis, run after the primary analysis was locked: the whole swap stage repeated on the same 307 main situations at α = 1 and α = 2, '
                   'with the same blocks (48–53), positions (last five prompt tokens), questions and measures. α = 4 is the frozen main run. '
                   'The no-edit state, context prediction and the menus do not depend on α; the no-edit reports reproduced exactly in every rerun (see note).</p>')
        rows = []
        for al in sorted(DOSE):
            g = DOSE[al]['groups']['all']; e = g['edit_shift']; v = g['validity']
            cell = lambda k: f'{g[k]["swap"]} vs {g[k]["control"]} / {g[k]["n"]}<br><span class="muted">{100*g[k]["diff"]:+.1f} pp, p = {g[k]["p"]:.2g}</span>'
            rows.append([f'α = {al}' + (' (main)' if al == 4 else ''), f'{100*v["swap"]["valid"]/v["swap"]["n"]:.0f}% / {100*v["control"]["valid"]/v["control"]["n"]:.0f}%',
                         f'{e["mean"]:+.2f} [{e["lo"]:+.2f}, {e["hi"]:+.2f}]', f'{100*e["pos"]:.0f}%', f'{100*e["flip"]:.0f}%',
                         cell('report_follow'), cell('second_choice'), cell('third_follow'), cell('late_follow')])
        out.append(table(['Strength', 'Answer unchanged (swap / control)', 'Edit-shift (nats)', 'Shift > 0', 'C overtakes B', 'Report names C', 'Second choice names C', 'Edited third-person names C', 'Late edit names C'], rows, 'text',
                         cap='<b>Both categories.</b> Counts: swap vs control over situations valid under both at that α (the late edit uses the same situations).'))
        for c in ('instrument', 'country'):
            rows = []
            for al in sorted(DOSE):
                g = DOSE[al]['groups'][c]; e = g['edit_shift']
                rows.append([f'α = {al}', f'{e["mean"]:+.2f} [{e["lo"]:+.2f}, {e["hi"]:+.2f}]', f'{100*e["flip"]:.0f}%'] +
                            [f'{g[k]["swap"]} vs {g[k]["control"]} / {g[k]["n"]}' for k in ('report_follow', 'B_retention', 'injection', 'late_follow')] +
                            [f'{g["recognition"]["swap"]["C"]} vs {g["recognition"]["control"]["C"]} / {g["recognition"]["swap"]["n"]}'])
            out.append(table(['Strength', 'Edit-shift', 'C overtakes B', 'Report names C', 'Report names B', 'Injection names C', 'Late edit names C', 'Recognition picks C'], rows, 'text', cap=f'<b>{CAT[c]}</b>'))
        fig = dict(alphas=sorted(DOSE), early=[100 * DOSE[al]['groups']['all']['report_follow']['diff'] for al in sorted(DOSE)],
                   late=[100 * DOSE[al]['groups']['all']['late_follow']['diff'] for al in sorted(DOSE)],
                   shift=[DOSE[al]['groups']['all']['edit_shift']['mean'] for al in sorted(DOSE)])
        out.append('<figure class="wide" id="fig-dose"><div class="fig-panel"><div class="fig-top"><div class="fig-title">Report-follow (swap − control) by edit strength</div>'
                   '<div class="legend" aria-hidden="true"><span><i style="border-color:#235fa6;border-top-width:3px"></i>Prompt edit (before the answer)</span><span><i style="border-color:#b0702a;border-top-width:3px"></i>Late edit (question tokens)</span></div></div>'
                   '<div id="chart-dose" class="chart" role="img" aria-label="Report-follow by alpha"></div><div class="fig-note">Both categories; percentage points.</div></div>'
                   f'<figcaption><b>Figure 4.</b> {DOSECAP}</figcaption></figure>')
        out.append('<script>window.DOSEFIG = ' + json.dumps(fig) + ';</script>')
        if DOSE_NOTE: out.append(DOSE_NOTE)
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
function renderDev() {{
  const el = document.getElementById("chart-dev"); const F = window.DEVFIG; if (!el || !F) return;
  const tr = F.series.map(s => ({{type:"bar", name:s.name, x:F.groups, y:s.y, marker:{{color:s.color}},
    error_y:{{type:"data", symmetric:false, array:s.hi.map((h,i)=>h-s.y[i]), arrayminus:s.lo.map((l,i)=>s.y[i]-l), color:"#8a7d6d", thickness:1.2, width:3}},
    hovertemplate:"%{{x}}: %{{y:.3f}}<extra>"+s.name+"</extra>"}}));
  Plotly.react(el, tr, {{font:{{family:FONT,size:12,color:"#5e5245"}}, paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", showlegend:false, dragmode:false, height:340,
    barmode:"group", bargap:0.25, margin:{{l:50,r:10,t:14,b:90}}, xaxis:ax({{type:"category", tickangle:-40}}),
    yaxis:ax({{showgrid:true, gridcolor:"#efe8dc", title:{{text:"Edit-shift (nats)",font:{{size:12,color:"#8a7d6d"}}}}, zeroline:true, zerolinecolor:"#cfc4b4"}})}}, {{displayModeBar:false, responsive:true}});
}}
function renderMain() {{
  const el = document.getElementById("chart-main"); const F = window.MAINFIG; if (!el || !F) return;
  const mk = (name, y, color) => ({{type:"bar", name:name, x:F.groups, y:y, marker:{{color:color}}, customdata:F.n, hovertemplate:"%{{x}}: %{{y:.1f}}% (n = %{{customdata}})<extra>"+name+"</extra>"}});
  Plotly.react(el, [mk("Swap", F.swap, "#235fa6"), mk("Control", F.control, "#b8ab98")], {{font:{{family:FONT,size:12,color:"#5e5245"}}, paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", showlegend:false, dragmode:false, height:320,
    barmode:"group", bargap:0.3, margin:{{l:50,r:10,t:14,b:60}}, xaxis:ax({{type:"category"}}),
    yaxis:ax({{showgrid:true, gridcolor:"#efe8dc", title:{{text:"Reports naming C (%)",font:{{size:12,color:"#8a7d6d"}}}}, rangemode:"tozero"}})}}, {{displayModeBar:false, responsive:true}});
}}
function renderDose() {{
  const el = document.getElementById("chart-dose"); const F = window.DOSEFIG; if (!el || !F) return;
  const mk = (name, y, color) => ({{type:"scatter", mode:"lines+markers", name:name, x:F.alphas, y:y, line:{{color:color, width:2}}, marker:{{size:8, color:color}}, hovertemplate:"α = %{{x}}: %{{y:+.1f}} pp<extra>"+name+"</extra>"}});
  Plotly.react(el, [mk("Prompt edit", F.early, "#235fa6"), mk("Late edit", F.late, "#b0702a")], {{font:{{family:FONT,size:12,color:"#5e5245"}}, paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", showlegend:false, dragmode:false, height:300,
    margin:{{l:50,r:10,t:14,b:44}}, xaxis:ax({{type:"log", tickvals:F.alphas, ticktext:F.alphas.map(a=>"α = "+a)}}),
    yaxis:ax({{showgrid:true, gridcolor:"#efe8dc", title:{{text:"Report-follow (pp)",font:{{size:12,color:"#8a7d6d"}}}}, zeroline:true, zerolinecolor:"#cfc4b4"}})}}, {{displayModeBar:false, responsive:true}});
}}
let t; window.addEventListener("resize", () => {{ clearTimeout(t); t = setTimeout(() => {{ render(); renderDev(); renderMain(); renderDose(); }}, 150); }}); render(); renderDev(); renderMain(); renderDose();
</script>
</body>
</html>
'''
open(os.path.join(HERE, 'v3.html'), 'w').write(page)
print('wrote v3.html', len(page))
