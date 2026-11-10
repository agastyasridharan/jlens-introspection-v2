// v2 readout dashboard: one copy-and-hold trial at a time, loaded from data/s/{id}.json.
const $ = id => document.getElementById(id);
const CATS = [["grocery", "Groceries"], ["animal", "Animals"], ["country", "Countries"]];
const RB = 54;
const VER = "20261110a";  // bump on every data/code change so browsers skip stale cached copies
const state = { index: null, cat: "grocery", filter: "eligible", id: null, pos: null, block: RB, view: "text", badge: null, data: null };
const cache = {};
const COND = [["1_abstain_allowed", "1 · abstention allowed (or NONE)"], ["2_not_mentioned", "2 · name the item (primary)"], ["3_required", "3 · must name one"]];

const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const vis = s => s.replace(/ /g, "·").replace(/\n/g, "↵");
const chip = (cls, t) => `<span class="chip chip-${cls}">${esc(t)}</span>`;

const posIdx = p => state.data.positions.indexOf(p);
const blkIdx = () => state.data.blocks.indexOf(state.block);
const itemRankAt = (it, p, bi = blkIdx()) => { const j = posIdx(p); return j < 0 || !it ? undefined : state.data.ranks[j][bi][0][it]; };
const posName = p => p === state.data.site ? "the assistant-start token" : `copied token ${posIdx(p) + 1}`;
function rkBadge(r, what, where) {
  const D = state.data.rank_depth;
  return r ? `<sup class="rk${r <= 10 ? " top" : ""}" title="${esc(what)}: rank ${r} in the readout at ${esc(where)}, block ${state.block} (top ${D})">#${r}</sup>`
    : `<sup class="rk none" title="${esc(what)}: not in the top ${D} at ${esc(where)}, block ${state.block}">&gt;${D}</sup>`;
}
const itemBadge = it => rkBadge(itemRankAt(it, state.pos), it, posName(state.pos));

async function load(id) {
  if (!cache[id]) cache[id] = fetch(`data/s/${id}.json?v=${VER}`).then(r => r.json());
  return cache[id];
}
function parseHash() {
  const [id, tok, blk] = decodeURIComponent(location.hash.slice(1)).split("/");
  return { id: id || null, pos: tok && tok.startsWith("token-") ? +tok.slice(6) : null, block: blk && blk.startsWith("block-") ? +blk.slice(6) : null };
}
const hashFor = (id, pos, block) => `#${id}/token-${pos}/block-${block}`;
function setHash() {
  const h = hashFor(state.id, state.pos, state.block);
  if (location.hash !== h) history.replaceState(null, "", h);
  $("token-link").href = h;
}

function filtered() {
  const S = state.index.situations.filter(s => s.category === state.cat);
  const f = {
    eligible: s => s.eligible, match: s => s.eligible && s.match2, nomatch: s => s.eligible && !s.match2, swap: s => s.swap,
    swapB: s => s.swap && s.swap_tag === "B", v5: s => s.v5, skipped: s => !s.eligible, all: () => true,
  }[state.filter];
  return S.filter(f);
}
const optLabel = s => `${esc(s.id.replace(/^m-[a-z]+-/, "#"))} · ${esc(s.scenario)} · A = ${esc(s.ref || "—")}`;

function renderTabs() {
  $("tabs").innerHTML = CATS.map(([c, t]) => `<button class="tab${c === state.cat ? " active" : ""}" data-cat="${c}">${t}</button>`).join("");
  $("tabs").querySelectorAll(".tab").forEach(b => b.onclick = () => { state.cat = b.dataset.cat; state.id = null; renderTabs(); renderSelect(); });
}
function renderSelect() {
  const list = filtered();
  $("sit-select").innerHTML = list.map(s => `<option value="${s.id}">${optLabel(s)}</option>`).join("") || `<option value="">(none match)</option>`;
  if (!list.length) { showEmpty(); return; }
  if (!list.some(s => s.id === state.id)) state.id = list[0].id;
  $("sit-select").value = state.id;
  openSituation(state.id);
}
function showEmpty() {
  $("sit-title").textContent = "No trials match this filter";
  ["sit-description", "tokens", "plain-prompt", "predictions", "design", "reports", "swap", "v5", "rank-table", "token-meta"].forEach(k => $(k).innerHTML = "");
}

