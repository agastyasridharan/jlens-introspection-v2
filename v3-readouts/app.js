// v3 readout dashboard: one situation at a time, loaded from data/s/{id}.json.
const $ = id => document.getElementById(id);
const CATS = [["instrument", "Musical instruments"], ["country", "Countries"]];
const RB = 53;
const state = { index: null, cat: "instrument", filter: "eligible", id: null, pos: null, block: RB, view: "text", rankRef: "site", data: null };
const cache = {};
const VER = "20261110b";  // bump on every data/code change so browsers skip stale cached copies

const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const vis = s => s.replace(/ /g, "·").replace(/\n/g, "↵");
const chip = (cls, t) => `<span class="chip chip-${cls}">${esc(t)}</span>`;
// ranks in the top-100 J++ readout at the reference position (assistant-start site, or the selected token) and selected block
const refPos = () => state.rankRef === "site" ? state.data.site : state.pos;
function refRanks() {
  const d = state.data, j = d.positions.indexOf(refPos()), bi = d.blocks.indexOf(state.block);
  return d.ranks[j][bi];
}
const refLabel = () => `${state.rankRef === "site" ? "the assistant-start readout" : "the selected token's readout"}, block ${state.block}`;
const rkBadge = (r, what) => r ? `<sup class="rk${r <= 10 ? " top" : ""}" title="${esc(what)}: rank ${r} in ${refLabel()} (top ${state.data.rank_depth})">#${r}</sup>` : "";
const itemRank = it => (refRanks()[0] || {})[it];
const itemBadge = it => { const r = itemRank(it); return r ? rkBadge(r, it) : `<sup class="rk none" title="${esc(it)}: not in the top ${state.data.rank_depth} of ${refLabel()}">&gt;${state.data.rank_depth}</sup>`; };

async function load(id) {
  if (!cache[id]) cache[id] = fetch(`data/s/${id}.json?v=${VER}`).then(r => r.json());
  return cache[id];
}

function parseHash() {
  const [id, tok, blk] = decodeURIComponent(location.hash.slice(1)).split("/");
  return { id: id || null, pos: tok && tok.startsWith("token-") ? +tok.slice(6) : null, block: blk && blk.startsWith("block-") ? +blk.slice(6) : null };
}
function hashFor(id, pos, block) { return `#${id}/token-${pos}/block-${block}`; }
function setHash() {
  const h = hashFor(state.id, state.pos, state.block);
  if (location.hash !== h) history.replaceState(null, "", h);
  $("token-link").href = h;
}

function filtered() {
  const S = state.index.situations.filter(s => s.category === state.cat);
  const f = {
    eligible: s => s.eligible, pair: s => s.eligible && s.valid_pair, flip: s => s.eligible && s.flip,
    swapC: s => s.eligible && s.swap_free1 === "C", controlC: s => s.eligible && s.control_free1 === "C",
    skipped: s => !s.eligible, all: () => true,
  }[state.filter];
  return S.filter(f);
}

function renderTabs() {
  $("tabs").innerHTML = CATS.map(([c, t]) => `<button class="tab${c === state.cat ? " active" : ""}" data-cat="${c}">${t}</button>`).join("");
  $("tabs").querySelectorAll(".tab").forEach(b => b.onclick = () => { state.cat = b.dataset.cat; state.id = null; renderTabs(); renderSelect(); });
}

function renderSelect() {
  const list = filtered();
  $("sit-select").innerHTML = list.map(s => `<option value="${s.id}">${esc(s.id.replace(/^m-[a-z]+-/, "#"))} · ${esc(s.scenario)}</option>`).join("") || `<option value="">(none match)</option>`;
  if (!list.length) { showEmpty(); return; }
  if (!list.some(s => s.id === state.id)) state.id = list[0].id;
  $("sit-select").value = state.id;
  openSituation(state.id);
}

