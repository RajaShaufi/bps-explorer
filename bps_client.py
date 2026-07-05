"""Klien untuk Web API BPS (webapi.bps.go.id) - Dynamic Data & Static Table."""

import requests

BASE_URL = "https://webapi.bps.go.id/v1/api"
TIMEOUT = 30


class BPSAPIError(Exception):
    pass


def _get(path, params):
    resp = requests.get(f"{BASE_URL}/{path}", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
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
    resp = requests.get("https://webapi.bps.go.id/v1/view", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_tablestatistic_detail(key, domain, table_id, lang="ind"):
    """Detail of Table (Using CSA Subject) - id di sini adalah id ter-encode dari
    List of Table (Using CSA Subject), BUKAN table_id polos punya statictable lama."""
    params = {"domain": domain, "model": "tablestatistic", "lang": lang, "id": table_id, "key": key}
    resp = requests.get("https://webapi.bps.go.id/v1/api/view", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def paginate_all(list_fn, max_pages=300, **kwargs):
    """Panggil list_fn(page=N, **kwargs) berulang sampai semua halaman BPS habis.

    Endpoint list BPS defaultnya cuma ngasih ~10 item per halaman (field 'pages'
    di response), jadi tanpa ini dropdown cuma nampilin sebagian kecil data.
    """
    page = 1
    all_items = []
    while True:
        resp = list_fn(page=page, **kwargs)
        info = resp.get("data", [{}, []])[0] or {}
        items = resp.get("data", [{}, []])[1] or []
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