async function openSituation(id, pos = null, block = null) {
  state.id = id;
  const d = await load(id);
  if (state.id !== id) return;
  state.data = d;
  state.pos = pos != null && d.positions.includes(pos) ? pos : d.positions[0];
  if (block != null && d.blocks.includes(block)) state.block = block;
  $("sit-kicker").textContent = `${d.category} · ${id}`;
  $("sit-title").textContent = d.scenario[0].toUpperCase() + d.scenario.slice(1);
  $("prompt-label").textContent = id;
  // badge item choices: A, B, the cond-2 report item, then the rest of the reference ranking
  const g = d.design, r2 = d.reports["2_not_mentioned"];
  const opts = [[g.A, `A = ${g.A} (reference)`]];
  if (g.B) opts.push([g.B, `B = ${g.B} (swap partner)`]);
  if (r2.item && r2.item !== g.A && r2.item !== g.B) opts.push([r2.item, `${r2.item} (cond. 2 report)`]);
  g.ranked.forEach((it, i) => { if (!opts.some(o => o[0] === it)) opts.push([it, `${it} (reference rank ${i + 1})`]); });
  $("badge-item").innerHTML = opts.filter(o => o[0]).map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join("");
  state.badge = opts[0][0];
  renderAll();
}

function renderDesc() {
  const d = state.data, g = d.design, r2 = d.reports["2_not_mentioned"];
  const elig = !d.valid ? `<span class="bad">copy invalid</span>` : g.eligible ? `eligible (A reaches rank ${g.best_rank} ≤ ${d.K})` : `<span class="bad">not eligible (A best rank ${g.best_rank ?? ">100"})</span>`;
  $("sit-description").innerHTML = `Reference A = <b>${esc(g.A ?? "—")}</b>${g.A ? itemBadge(g.A) : ""}` +
    (g.B ? ` · B = <b>${esc(g.B)}</b>${itemBadge(g.B)}` : "") +
    ` · report (cond. 2) = <b>${esc(r2.item || r2.label)}</b>${r2.item ? itemBadge(r2.item) : ""} · ${elig}` +
    ` <span class="muted">· # = rank at ${posName(state.pos)}, block ${state.block}</span>`;
}
function renderAll() { renderDesc(); renderPrompt(); renderReadout(); renderDesign(); renderReports(); renderSwap(); renderV5(); }
function renderRanked() { renderDesc(); renderPrompt(); renderReports(); renderSwap(); renderV5(); }

function renderPrompt() {
  const d = state.data, live = new Set(d.positions), n0 = d.prompt_tokens.length;
  const P = d.prompt_tokens.map((t, i) => ({ text: t, pos: i })), A = d.answer_tokens.map((t, k) => ({ text: t, pos: n0 + k }));
  const bd = t => live.has(t.pos) ? rkBadge(itemRankAt(state.badge, t.pos), state.badge, posName(t.pos)) : "";
  const cls = t => `${live.has(t.pos) ? "" : " inert"}${t.pos === d.site ? " site" : ""}${t.pos === state.pos ? " active" : ""}`;
  const tok = t => `<button class="token${cls(t)}" data-pos="${t.pos}"${live.has(t.pos) ? "" : " tabindex=-1"}>${esc(vis(t.text))}${bd(t)}</button>`;
  const plain = t => `<span class="plain-token${live.has(t.pos) ? " live" : ""}${cls(t)}" data-pos="${t.pos}"${live.has(t.pos) ? ' tabindex="0" role="button"' : ""}>${live.has(t.pos) && !/\S/.test(t.text) ? `<span class="ws">${esc(vis(t.text))}</span>${esc(t.text)}` : esc(t.text)}${bd(t)}</span>`;
  const sep = cl => `<span class="${cl}">END OF REQUEST · COPIED SENTENCE (assistant turn)</span>`;
  $("tokens").innerHTML = P.map(tok).join("") + sep("boundary") + A.map(tok).join("");
  $("plain-prompt").innerHTML = P.map(plain).join("") + sep("plain-boundary") + A.map(plain).join("");
  document.querySelectorAll("#tokens .token:not(.inert), #plain-prompt .plain-token.live").forEach(el => {
    const go = () => { state.pos = +el.dataset.pos; renderRanked(); renderReadout(); };
    el.onclick = go; el.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } };
  });
  $("tokens").classList.toggle("hidden", state.view !== "tokens");
  $("plain-prompt").classList.toggle("hidden", state.view !== "text");
}

