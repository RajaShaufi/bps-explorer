function apiKey() {
    return document.getElementById("api_key").value.trim();
}

function setStatus(elId, msg, type) {
    const el = document.getElementById(elId);
    el.textContent = msg || "";
    el.className = "status " + (type || "");
}

async function fetchJSON(url, opts) {
    const resp = await fetch(url, opts);
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "Terjadi kesalahan.");
    return data;
}

function fillSelect(selectEl, items, valueKey, labelKey, placeholder) {
    selectEl.innerHTML = "";
    if (placeholder) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = placeholder;
        selectEl.appendChild(opt);
    }
    items.forEach(item => {
        const opt = document.createElement("option");
        opt.value = item[valueKey];
        opt.textContent = item[labelKey];
        selectEl.appendChild(opt);
    });
}

function selectedValues(selectEl) {
    return Array.from(selectEl.selectedOptions).map(o => o.value).filter(Boolean);
}

// ---------- Domain loading ----------
const domainTypeSel = document.getElementById("domain_type");
const provPickerWrap = document.getElementById("prov_picker_wrap");
const provPicker = document.getElementById("prov_picker");
const domainSel = document.getElementById("domain");

async function loadProvinces() {
    const data = await fetchJSON(`/api/domains?key=${encodeURIComponent(apiKey())}&type=prov`);
    const list = data.data[1] || [];
    fillSelect(provPicker, list, "domain_id", "domain_name", null);
}

async function loadDomains() {
    if (!apiKey()) {
        setStatus("status-subject", "Isi API key BPS dulu.", "warning");
        return;
    }
    const type = domainTypeSel.value;
    provPickerWrap.style.display = type === "kabbyprov" ? "" : "none";

    if (type === "kabbyprov") {
        await loadProvinces();
        if (!provPicker.value) return;
    }

    let url = `/api/domains?key=${encodeURIComponent(apiKey())}&type=${type}`;
    if (type === "kabbyprov") url += `&prov=${provPicker.value}`;

    try {
        const data = await fetchJSON(url);
        const list = data.data[1] || [];
        fillSelect(domainSel, list, "domain_id", "domain_name", null);
        setStatus("status-subject", `${list.length} domain dimuat.`, "info");
        await loadCSATree();
    } catch (err) {
        setStatus("status-subject", err.message, "error");
    }
}

domainTypeSel.addEventListener("change", loadDomains);
provPicker.addEventListener("change", loadDomains);
document.getElementById("api_key").addEventListener("change", loadDomains);
domainSel.addEventListener("change", loadCSATree);

// =====================================================================
// Statistik menurut Subjek (CSA Subject browsing + fast download)
// =====================================================================
const csaTreeEl = document.getElementById("csa-tree");
const searchAllNode = document.getElementById("search-all-node");
const subjectSearchBox = document.getElementById("subject-search-box");
const subjectTitleEl = document.getElementById("subject-title");
const tablesTbody = document.querySelector("#tables-table tbody");

let csaSubjectsCache = {}; // subcat_id -> [subjects]
let currentRows = []; // baris tabel yang sedang tampil {id, title, updt_date, size, excel, tablesource}

async function loadCSATree() {
    if (!apiKey() || !domainSel.value) return;
    csaSubjectsCache = {};
    csaTreeEl.innerHTML = "Memuat kategori...";
    try {
        const data = await fetchJSON(`/api/csa/subcat?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}`);
        const subcats = data.data[1] || [];
        csaTreeEl.innerHTML = "";
        subcats.forEach(sc => {
            const header = document.createElement("div");
            header.className = "subcat-header";
            header.textContent = sc.title;
            header.dataset.subcatId = sc.subcat_id;

            const body = document.createElement("div");
            body.className = "subcat-body";
            body.style.display = "none";

            header.addEventListener("click", () => toggleSubcat(sc.subcat_id, header, body));
            csaTreeEl.appendChild(header);
            csaTreeEl.appendChild(body);
        });
    } catch (err) {
        csaTreeEl.innerHTML = `<span class="hint">${err.message}</span>`;
    }
}

async function toggleSubcat(subcatId, header, body) {
    const isOpen = body.style.display !== "none";
    if (isOpen) { body.style.display = "none"; return; }
    body.style.display = "";

    if (csaSubjectsCache[subcatId]) return; // sudah pernah dimuat

    body.innerHTML = `<div class="hint" style="padding:6px 14px">Memuat...</div>`;
    try {
        const data = await fetchJSON(`/api/csa/subject?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&subcat=${subcatId}`);
        const subjects = data.data[1] || [];
        csaSubjectsCache[subcatId] = subjects;
        body.innerHTML = "";
        subjects.forEach(sub => {
            const item = document.createElement("div");
            item.className = "subject-item";
            item.textContent = sub.title;
            item.dataset.subId = sub.sub_id;
            item.addEventListener("click", () => selectSubject(sub.sub_id, sub.title, item));
            body.appendChild(item);
        });
    } catch (err) {
        body.innerHTML = `<div class="hint">${err.message}</div>`;
    }
}

