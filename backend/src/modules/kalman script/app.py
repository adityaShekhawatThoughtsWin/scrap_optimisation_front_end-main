import base64
import os
import sys
import threading
import webbrowser
from pathlib import Path
import queue
import random
import time
import logbook
from flask_cors import CORS

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file, Response, stream_with_context

from Future_Heats_Run import run_planner, _register, _unregister
from Kalman_Scrap_Chemistry_Prediction import read_csv_auto
from kf_runner import resolve_config_file, resolve_uploads_dir, run_kf_configuration

app = Flask(__name__)
CORS(app)

# Sentinel object — placed in the queue when the worker thread is done
_DONE = object()

uploaded_file_paths = {}
planner_file_paths = {}
last_kf_output_file = None


def get_base_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


BASE_DIR = get_base_path()
OUTPUT_FOLDER = BASE_DIR / "outputs"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


def solver_port():
    return int(os.environ.get("SOLVER_PORT", "5000"))


def cleanup_kf_outputs(output_folder):
    try:
        patterns = [
            "KF_Scarp_Chemistry_File_*.xlsx",
            "KF_*_Prediction_*.xlsx",
            "KF_*_Prediction_*.csv",
            "pred_vs_actual_*.png",
        ]
        deleted = []
        for pattern in patterns:
            for file_path in Path(output_folder).glob(pattern):
                try:
                    file_path.unlink()
                    deleted.append(file_path.name)
                except Exception as e:
                    print(f"Failed to delete {file_path.name}: {e}")
        print(f"KF output cleanup done. Deleted {len(deleted)} files")
    except Exception as e:
        print(f"KF cleanup failed: {e}")


def build_file_response(output_path: Path, return_format: str, success_message: str, extra=None):
    output_path = Path(output_path)

    if return_format == "file":
        if not output_path.exists():
            return jsonify({"success": False, "message": f"Output file not found: {output_path.name}"}), 404
        return send_file(
            output_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=output_path.name,
        )

    payload = {
        "success": True,
        "message": success_message,
        "output_filename": output_path.name if output_path.exists() else None,
        "output_path": str(output_path) if output_path.exists() else None,
    }
    if extra:
        payload.update(extra)

    if return_format in ("both", "json") and output_path.exists():
        if return_format == "both":
            with open(output_path, "rb") as f:
                file_b64 = base64.b64encode(f.read()).decode("utf-8")
            payload["output_file"] = {
                "filename": output_path.name,
                "content_base64": file_b64,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }

    return jsonify(payload)


def count_heats_in_heat_query_all(file_path: Path) -> int:
    """Derive numb_heats_pass from the uploaded HeatQuery_All file."""
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = read_csv_auto(file_path)
    else:
        df = pd.read_excel(file_path)

    if df.empty:
        return 0
    if "HeatID" in df.columns:
        return int(df["HeatID"].dropna().nunique())
    return len(df)


def read_tabular_upload(file_storage, label: str) -> pd.DataFrame:
    if file_storage is None or not file_storage.filename:
        raise ValueError(f"Missing required file: {label}")

    suffix = Path(file_storage.filename).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_storage)
    if suffix in (".xlsx", ".xls", ".xlsm"):
        return pd.read_excel(file_storage)
    raise ValueError(f"{label}: unsupported file type '{suffix}' (use .csv or .xlsx)")


def open_browser():
    webbrowser.open(f"http://127.0.0.1:{solver_port()}")


def solver_port() -> int:
    return int(os.environ.get("SOLVER_PORT", "5000"))


