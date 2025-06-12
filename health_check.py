"""
health_check.py

Flask-based health check and status reporting service for system/service monitoring.

Endpoints:
- GET /health: Returns 200 OK and {"status": "ok"} for basic liveness check.
- GET /status: Returns system and service status, including cron job state and error counts.

Usage:
- Run as a standalone service: `python health_check.py`
- Can be managed by a process supervisor (e.g., systemd).

Requirements:
- Integrates with cron_utils.py for persistent job state.
- Uses log_config.py for logging.
- Loads configuration from settings.json.
- No business logic—only health/status reporting and integration.

"""

import os
import json
from flask import Flask, jsonify
from flask import request
from lm_studio_integration import lm_studio
from log_config import init_logging, get_logger
from cron_utils import CronScheduler, DEFAULT_STATE_FILE
from datetime import datetime
import traceback

# --- Load configuration ---
def load_settings(settings_path="config/settings.json"):
    try:
        with open(settings_path, "r") as f:
            # Remove JS-style comments if present
            content = f.read()
            content = "\n".join(line for line in content.splitlines() if not line.strip().startswith("//"))
            return json.loads(content)
    except Exception as e:
        print(f"Failed to load settings.json: {e}")
        return {}

settings = load_settings()

# --- Logging setup ---
log_dir = settings.get("paths", {}).get("logs", "logs")
log_file_name = "health_check.log"
init_logging(log_dir=log_dir, log_file_name=log_file_name)
logger = get_logger(__name__)

# --- Build jobs config for CronScheduler ---
def build_jobs_config(settings):
    jobs = {}
    automation = settings.get("automation", {})
    if "batch_analysis_cron" in automation:
        jobs["batch_analysis"] = automation["batch_analysis_cron"]
    if "realtime_processing_interval_minutes" in automation:
        interval = automation["realtime_processing_interval_minutes"]
        if isinstance(interval, int) and interval > 0:
            jobs["realtime_processing"] = f"*/{interval} * * * *"
    return jobs

jobs_config = build_jobs_config(settings)
state_file = DEFAULT_STATE_FILE  # Could be made configurable