function classify(d, s) {
  const it = d.items[s];
  if (!it) return null;
  return it === d.design.A ? "A" : it === d.design.B ? "B" : "item";
}

function renderReadout() {
  const d = state.data, j = posIdx(state.pos), bi = blkIdx();
  const all = [...d.prompt_tokens, ...d.answer_tokens];
  const isSite = state.pos === d.site;
  $("token-title").textContent = vis(all[state.pos] ?? "");
  $("block-badge").textContent = state.block; $("block-val").textContent = state.block; $("block-range").value = state.block;
  $("lens-heading").textContent = isSite ? "J++ lens readout · assistant-start token" : "J++ lens readout · copied token";
  $("token-meta").textContent = (isSite ? `Prompt position ${state.pos} (assistant <|im_start|>)` : `Copied token ${j + 1} of ${d.n_copied} · position ${state.pos}`) +
    ` · block ${state.block}${state.block === RB ? " (v2 readout block)" : ""}`;
  const rows = d.lens[j][bi], top = Math.max(...rows.map(r => r[1]));
  $("predictions").innerHTML = rows.map(([s, lp], r) => {
    const k = classify(d, s), it = d.items[s];
    const w = Math.max(2, 100 * Math.exp(lp - top));
    const tag = k === "item" ? chip("item", it) : k ? chip(k, `${k}: ${it}`) : "";
    return `<li class="prediction${k ? " is-" + k : ""}"><div class="prediction-fill" style="width:${w.toFixed(1)}%"></div>` +
      `<div class="prediction-row"><span class="prediction-rank">${r + 1}</span><span class="prediction-text">${esc(vis(d.strings[s]))}${tag}</span>` +
      `<span class="prediction-probability">${lp.toFixed(2)}</span></div></li>`;
  }).join("");
  const g = d.design, r2 = d.reports["2_not_mentioned"];
  const lines = [["A", g.A], ["B", g.B], ["report", r2.item]].filter(([, it], i, a) => it && a.findIndex(x => x[1] === it) === i);
  const head1 = d.blocks.map(b => `<th>${b}</th>`).join("");
  const byBlock = lines.map(([lab, it]) => `<tr><th>${lab}</th>` + d.blocks.map((b, i) => `<td class="${b === state.block ? "cur" : ""}">${itemRankAt(it, state.pos, i) ?? "—"}</td>`).join("") + "</tr>").join("");
  const cp = d.positions.slice(0, d.n_copied);
  const head2 = cp.map((p, i) => `<th>${i + 1}</th>`).join("") + "<th>start</th>";
  const byPos = lines.map(([lab, it]) => `<tr><th>${lab}</th>` + [...cp, d.site].map(p => `<td class="${p === state.pos ? "cur" : ""}">${itemRankAt(it, p) ?? "—"}</td>`).join("") + "</tr>").join("");
  $("rank-table").innerHTML = `<p class="sub">By block · ${esc(posName(state.pos))}</p><div class="tbl-wrap"><table class="rank-grid"><thead><tr><th></th>${head1}</tr></thead><tbody>${byBlock}</tbody></table></div>` +
    `<p class="sub">By copied token · block ${state.block}</p><div class="tbl-wrap"><table class="rank-grid"><thead><tr><th></th>${head2}</tr></thead><tbody>${byPos}</tbody></table></div>` +
    `<p class="token-help">Rank of the item&#8217;s best token in the top ${d.rank_depth} (— if absent). Unedited readout. ${lines.map(([l, it]) => `${l} = ${esc(it)}`).join(" · ")}</p>`;
  setHash();
}

function rep(r) {
  if (!r) return `<span class="muted">—</span>`;
  const t = r.tag ? chip(r.tag, r.tag) : r.label && r.label !== "Item" ? chip("X", r.label) : "";
  return `<span class="rep">${esc(r.text)}</span>${t}${r.item ? itemBadge(r.item) : ""}`;
}
const pick = r => !r ? `<span class="muted">—</span>` : r.pick ? `${esc(r.text.trim())} = <b>${esc(r.pick)}</b>${r.pick === state.data.design.A ? chip("A", "A") : ""}` : `<span class="muted">${esc(r.text)} (invalid)</span>`;

