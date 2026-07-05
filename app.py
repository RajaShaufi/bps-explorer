import csv
import io
import json

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
        data = bps.get_subcat(key, domain=request.args["domain"], page=request.args.get("page"))
        return jsonify(data)
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil subject category: {e}"}), 500


@app.route("/api/subject")
def api_subject():
    try:
        key = _key()
        data = bps.get_subject(key, domain=request.args["domain"],
                                subcat=request.args.get("subcat"), page=request.args.get("page"))
        return jsonify(data)
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil subject: {e}"}), 500


@app.route("/api/variable")
def api_variable():
    try:
        key = _key()
        data = bps.get_variable(key, domain=request.args["domain"],
                                 subject=request.args.get("subject"), page=request.args.get("page"))
        return jsonify(data)
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil variable: {e}"}), 500


@app.route("/api/vervar")
def api_vervar():
    try:
        key = _key()
        data = bps.get_vervar(key, domain=request.args["domain"], var=request.args.get("var"))
        return jsonify(data)
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil vervar: {e}"}), 500


@app.route("/api/turvar")
def api_turvar():
    try:
        key = _key()
        data = bps.get_turvar(key, domain=request.args["domain"], var=request.args.get("var"))
        return jsonify(data)
    except BPSAPIError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil turvar: {e}"}), 500


@app.route("/api/th")
def api_th():
    try:
        key = _key()
        data = bps.get_th(key, domain=request.args["domain"], var=request.args.get("var"))
        return jsonify(data)
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
    app.run(debug=True, port=5001)
