// Renders the page from the repository's own data files (copied to data/ at
// build time by scripts/build_site.py). Every figure comes from data/ — the
// voltage ladder included (data/voltage-ladder.json, built from params.py).
(() => {
  const REPO = "https://github.com/Savues/apple-device-metrics/blob/main/";
  const DOCS = {
    "findings": "docs/findings", "iphone17-forecast": "docs/iphone17-forecast",
    "voltage-nodes": "docs/voltage-nodes", "shallow-charging-accuracy": "docs/shallow-charging-accuracy",
    "lifetime-projection": "docs/lifetime-projection", "methodology": "docs/methodology",
    "corrections": "docs/corrections", "ANALYTICS-EVIDENCE": "devices/iphone-01/ANALYTICS-EVIDENCE",
  };
  let lang = localStorage.getItem("adm-lang") ||
    ((navigator.language || "en").toLowerCase().startsWith("zh") ? "zh" : "en");
  let D = null;

  const $ = (s) => document.querySelector(s);
  const t = (k) => {
    const v = I18N[lang][k] ?? I18N.en[k] ?? k;
    if (typeof v !== "string") return v;  // some entries are [title, desc] arrays
    if (!D) return v.replace(/\{\w+\}/g, "…");
    // Counts and cycle numbers come from the data, not from the string.
    const vars = {
      rated: fmt(D.rated),
      exportrows: String(D.hx.length),
      registered: String(D.pred.predictions[0].registered_at_cycle),
    };
    return v.replace(/\{(\w+)\}/g, (m, k2) => (k2 in vars ? vars[k2] : m));
  };
  const docUrl = (k, l = lang) => REPO + DOCS[k] + (l === "zh" ? ".zh.md" : ".md");
  const fill = (s) => s.replace(/\{doc:([\w-]+)\}/g, (_, k) => docUrl(k));
  const fmt = (n, d = 0) => Number(n).toLocaleString(lang === "zh" ? "zh-CN" : "en-US",
    { minimumFractionDigits: d, maximumFractionDigits: d });
  const NS = "http://www.w3.org/2000/svg";

  // Minimal RFC 4180 reader: quoted fields may contain commas and "" escapes.
  function parseLine(line) {
    const out = []; let cur = "", q = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (q) {
        if (c === '"' && line[i + 1] === '"') { cur += '"'; i++; }
        else if (c === '"') q = false;
        else cur += c;
      } else if (c === '"') q = true;
      else if (c === ",") { out.push(cur); cur = ""; }
      else cur += c;
    }
    out.push(cur);
    return out;
  }
  function csv(text) {
    const [h, ...rows] = text.trim().split(/\r?\n/);
    const keys = parseLine(h);
    return rows.map((r) => Object.fromEntries(parseLine(r).map((v, i) => [keys[i], v])));
  }
  async function load() {
    const get = (f) => fetch("data/" + f).then((r) => { if (!r.ok) throw new Error(f); return r; });
    const [fc, pred, sum, tl, hx, ss, lad] = await Promise.all([
      get("iphone17-forecast.json").then((r) => r.json()),
      get("predictions.json").then((r) => r.json()),
      get("charging-summary.json").then((r) => r.json()),
      get("analytics-timeline.csv").then((r) => r.text()).then(csv),
      get("health-samples.csv").then((r) => r.text()).then(csv),
      get("charging-sessions.csv").then((r) => r.text()).then(csv),
      get("voltage-ladder.json").then((r) => r.json()),
    ]);
    const fcRows = await get("iphone17-forecast.csv").then((r) => r.text()).then(csv);
    D = { fc, pred, sum, tl, hx, ss, fcRows,
      ladder: lad.bands.map((b) => [b.from, b.mv]), rated: lad.rated_mah };
  }

  // ---------- tiny SVG helpers ----------
  // Draw in real CSS pixels so text is never stretched.
  const size = (el) => [Math.max(300, el.clientWidth), el.clientHeight || 260];
  function svg(el, w, h) {
    el.innerHTML = "";
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", `0 0 ${w} ${h}`);
    el.appendChild(s);
    return s;
  }
  function add(s, tag, attrs, text) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    s.appendChild(e);
    return e;
  }
  function axes(s, W, H, m, ys, yfmt, xs, xfmt, X, Y) {
    ys.forEach((v) => {
      add(s, "line", { class: "grid", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) });
      add(s, "text", { x: m.l - 6, y: Y(v) + 4, "text-anchor": "end" }, yfmt(v));
    });
    xs.forEach((v) => add(s, "text", { x: X(v), y: H - m.b + 16, "text-anchor": "middle" }, xfmt(v)));
  }
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

  // ---------- sections ----------
  function kpis() {
    const b = D.fc.base, last = D.tl[D.tl.length - 1];
    const items = [
      [fmt(b.cycle), "", "kpi.cycles"],
      [fmt(b.ncc_mah), "mAh", "kpi.ncc"],
      [fmt(b.health_pct, 2), "%", "kpi.health"],
      [b.apple_max_capacity_percent, "%", "kpi.apple"],
      [fmt(last.vac_voltage_limit_mv), "mV", "kpi.voltage"],
      [fmt(D.fc.current_usage.cycles_per_day, 2), "", "kpi.rate"],
    ];
    $("#kpis").innerHTML = items.map(([v, u, k]) =>
      `<div class="kpi"><div class="v">${v}<small>${u}</small></div><div class="k">${t(k)}</div></div>`).join("");
  }

  function ladder() {
    const cyc = D.fc.base.cycle;
    const L = D.ladder;
    const cur = L.filter(([c]) => cyc >= c).pop()[0];
    const lo = L[L.length - 1][1] - 40, hi = L[0][1];
    $("#ladder").innerHTML = L.map(([c, mv], i) => {
      const next = L[i + 1] ? L[i + 1][0] - 1 : "∞";
      const cls = c === cur ? "now" : c < cur ? "past" : "";
      const tag = c === cur ? `<span class="tag">${t("now")}</span>` : "";
      const pct = ((mv - lo) / (hi - lo)) * 100;
      return `<div class="rung ${cls}"><div class="label"><div>${c}–${next}</div><div class="mv">${mv} mV</div></div><div class="bar"><i style="width:${pct}%"></i></div>${tag}</div>`;
    }).join("");
  }

  function two() {
    $("#two-ncc").textContent = fmt(D.fc.base.health_pct, 2) + "%";
    $("#two-apple").textContent = D.fc.base.apple_max_capacity_percent + "%";
  }

  function history() {
    // merge sparse export (date, cycle, NCC) with daily analytics
    const pts = new Map();
    D.hx.forEach((r) => pts.set(+r.cycle_count, +r.nominal_capacity_mah));
    D.tl.forEach((r) => pts.set(+r.cycle_count, +r.nominal_charge_capacity_mah));
    const data = [...pts].sort((a, b) => a[0] - b[0]);
    const [W, H] = size($("#hist")), m = { l: 46, r: 14, t: 14, b: 26 };
    // Domains follow the data: a fixed 3650-3700 window silently clipped the
    // newest points once a voltage step pushed NCC below it.
    const cs = data.map((d) => d[0]), vs = data.map((d) => d[1]);
    const x0 = Math.min(...cs) - 4, x1 = Math.max(...cs) + 4;
    const lo = Math.min(...vs), hi = Math.max(...vs);
    const pad = Math.max(4, (hi - lo) * 0.15);
    const ystep = Math.max(5, Math.ceil((hi - lo + 2 * pad) / 5 / 5) * 5);
    const y0 = Math.floor((lo - pad) / ystep) * ystep;
    const y1 = Math.ceil((hi + pad) / ystep) * ystep;
    const yt = [];
    for (let v = y0; v <= y1; v += ystep) yt.push(v);
    const xstep = Math.max(20, Math.ceil((x1 - x0) / 4 / 20) * 20);
    const xt = [];
    for (let c = Math.ceil(x0 / xstep) * xstep; c <= x1; c += xstep) xt.push(c);
    const X = (c) => m.l + (c - x0) / (x1 - x0) * (W - m.l - m.r);
    const Y = (v) => m.t + (y1 - v) / (y1 - y0) * (H - m.t - m.b);
    const s = svg($("#hist"), W, H);
    axes(s, W, H, m, yt, (v) => v, xt, (v) => v, X, Y);
    // Mark the start of the band the device is in now, from the ladder data.
    const band = D.ladder.filter(([c]) => D.fc.base.cycle >= c).pop();
    if (band && band[0] > x0) {
      add(s, "line", { x1: X(band[0]), x2: X(band[0]), y1: m.t, y2: H - m.b,
        stroke: css("--amber"), "stroke-dasharray": "4 4" });
      add(s, "text", { x: X(band[0]) + 4, y: m.t + 10, class: "lbl" }, `${band[0]} → ${band[1]} mV`);
    }
    add(s, "path", { d: data.map(([c, v], i) => `${i ? "L" : "M"}${X(c)},${Y(v)}`).join(""),
      fill: "none", stroke: css("--blue"), "stroke-width": 2.5 });
    data.forEach(([c, v]) => add(s, "circle", { cx: X(c), cy: Y(v), r: 3.2, fill: css("--blue") }));
  }

  function facts() {
    $("#facts").innerHTML = [1, 2, 3, 4].map((i) => `<li>${t("fact." + i)}</li>`).join("");
  }

  function forecast() {
    // Node steps are instantaneous: before each row where lock-in grows, add a
    // point at the same cycle with the pre-step value so the line drops vertically.
    const rows = [];
    D.fcRows.forEach((r, i) => {
      const cur = { c: +r.cycle, n: +r.ncc_mah, k: +r.chemical_only_mah };
      const prev = D.fcRows[i - 1];
      const jump = prev ? +r.node_lockin_mah - +prev.node_lockin_mah : 0;
      if (jump > 0) rows.push({ c: cur.c, n: cur.n + jump, k: cur.k });
      rows.push(cur);
    });
    const [W, H] = size($("#fc")), m = { l: 52, r: 16, t: 34, b: 26 };
    const x0 = rows[0].c, x1 = rows[rows.length - 1].c;
    const lo = Math.min(...rows.map((r) => r.n));
    const y0 = Math.floor((lo - 10) / 50) * 50, y1 = Math.ceil((rows[0].n + 10) / 50) * 50;
    const yt = []; for (let v = y0; v <= y1; v += 50) yt.push(v);
    const X = (c) => m.l + (c - x0) / (x1 - x0) * (W - m.l - m.r);
    const Y = (v) => m.t + (y1 - v) / (y1 - y0) * (H - m.t - m.b);
    const s = svg($("#fc"), W, H);
    axes(s, W, H, m, yt, (v) => v + "", [250, 400, 600, 800, 1000, 1200, 1400], (v) => v, X, Y);
    D.fc.nodes.forEach((n, i) => {
      add(s, "line", { x1: X(n.cycle), x2: X(n.cycle), y1: m.t - 18 + (i % 2) * 14, y2: H - m.b, stroke: css("--muted"), "stroke-opacity": 0.4, "stroke-dasharray": "4 4" });
      add(s, "text", { x: X(n.cycle) + 4, y: m.t - 22 + (i % 2) * 14 + 10 }, `${n.cycle} · ${n.vac_voltage_limit_mv} mV`);
    });
    const path = (k, col, dash) => add(s, "path", {
      d: rows.map((r, i) => `${i ? "L" : "M"}${X(r.c)},${Y(r[k])}`).join(""), fill: "none", stroke: col,
      "stroke-width": 2.5, "stroke-dasharray": dash || "" });
    path("k", css("--green"), "6 5");
    path("n", css("--blue"));
    add(s, "circle", { cx: X(rows[0].c), cy: Y(rows[0].n), r: 5, fill: css("--blue") });

    const tr = [{ cycle: D.fc.base.cycle, date: D.fc.base.date, vac_voltage_limit_mv: +D.tl[D.tl.length - 1].vac_voltage_limit_mv,
      ncc_health_pct: D.fc.base.health_pct, ncc_mah: D.fc.base.ncc_mah, node_lockin_mah: 0, chemical_only_mah: D.fc.base.ncc_mah, now: true },
      ...D.fc.nodes];
    $("#fc-table").innerHTML =
      `<thead><tr>${["date", "cycle", "mv", "health", "mah", "lock", "chem"].map((k) => `<th>${t("th." + k)}</th>`).join("")}</tr></thead><tbody>` +
      tr.map((r) => `<tr class="${r.now ? "now" : ""}"><td>${r.date}${r.now ? " · " + t("now") : ""}</td><td>${r.cycle}</td><td>${r.vac_voltage_limit_mv} mV</td>` +
        `<td>${fmt(r.ncc_health_pct, 3)}%</td><td><b>${fmt(r.ncc_mah, 1)}</b></td><td>${fmt(r.node_lockin_mah, 1)}</td><td>${fmt(r.chemical_only_mah, 1)}</td></tr>`).join("") +
      "</tbody>";
  }

  function score(p) {
    const snaps = D.tl.map((r) => ({ d: r.date, c: +r.cycle_count, mv: +r.vac_voltage_limit_mv,
      n: +r.nominal_charge_capacity_mah, a: r.maximum_capacity_percent_reported,
      g: r.gauge_update_time_utc }));
    // Ignore stale re-reports (same gauge write as the row before) so the
    // "last snapshot before the node" is a real measurement.
    const uniq = snaps.filter((s, i) => i === 0 || s.g !== snaps[i - 1].g);
    const pre = uniq.filter((s) => s.c < 250), post = uniq.filter((s) => s.c >= 250);
    const f = post[0];
    if (!f) return ["pending", ""];
    if (p.observe_only) return ["obs", f.a + "%"];
    if (p.id === "node-250-voltage") return [Math.abs(f.mv - p.expected) <= p.tolerance ? "hit" : "miss", f.mv + " mV"];
    if (p.id === "node-250-ncc-step") { const d = pre[pre.length - 1].n - f.n; return [Math.abs(d - p.expected) <= p.tolerance ? "hit" : "miss", d + " mAh"]; }
    if (p.id === "node-250-date") return [f.d >= p.expected_range[0] && f.d <= p.expected_range[1] ? "hit" : "miss", f.d];
    return ["pending", ""];
  }
  function preds() {
    $("#preds").innerHTML = D.pred.predictions.map((p) => {
      const [st, got] = score(p);
      const exp = p.observe_only ? "—" : p.expected_range ? p.expected_range.join(" … ")
        : p.expected + (p.tolerance ? " ± " + p.tolerance : "") + (p.id.includes("voltage") ? " mV" : " mAh");
      return `<li><span class="badge ${st}">${t("st." + st)}</span><div><div>${t("pred." + p.id)}</div>` +
        `<div class="exp">${exp}${got ? " → " + got : ""}</div></div></li>`;
    }).join("");
  }

  function charging() {
    const bins = Array(10).fill(0);
    D.ss.forEach((r) => { bins[Math.min(9, Math.floor(+r.soc_end / 10))]++; });
    const [W, H] = size($("#endsoc")), m = { l: 36, r: 10, t: 14, b: 26 };
    const max = Math.max(...bins), top = Math.ceil(max / 40) * 40;
    const bw = (W - m.l - m.r) / 10;
    const Y = (v) => m.t + (top - v) / top * (H - m.t - m.b);
    const s = svg($("#endsoc"), W, H);
    for (let v = 0; v <= top; v += 40) {
      add(s, "line", { class: "grid", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) });
      add(s, "text", { x: m.l - 6, y: Y(v) + 4, "text-anchor": "end" }, v);
    }
    bins.forEach((n, i) => {
      const x = m.l + i * bw;
      add(s, "rect", { x: x + 3, y: Y(n), width: bw - 6, height: Y(0) - Y(n), rx: 4,
        fill: i >= 8 ? css("--amber") : css("--green") });
      if (n) add(s, "text", { x: x + bw / 2, y: Y(n) - 4, "text-anchor": "middle", class: "lbl" }, n);
      add(s, "text", { x: x + bw / 2, y: H - m.b + 16, "text-anchor": "middle" }, `${i * 10}`);
    });
    const S = D.sum;
    const maxEnd = Math.max(...D.ss.map((r) => +r.soc_end));
    const anom = D.ss.filter((r) => r.anomaly).length;
    const st = [
      ["s.sessions", fmt(S.sessions)], ["s.days", fmt(S.span_days)],
      ["s.efc", fmt(S.equivalent_full_cycles, 2)], ["s.mah", fmt(D.fc.current_usage.mah_per_day_throughput) + " mAh"],
      ["s.rate", fmt(S.avg_rate_pct_per_min, 2) + " %/min"], ["s.dur", fmt(S.avg_duration_min, 1) + " min"],
      ["s.max", maxEnd + "%"], ["s.anom", `${anom} (${fmt(anom / S.sessions * 100, 1)}%)`],
    ];
    $("#chstats").innerHTML = st.map(([k, v]) => `<dt>${t(k)}</dt><dd>${v}</dd>`).join("");
  }

  function docs() {
    $("#doclist").innerHTML = Object.keys(DOCS).map((k) => {
      const [title, desc] = t("doc." + k);
      return `<div class="doc"><b>${title}</b><span>${desc}</span><div class="ln">` +
        `<a href="${docUrl(k, "en")}">English</a><a href="${docUrl(k, "zh")}">中文</a></div></div>`;
    }).join("");
  }

  function text() {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-i18n]").forEach((e) => { e.textContent = t(e.dataset.i18n); });
    document.querySelectorAll("[data-i18n-html]").forEach((e) => { e.innerHTML = fill(t(e.dataset.i18nHtml)); });
    $("#lang").textContent = lang === "zh" ? "English" : "中文";
    if (D) $("#gen").textContent = `${t("gen")} ${D.tl[D.tl.length - 1].date}`;
  }

  function render() {
    text();
    if (!D) return;
    kpis(); ladder(); two(); history(); facts(); forecast(); preds(); charging(); docs();
  }

  $("#lang").addEventListener("click", () => {
    lang = lang === "zh" ? "en" : "zh";
    localStorage.setItem("adm-lang", lang);
    render();
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);
  let rt;
  addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(render, 150); });

  text();
  load().then(render).catch((e) => {
    document.querySelector("main").insertAdjacentHTML("afterbegin",
      `<p class="wrap callout">Data failed to load: ${e.message}. Run <code>python3 scripts/build_site.py</code>.</p>`);
  });
})();