function showEmpty() {
  $("sit-title").textContent = "No situations match this filter";
  ["sit-description", "tokens", "plain-prompt", "predictions", "design", "swap", "v5", "rank-table", "token-meta"].forEach(k => $(k).innerHTML = "");
}

async function openSituation(id, pos = null, block = null) {
  state.id = id;
  const d = await load(id);
  if (state.id !== id) return;
  state.data = d;
  const posSet = new Set(d.positions);
  state.pos = pos != null && posSet.has(pos) ? pos : d.site;
  if (block != null && d.blocks.includes(block)) state.block = block;
  const row = state.index.situations.find(s => s.id === id);
  $("sit-kicker").textContent = `${row.category} · ${id}`;
  $("sit-title").textContent = d.scenario;
  $("prompt-label").textContent = id;
  renderAll();
}

function renderDesc() {
  const d = state.data, row = state.index.situations.find(s => s.id === state.id);
  $("sit-description").innerHTML = d.design
    ? `Answer item <b>${esc(d.design.X)}</b>${itemBadge(d.design.X)} · B = <b>${esc(d.design.B)}</b>${itemBadge(d.design.B)} · C = <b>${esc(d.design.C)}</b>${itemBadge(d.design.C)} · ` +
      `${row.valid_pair ? "swap and control keep the answer" : `<span class="bad">swap or control changes the answer</span>`}` +
      ` <span class="muted">· # = rank in ${refLabel()}</span>`
    : `<span class="bad">Not eligible: ${esc(row.skipped || "")}</span>. Readouts only.`;
}
function renderAll() { renderDesc(); renderPrompt(); renderReadout(); renderDesign(); renderSwap(); renderV5(); }
// what depends on the rank reference (block, and the selected token when the reference follows it)
function renderRanked() { renderDesc(); renderPrompt(); renderSwap(); renderV5(); }

function tokenSeq(d) {
  // [{text, pos, live}] for the prompt then the answer; readouts exist at d.positions
  const live = new Set(d.positions);
  const P = d.prompt_tokens.map((t, i) => ({ text: t, pos: i, live: live.has(i) }));
  const A = d.answer_tokens.map((t, k) => ({ text: t, pos: d.prompt_tokens.length + k, live: live.has(d.prompt_tokens.length + k) }));
  return { P, A };
}

function renderPrompt() {
  const d = state.data, { P, A } = tokenSeq(d), tm = refRanks()[1] || {};
  const bd = t => rkBadge(tm[t.pos], vis(t.text));
  const tok = t => `<button class="token${t.live ? "" : " inert"}${t.pos === d.site ? " site" : ""}${t.pos === state.pos ? " active" : ""}" data-pos="${t.pos}"${t.live ? "" : " tabindex=-1"}>${esc(vis(t.text))}${bd(t)}</button>`;
  const plain = t => `<span class="plain-token${t.live ? " live" : " inert"}${t.pos === d.site ? " site" : ""}${t.pos === state.pos ? " active" : ""}" data-pos="${t.pos}"${t.live ? ' tabindex="0" role="button"' : ""}>${t.live && !/\S/.test(t.text) ? `<span class="ws">${esc(vis(t.text))}</span>${esc(t.text)}` : esc(t.text)}${bd(t)}</span>`;
  $("tokens").innerHTML = P.map(tok).join("") + `<span class="boundary">END OF REQUEST · ASSISTANT ANSWER BEGINS</span>` + A.map(tok).join("");
  $("plain-prompt").innerHTML = P.map(plain).join("") + `<span class="plain-boundary">END OF REQUEST · ASSISTANT ANSWER BEGINS</span>` + A.map(plain).join("");
  document.querySelectorAll("#tokens .token:not(.inert), #plain-prompt .plain-token.live").forEach(el => {
    const go = () => { state.pos = +el.dataset.pos; if (state.rankRef === "selected") renderRanked(); else markActive(); renderReadout(); };
    el.onclick = go; el.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } };
  });
  $("tokens").classList.toggle("hidden", state.view !== "tokens");
  $("plain-prompt").classList.toggle("hidden", state.view !== "text");
}

