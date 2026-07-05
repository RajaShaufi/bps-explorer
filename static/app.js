function apiKey() {
    return document.getElementById("api_key").value.trim();
}

function setStatus(elId, msg, type) {
    const el = document.getElementById(elId);
    el.textContent = msg || "";
    el.className = "status " + (type || "");
}

async function fetchJSON(url) {
    const resp = await fetch(url);
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

// ---------- Tabs ----------
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
        btn.classList.add("active");
        document.getElementById("tab-" + btn.dataset.tab).style.display = "";
    });
});

// ---------- Domain loading ----------
const domainTypeSel = document.getElementById("domain_type");
const provPickerWrap = document.getElementById("prov_picker_wrap");
const provPicker = document.getElementById("prov_picker");
const domainSel = document.getElementById("domain");
const stDomainSel = document.getElementById("st_domain");

async function loadProvinces() {
    const data = await fetchJSON(`/api/domains?key=${encodeURIComponent(apiKey())}&type=prov`);
    const list = data.data[1] || [];
    fillSelect(provPicker, list, "domain_id", "domain_name", null);
}

async function loadDomains() {
    if (!apiKey()) {
        setStatus("status-dynamic", "Isi API key BPS dulu.", "warning");
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
        fillSelect(stDomainSel, list, "domain_id", "domain_name", null);
        setStatus("status-dynamic", `${list.length} domain dimuat.`, "info");
        await loadSubcat();
    } catch (err) {
        setStatus("status-dynamic", err.message, "error");
    }
}

domainTypeSel.addEventListener("change", loadDomains);
provPicker.addEventListener("change", loadDomains);
domainSel.addEventListener("change", loadSubcat);

// ---------- Subject cascade ----------
const subcatSel = document.getElementById("subcat");
const subjectSel = document.getElementById("subject");
const variableSel = document.getElementById("variable");
const vervarSel = document.getElementById("vervar");
const turvarSel = document.getElementById("turvar");
const tahunSel = document.getElementById("tahun");

async function loadSubcat() {
    if (!domainSel.value) return;
    try {
        const data = await fetchJSON(`/api/subcat?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}`);
        const list = data.data[1] || [];
        fillSelect(subcatSel, list, "subcat_id", "title", "-- Semua --");
        await loadSubject();
    } catch (err) {
        setStatus("status-dynamic", err.message, "error");
    }
}

async function loadSubject() {
    if (!domainSel.value) return;
    try {
        let url = `/api/subject?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}`;
        if (subcatSel.value) url += `&subcat=${subcatSel.value}`;
        const data = await fetchJSON(url);
        const list = data.data[1] || [];
        fillSelect(subjectSel, list, "sub_id", "title", "-- Pilih Subjek --");
    } catch (err) {
        setStatus("status-dynamic", err.message, "error");
    }
}

async function loadVariable() {
    if (!domainSel.value || !subjectSel.value) return;
    try {
        const url = `/api/variable?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&subject=${subjectSel.value}`;
        const data = await fetchJSON(url);
        const list = data.data[1] || [];
        fillSelect(variableSel, list, "var_id", "title", "-- Pilih Variabel --");
    } catch (err) {
        setStatus("status-dynamic", err.message, "error");
    }
}

async function loadVariableDetails() {
    if (!domainSel.value || !variableSel.value) return;
    try {
        const [vervarData, turvarData, thData] = await Promise.all([
            fetchJSON(`/api/vervar?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&var=${variableSel.value}`),
            fetchJSON(`/api/turvar?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&var=${variableSel.value}`),
            fetchJSON(`/api/th?key=${encodeURIComponent(apiKey())}&domain=${domainSel.value}&var=${variableSel.value}`),
        ]);
        fillSelect(vervarSel, vervarData.data[1] || [], "vervar_id", "vervar", null);
        fillSelect(turvarSel, turvarData.data[1] || [], "turvar_id", "turvar", null);
        fillSelect(tahunSel, thData.data[1] || [], "th_id", "th", null);
    } catch (err) {
        setStatus("status-dynamic", err.message, "error");
    }
}

subcatSel.addEventListener("change", loadSubject);
subjectSel.addEventListener("change", loadVariable);
variableSel.addEventListener("change", loadVariableDetails);

// ---------- Fetch dynamic data ----------
document.getElementById("fetch-data-btn").addEventListener("click", async () => {
    if (!apiKey()) { setStatus("status-dynamic", "Isi API key BPS dulu.", "warning"); return; }
    if (!domainSel.value || !variableSel.value) {
        setStatus("status-dynamic", "Pilih domain dan variabel dulu.", "warning");
        return;
    }

    setStatus("status-dynamic", "Mengambil data...", "info");

    const payload = {
        key: apiKey(),
        domain: domainSel.value,
        var: variableSel.value,
        vervar: selectedValues(vervarSel).join(","),
        turvar: selectedValues(turvarSel).join(","),
        th: selectedValues(tahunSel).join(","),
    };

    try {
        const resp = await fetch("/api/data", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || "Gagal mengambil data.");

        setStatus("status-dynamic", `${data.count} baris ditemukan.`, "info");
        const tbody = document.querySelector("#data-table tbody");
        tbody.innerHTML = data.rows.map(r => `
            <tr>
                <td>${r.wilayah}</td>
                <td>${r.variabel}</td>
                <td>${r.turvar}</td>
                <td>${r.tahun}</td>
                <td>${r.nilai}</td>
                <td>${r.unit}</td>
            </tr>
        `).join("");
        document.getElementById("result-count").textContent = data.count;
        document.getElementById("results-dynamic").style.display = "";
    } catch (err) {
        setStatus("status-dynamic", err.message, "error");
    }
});

// ---------- Static table ----------
document.getElementById("fetch-static-btn").addEventListener("click", async () => {
    if (!apiKey()) { setStatus("status-static", "Isi API key BPS dulu.", "warning"); return; }
    if (!stDomainSel.value) { setStatus("status-static", "Pilih domain dulu.", "warning"); return; }

    setStatus("status-static", "Mencari static table...", "info");

    let url = `/api/statictable?key=${encodeURIComponent(apiKey())}&domain=${stDomainSel.value}`;
    const keyword = document.getElementById("st_keyword").value;
    const year = document.getElementById("st_year").value;
    if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;
    if (year) url += `&year=${encodeURIComponent(year)}`;

    try {
        const data = await fetchJSON(url);
        const list = data.data[1] || [];
        setStatus("status-static", `${list.length} tabel ditemukan.`, "info");
        const tbody = document.querySelector("#static-table tbody");
        tbody.innerHTML = list.map(t => `
            <tr>
                <td>${t.title}</td>
                <td>${t.size || ""}</td>
                <td>${t.updt_date || ""}</td>
                <td>${t.excel ? `<a href="${t.excel}" target="_blank">Download</a>` : ""}</td>
            </tr>
        `).join("");
        document.getElementById("results-static").style.display = "";
    } catch (err) {
        setStatus("status-static", err.message, "error");
    }
});

// ---------- Init ----------
document.getElementById("api_key").addEventListener("change", loadDomains);