function clearSidebarSelection() {
    document.querySelectorAll(".subject-item.selected").forEach(el => el.classList.remove("selected"));
    searchAllNode.classList.remove("selected");
}

function normalizeTitle(s) {
    return (s || "").replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim().toLowerCase();
}

async function selectSubject(subId, title, el) {
    clearSidebarSelection();
    el.classList.add("selected");
    subjectSearchBox.style.display = "none";
    subjectTitleEl.textContent = title;
    setStatus("status-subject", "Memuat daftar tabel...", "info");
    tablesTbody.innerHTML = "";
    currentRows = [];

    try {
        const [csaResult, simdasiResult] = await Promise.allSettled([
            fetchJSON(`/api/csa/tables?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&subject=${subId}`),
            fetchJSON(`/api/simdasi/tables?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&subject=${subId}`),
        ]);

        const items = csaResult.status === "fulfilled" ? (csaResult.value.items || []) : [];
        if (csaResult.status === "rejected") throw csaResult.reason;

        const simdasiItems = simdasiResult.status === "fulfilled" ? (simdasiResult.value.items || []) : [];
        const simdasiLookup = {};
        simdasiItems.forEach(s => { simdasiLookup[normalizeTitle(s.judul)] = s; });

        currentRows = items.map(it => {
            const tablesource = Number(it.tablesource);
            const row = { id: it.id, title: it.title, tablesource, updt_date: null, size: null, excel: null };
            if (tablesource === 3) {
                const match = simdasiLookup[normalizeTitle(it.title)];
                if (match) {
                    row.simdasi = { id_tabel: match.id_tabel, years: match.ketersediaan_tahun || [] };
                }
            }
            return row;
        });
        renderTableRows();
        setStatus("status-subject", `${currentRows.length} tabel ditemukan.`, "info");
        resolveStaticDetails();
    } catch (err) {
        setStatus("status-subject", err.message, "error");
    }
}

searchAllNode.addEventListener("click", () => {
    clearSidebarSelection();
    searchAllNode.classList.add("selected");
    subjectSearchBox.style.display = "flex";
    subjectTitleEl.textContent = "Cari Semua Tabel";
    tablesTbody.innerHTML = "";
    currentRows = [];
    setStatus("status-subject", "Ketik kata kunci lalu klik Cari.", "info");
});

document.getElementById("global-search-btn").addEventListener("click", async () => {
    const keyword = document.getElementById("global_keyword").value.trim();
    if (!keyword) { setStatus("status-subject", "Isi kata kunci dulu.", "warning"); return; }
    if (!domainSel.value) { setStatus("status-subject", "Pilih domain dulu.", "warning"); return; }

    setStatus("status-subject", "Mencari lintas semua tabel...", "info");
    tablesTbody.innerHTML = "";
    currentRows = [];

    try {
        let page = 1, allItems = [];
        while (true) {
            const data = await fetchJSON(`/api/statictable?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&keyword=${encodeURIComponent(keyword)}&page=${page}`);
            const info = data.data[0] || {};
            const items = data.data[1] || [];
            allItems = allItems.concat(items);
            if (page >= (info.pages || 1) || page >= 20) break;
            page++;
        }
        currentRows = allItems.map(it => ({
            id: it.table_id, title: it.title, tablesource: 1,
            updt_date: it.updt_date, size: it.size, excel: it.excel,
        }));
        renderTableRows();
        setStatus("status-subject", `${currentRows.length} tabel ditemukan untuk "${keyword}".`, "info");
    } catch (err) {
        setStatus("status-subject", err.message, "error");
    }
});

function dlCellContent(r, idx) {
    if (r.tablesource === 1) {
        return r.excel
            ? `<a class="dl-link" href="${r.excel}" target="_blank">Unduh</a>`
            : `<span class="hint">memuat...</span>`;
    }
    if (r.tablesource === 2) {
        return `<button class="view-data-btn" data-action="view-dynamic" data-idx="${idx}">Lihat Data</button>`;
    }
    if (r.tablesource === 3) {
        return r.simdasi
            ? `<button class="view-data-btn" data-action="view-simdasi" data-idx="${idx}">Lihat Data</button>`
            : `<span class="hint">SIMDASI (tidak dapat dibuka)</span>`;
    }
    return `<span class="hint">tidak diketahui</span>`;
}

