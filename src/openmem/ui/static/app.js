/* OpenMem Web UI */

const state = {
  memories: [],
  sort: "created_at",
  order: "desc",
  searchTimeout: null,
  selectedId: null,
  activeTab: "table",
  activeSource: "",
  cy: null,
};

/* ── Source icons ── */

const CLAUDE_ICON = `<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16.28 2.477a1.04 1.04 0 0 0-1.253.556l-5.61 12.069-2.005-4.16a1.04 1.04 0 0 0-1.878 0L2.082 18.2a1.04 1.04 0 0 0 .938 1.493H21.1a1.04 1.04 0 0 0 .92-1.52L16.281 2.477z" fill="#D97757"/></svg>`;

const CLAUDE_ICON_SMALL = `<svg class="source-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16.28 2.477a1.04 1.04 0 0 0-1.253.556l-5.61 12.069-2.005-4.16a1.04 1.04 0 0 0-1.878 0L2.082 18.2a1.04 1.04 0 0 0 .938 1.493H21.1a1.04 1.04 0 0 0 .92-1.52L16.281 2.477z" fill="#D97757"/></svg>`;

const GENERIC_SOURCE_ICON = `<svg class="sidebar-icon" viewBox="0 0 16 16" fill="currentColor"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>`;

const SOURCE_LABELS = {
  "claude-code": "Claude Code",
};

function sourceDisplayName(source) {
  if (!source) return "Other";
  return SOURCE_LABELS[source] || source;
}

function sidebarIcon(source) {
  if (source === "claude-code") return CLAUDE_ICON;
  return GENERIC_SOURCE_ICON;
}

function sourceIcon(source) {
  if (source === "claude-code") return CLAUDE_ICON_SMALL;
  if (source) return `<span class="source-label">${escapeHtml(source)}</span>`;
  return '<span class="source-label source-empty">—</span>';
}

/* ── API helpers ── */

async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || res.statusText);
  }
  return res.json();
}

/* ── Stats ── */

async function loadStats() {
  const s = await api("/api/stats");
  document.getElementById("stat-total").innerHTML =
    `<span class="label">Total</span> <span class="value">${s.memory_count}</span>`;
  document.getElementById("stat-active").innerHTML =
    `<span class="label">Active</span> <span class="value">${s.active_count}</span>`;
  document.getElementById("stat-strength").innerHTML =
    `<span class="label">Avg strength</span> <span class="value">${s.avg_strength.toFixed(2)}</span>`;
  document.getElementById("stat-edges").innerHTML =
    `<span class="label">Edges</span> <span class="value">${s.edge_count}</span>`;
}

/* ── Sidebar ── */

async function loadSources() {
  const sources = await api("/api/sources");
  const container = document.getElementById("sidebar-sources");
  const totalCount = sources.reduce((sum, s) => sum + s.count, 0);

  // Update "All" count
  document.getElementById("count-all").textContent = totalCount;

  // Build source items (skip empty source — those show under "All" only)
  const named = sources.filter((s) => s.source);
  container.innerHTML = named.map((s) => `
    <div class="sidebar-item${state.activeSource === s.source ? " active" : ""}" data-source="${escapeHtml(s.source)}">
      ${sidebarIcon(s.source)}
      <span class="sidebar-label">${escapeHtml(sourceDisplayName(s.source))}</span>
      <span class="sidebar-count">${s.count}</span>
    </div>
  `).join("");

  // Wire click handlers
  document.querySelectorAll("#sidebar-nav .sidebar-item").forEach((item) => {
    item.addEventListener("click", () => selectSource(item.dataset.source));
  });
}

function selectSource(source) {
  state.activeSource = source;
  // Update active state
  document.querySelectorAll("#sidebar-nav .sidebar-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.source === source);
  });
  // Reload
  document.getElementById("search-input").value = "";
  loadMemories();
}

/* ── Memory list ── */