# --- Flask app setup ---
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    Returns 200 OK and {"status": "ok"} if the service is running.
    """
    logger.info("Health check requested")
    return jsonify({"status": "ok"}), 200

@app.route("/status", methods=["GET"])
def status():
    """
    Status endpoint.
    Returns system and service status, including cron job state and error counts.
    """
    try:
        logger.info("Status check requested")
        # Gather cron job status
        scheduler = CronScheduler(jobs_config, state_file=state_file)
        jobs_status = []
        now = datetime.utcnow()
        for job_name in jobs_config:
            last_run = scheduler.get_last_run(job_name)
            status = scheduler.get_job_status(job_name)
            missed = scheduler.get_missed_runs(job_name, now)
            next_run = scheduler.get_next_run(job_name, now)
            jobs_status.append({
                "name": job_name,
                "cron_expr": jobs_config[job_name],
                "last_run": last_run.isoformat() if last_run else None,
                "status": status,
                "missed_runs": missed,
                "next_run": next_run.isoformat() if next_run else None,
            })

        # Error counts: count "error" statuses in jobs
        error_count = sum(1 for job in jobs_status if job["status"] == "error")

        # Optionally, add log file info (e.g., last N lines, size)
        log_info = {}
        log_path = os.path.join(log_dir, log_file_name)
        if os.path.exists(log_path):
            log_info["log_file"] = log_path
            log_info["size_bytes"] = os.path.getsize(log_path)
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    log_info["last_10_lines"] = lines[-10:] if len(lines) >= 10 else lines
            except Exception as e:
                log_info["last_10_lines"] = [f"Failed to read log file: {e}"]

        # Compose status response
        resp = {
            "service": "health_check",
            "timestamp_utc": datetime.utcnow().isoformat(),
            "jobs": jobs_status,
            "error_count": error_count,
            "log_info": log_info,
        }
        return jsonify(resp), 200
    except Exception as e:
        logger.error(f"Status endpoint error: {e}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
# --- LM Studio Integration Endpoints ---

@app.route("/api/lmstudio/status", methods=["GET"])
def lm_studio_status():
    """Check the status of the LM Studio server."""
    logger.info("LM Studio status requested")
    if lm_studio.is_server_running():
        loaded_model = lm_studio.get_loaded_model()
        return jsonify({
            "status": "running",
            "loaded_model": loaded_model
        }), 200
    else:
        return jsonify({"status": "not_running"}), 503

@app.route("/api/lmstudio/models", methods=["GET"])
def lm_studio_models():
    """Get the list of available models."""
    logger.info("LM Studio models list requested")
    return jsonify(lm_studio.models), 200

@app.route("/api/lmstudio/analyze", methods=["POST"])
def lm_studio_analyze():
    """
    Trigger an email analysis using LM Studio.
    Expects a JSON payload with 'use_existing_export' (boolean).
    """
    logger.info("LM Studio analysis requested")
    data = request.get_json()
    use_existing_export = data.get("use_existing_export", False) if data else False
    
    # This is a long-running task, so we should run it in the background
    # For now, we'll run it synchronously for simplicity
    from lm_studio_integration import analyze_email_subjects_with_lm_studio
    result = analyze_email_subjects_with_lm_studio(use_existing_export)
    
    if result:
        return jsonify(result), 200
    else:
        return jsonify({"error": "Analysis failed"}), 500
    return jsonify({"status": "error", "message": str(e)}), 500
@app.route("/api/lmstudio/apply-suggestions", methods=["POST"])
def lm_studio_apply_suggestions():
    """
    Apply suggestions from an LM Studio analysis.
    Expects a JSON payload with a 'suggestions' object.
    """
    logger.info("LM Studio apply suggestions requested")
    data = request.get_json()
    suggestions = data.get("suggestions") if data else None
    
    if not suggestions:
        return jsonify({"error": "No suggestions provided"}), 400
        
    from lm_studio_integration import apply_lm_studio_suggestions
    success = apply_lm_studio_suggestions(suggestions)
    
    if success:
        return jsonify({"status": "suggestions_applied"}), 200
    else:
        return jsonify({"error": "Failed to apply suggestions"}), 500

@app.route("/api/lmstudio/switch-model", methods=["POST"])
def lm_studio_switch_model():
    """
    Switch the model used by LM Studio.
    Expects a JSON payload with a 'model_key' string.
    """
    logger.info("LM Studio switch model requested")
    data = request.get_json()
    model_key = data.get("model_key") if data else None

    if not model_key:
        return jsonify({"error": "No model_key provided"}), 400

    success = lm_studio.load_model(model_key)

    if success:
        return jsonify({"status": f"model_switched_to_{model_key}"}), 200
    else:
        return jsonify({"error": f"Failed to switch model to {model_key}"}), 500
# --- Documentation endpoint ---
@app.route("/", methods=["GET"])
def docs():
    """
    API documentation endpoint.
    """
    doc = {
        "service": "health_check",
        "description": "Health, status, and LM Studio integration endpoints.",
        "endpoints": {
            "/health": {
                "method": "GET",
                "description": "Basic liveness check. Returns {'status': 'ok'}."
            },
            "/status": {
                "method": "GET",
                "description": "Returns system and service status, including cron job state and error counts."
            },
            "/api/lmstudio/status": {
                "method": "GET",
                "description": "Check the status of the LM Studio server."
            },
            "/api/lmstudio/models": {
                "method": "GET",
                "description": "Get the list of available models."
            },
            "/api/lmstudio/analyze": {
                "method": "POST",
                "description": "Trigger an email analysis using LM Studio.",
                "payload": {
                    "use_existing_export": "boolean (optional)"
                }
            },
            "/api/lmstudio/apply-suggestions": {
                "method": "POST",
                "description": "Apply suggestions from an LM Studio analysis.",
                "payload": {
                    "suggestions": "object"
                }
            },
            "/api/lmstudio/switch-model": {
                "method": "POST",
                "description": "Switch the model used by LM Studio.",
                "payload": {
                    "model_key": "string"
                }
            }
        },
        "usage": [
            "Start the service: python health_check.py",
            "GET /health  -> 200 OK, {'status': 'ok'}",
            "GET /status  -> 200 OK, system/service status JSON"
        ]
    }
    return jsonify(doc), 200

# --- Entrypoint ---
if __name__ == "__main__":
    logger.info("Starting health_check Flask service...")
    app.run(host="0.0.0.0", port=8080)