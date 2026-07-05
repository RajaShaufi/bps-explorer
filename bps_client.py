"""Klien untuk Web API BPS (webapi.bps.go.id) - Dynamic Data & Static Table."""

import time

import requests

BASE_URL = "https://webapi.bps.go.id/v1/api"
TIMEOUT = 30
RETRY_DELAYS = [0.5, 1.5, 3.0]  # backoff kalau WAF BPS ngeblok request secara acak


class BPSAPIError(Exception):
    pass


def data_parts(resp):
    """BPS normalnya balikin 'data': [info, items], tapi kalau hasilnya benar-benar
    kosong (data-availability: "list-not-available") 'data' malah jadi string kosong
    "" alih-alih array - indexing [0]/[1] langsung bakal IndexError. Fungsi ini
    selalu ngasih (info_dict, items_list) yang aman dipakai walau kosong."""
    data = resp.get("data")
    if isinstance(data, list) and len(data) >= 2:
        return (data[0] or {}), (data[1] or [])
    return {}, []


def _fetch_json(url, params):
    """GET dengan retry, karena WAF BPS kadang ngeblok request valid secara acak
    (respons HTML "LTM WAF Block" dengan status 200, bukan error HTTP asli)."""
    last_error = None
    for attempt, delay in enumerate([0] + RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        try:
            return resp.json()
        except ValueError:
            last_error = resp.text[:200]
            continue
    raise BPSAPIError(
        f"BPS API tidak merespons dengan data valid setelah beberapa percobaan "
        f"(kemungkinan rate-limit/WAF sementara) - coba lagi. Detail: {last_error}"
    )


def _get(path, params):
    data = _fetch_json(f"{BASE_URL}/{path}", params)
    if data.get("status") == "Error":
        raise BPSAPIError(f"BPS API error untuk request {path}: {data}")
    return data


def get_domains(key, dom_type="all", prov=None):
    params = {"type": dom_type, "key": key}
    if prov:
        params["prov"] = prov
    return _get("domain", params)


def _list(model, key, domain, lang="ind", page=None, **extra):
    params = {"model": model, "domain": domain, "lang": lang, "key": key}
    if page:
        params["page"] = page
    for k, v in extra.items():
        if v is not None and v != "":
            params[k] = v
    return _get("list/", params)


def get_subcat(key, domain, lang="ind", page=None):
    return _list("subcat", key, domain, lang, page)


def get_subject(key, domain, lang="ind", page=None, subcat=None):
    return _list("subject", key, domain, lang, page, subcat=subcat)


def get_variable(key, domain, lang="ind", page=None, subject=None, year=None, area=None, vervar=None):
    return _list("var", key, domain, lang, page, subject=subject, year=year, area=area, vervar=vervar)


def get_vervar(key, domain, lang="ind", page=None, var=None):
    return _list("vervar", key, domain, lang, page, var=var)


def get_turvar(key, domain, lang="ind", page=None, var=None, group=None, nopage=None):
    return _list("turvar", key, domain, lang, page, var=var, group=group, nopage=nopage)


def get_th(key, domain, lang="ind", page=None, var=None):
    return _list("th", key, domain, lang, page, var=var)


def get_turth(key, domain, lang="ind", page=None, var=None):
    return _list("turth", key, domain, lang, page, var=var)


def get_unit(key, domain, lang="ind", page=None):
    return _list("unit", key, domain, lang, page)


def get_data(key, domain, var, turvar=None, vervar=None, th=None, turth=None, lang="ind"):
    params = {"model": "data", "domain": domain, "var": var, "lang": lang, "key": key}
    if turvar:
        params["turvar"] = turvar
    if vervar:
        params["vervar"] = vervar
    if th:
        params["th"] = th
    if turth:
        params["turth"] = turth
    return _get("list", params)


def get_statictable_list(key, domain, lang="ind", page=None, month=None, year=None, keyword=None):
    return _list("statictable", key, domain, lang, page, month=month, year=year, keyword=keyword)


def get_statictable_detail(key, domain, table_id, lang="ind"):
    params = {"domain": domain, "model": "statictable", "lang": lang, "id": table_id, "key": key}
    return _fetch_json("https://webapi.bps.go.id/v1/view", params)


def get_tablestatistic_detail(key, domain, table_id, lang="ind"):
    """Detail of Table (Using CSA Subject) - id di sini adalah id ter-encode dari
    List of Table (Using CSA Subject), BUKAN table_id polos punya statictable lama."""
    params = {"domain": domain, "model": "tablestatistic", "lang": lang, "id": table_id, "key": key}
    return _fetch_json("https://webapi.bps.go.id/v1/api/view", params)


def paginate_all(list_fn, max_pages=300, **kwargs):
    """Panggil list_fn(page=N, **kwargs) berulang sampai semua halaman BPS habis.

    Endpoint list BPS defaultnya cuma ngasih ~10 item per halaman (field 'pages'
    di response), jadi tanpa ini dropdown cuma nampilin sebagian kecil data.
    """
    page = 1
    all_items = []
    while True:
        resp = list_fn(page=page, **kwargs)
        info, items = data_parts(resp)
        all_items.extend(items)
        total_pages = info.get("pages", 1) or 1
        if page >= total_pages or page >= max_pages:
            break
        page += 1
    return all_items


def get_subcatcsa(key, domain, page=None):
    params = {"model": "subcatcsa", "domain": domain, "key": key}
    if page:
        params["page"] = page
    return _get("list", params)


def get_subjectcsa(key, domain, subcat=None, page=None):
    params = {"model": "subjectcsa", "domain": domain, "key": key}
    if subcat:
        params["subcat"] = subcat
    if page:
        params["page"] = page
    return _get("list", params)


def get_tablestatistic(key, domain, subject=None, page=None, perpage=None):
    params = {"model": "tablestatistic", "domain": domain, "key": key}
    if subject:
        params["subject"] = subject
    if page:
        params["page"] = page
    if perpage:
        params["perpage"] = perpage
    return _get("list", params)


SIMDASI_BASE = "interoperabilitas/datasource/simdasi/id"


def get_simdasi_area_tables(key, wilayah):
    """List of SIMDASI Table Based on Area - TANPA filter id_subjek.

    Endpoint 24 (Based on Area AND Subject) selalu balikin halaman "LTM WAF
    Block" kalau id_subjek yang diminta nggak punya tabel SIMDASI sama sekali
    (mis. subjek IPTEK/Statistik Makroekonomi) - ini bug di backend BPS
    sendiri (server error yang ke-mask jadi WAF block), bukan rate limit.
    Endpoint 23 (tanpa filter subjek) selalu stabil, jadi filter subjeknya
    dipindah ke sisi kita (title-matching terhadap listing CSA)."""
    return _get(f"{SIMDASI_BASE}/23/", {"wilayah": wilayah, "key": key})


def get_simdasi_table_detail(key, wilayah, tahun, id_tabel):
    return _get(f"{SIMDASI_BASE}/25/", {"wilayah": wilayah, "tahun": tahun, "id_tabel": id_tabel, "key": key})


def _data_second_obj(response):
    """Sama seperti data_parts(), tapi buat endpoint SIMDASI yang elemen ke-2-nya
    berupa object (bukan list of items) - balikin dict kosong kalau malformed."""
    data = response.get("data")
    if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], dict):
        return data[1]
    return {}


