// <project-tracker src="https://solutionsasservice.github.io/project-tracker/data/status.json" group="Autheo" compact></project-tracker>
// Renders status.json (schema_version 1, see docs/UBM-PLUGIN.md). No dependencies; styles live in shadow DOM.
(() => {
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const ago = (iso) => {
    const d = Math.floor((Date.now() - new Date(iso)) / 864e5);
    return d <= 0 ? "today" : d === 1 ? "yesterday" : d + " days ago";
  };
  const RAG = { green: "On track", amber: "At risk", red: "Off track" };
  const CI = { success: "CI passing", failure: "CI failing", pending: "CI running", none: "No CI" };
  const CSS = `
  :host{--bg:#f6f7f9;--card:#fff;--ink:#1b1f24;--muted:#5b6470;--line:#e3e6ea;--green:#1a7f37;--amber:#9a6700;--red:#cf222e;--accent:#0969da;
    display:block;font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink)}
  @media (prefers-color-scheme:dark){:host{--bg:#0d1117;--card:#161b22;--ink:#e6edf3;--muted:#9198a1;--line:#30363d;--green:#3fb950;--amber:#d29922;--red:#f85149;--accent:#4493f8}}
  *{box-sizing:border-box} a{color:var(--accent);text-decoration:none} a:hover{text-decoration:underline}
  header{margin:0 0 20px} h1{font-size:1.6rem;margin:0 0 4px} .ns{color:var(--muted);margin:0 0 10px;max-width:70ch}
  .sum{display:flex;flex-wrap:wrap;gap:8px;font-size:.85rem;color:var(--muted)}
  h2{font-size:1.05rem;margin:28px 0 10px;display:flex;gap:8px;align-items:baseline} h2 small{color:var(--muted);font-weight:400}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr));gap:14px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:8px;min-width:0}
  .top{display:flex;justify-content:space-between;gap:8px;align-items:flex-start} .name{font-weight:600;font-size:1rem;overflow-wrap:anywhere}
  .pill{display:inline-flex;align-items:center;gap:5px;font-size:.75rem;font-weight:600;border-radius:999px;padding:2px 9px;white-space:nowrap;border:1px solid var(--line);color:var(--muted)}
  .pill::before{content:"";width:8px;height:8px;border-radius:50%;background:currentColor}
  .pill.plain::before{display:none}
  .g{color:var(--green)} .a{color:var(--amber)} .r{color:var(--red)}
  .one{margin:0;color:var(--ink)} .meta{font-size:.82rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 12px}
  .bar{height:8px;border-radius:4px;background:var(--line);overflow:hidden} .bar>i{display:block;height:100%;background:var(--accent)}
  .prog{font-size:.8rem;color:var(--muted);display:flex;justify-content:space-between}
  .commit{font-size:.82rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .stale{color:var(--amber);font-weight:600} .lock{font-size:.8rem;color:var(--muted)}
  details{font-size:.85rem} summary{cursor:pointer;color:var(--muted)} details ul{margin:6px 0 0;padding-left:18px} details p{margin:6px 0 0}
  .foot{margin-top:24px;font-size:.8rem;color:var(--muted)} .err{color:var(--red)}
  :host([compact]) .one,:host([compact]) details,:host([compact]) header .ns{display:none}`;

  function card(p) {
    const l = p.live, rag = (p.rag || "").toLowerCase();
    const name = l ? `<a href="${esc(l.url)}">${esc(p.name)}</a>` : esc(p.name);
    const prog = p.progress != null
      ? `<div class="prog"><span>Progress</span><span>${p.progress}%${p.progress_source && p.progress_source !== "manual" ? " · " + esc(p.progress_source.replace("github-milestone:", "milestone ")) : ""}</span></div>
         <div class="bar" role="progressbar" aria-valuenow="${p.progress}" aria-valuemin="0" aria-valuemax="100"><i style="width:${Math.max(0, Math.min(100, p.progress))}%"></i></div>`
      : "";
    const ci = l ? `<span class="pill ${{ success: "g", failure: "r", pending: "a" }[l.ci] || "plain"}">${l.ci_url ? `<a href="${esc(l.ci_url)}" style="color:inherit">${CI[l.ci]}</a>` : CI[l.ci] || esc(l.ci)}</span>` : "";
    const ms = p.milestone ? `<details><summary>Milestone: ${esc(p.milestone.id)} ${esc(p.milestone.name)}</summary>${p.milestone.exit_test ? `<p><b>Exit test:</b> ${esc(p.milestone.exit_test)}</p>` : ""}</details>` : "";
    const na = (p.next_actions || []).filter((a) => a.status !== "done");
    const next = na.length ? `<details><summary>Next actions (${na.length})</summary><ul>${na.map((a) => `<li>${esc(a.action)}${a.status === "doing" ? " <em>(doing)</em>" : ""}</li>`).join("")}</ul></details>` : "";
    return `<article class="card">
      <div class="top"><span class="name">${name}</span><span class="pill ${rag[0] || "plain"}" title="RAG status">${RAG[rag] || esc(p.rag || "No status")}</span></div>
      <p class="one">${esc(p.one_line || (l && l.description) || "")}</p>
      ${prog}
      <div class="meta"><span>${esc(p.state || "")}</span>
        ${l && l.head_date ? `<span class="${p.stale ? "stale" : ""}">${p.stale ? "Stale · " : ""}last commit ${ago(l.head_date)}</span>` : ""}
        ${l ? `<span>${l.open_issues} issues · ${l.open_prs} PRs · ★ ${l.stars}</span>` : ""}
        ${l && l.languages.length ? `<span>${l.languages.map(esc).join(", ")}</span>` : ""}</div>
      ${l && l.head_subject ? `<div class="commit" title="${esc(l.head_subject)}">${esc(l.head)} · ${esc(l.head_subject)}</div>` : ""}
      ${p.details === "public-safe" ? `<div class="lock">Private repo · summary only</div>` : ""}
      ${p.live_error ? `<div class="lock err">${esc(p.live_error)}</div>` : ""}
      <div>${ci}</div>${ms}${next}
    </article>`;
  }

  class ProjectTracker extends HTMLElement {
    static observedAttributes = ["src", "group"];
    connectedCallback() { this.load(); }
    attributeChangedCallback() { if (this.isConnected) this.load(); }
    async load() {
      const root = this.shadowRoot || this.attachShadow({ mode: "open" });
      const src = this.getAttribute("src") || "data/status.json";
      try {
        const d = await (await fetch(src, { cache: "no-cache" })).json();
        if (d.schema_version !== 1) throw new Error("unsupported schema_version " + d.schema_version);
        const want = this.getAttribute("group");
        const groups = d.groups.filter((g) => !want || g === want);
        const ps = d.projects.filter((p) => groups.includes(p.group));
        const n = (r) => ps.filter((p) => p.rag === r).length;
        root.innerHTML = `<style>${CSS}</style>
          <header><h1>${esc(want || d.title)}</h1>${d.north_star && !want ? `<p class="ns">${esc(d.north_star)}</p>` : ""}
            <div class="sum"><span class="pill g">${n("green")} on track</span><span class="pill a">${n("amber")} at risk</span><span class="pill r">${n("red")} off track</span>
            <span class="pill plain">${ps.filter((p) => p.stale).length} stale</span></div></header>
          ${groups.map((g) => { const gp = ps.filter((p) => p.group === g);
            return `<section><h2>${esc(g)} <small>${gp.length}</small></h2><div class="grid">${gp.map(card).join("")}</div></section>`; }).join("")}
          <p class="foot">Updated ${esc(new Date(d.generated_at).toLocaleString())} · live from GitHub · private repos show a summary only</p>`;
      } catch (e) {
        root.innerHTML = `<style>${CSS}</style><p class="err">Could not load project status: ${esc(e.message)}</p>`;
      }
    }
  }
  if (!customElements.get("project-tracker")) customElements.define("project-tracker", ProjectTracker);
})();