function markActive() {
  document.querySelectorAll("#tokens .token, #plain-prompt .plain-token").forEach(el => el.classList.toggle("active", +el.dataset.pos === state.pos));
}

function classify(d, s) {
  const it = d.items[s];
  if (!it) return null;
  if (d.design) {
    if (it === d.design.C) return "C";
    if (it === d.design.B) return "B";
    if (d.design.named.includes(it)) return "X";
  }
  return "item";
}

function renderReadout() {
  const d = state.data, j = d.positions.indexOf(state.pos), bi = d.blocks.indexOf(state.block);
  const all = [...d.prompt_tokens, ...d.answer_tokens];
  const isSite = state.pos === d.site;
  $("token-title").textContent = vis(all[state.pos] ?? "");
  $("block-badge").textContent = state.block; $("block-val").textContent = state.block; $("block-range").value = state.block;
  $("lens-heading").textContent = isSite ? "J++ lens readout · assistant-start (edit site)" : "J++ lens readout · answer token";
  $("token-meta").textContent = isSite ? `Prompt position ${state.pos} (last prompt token) · block ${state.block}${state.block === RB ? " (v3 readout block)" : ""}`
    : `Answer token ${state.pos - d.prompt_tokens.length + 1} of ${d.answer_tokens.length} · position ${state.pos} · block ${state.block}`;
  const rows = d.lens[j][bi];
  const top = Math.max(...rows.map(r => r[1]));
  $("predictions").innerHTML = rows.map(([s, lp], r) => {
    const k = classify(d, s), it = d.items[s];
    const w = Math.max(2, 100 * Math.exp(lp - top));
    const tag = k === "item" ? chip("item", it) : k === "X" ? chip("X", `answer: ${it}`) : k ? chip(k, `${k}: ${it}`) : "";
    return `<li class="prediction${k ? " is-" + k : ""}"><div class="prediction-fill" style="width:${w.toFixed(1)}%"></div>` +
      `<div class="prediction-row"><span class="prediction-rank">${r + 1}</span><span class="prediction-text">${esc(vis(d.strings[s]))}${tag}</span>` +
      `<span class="prediction-probability">${lp.toFixed(2)}</span></div></li>`;
  }).join("");
  // rank of B / C tokens by block at this position
  if (d.design) {
    const rankOf = (i, item) => d.ranks[j][i][0][item] ?? "—";
    const head = d.blocks.map(b => `<th>${b}</th>`).join("");
    const line = (lab, item) => `<tr><th>${lab}</th>` + d.blocks.map((b, i) => `<td class="${b === state.block ? "cur" : ""}">${rankOf(i, item)}</td>`).join("") + "</tr>";
    $("rank-table").innerHTML = `<div class="tbl-wrap"><table class="rank-grid"><thead><tr><th></th>${head}</tr></thead><tbody>${line("B", d.design.B)}${line("C", d.design.C)}${line("X", d.design.X)}</tbody></table></div>` +
      `<p class="token-help">Rank of the item&#8217;s best token in the top ${d.rank_depth} (— if absent). Unedited readout.</p>`;
  } else $("rank-table").innerHTML = "";
  setHash();
}

function rep(r) {
  if (!r) return `<span class="muted">—</span>`;
  const t = r.tag ? chip(r.tag, r.tag) : r.label && r.label !== "Item" ? chip("X", r.label) : "";
  return `<span class="rep">${esc(r.text)}</span>${t}${r.item ? itemBadge(r.item) : ""}`;
}

