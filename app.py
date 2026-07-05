import csv
import io
import json
import re
import zipfile

import requests
from flask import Flask, render_template, request, jsonify, send_file

import bps_client as bps
from bps_client import BPSAPIError

app = Flask(__name__)

_last_result = {"rows": []}


def _key():
    key = request.args.get("key") or (request.get_json(silent=True) or {}).get("key")
    if not key:
        raise BPSAPIError("API key BPS wajib diisi.")
    return key


def _all_items_response(items):
    """Bungkus list hasil paginate_all supaya bentuknya tetap kompatibel dengan
    kontrak {"data": [info, items]} yang dipakai frontend."""
    return {"data": [{"page": 1, "pages": 1, "total": len(items)}, items]}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/domains")
def api_domains():
    try:
        key = _key()
        dom_type = request.args.get("type", "all")
        prov = request.args.get("prov")
        data = bps.get_domains(key, dom_type=dom_type, prov=prov)
        return jsonify(data)
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil domain: {e}"}), 500


@app.route("/api/subcat")
def api_subcat():
    try:
        key = _key()
        items = bps.paginate_all(bps.get_subcat, key=key, domain=request.args["domain"])
        return jsonify(_all_items_response(items))
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil subject category: {e}"}), 500


@app.route("/api/subject")
def api_subject():
    try:
        key = _key()
        items = bps.paginate_all(bps.get_subject, key=key, domain=request.args["domain"],
                                  subcat=request.args.get("subcat"))
        return jsonify(_all_items_response(items))
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil subject: {e}"}), 500


@app.route("/api/variable")
def api_variable():
    try:
        key = _key()
        items = bps.paginate_all(bps.get_variable, key=key, domain=request.args["domain"],
                                  subject=request.args.get("subject"))
        return jsonify(_all_items_response(items))
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil variable: {e}"}), 500


@app.route("/api/vervar")
def api_vervar():
    try:
        key = _key()
        items = bps.paginate_all(bps.get_vervar, key=key, domain=request.args["domain"],
                                  var=request.args.get("var"))
        return jsonify(_all_items_response(items))
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil vervar: {e}"}), 500


@app.route("/api/turvar")
def api_turvar():
    try:
        key = _key()
        items = bps.paginate_all(bps.get_turvar, key=key, domain=request.args["domain"],
                                  var=request.args.get("var"))
        return jsonify(_all_items_response(items))
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil turvar: {e}"}), 500


@app.route("/api/th")
def api_th():
    try:
        key = _key()
        items = bps.paginate_all(bps.get_th, key=key, domain=request.args["domain"],
                                  var=request.args.get("var"))
        return jsonify(_all_items_response(items))
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil periode: {e}"}), 500


@app.route("/api/data", methods=["POST"])
def api_data():
    payload = request.get_json(force=True)
    try:
        key = payload.get("key")
        if not key:
            return jsonify({"error": "API key BPS wajib diisi."}), 400

        response = bps.get_data(
            key,
            domain=payload["domain"],
            var=payload["var"],
            turvar=payload.get("turvar"),
            vervar=payload.get("vervar"),
            th=payload.get("th"),
            turth=payload.get("turth"),
        )
        rows = bps.parse_dynamic_data(response)
        _last_result["rows"] = rows
        return jsonify({"rows": rows, "count": len(rows)})
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data: {e}"}), 500


@app.route("/api/statictable")
def api_statictable():
    try:
        key = _key()
        data = bps.get_statictable_list(
            key,
            domain=request.args["domain"],
            page=request.args.get("page"),
            month=request.args.get("month"),
            year=request.args.get("year"),
            keyword=request.args.get("keyword"),
        )
        return jsonify(data)
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil static table: {e}"}), 500


@app.route("/api/csa/subcat")
def api_csa_subcat():
    try:
        key = _key()
        items = bps.paginate_all(bps.get_subcatcsa, key=key, domain=request.args["domain"])
        return jsonify(_all_items_response(items))
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil CSA subject category: {e}"}), 500


@app.route("/api/csa/subject")
def api_csa_subject():
    try:
        key = _key()
        items = bps.paginate_all(bps.get_subjectcsa, key=key, domain=request.args["domain"],
                                  subcat=request.args.get("subcat"))
        return jsonify(_all_items_response(items))
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil CSA subject: {e}"}), 500