function renderTableRows() {
    tablesTbody.innerHTML = currentRows.map((r, idx) => `
        <tr data-idx="${idx}">
            <td><input type="checkbox" class="row-check" data-idx="${idx}"></td>
            <td class="row-title">${r.title}</td>
            <td class="row-date">${r.updt_date || (r.tablesource === 1 ? "..." : "-")}</td>
            <td class="row-size">${r.size || (r.tablesource === 1 ? "..." : "-")}</td>
            <td class="row-dl">${dlCellContent(r, idx)}</td>
        </tr>
    `).join("");
}

tablesTbody.addEventListener("click", (e) => {
    const btn = e.target.closest(".view-data-btn");
    if (!btn) return;
    const row = currentRows[parseInt(btn.dataset.idx, 10)];
    if (btn.dataset.action === "view-dynamic") openDynamicDetail(row);
    else if (btn.dataset.action === "view-simdasi") openSimdasiDetail(row);
});

// ---------- Modal: Lihat Data (Dynamic Table / SIMDASI) ----------
const modalOverlay = document.getElementById("detail-modal");
const modalTitleEl = document.getElementById("detail-modal-title");
const modalControls = document.getElementById("detail-modal-controls");
const yearSelect = document.getElementById("detail-year-select");
const detailTable = document.getElementById("detail-table");
const exportButtons = document.querySelectorAll("#detail-export-buttons .btn-export");

document.getElementById("detail-modal-close").addEventListener("click", () => {
    modalOverlay.style.display = "none";
});

function renderDetailTable(columns, rows) {
    detailTable.querySelector("thead tr").innerHTML = columns.map(c => `<th>${c.label}</th>`).join("");
    detailTable.querySelector("tbody").innerHTML = rows.map(row => `
        <tr>${columns.map(c => `<td>${row[c.key] ?? ""}</td>`).join("")}</tr>
    `).join("");
}

async function openDynamicDetail(row) {
    modalOverlay.style.display = "flex";
    modalTitleEl.textContent = row.title;
    modalControls.style.display = "none";
    detailTable.querySelector("thead tr").innerHTML = "";
    detailTable.querySelector("tbody").innerHTML = "";
    setStatus("detail-modal-status", "Memuat data...", "info");
    exportButtons.forEach(a => { a.href = `/api/export/${a.dataset.fmt}`; });

    try {
        const data = await fetchJSON(`/api/csa/dynamic-data?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&id=${row.id}`);
        setStatus("detail-modal-status", `${data.count} baris ditemukan.`, "info");
        renderDetailTable([
            { key: "wilayah", label: "Wilayah" },
            { key: "variabel", label: "Variabel" },
            { key: "turvar", label: "Rincian" },
            { key: "tahun", label: "Tahun" },
            { key: "nilai", label: "Nilai" },
            { key: "unit", label: "Unit" },
        ], data.rows);
    } catch (err) {
        setStatus("detail-modal-status", err.message, "error");
    }
}

async function openSimdasiDetail(row) {
    modalOverlay.style.display = "flex";
    modalTitleEl.textContent = row.title;
    modalControls.style.display = "";
    exportButtons.forEach(a => { a.href = `/api/simdasi/export/${a.dataset.fmt}`; });

    const years = row.simdasi.years || [];
    fillSelect(yearSelect, years.map(y => ({ val: y, label: String(y) })), "val", "label", null);
    if (years.length) yearSelect.value = years[years.length - 1];

    async function loadYear() {
        detailTable.querySelector("thead tr").innerHTML = "";
        detailTable.querySelector("tbody").innerHTML = "";
        setStatus("detail-modal-status", "Memuat data...", "info");
        try {
            const data = await fetchJSON(`/api/simdasi/data?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&id_tabel=${encodeURIComponent(row.simdasi.id_tabel)}&tahun=${yearSelect.value}`);
            setStatus("detail-modal-status", `${data.count} baris ditemukan (tahun ${yearSelect.value}).`, "info");
            renderDetailTable([
                { key: "kategori", label: "Kategori" },
                { key: "variabel", label: "Variabel" },
                { key: "nilai", label: "Nilai" },
                { key: "satuan", label: "Satuan" },
            ], data.rows);
        } catch (err) {
            setStatus("detail-modal-status", err.message, "error");
        }
    }

    yearSelect.onchange = loadYear;
    if (years.length) {
        await loadYear();
    } else {
        setStatus("detail-modal-status", "Tidak ada tahun tersedia untuk tabel ini.", "warning");
    }
}