function renderDesign() {
  const d = state.data;
  if (!d.design) { $("design").innerHTML = `<p class="muted">No design: this request was not eligible.</p>`; return; }
  const g = d.design;
  const comp = g.competitors.map(c => `${esc(c)} <span class="muted">${g.corr[c].toFixed(2)}</span>${c === g.B ? chip("B", "B") : c === g.C ? chip("C", "C") : ""}`).join(" · ");
  $("design").innerHTML = `<dl class="kv">
    <dt>Answer</dt><dd>${esc(d.answer)}</dd>
    <dt>Named items</dt><dd>${esc(g.named.join(", "))}</dd>
    <dt>Competitors (corrected score)</dt><dd>${comp}</dd>
    <dt>B / C tokens</dt><dd><span class="mono">${esc(vis(g.tok_B_str))}</span> (rank ${g.rank_B}) / <span class="mono">${esc(vis(g.tok_C_str))}</span> (rank ${g.rank_C})</dd>
    <dt>B − C margin</dt><dd>${g.margin_BC.toFixed(2)}${g.reoriented ? ' <span class="muted">(reoriented: B has the larger unedited coordinate)</span>' : ""}</dd>
    <dt>Unedited coordinates</dt><dd>c<sub>B</sub> = ${g.c_site[0].toFixed(2)}, c<sub>C</sub> = ${g.c_site[1].toFixed(2)} at block 53</dd>
    <dt>Stable top competitor</dt><dd>block 52: ${g.stable_rb1 ? "yes" : "no"} · block 51: ${g.stable_rb2 ? "yes" : "no"}</dd>
    <dt>Answer item rank</dt><dd>${g.X_rank ?? "not in top 100"}</dd></dl>`;
}

