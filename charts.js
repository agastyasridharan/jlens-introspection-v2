const C = { accent: "#235fa6", a: "#b0702a", mid: "#2f8a57", ink: "#2a2318", ink2: "#5e5245", ink3: "#8a7d6d", rule: "#e6ddd0", rule2: "#cfc4b4", panel: "#fffdf9" };
const FONT = "'Source Sans 3', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";
const CONFIG = { displayModeBar: false, responsive: true, scrollZoom: false };
const CATS = [["grocery", "Groceries", C.a], ["animal", "Animals", C.mid], ["country", "Countries", C.accent]];
function baseLayout(extra) {
  return Object.assign({ font: { family: FONT, size: 12.5, color: C.ink2 }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: false, dragmode: false, hoverlabel: { bgcolor: C.panel, bordercolor: C.rule2, font: { family: FONT, size: 13, color: C.ink } } }, extra);
}
function axis(extra) {
  return Object.assign({ showgrid: false, zeroline: false, fixedrange: true, showline: true, linecolor: C.rule2, linewidth: 1,
    ticks: "outside", ticklen: 4, tickcolor: C.rule2, tickfont: { family: FONT, size: 12, color: C.ink2 } }, extra);
}
const grid = extra => axis(Object.assign({ showgrid: true, gridcolor: "#efe8dc", gridwidth: 1 }, extra));
const ttl = text => ({ text, font: { family: FONT, size: 12, color: C.ink3 }, standoff: 6 });
const W = el => el.getBoundingClientRect().width;
const draw = (el, traces, layout) => Plotly.react(el, traces, baseLayout(layout), CONFIG);

function figCurve() {
  const el = document.getElementById("chart-curve"); if (!el || !R.curve) return;
  const xs = R.curve.blocks, traces = [];
  CATS.forEach(([k, n, col]) => traces.push({ type: "scatter", mode: "lines", x: xs, y: R.curve[k], name: n, line: { color: col, width: 2 },
    hovertemplate: "Block %{x}: %{y:.2f}<extra>" + n + "</extra>" }));
  traces.push({ type: "scatter", mode: "lines", x: xs, y: R.curve.mean, name: "Mean", line: { color: C.ink, width: 2.5 },
    hovertemplate: "Block %{x}: %{y:.2f}<extra>Mean</extra>" });
  const b = R.curve.chosen;
  draw(el, traces, { height: 320, margin: { l: 50, r: 10, t: 14, b: 40 }, hovermode: "x unified",
    xaxis: axis({ title: ttl("Block (0-based block output)"), dtick: 6 }), yaxis: grid({ title: ttl("Items per position"), rangemode: "tozero" }),
    shapes: [{ type: "line", x0: b, x1: b, yref: "paper", y0: 0, y1: 1, line: { color: C.ink3, width: 1, dash: "dot" } }],
    annotations: [{ x: b, yref: "paper", y: 1, text: "readout block " + b, showarrow: false, xanchor: "left", xshift: 4, yanchor: "top",
      font: { family: FONT, size: 12, color: C.ink2 } }] });
}

function bars(id, groups, series, ymax) {
  const el = document.getElementById(id); if (!el) return;
  const traces = series.map(s => ({ type: "bar", name: s.name, x: groups, y: s.y, marker: { color: s.color, line: { color: C.panel, width: 2 } },
    error_y: { type: "data", symmetric: false, array: s.hi.map((h, i) => h - s.y[i]), arrayminus: s.lo.map((l, i) => s.y[i] - l), color: C.ink3, thickness: 1.2, width: 3 },
    text: s.y.map((v, i) => v.toFixed(0) + "%" + (s.n ? "<br><span style='font-size:10px'>n=" + s.n[i] + "</span>" : "")), textposition: "outside", cliponaxis: false,
    textfont: { family: FONT, size: 10.5, color: C.ink2 }, hovertemplate: "%{x}: %{y:.1f}%<extra>" + s.name + "</extra>" }));
  const shapes = R[id + "_chance"] ? [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: R[id + "_chance"], y1: R[id + "_chance"], line: { color: C.ink3, width: 1, dash: "dot" } }] : [];
  draw(el, traces, { barmode: "group", bargap: 0.25, bargroupgap: 0.05, height: 330, margin: { l: 48, r: 8, t: 20, b: 34 }, shapes,
    xaxis: axis({ type: "category" }), yaxis: grid({ range: [0, ymax], ticksuffix: "%", title: ttl("Matches lens reference"), showline: false, ticks: "" }) });
}

function figPerblock() {
  const el = document.getElementById("chart-perblock"); if (!el || !R.perblock) return;
  const P = R.perblock;
  const traces = [{ type: "scatter", mode: "lines", x: P.blocks, y: P.all, name: "All valid", line: { color: C.accent, width: 2 } },
                  { type: "scatter", mode: "lines", x: P.blocks, y: P.elig, name: "Eligible", line: { color: C.a, width: 2 } }];
  draw(el, traces, { height: 300, margin: { l: 50, r: 10, t: 14, b: 40 }, hovermode: "x unified",
    xaxis: axis({ title: ttl("Readout block"), dtick: 6 }), yaxis: grid({ title: ttl("Agreement"), ticksuffix: "%", rangemode: "tozero" }),
    shapes: [{ type: "line", x0: P.chosen, x1: P.chosen, yref: "paper", y0: 0, y1: 1, line: { color: C.ink3, width: 1, dash: "dot" } }] });
}

function render() {
  figCurve(); figPerblock();
  if (R.agree) bars("chart-agree", R.agree.groups, R.agree.series, R.agree.ymax || 100);
  if (R.recog) { R["chart-recog_chance"] = 25; bars("chart-recog", R.recog.groups, R.recog.series, R.recog.ymax || 100); }
}
let tmr; window.addEventListener("resize", () => { clearTimeout(tmr); tmr = setTimeout(render, 150); });
render();