async function resolveStaticDetails() {
    const staticRows = currentRows.map((r, idx) => ({...r, idx})).filter(r => r.tablesource === 1);
    const concurrency = 5;
    let cursor = 0;

    async function worker() {
        while (cursor < staticRows.length) {
            const row = staticRows[cursor++];
            try {
                const detail = await fetchJSON(`/api/csa/table-detail?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&id=${row.id}`);
                currentRows[row.idx].excel = detail.excel;
                currentRows[row.idx].size = detail.size;
                currentRows[row.idx].updt_date = detail.updt_date;
                updateRowCells(row.idx);
            } catch (err) {
                currentRows[row.idx].excel = null;
                updateRowCells(row.idx);
            }
        }
    }
    await Promise.all(Array.from({length: concurrency}, worker));
}

function updateRowCells(idx) {
    const tr = tablesTbody.querySelector(`tr[data-idx="${idx}"]`);
    if (!tr) return;
    const r = currentRows[idx];
    tr.querySelector(".row-date").textContent = r.updt_date || "-";
    tr.querySelector(".row-size").textContent = r.size || "-";
    const dlCell = tr.querySelector(".row-dl");
    dlCell.innerHTML = r.excel ? `<a class="dl-link" href="${r.excel}" target="_blank">Unduh</a>` : `<span class="hint">tidak tersedia</span>`;
}

// ---------- Toolbar: filter, select all, copy titles, bulk download ----------
document.getElementById("filter-box").addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase();
    tablesTbody.querySelectorAll("tr").forEach(tr => {
        const title = tr.querySelector(".row-title").textContent.toLowerCase();
        tr.style.display = title.includes(q) ? "" : "none";
    });
});

function visibleRowIndexes() {
    return Array.from(tablesTbody.querySelectorAll("tr"))
        .filter(tr => tr.style.display !== "none")
        .map(tr => parseInt(tr.dataset.idx, 10));
}

document.getElementById("select-all-btn").addEventListener("click", () => {
    const idxs = visibleRowIndexes();
    const allChecked = idxs.every(i => tablesTbody.querySelector(`.row-check[data-idx="${i}"]`).checked);
    idxs.forEach(i => { tablesTbody.querySelector(`.row-check[data-idx="${i}"]`).checked = !allChecked; });
});

document.getElementById("check-all-header").addEventListener("change", (e) => {
    visibleRowIndexes().forEach(i => { tablesTbody.querySelector(`.row-check[data-idx="${i}"]`).checked = e.target.checked; });
});

document.getElementById("copy-titles-btn").addEventListener("click", async () => {
    const idxs = visibleRowIndexes();
    const titles = idxs.map(i => currentRows[i].title).join("\n");
    if (!titles) { setStatus("status-subject", "Tidak ada judul untuk disalin.", "warning"); return; }
    try {
        await navigator.clipboard.writeText(titles);
        setStatus("status-subject", `${idxs.length} judul disalin ke clipboard.`, "info");
    } catch (err) {
        setStatus("status-subject", "Gagal menyalin ke clipboard: " + err.message, "error");
    }
});

document.getElementById("download-selected-btn").addEventListener("click", async () => {
    const checked = Array.from(tablesTbody.querySelectorAll(".row-check:checked")).map(cb => parseInt(cb.dataset.idx, 10));
    if (!checked.length) { setStatus("status-subject", "Pilih minimal satu tabel dulu.", "warning"); return; }

    const files = checked.map(i => ({ id: currentRows[i].id, title: currentRows[i].title, excel: currentRows[i].excel }));
    setStatus("status-subject", `Menyiapkan ${files.length} file untuk diunduh...`, "info");

    try {
        const resp = await fetch("/api/csa/bulk-download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: apiKey(), domain: domainSel.value, files }),
        });
        if (!resp.ok) {
            const data = await resp.json();
            throw new Error(data.error || "Gagal membuat file zip.");
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "bps_tabel_terpilih.zip";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);

        const skipped = resp.headers.get("X-Skipped-Files");
        if (skipped) {
            const list = JSON.parse(skipped);
            setStatus("status-subject", `Selesai. ${list.length} file dilewati (tidak tersedia): ${list.join(", ")}`, "warning");
        } else {
            setStatus("status-subject", "Download zip berhasil.", "info");
        }
    } catch (err) {
        setStatus("status-subject", err.message, "error");
    }
});