function letter(r, opts) {
  const s = (r.text || "").trim().replace(/[ .,:;!?()\[\]"'*`]/g, "");
  const i = "ABCD".indexOf(s);
  return i >= 0 && s.length === 1 ? `${esc(s)} = ${esc(opts[i])}` : esc(r.text);
}

function renderSwap() {
  const d = state.data;
  if (!d.v3) { $("swap").innerHTML = `<p class="muted">Not run (not eligible).</p>`; return; }
  const C = d.v3.conditions, modes = ["none", "swap", "control", "inject"].filter(m => C[m]);
  const head = `<tr><th></th>${modes.map(m => `<th>${m === "none" ? "No edit" : m}</th>`).join("")}</tr>`;
  const row = (lab, f) => `<tr><td class="q">${lab}</td>${modes.map(m => `<td>${f(C[m], m)}</td>`).join("")}</tr>`;
  const reports = ["free1", "free2", "free3", "anchor", "second"];
  const qlab = { free1: "Competitor question · free naming 1 (primary)", free2: "… or NONE", free3: "… must name one", anchor: "Anchor: most strongly represented", second: "Second choice (preference)" };
  let h = `<div class="tbl-wrap"><table class="rep-table"><thead>${head}</thead><tbody>`;
  h += row("Answer unchanged", c => c.valid ? "yes" : `<span class="bad">no</span>`);
  h += row("Δ = log p(C) − log p(B) at the answer item", c => c.delta.toFixed(2));
  h += row("rank B / rank C at the answer item", c => `${c.rankB} / ${c.rankC}`);
  h += row("Edit size (mean ‖δ‖/‖h‖)", c => c.rel == null ? "—" : c.rel.toFixed(3));
  h += row("c<sub>B</sub>, c<sub>C</sub> at block 53 after edit", c => c.c_after ? `${c.c_after[0].toFixed(2)}, ${c.c_after[1].toFixed(2)}` : "—");
  reports.forEach(k => { h += row(qlab[k], c => c.reports ? rep(c.reports[k]) : `<span class="muted">not asked</span>`); });
  const opts = d.design.options;
  [0, 1].forEach(o => { h += row(`Recognition (answer required), order ${o + 1}: ${esc(opts[o].map((x, i) => "ABCD"[i] + " " + x).join(", "))}`, c => c.reports && c.reports[`rec_req_${o}`] ? letter(c.reports[`rec_req_${o}`], opts[o]) : `<span class="muted">—</span>`); });
  h += `</tbody></table></div>`;
  const q = C.none.reports && C.none.reports.free1 ? C.none.reports.free1.question : "";
  h += `<p class="token-help">Competitor question: <i>${esc(q)}</i></p>`;
  h += `<p class="sub">Late edit (same V and α on the question tokens)</p><p>swap: ${rep(d.v3.late.swap)} · control: ${rep(d.v3.late.control)}</p>`;
  h += `<p class="sub">Another-instance prediction (no edit)</p><p>free naming 1: ${rep(d.v3.context.ctx_free1)} · or NONE: ${rep(d.v3.context.ctx_free2)} · must name: ${rep(d.v3.context.ctx_free3)}</p>`;
  h += `<p class="sub">Edited third-person prediction</p><p>swap: ${rep(d.v3.third.swap)} · control: ${rep(d.v3.third.control)}</p>`;
  $("swap").innerHTML = h;
}

function renderV5() {
  const d = state.data;
  if (!d.v5) { $("v5").innerHTML = `<p class="muted">Not run.</p>`; return; }
  const V = d.v5;
  const head = `<tr><th>Framing × document</th><th>No edit</th><th>Swap${V.valid.swap ? "" : " (answer changed)"}</th><th>Control${V.valid.control ? "" : " (answer changed)"}</th><th>Another instance</th></tr>`;
  const body = state.index.cells.map(c => { const e = V.cells[c.id] || {}; return `<tr><td class="q">${esc(c.label)}</td><td>${rep(e.none)}</td><td>${rep(e.swap)}</td><td>${rep(e.control)}</td><td>${rep(e.context)}</td></tr>`; }).join("");
  $("v5").innerHTML = `<div class="tbl-wrap"><table class="rep-table"><thead>${head}</thead><tbody>${body}</tbody></table></div>` +
    `<p class="token-help">bf16 rerun; swap/control validity is the edited bf16 answer matching the unedited bf16 answer. See the <a href="../v5.html">v5 page</a> for the scaffold texts.</p>`;
}

async function init() {
  state.index = await fetch(`data/index.json?v=${VER}`).then(r => r.json());
  const S = state.index.situations;
  $("run-meta").innerHTML = `<dt>Model</dt><dd>Qwen3.6-27B</dd><dt>Lens</dt><dd>J++ · blocks 40–54</dd><dt>Requests</dt><dd>${S.length}</dd>` +
    `<dt>Eligible</dt><dd>${S.filter(s => s.eligible).length}</dd><dt>Valid swap pairs</dt><dd>${S.filter(s => s.valid_pair).length}</dd>`;
  document.querySelectorAll(".view-button").forEach(b => b.onclick = () => {
    state.view = b.dataset.view;
    document.querySelectorAll(".view-button").forEach(x => x.classList.toggle("active", x === b));
    renderPrompt();
  });
  $("filter-select").onchange = e => { state.filter = e.target.value; renderSelect(); };
  $("sit-select").onchange = e => openSituation(e.target.value);
  $("block-range").oninput = e => { state.block = +e.target.value; renderReadout(); renderRanked(); };
  $("rank-ref").onchange = e => { state.rankRef = e.target.value; renderRanked(); };
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
  $("sit-select").innerHTML = list.map(s => `<option value="${s.id}">${esc(s.id.replace(/^m-[a-z]+-/, "#"))} · ${esc(s.scenario)}</option>`).join("");
  if (!state.id) state.id = list[0].id;
  $("sit-select").value = state.id;
  openSituation(state.id, row ? h.pos : null, row ? h.block : null);
  window.addEventListener("hashchange", () => { const x = parseHash(); if (x.id && x.id !== state.id && S.some(s => s.id === x.id)) openSituation(x.id, x.pos, x.block); });
}
init();