@app.route("/health")
def health():
    return jsonify({"status": "UP"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """Upload HeatQuery_All + HeatQuery_Chemistry for KF /run."""
    global uploaded_file_paths

    file1 = request.files.get("file1")
    file2 = request.files.get("file2")

    if not file1 or not file2:
        return jsonify({"success": False, "message": "Please upload both files"}), 400

    f1_name = file1.filename
    f2_name = file2.filename

    if f1_name == f2_name:
        return jsonify({"success": False, "message": "Same file uploaded twice."}), 400

    if not (
        (f1_name.startswith("HeatQuery_All_") and f2_name.startswith("HeatQuery_Chemistry_"))
        or (f2_name.startswith("HeatQuery_All_") and f1_name.startswith("HeatQuery_Chemistry_"))
    ):
        return jsonify({
            "success": False,
            "message": "Upload HeatQuery_All_* and HeatQuery_Chemistry_* files.",
        }), 400

    uploads_dir = resolve_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    path1 = uploads_dir / f1_name
    path2 = uploads_dir / f2_name
    file1.save(path1)
    file2.save(path2)

    if f1_name.startswith("HeatQuery_All_"):
        all_file, chem_file = path1, path2
    else:
        all_file, chem_file = path2, path1

    uploaded_file_paths = {"all_file": all_file, "chem_file": chem_file}

    return jsonify({
        "success": True,
        "filename": f"{all_file.name}\n{chem_file.name}",
    })


@app.route("/run", methods=["POST"])
def run_kf():
    """
    KF-only endpoint. Runs Kalman configuration (single chem or ALL).
    Returns KF_Scarp_Chemistry_File_{heat_id}.xlsx — does NOT call planner.
    """
    global last_kf_output_file

    cleanup_kf_outputs(OUTPUT_FOLDER)

    data = request.json or {}
    target_chem_ui = data.get("target_chem", "Cu")
    return_format = data.get("return_format", "both")

    if not uploaded_file_paths.get("all_file"):
        return jsonify({"success": False, "message": "Upload HeatQuery files first via POST /upload"}), 400

    input_file = uploaded_file_paths["all_file"]
    input_ext = input_file.suffix.lower()
    if input_ext not in (".xlsx", ".csv"):
        return jsonify({"success": False, "message": "Only .xlsx or .csv input supported"}), 400

    try:
        numb_heats_pass = count_heats_in_heat_query_all(input_file)
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to read HeatQuery_All file: {e}"}), 400

    if numb_heats_pass == 0:
        return jsonify({"success": False, "message": "HeatQuery_All file contains no heats"}), 400

    try:
        success, message, output_file = run_kf_configuration(
            input_file=input_file,
            chemistry_file_path=uploaded_file_paths["chem_file"],
            output_dir=OUTPUT_FOLDER,
            target_chem_ui=target_chem_ui,
            numb_heats_pass=numb_heats_pass,
            input_ext=input_ext,
        )
    except Exception as e:
        return jsonify({"success": False, "phase": "kalman", "message": str(e)}), 500

    if not success:
        return jsonify({"success": False, "phase": "kalman", "message": message}), 422

    if output_file is None or not Path(output_file).exists():
        return jsonify({
            "success": False,
            "phase": "kalman",
            "message": "Kalman completed but output workbook was not created.",
        }), 500

    last_kf_output_file = Path(output_file)

    return build_file_response(
        last_kf_output_file,
        return_format,
        message,
        extra={"target_chem": target_chem_ui, "numb_heats_pass": numb_heats_pass},
    )


@app.route("/planner/upload", methods=["POST"])
def upload_planner_files():
    """
    Upload inputs for POST /planner (optional two-step flow).
    Files: heat_query, scrap_inventory, kf_file (optional if /run was done), grade_spec (optional).
    """
    global planner_file_paths

    uploads_dir = resolve_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    saved = {}

    for field in ("heat_query", "scrap_inventory", "kf_file", "grade_spec"):
        f = request.files.get(field)
        if f and f.filename:
            dest = uploads_dir / f.filename
            f.save(dest)
            saved[field] = str(dest)

    if "heat_query" not in saved:
        return jsonify({"success": False, "message": "heat_query file is required"}), 400
    if "scrap_inventory" not in saved:
        return jsonify({"success": False, "message": "scrap_inventory file is required"}), 400

    planner_file_paths = saved

    return jsonify({"success": True, "files": saved})


@app.route("/planner", methods=["POST"])
def run_planner_api():
    """
    Independent planner endpoint. Does NOT run Kalman.
    Accepts multipart files or JSON with return_format; uses /planner/upload cache when files omitted.
    """
    global planner_file_paths, last_kf_output_file

    return_format = "both"
    if request.is_json:
        return_format = (request.json or {}).get("return_format", "both")
    elif request.form.get("return_format"):
        return_format = request.form.get("return_format")

    try:
        if request.files:
            heat_query_df = read_tabular_upload(request.files.get("heat_query"), "heat_query")
            scrap_df = read_tabular_upload(request.files.get("scrap_inventory"), "scrap_inventory")

            grade_file = request.files.get("grade_spec")
            if grade_file and grade_file.filename:
                grade_spec_df = read_tabular_upload(grade_file, "grade_spec")
                if grade_spec_df.empty:
                    return jsonify({"success": False, "message": "Uploaded grade file is empty"}), 400
            else:
                grade_path = resolve_config_file("Grade_Specifications.xlsx")
                if not grade_path.exists():
                    return jsonify({"success": False, "message": "grade_spec file required or missing in Uploads/"}), 400
                grade_spec_df = pd.read_excel(grade_path)

            kf_upload = request.files.get("kf_file")
            if kf_upload and kf_upload.filename:
                kf_dest = OUTPUT_FOLDER / kf_upload.filename
                kf_upload.save(kf_dest)
                kf_source = kf_dest
            elif last_kf_output_file and Path(last_kf_output_file).exists():
                kf_source = last_kf_output_file
            else:
                return jsonify({
                    "success": False,
                    "message": "kf_file required (upload or run POST /run first in same session)",
                }), 400
        else:
            if not planner_file_paths.get("heat_query") or not planner_file_paths.get("scrap_inventory"):
                return jsonify({
                    "success": False,
                    "message": "Upload planner files via POST /planner/upload or send multipart to POST /planner",
                }), 400

            heat_path = Path(planner_file_paths["heat_query"])
            scrap_path = Path(planner_file_paths["scrap_inventory"])

            heat_query_df = pd.read_csv(heat_path) if heat_path.suffix.lower() == ".csv" else pd.read_excel(heat_path)
            scrap_df = pd.read_excel(scrap_path)

            if planner_file_paths.get("grade_spec"):
                grade_path = Path(planner_file_paths["grade_spec"])
                grade_spec_df = pd.read_csv(grade_path) if grade_path.suffix.lower() == ".csv" else pd.read_excel(grade_path)
                if grade_spec_df.empty:
                    return jsonify({"success": False, "message": "Uploaded grade file is empty"}), 400
            else:
                grade_path = resolve_config_file("Grade_Specifications.xlsx")
                if not grade_path.exists():
                    return jsonify({"success": False, "message": "grade_spec missing"}), 400
                grade_spec_df = pd.read_excel(grade_path)

            if planner_file_paths.get("kf_file"):
                kf_source = Path(planner_file_paths["kf_file"])
            elif last_kf_output_file and Path(last_kf_output_file).exists():
                kf_source = last_kf_output_file
            else:
                return jsonify({"success": False, "message": "kf_file missing"}), 400

        output_file, _ = run_planner(
            heat_query=heat_query_df,
            scrap_availability_df=scrap_df,
            grade_spec_df=grade_spec_df,
            kf_source=kf_source,
            output_dir=OUTPUT_FOLDER,
        )

    except Exception as e:
        return jsonify({"success": False, "phase": "planner", "message": str(e)}), 500

    return build_file_response(
        Path(output_file),
        return_format,
        "Planner optimization completed",
    )



# ── Custom logbook handler ────────────────────────────────────────────────────

class SSEHandler(logbook.Handler):
    """
    Captures every logbook record emitted inside its scope and puts a
    formatted string into a queue.Queue so the SSE generator can stream it.
    """

    FORMAT = "[{level}] {channel}: {message}"

    def __init__(self, log_queue: queue.Queue, level=logbook.DEBUG):
        super().__init__(level=level, bubble=True)
        self.log_queue = log_queue

    def emit(self, record: logbook.LogRecord):
        line = self.FORMAT.format(
            level=record.level_name,
            channel=record.channel,
            message=record.message,
        )
        self.log_queue.put(line)


# ── Simulated worker ──────────────────────────────────────────────────────────

def run_pipeline(log_queue: queue.Queue):
    """
    Runs in a background thread and performs a series of realistic operations,
    logging every step via logbook. Logs are captured by SSEHandler and pushed
    into the queue for the SSE generator to forward to the client.
    """
    handler = SSEHandler(log_queue)

    with handler.applicationbound():
        boot  = logbook.Logger("Boot")
        db    = logbook.Logger("Database")
        cache = logbook.Logger("Cache")
        api   = logbook.Logger("API")
        job   = logbook.Logger("Scheduler")

        # ── Boot sequence
        boot.info("Starting application server")
        time.sleep(0.3)
        boot.debug("Loading config from /etc/app/config.yaml")
        time.sleep(0.2)
        for i in range(5):
            boot.debug(f"Initializing module {i+1}/5")
            time.sleep(5)
        boot.info("Environment: production  |  Port: 8080  |  Workers: 4")
        time.sleep(0.15)

    # Signal the generator that we're done
    log_queue.put(_DONE)


# ── /fetchTerminalLogs SSE endpoint ──────────────────────────────────────────

@app.route("/fetchTerminalLogs")
def fetch_terminal_logs():
    """
    SSE endpoint. Registers a per-client queue, streams log lines pushed by
    /generateLogs, and unregisters the queue when the client disconnects.
    """
    client_queue = _register()

    def generate():
        try:
            while True:
                try:
                    item = client_queue.get(timeout=5.0)
                except queue.Empty:
                    # Nothing in the queue — close the stream
                    yield "data: [DONE] No logs available\n\n"
                    break
                if item is _DONE:
                    yield "data: [DONE] Stream ended\n\n"
                    break
                yield f"data: {item}\n\n"
        finally:
            _unregister(client_queue)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )



if __name__ == "__main__":
    headless = os.environ.get("SOLVER_HEADLESS", "").lower() in ("1", "true", "yes")
    # if not headless:
    #     threading.Timer(1.5, open_browser).start()
    app.run(host="127.0.0.1", port=solver_port(), debug=False)