function formatDate(ts) {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return d.toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function shortDate(ts) {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function truncate(text, len = 100) {
  if (!text) return "";
  return text.length > len ? text.slice(0, len - 1) + "\u2026" : text;
}

function renderTable(memories) {
  const tbody = document.getElementById("memory-tbody");

  if (!memories.length) {
    tbody.innerHTML = `
      <tr><td colspan="8">
        <div class="empty-state">
          <h3>No memories found</h3>
          <p>Store some memories via Claude Code or the Python API.</p>
        </div>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = memories.map((m) => {
    const projectShort = m.project ? m.project.split("/").filter(Boolean).pop() : "";
    return `
    <tr data-id="${m.id}" class="${m.id === state.selectedId ? "selected" : ""}">
      <td>${shortDate(m.created_at)}</td>
      <td class="agent-cell">${sourceIcon(m.source)}</td>
      <td class="project-cell" title="${escapeHtml(m.project || "")}">${escapeHtml(projectShort)}</td>
      <td><span class="badge badge-${m.type}">${m.type}</span></td>
      <td><span class="badge badge-${m.status}">${m.status}</span></td>
      <td>
        <span class="strength-bar"><span class="strength-fill" style="width:${(m.strength * 100).toFixed(0)}%"></span></span>
        ${m.strength.toFixed(2)}
      </td>
      <td>${m.confidence.toFixed(2)}</td>
      <td class="text-cell">${m.score != null ? `<span class="score-badge">${m.score.toFixed(3)}</span>` : ""}${escapeHtml(truncate(m.gist || m.text))}</td>
    </tr>`;
  }).join("");

  tbody.querySelectorAll("tr[data-id]").forEach((tr) => {
    tr.addEventListener("click", () => openDetail(tr.dataset.id));
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function loadMemories() {
  const type = document.getElementById("filter-type").value;
  const status = document.getElementById("filter-status").value;
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  if (status) params.set("status", status);
  if (state.activeSource) params.set("source", state.activeSource);
  params.set("sort", state.sort);
  params.set("order", state.order);

  state.memories = await api(`/api/memories?${params}`);
  renderTable(state.memories);
}

async function doSearch(query) {
  if (!query.trim()) {
    await loadMemories();
    return;
  }
  const results = await api(`/api/search?q=${encodeURIComponent(query)}`);
  state.memories = results;
  renderTable(results);
}

/* ── Detail panel ── */

async function openDetail(id) {
  state.selectedId = id;
  // Highlight selected row
  document.querySelectorAll("#memory-tbody tr").forEach((tr) => {
    tr.classList.toggle("selected", tr.dataset.id === id);
  });

  const panel = document.getElementById("detail-panel");
  const content = document.getElementById("detail-content");
  panel.classList.remove("hidden");

  const m = await api(`/api/memories/${id}`);

  content.innerHTML = `
    <div class="detail-field">
      <div class="label">ID</div>
      <div class="value mono">${m.id}</div>
    </div>
    <div class="detail-field">
      <div class="label">Type / Status</div>
      <div class="value">
        <span class="badge badge-${m.type}">${m.type}</span>
        <span class="badge badge-${m.status}">${m.status}</span>
      </div>
    </div>
    ${m.gist ? `
    <div class="detail-field">
      <div class="label">Gist</div>
      <div class="value">${escapeHtml(m.gist)}</div>
    </div>` : ""}
    <div class="detail-field">
      <div class="label">Content</div>
      <div class="detail-text">${escapeHtml(m.text)}</div>
    </div>
    ${m.entities && m.entities.length ? `
    <div class="detail-field">
      <div class="label">Entities</div>
      <div class="value">${m.entities.map((e) => `<span class="entity-tag">${escapeHtml(e)}</span>`).join("")}</div>
    </div>` : ""}
    <div class="detail-field">
      <div class="label">Strength</div>
      <div class="value">
        <span class="strength-bar"><span class="strength-fill" style="width:${(m.strength * 100).toFixed(0)}%"></span></span>
        ${m.strength.toFixed(2)}
      </div>
    </div>
    <div class="detail-field">
      <div class="label">Confidence</div>
      <div class="value">${m.confidence.toFixed(2)}</div>
    </div>
    <div class="detail-field">
      <div class="label">Access count</div>
      <div class="value">${m.access_count}</div>
    </div>
    <div class="detail-field">
      <div class="label">Created</div>
      <div class="value">${formatDate(m.created_at)}</div>
    </div>
    <div class="detail-field">
      <div class="label">Updated</div>
      <div class="value">${formatDate(m.updated_at)}</div>
    </div>
    <div class="detail-field">
      <div class="label">Last accessed</div>
      <div class="value">${m.last_accessed ? formatDate(m.last_accessed) : "never"}</div>
    </div>
    ${m.source ? `
    <div class="detail-field">
      <div class="label">Source</div>
      <div class="value detail-source">${sourceIcon(m.source)} ${escapeHtml(sourceDisplayName(m.source))}</div>
    </div>` : ""}
    ${m.project ? `
    <div class="detail-field">
      <div class="label">Project</div>
      <div class="value mono">${escapeHtml(m.project)}</div>
    </div>` : ""}
    ${m.edges && m.edges.length ? `
    <div class="detail-field">
      <div class="label">Edges (${m.edges.length})</div>
      <div class="edge-list">
        ${m.edges.map((e) => {
          const direction = e.source_id === m.id ? "\u2192" : "\u2190";
          const otherId = e.source_id === m.id ? e.target_id : e.source_id;
          return `<div class="edge-item">
            <span class="edge-direction">${direction}</span>
            <span class="mono" style="font-size:12px;cursor:pointer" onclick="openDetail('${otherId}')">${otherId.slice(0, 8)}</span>
            <span class="edge-type">${e.rel_type} (w=${e.weight})</span>
          </div>`;
        }).join("")}
      </div>
    </div>` : ""}
    <div class="detail-actions">
      <button class="btn btn-primary" onclick="reinforceMemory('${m.id}')">Reinforce</button>
      <button class="btn btn-danger" onclick="deleteMemory('${m.id}')">Delete</button>
    </div>
  `;
}

function closeDetail() {
  document.getElementById("detail-panel").classList.add("hidden");
  state.selectedId = null;
  document.querySelectorAll("#memory-tbody tr").forEach((tr) => tr.classList.remove("selected"));
}

async function reinforceMemory(id) {
  await api(`/api/memories/${id}/reinforce`, { method: "POST" });
  await openDetail(id);
  await loadStats();
  await loadSources();
  const query = document.getElementById("search-input").value;
  if (query.trim()) {
    await doSearch(query);
  } else {
    await loadMemories();
  }
}

async function deleteMemory(id) {
  if (!confirm("Delete this memory?")) return;
  await api(`/api/memories/${id}`, { method: "DELETE" });
  closeDetail();
  await loadStats();
  await loadSources();
  const query = document.getElementById("search-input").value;
  if (query.trim()) {
    await doSearch(query);
  } else {
    await loadMemories();
  }
}

/* ── Graph view ── */

const TYPE_COLORS = {
  fact: "#79c0ff",
  decision: "#e3b341",
  preference: "#bc8cff",
  incident: "#ff7b72",
  plan: "#7ee787",
  constraint: "#ffa657",
};

const EDGE_COLORS = {
  mentions: "#8b949e",
  supports: "#7ee787",
  contradicts: "#ff7b72",
  depends_on: "#79c0ff",
  same_as: "#bc8cff",
};

function switchTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });
  const table = document.getElementById("memory-table");
  const graph = document.getElementById("graph-container");

  if (tab === "graph") {
    table.style.display = "none";
    graph.classList.remove("hidden");
    requestAnimationFrame(() => loadGraph());
  } else {
    table.style.display = "";
    graph.classList.add("hidden");
  }
}

async function loadGraph() {
  const data = await api("/api/graph");

  const elements = [];

  data.nodes.forEach((n) => {
    const strength = n.strength || 0;
    const projectShort = n.project ? n.project.split("/").filter(Boolean).pop() : "";
    elements.push({
      data: {
        id: n.id,
        label: n.label || n.id.slice(0, 8),
        projectLabel: projectShort,
        type: n.type,
        status: n.status,
        strength: strength,
        color: TYPE_COLORS[n.type] || "#8b949e",
        nodeWidth: Math.round(40 + strength * 50),
        nodeHeight: Math.round(28 + strength * 22),
        bgOpacity: n.status === "active" ? 0.85 : 0.4,
      },
    });
  });

  data.edges.forEach((e) => {
    const w = e.weight || 0.5;
    elements.push({
      data: {
        id: e.id,
        source: e.source_id,
        target: e.target_id,
        rel_type: e.rel_type,
        weight: w,
        color: EDGE_COLORS[e.rel_type] || "#8b949e",
        edgeWidth: Math.round(1 + w * 3),
        edgeOpacity: 0.4 + w * 0.6,
      },
    });
  });

  if (state.cy) {
    state.cy.destroy();
  }

  const hasEdges = data.edges.length > 0;
  const layout = hasEdges
    ? {
        name: "cose",
        animate: true,
        animationDuration: 500,
        nodeRepulsion: function () { return 8000; },
        idealEdgeLength: function () { return 120; },
        gravity: 0.25,
        padding: 40,
      }
    : {
        name: "grid",
        padding: 40,
        avoidOverlap: true,
        condense: true,
      };

  state.cy = cytoscape({
    container: document.getElementById("graph-container"),
    elements: elements,
    style: [
      {
        selector: "node",
        style: {
          "label": "data(label)",
          "shape": "round-rectangle",
          "width": "data(nodeWidth)",
          "height": "data(nodeHeight)",
          "background-color": "data(color)",
          "background-opacity": "data(bgOpacity)",
          "color": "#f0f6fc",
          "font-size": "9px",
          "text-wrap": "ellipsis",
          "text-max-width": "80px",
          "text-valign": "center",
          "text-halign": "center",
          "border-width": 1,
          "border-color": "#30363d",
        },
      },
      {
        selector: "node:selected",
        style: {
          "border-width": 2,
          "border-color": "#58a6ff",
        },
      },
      {
        selector: "edge",
        style: {
          "label": "data(rel_type)",
          "width": "data(edgeWidth)",
          "line-color": "data(color)",
          "target-arrow-color": "data(color)",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          "font-size": "8px",
          "color": "#8b949e",
          "text-rotation": "autorotate",
          "text-margin-y": -8,
          "opacity": "data(edgeOpacity)",
        },
      },
    ],
    layout: layout,
    minZoom: 0.2,
    maxZoom: 3,
  });

  state.cy.on("tap", "node", function (evt) {
    openDetail(evt.target.id());
  });
}

/* ── Event wiring ── */

document.addEventListener("DOMContentLoaded", () => {
  loadStats();
  loadSources();
  loadMemories();

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  // Search
  const searchInput = document.getElementById("search-input");
  searchInput.addEventListener("input", () => {
    clearTimeout(state.searchTimeout);
    state.searchTimeout = setTimeout(() => doSearch(searchInput.value), 300);
  });

  // Filters
  document.getElementById("filter-type").addEventListener("change", () => {
    document.getElementById("search-input").value = "";
    loadMemories();
  });
  document.getElementById("filter-status").addEventListener("change", () => {
    document.getElementById("search-input").value = "";
    loadMemories();
  });

  // Column sorting
  document.querySelectorAll("th.sortable").forEach((th) => {
    th.addEventListener("click", () => {
      const col = th.dataset.sort;
      if (state.sort === col) {
        state.order = state.order === "desc" ? "asc" : "desc";
      } else {
        state.sort = col;
        state.order = "desc";
      }
      document.querySelectorAll("th.sortable").forEach((h) => {
        h.classList.remove("active", "asc", "desc");
      });
      th.classList.add("active", state.order);

      if (state.memories.length && state.memories[0].score != null) {
        sortClientSide();
      } else {
        loadMemories();
      }
    });
  });

  // Close detail
  document.getElementById("detail-close").addEventListener("click", closeDetail);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDetail();
  });
});

function sortClientSide() {
  const key = state.sort;
  const dir = state.order === "desc" ? -1 : 1;
  state.memories.sort((a, b) => {
    const va = a[key] ?? 0;
    const vb = b[key] ?? 0;
    if (typeof va === "string") return dir * va.localeCompare(vb);
    return dir * (va - vb);
  });
  renderTable(state.memories);
}