function renderDesign() {
  const d = state.data, g = d.design;
  const ranked = g.ranked.map((it, i) => `${esc(it)} <span class="muted">${g.scores[i].toFixed(2)}</span>${it === g.A ? chip("A", "A") : it === g.B ? chip("B", "B") : ""}`).join(" · ");
  $("design").innerHTML = `<dl class="kv">
    <dt>Copied sentence</dt><dd>${esc(d.carrier)} ${d.valid ? "" : '<span class="bad">(copy invalid)</span>'}</dd>
    <dt>Reference ranking (corrected score, top 10)</dt><dd>${ranked || '<span class="muted">no item in the readout</span>'}</dd>
    <dt>Margin A − second</dt><dd>${g.margin == null ? "—" : g.margin.toFixed(3)}</dd>
    <dt>Best rank of A at any copied token</dt><dd>${g.best_rank ?? "not in top 100"} ${g.eligible ? `(eligible, ≤ ${d.K})` : `<span class="bad">(not eligible)</span>`}</dd>
    ${g.B ? `<dt>Swap partner B</dt><dd>${esc(g.B)} <span class="muted">cos(A, B) = ${d.swap.cos_AB.toFixed(2)}</span></dd>` : ""}</dl>`;
}

function renderReports() {
  const d = state.data;
  let h = `<div class="tbl-wrap"><table class="rep-table"><thead><tr><th>Free naming</th><th>Report</th></tr></thead><tbody>`;
  COND.forEach(([k, lab]) => { h += `<tr><td class="q">${lab}</td><td>${rep(d.reports[k])}</td></tr>`; });
  h += `</tbody></table></div><p class="token-help">Question (cond. 2): <i>${esc(d.reports["2_not_mentioned"].question)}</i></p>`;
  if (d.recog) {
    h += `<p class="sub">Recognition among the lens top 4</p><div class="tbl-wrap"><table class="rep-table"><thead><tr><th>Options</th><th>Mode</th><th>Reply</th></tr></thead><tbody>`;
    d.recog.forEach(r => { h += `<tr><td class="q">${r.options.map((o, i) => `${"ABCD"[i]} ${esc(o)}`).join(", ")}</td><td>${r.mode === "required" ? "answer required" : "U allowed"}</td><td>${pick(r)}</td></tr>`; });
    h += `</tbody></table></div>`;
  }
  $("reports").innerHTML = h;
}

function renderSwap() {
  const d = state.data;
  if (!d.swap) { $("swap").innerHTML = `<p class="muted">Not in the swap stage (120 eligible situations, 40 per category, drawn with a fixed seed).</p>`; return; }
  const R = d.swap.results, lab = x => x.mode === "none" ? "No edit" : `${x.mode} α = ${x.alpha}`;
  const row = (l, f) => `<tr><td class="q">${l}</td>${R.map(x => `<td>${f(x)}</td>`).join("")}</tr>`;
  let h = `<div class="tbl-wrap"><table class="rep-table"><thead><tr><th></th>${R.map(x => `<th>${lab(x)}</th>`).join("")}</tr></thead><tbody>`;
  h += row("Copy unchanged", x => x.valid ? "yes" : `<span class="bad">no</span>`);
  h += row("Edit size (mean ‖δ‖/‖h‖)", x => x.rel == null ? "—" : x.rel.toFixed(3));
  h += row("c<sub>A</sub>, c<sub>B</sub> at copied token 1 before → after", x => x.c_before ? `${x.c_before[0].toFixed(2)}, ${x.c_before[1].toFixed(2)} → ${x.c_after[0].toFixed(2)}, ${x.c_after[1].toFixed(2)}` : "—");
  h += row("Free naming (cond. 2)", x => rep(x.free));
  [0, 1].forEach(o => ["required", "abstain"].forEach(m => {
    const f = x => x.recog.find(r => r.order === o && r.mode === m);
    const any = R.map(f).find(Boolean);
    if (any) h += row(`Recognition, order ${o + 1}, ${m === "required" ? "answer required" : "U allowed"}: ${any.options.map((q, i) => `${"ABCD"[i]} ${esc(q)}`).join(", ")}`, x => pick(f(x)));
  }));
  h += `</tbody></table></div>`;
  $("swap").innerHTML = h;
}

