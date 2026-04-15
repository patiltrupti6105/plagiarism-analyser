"""
app.py — PlagiaGuard Flask Application Entry Point

Routes:
  GET  /                  → Landing / upload page
  POST /analyze           → Run plagiarism analysis
  GET  /download/<fname>  → Download generated PDF report
"""

import os
import uuid
from flask import Flask, request, jsonify, render_template, send_file, abort
from werkzeug.utils import secure_filename

from backend.parser import extract_text
from backend.analyzer import analyze
from backend.report_generator import generate_report


# ─────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)

UPLOAD_FOLDER  = os.path.join(os.path.dirname(__file__), "uploads")
REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), "reports")
ALLOWED_EXTS   = {"pdf", "docx", "txt"}
MAX_FILE_SIZE  = 10 * 1024 * 1024  # 10 MB

app.config["UPLOAD_FOLDER"]  = UPLOAD_FOLDER
app.config["REPORTS_FOLDER"] = REPORTS_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER,  exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS


def save_upload(file_obj) -> tuple[str, str]:
    """Save uploaded file with a UUID prefix. Returns (path, original_name)."""
    original_name = secure_filename(file_obj.filename)
    unique_name   = f"{uuid.uuid4().hex}_{original_name}"
    filepath      = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file_obj.save(filepath)
    return filepath, original_name


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """Render the main UI page."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_documents():
    """
    Expects multipart/form-data with:
      - source_file     : the document to check (required)
      - reference_files : one or more reference documents (at least 1 required)

    Returns JSON analysis result.
    """
    # ── Validate source file ──
    if "source_file" not in request.files:
        return jsonify({"error": "No source file provided."}), 400

    source_file = request.files["source_file"]
    if not source_file.filename or not allowed_file(source_file.filename):
        return jsonify({"error": "Source file must be PDF, DOCX, or TXT."}), 400

    # ── Validate reference files ──
    ref_files = request.files.getlist("reference_files")
    if not ref_files or all(f.filename == "" for f in ref_files):
        return jsonify({"error": "At least one reference file is required."}), 400

    saved_paths = []

    try:
        # Save & extract source
        src_path, src_name = save_upload(source_file)
        saved_paths.append(src_path)
        source_text = extract_text(src_path)

        if len(source_text.strip()) < 50:
            return jsonify({"error": "Source document appears to be empty or too short."}), 400

        # Save & extract references
        reference_texts = []
        for ref_file in ref_files:
            if ref_file.filename and allowed_file(ref_file.filename):
                ref_path, _ = save_upload(ref_file)
                saved_paths.append(ref_path)
                ref_text = extract_text(ref_path)
                if ref_text.strip():
                    reference_texts.append(ref_text)

        if not reference_texts:
            return jsonify({"error": "No valid reference documents could be parsed."}), 400

        # ── Run Analysis ──
        result = analyze(source_text, reference_texts)

        if "error" in result:
            return jsonify(result), 422

        # ── Generate PDF Report ──
        report_path = generate_report(result, src_name, app.config["REPORTS_FOLDER"])
        report_filename = os.path.basename(report_path)

        result["report_filename"] = report_filename
        result["source_filename"]  = src_name

        return jsonify(result), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 422
    except Exception as e:
        app.logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error during analysis."}), 500
    finally:
        # Clean up uploaded files (keep reports)
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)


@app.route("/download/<filename>")
def download_report(filename: str):
    """Serve the generated PDF report for download."""
    safe_name = secure_filename(filename)
    filepath  = os.path.join(app.config["REPORTS_FOLDER"], safe_name)

    if not os.path.exists(filepath):
        abort(404)

    return send_file(
        filepath,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=safe_name
    )


# ─────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