@app.route("/api/csa/tables")
def api_csa_tables():
    try:
        key = _key()
        domain = request.args["domain"]
        subject = request.args.get("subject")
        items = []
        page = 1
        while True:
            resp = bps.get_tablestatistic(key, domain=domain, subject=subject, page=page, perpage=100)
            info = resp.get("data", [{}, []])[0] or {}
            page_items = resp.get("data", [{}, []])[1] or []
            items.extend(page_items)
            total_pages = info.get("pages", 1) or 1
            if page >= total_pages or page >= 50:
                break
            page += 1
        return jsonify({"items": items})
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil daftar tabel: {e}"}), 500


@app.route("/api/csa/table-detail")
def api_csa_table_detail():
    """Resolusi link download & tanggal update satu tabel lewat endpoint
    Detail of Table (Using CSA Subject) - id yang dipakai adalah id ter-encode
    dari listing CSA, bukan table_id polos punya statictable lama."""
    try:
        key = _key()
        domain = request.args["domain"]
        table_id = request.args["id"]
        detail = bps.get_tablestatistic_detail(key, domain=domain, table_id=table_id)
        d = detail.get("data", {}) or {}
        return jsonify({
            "table_id": table_id,
            "excel": d.get("excel"),
            "size": d.get("size"),
            "updt_date": d.get("updt_date"),
        })
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil detail tabel {request.args.get('id', '')}: {e}"}), 500


def _guess_extension(resp):
    """BPS nyajiin file lewat script download.php?f=... jadi ekstensi harus
    ditebak dari header respons, bukan dari path URL-nya."""
    cd = resp.headers.get("Content-Disposition", "")
    m = re.search(r'filename="?([^";]+)"?', cd)
    if m and "." in m.group(1):
        return m.group(1).rsplit(".", 1)[-1][:5]

    content_type = resp.headers.get("Content-Type", "")
    type_map = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "application/vnd.ms-excel": "xls",
        "application/pdf": "pdf",
        "text/csv": "csv",
    }
    for mime, ext in type_map.items():
        if mime in content_type:
            return ext
    return "xls"


@app.route("/api/csa/bulk-download", methods=["POST"])
def api_csa_bulk_download():
    """Unduh beberapa tabel Excel sekaligus dan bundel jadi satu file .zip."""
    payload = request.get_json(force=True)
    key = payload.get("key")
    domain = payload.get("domain")
    files = payload.get("files", [])  # [{id, title, excel}]

    if not key or not domain:
        return jsonify({"error": "API key dan domain wajib diisi."}), 400
    if not files:
        return jsonify({"error": "Tidak ada tabel yang dipilih."}), 400

    zip_buf = io.BytesIO()
    skipped = []
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            excel_url = f.get("excel")
            title = (f.get("title") or f"table_{f.get('id')}").strip()
            safe_name = "".join(c for c in title if c.isalnum() or c in " ._-")[:100] or f"table_{f.get('id')}"

            if not excel_url:
                # coba resolve dulu kalau belum ada link excel-nya
                try:
                    detail = bps.get_tablestatistic_detail(key, domain=domain, table_id=f.get("id"))
                    excel_url = (detail.get("data") or {}).get("excel")
                except Exception:
                    excel_url = None

            if not excel_url:
                skipped.append(title)
                continue

            try:
                file_resp = requests.get(excel_url, timeout=60)
                file_resp.raise_for_status()
                ext = _guess_extension(file_resp)
                zf.writestr(f"{safe_name}.{ext}", file_resp.content)
            except Exception:
                skipped.append(title)

    zip_buf.seek(0)
    resp = send_file(zip_buf, mimetype="application/zip", as_attachment=True,
                      download_name="bps_tabel_terpilih.zip")
    if skipped:
        resp.headers["X-Skipped-Files"] = json.dumps(skipped, ensure_ascii=False)
    return resp


@app.route("/api/export/<fmt>")
def api_export(fmt):
    rows = _last_result.get("rows", [])
    if not rows:
        return jsonify({"error": "Belum ada data untuk diekspor."}), 400

    fieldnames = list(rows[0].keys())

    if fmt == "json":
        buf = io.BytesIO(json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8"))
        return send_file(buf, mimetype="application/json", as_attachment=True,
                          download_name="bps_data.json")

    if fmt == "csv":
        text_buf = io.StringIO()
        writer = csv.DictWriter(text_buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        buf = io.BytesIO(text_buf.getvalue().encode("utf-8-sig"))
        return send_file(buf, mimetype="text/csv", as_attachment=True,
                          download_name="bps_data.csv")

    if fmt == "xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "BPS Data"
        ws.append(fieldnames)
        for r in rows:
            ws.append([r.get(f) for f in fieldnames])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          as_attachment=True, download_name="bps_data.xlsx")

    return jsonify({"error": "Format tidak didukung. Gunakan csv, json, atau xlsx."}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5002)
