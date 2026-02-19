/* OpenMem Web UI */

const state = {
  memories: [],
  sort: "created_at",
  order: "desc",
  searchTimeout: null,
  selectedId: null,
};

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
      <tr><td colspan="6">
        <div class="empty-state">
          <h3>No memories found</h3>
          <p>Store some memories via Claude Code or the Python API.</p>
        </div>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = memories.map((m) => `
    <tr data-id="${m.id}" class="${m.id === state.selectedId ? "selected" : ""}">
      <td>${shortDate(m.created_at)}</td>
      <td><span class="badge badge-${m.type}">${m.type}</span></td>
      <td><span class="badge badge-${m.status}">${m.status}</span></td>
      <td>
        <span class="strength-bar"><span class="strength-fill" style="width:${(m.strength * 100).toFixed(0)}%"></span></span>
        ${m.strength.toFixed(2)}
      </td>
      <td>${m.confidence.toFixed(2)}</td>
      <td class="text-cell">${m.score != null ? `<span class="score-badge">${m.score.toFixed(3)}</span>` : ""}${escapeHtml(truncate(m.gist || m.text))}</td>
    </tr>
  `).join("");

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
  // Refresh detail and list
  await openDetail(id);
  await loadStats();
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
  const query = document.getElementById("search-input").value;
  if (query.trim()) {
    await doSearch(query);
  } else {
    await loadMemories();
  }
}

/* ── Event wiring ── */

document.addEventListener("DOMContentLoaded", () => {
  loadStats();
  loadMemories();

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
      // Update header styles
      document.querySelectorAll("th.sortable").forEach((h) => {
        h.classList.remove("active", "asc", "desc");
      });
      th.classList.add("active", state.order);

      // If we have search results with scores, sort client-side
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
