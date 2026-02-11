const API_BASE = CONFIG.API_BASE_URL;

const statusFilter = document.getElementById("statusFilter");
const ufFilter = document.getElementById("ufFilter");
const municipioFilter = document.getElementById("municipioFilter");
const minMulta = document.getElementById("minMulta");
const maxMulta = document.getElementById("maxMulta");
const search = document.getElementById("search");
const tableBody = document.getElementById("tableBody");

const btnTop100 = document.getElementById("btnTop100");
const btnTop30 = document.getElementById("btnTop30");

let currentEndpoint = "/leads";

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("API error");
  }
  return await res.json();
}

function formatMoney(val) {
  if (val === null || val === undefined) return "-";
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(Number(val));
}

function statusBadge(status) {
  const st = (status || "").toUpperCase();
  if (st === "NULIDADE ALTA") return "badge high";
  if (st === "VERIFICAR EMBARGO") return "badge mid";
  return "badge low";
}

function buildRow(item) {
  const row = document.createElement("tr");
  row.innerHTML = `
    <td>${item.nome_infrator || "-"}</td>
    <td>${formatMoney(item.valor_multa)}</td>
    <td><span class="${statusBadge(item.status_ia)}">${item.status_ia || "-"}</span></td>
    <td>${item.municipio || "-"}</td>
    <td>${item.uf || "-"}</td>
    <td>${item.tese_primaria || "-"}</td>
    <td>${item.alerta_code || "-"}</td>
    <td>${Number(item.score_prioridade || 0).toFixed(1)}</td>
    <td>${item.link_rapido_contato ? `<a href="${item.link_rapido_contato}" target="_blank">Abrir</a>` : "-"}</td>
  `;
  return row;
}

async function loadFilters() {
  const data = await fetchJSON(`${API_BASE}/filters`);
  data.statuses.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    statusFilter.appendChild(opt);
  });
  data.ufs.forEach((u) => {
    const opt = document.createElement("option");
    opt.value = u;
    opt.textContent = u;
    ufFilter.appendChild(opt);
  });
}

async function loadStats() {
  const data = await fetchJSON(`${API_BASE}/stats`);
  document.querySelector("#kpi-total strong").textContent = data.total || "--";
  document.querySelector("#kpi-nulidade strong").textContent = data.by_status["NULIDADE ALTA"] || 0;
  document.querySelector("#kpi-embargo strong").textContent = data.by_status["VERIFICAR EMBARGO"] || 0;
  document.querySelector("#kpi-revisar strong").textContent = data.by_status["REVISAR"] || 0;
}

function buildQuery() {
  const params = new URLSearchParams();
  if (statusFilter.value) params.set("status_ia", statusFilter.value);
  if (ufFilter.value) params.set("uf", ufFilter.value);
  if (municipioFilter.value) params.set("municipio", municipioFilter.value.toUpperCase());
  if (minMulta.value) params.set("min_multa", minMulta.value);
  if (maxMulta.value) params.set("max_multa", maxMulta.value);
  if (search.value) params.set("search", search.value);
  return params.toString();
}

async function loadLeads() {
  const query = buildQuery();
  const url = `${API_BASE}${currentEndpoint}${query ? `?${query}` : ""}`;
  const data = await fetchJSON(url);
  tableBody.innerHTML = "";
  data.items.forEach((item) => tableBody.appendChild(buildRow(item)));
}

function attachEvents() {
  [statusFilter, ufFilter, municipioFilter, minMulta, maxMulta, search].forEach((el) => {
    el.addEventListener("change", loadLeads);
    el.addEventListener("keyup", (e) => {
      if (e.key === "Enter") loadLeads();
    });
  });

  btnTop100.addEventListener("click", () => {
    currentEndpoint = "/top100";
    btnTop100.classList.remove("ghost");
    btnTop30.classList.add("ghost");
    loadLeads();
  });

  btnTop30.addEventListener("click", () => {
    currentEndpoint = "/top30";
    btnTop30.classList.remove("ghost");
    btnTop100.classList.add("ghost");
    loadLeads();
  });
}

async function init() {
  await loadFilters();
  await loadStats();
  await loadLeads();
  attachEvents();
}

init().catch(() => {
  tableBody.innerHTML = "<tr><td colspan='9'>Falha ao carregar API</td></tr>";
});