def parse_simdasi_area_tables(response):
    inner = _data_second_obj(response)
    return inner.get("data", []) or []


def parse_simdasi_table_detail(response):
    """Ubah respons Detail of SIMDASI Table jadi (meta, rows rata kategori/variabel/nilai)."""
    inner = _data_second_obj(response)
    kolom = inner.get("kolom", {}) or {}
    data_rows = inner.get("data", []) or []

    rows = []
    for row in data_rows:
        kategori = row.get("label_raw") or row.get("label") or ""
        for col_key, val_obj in (row.get("variables") or {}).items():
            col_meta = kolom.get(col_key, {})
            rows.append({
                "kategori": kategori,
                "variabel": col_meta.get("nama_variabel", col_key),
                "satuan": col_meta.get("satuan", ""),
                "nilai": (val_obj or {}).get("value"),
            })

    meta = {
        "judul": inner.get("judul_tabel"),
        "tahun": inner.get("tahun_data"),
        "wilayah": inner.get("wilayah"),
    }
    return meta, rows


def parse_dynamic_data(response):
    """Ubah respons mentah 'data' jadi baris tabel rata (wilayah, variabel, tahun, nilai).

    BPS mengkodekan datacontent dengan key = concat(vervar_val, var_val, turvar_val, tahun_val, turtahun_val)
    tanpa padding, jadi kita rekonstruksi key yang sama dari kombinasi label yang dikembalikan.
    """
    var_list = response.get("var", []) or [{}]
    turvar_list = response.get("turvar", []) or [{"val": ""}]
    vervar_list = response.get("vervar", []) or []
    tahun_list = response.get("tahun", []) or []
    turtahun_list = response.get("turtahun", []) or [{"val": ""}]
    datacontent = response.get("datacontent", {}) or {}
    label_vervar = response.get("labelvervar", "Wilayah")

    rows = []
    for var in var_list:
        var_val = var.get("val", "")
        var_label = var.get("label", "")
        unit = var.get("unit", "")
        for vervar in vervar_list:
            for turvar in turvar_list:
                for tahun in tahun_list:
                    for turtahun in turtahun_list:
                        key = f"{vervar.get('val','')}{var_val}{turvar.get('val','')}{tahun.get('val','')}{turtahun.get('val','')}"
                        if key in datacontent:
                            rows.append({
                                "wilayah": vervar.get("label", ""),
                                "variabel": var_label,
                                "turvar": turvar.get("label", ""),
                                "tahun": tahun.get("label", ""),
                                "turtahun": turtahun.get("label", ""),
                                "unit": unit,
                                "nilai": datacontent[key],
                                "label_wilayah": label_vervar,
                            })
    return rows