function renderV5() {
  const d = state.data;
  if (!d.v5) { $("v5").innerHTML = `<p class="muted">Not in the v5 subsets (75 seeded hold trials, 60 swap situations).</p>`; return; }
  let h = "";
  if (d.v5.hold) {
    const C = d.v5.hold.cells;
    h += `<p class="sub">Hold, no edit${d.v5.hold.valid ? "" : " (bf16 copy changed)"}</p><div class="tbl-wrap"><table class="rep-table"><thead><tr><th>Framing × document</th><th>Self · name the item</th><th>Self · or NONE</th><th>Another instance · name</th></tr></thead><tbody>` +
      state.index.cells.map(c => { const e = C[c.id] || {}; return `<tr><td class="q">${esc(c.label)}</td><td>${rep(e.self2)}</td><td>${rep(e.self1)}</td><td>${rep(e.context2)}</td></tr>`; }).join("") + `</tbody></table></div>`;
  }
  if (d.v5.swap) {
    const R = d.v5.swap, cells = Object.keys(R[0].reports);
    h += `<p class="sub">Swap stage</p><div class="tbl-wrap"><table class="rep-table"><thead><tr><th>Framing × document</th>${R.map(x => `<th>${x.mode === "none" ? "No edit" : `${x.mode} α = ${x.alpha}`}${x.valid ? "" : " (copy changed)"}</th>`).join("")}</tr></thead><tbody>` +
      cells.map(c => `<tr><td class="q">${esc(c.replace("|", " × "))}</td>${R.map(x => `<td>${rep(x.reports[c])}</td>`).join("")}</tr>`).join("") + `</tbody></table></div>`;
  }
  $("v5").innerHTML = h + `<p class="token-help">bf16 rerun with the original copy teacher-forced. Reports cut at 16 tokens are tagged Truncated. See the <a href="../v5.html">v5 page</a> for the scaffold texts.</p>`;
}

async function init() {
  state.index = await fetch(`data/index.json?v=${VER}`).then(r => r.json());
  const S = state.index.situations;
  $("run-meta").innerHTML = `<dt>Model</dt><dd>Qwen3.6-27B</dd><dt>Lens</dt><dd>J++ · blocks 40–54</dd><dt>Trials</dt><dd>${S.length}</dd>` +
    `<dt>Eligible</dt><dd>${S.filter(s => s.eligible).length}</dd><dt>Cond. 2 names A</dt><dd>${S.filter(s => s.eligible && s.match2).length}</dd>`;
  document.querySelectorAll(".view-button").forEach(b => b.onclick = () => {
    state.view = b.dataset.view;
    document.querySelectorAll(".view-button").forEach(x => x.classList.toggle("active", x === b));
    renderPrompt();
  });
  $("filter-select").onchange = e => { state.filter = e.target.value; renderSelect(); };
  $("sit-select").onchange = e => openSituation(e.target.value);
  $("block-range").oninput = e => { state.block = +e.target.value; renderReadout(); renderRanked(); };
  $("badge-item").onchange = e => { state.badge = e.target.value; renderPrompt(); };
  $("copy-token-link").onclick = async () => {
    const url = location.href.split("#")[0] + hashFor(state.id, state.pos, state.block);
    try { await navigator.clipboard.writeText(url); $("copy-token-link").textContent = "Copied"; } catch { $("copy-token-link").textContent = "Copy failed"; }
    setTimeout(() => $("copy-token-link").textContent = "Copy token link", 1200);
  };
  const h = parseHash();
  const row = h.id && S.find(s => s.id === h.id);
  if (row) { state.cat = row.category; state.filter = row.eligible ? "eligible" : "all"; $("filter-select").value = state.filter; state.id = row.id; }
  renderTabs();
  const list = filtered();
  $("sit-select").innerHTML = list.map(s => `<option value="${s.id}">${optLabel(s)}</option>`).join("");
  if (!state.id) state.id = list[0].id;
  $("sit-select").value = state.id;
  openSituation(state.id, row ? h.pos : null, row ? h.block : null);
  window.addEventListener("hashchange", () => { const x = parseHash(); if (x.id && x.id !== state.id && S.some(s => s.id === x.id)) openSituation(x.id, x.pos, x.block); });
}
init();
