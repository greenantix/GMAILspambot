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
from flask import Flask, jsonify, render_template_string
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
# --- Web Dashboard ---
@app.route("/", methods=["GET"])
def dashboard():
    """
    Web dashboard for Gmail Spam Bot
    """
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📧 Gmail Spam Bot - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117; color: #e6edf3; line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { color: #58a6ff; font-size: 2.5em; margin-bottom: 10px; }
        .header p { color: #8b949e; font-size: 1.1em; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { 
            background: #161b22; border: 1px solid #30363d; border-radius: 8px; 
            padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .card h3 { color: #58a6ff; margin-bottom: 15px; font-size: 1.2em; }
        .status { display: flex; align-items: center; margin: 10px 0; }
        .status-dot { 
            width: 12px; height: 12px; border-radius: 50%; margin-right: 10px;
            animation: pulse 2s infinite;
        }
        .status-online { background: #2ea043; }
        .status-offline { background: #da3633; }
        .status-unknown { background: #f85149; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .btn { 
            background: #238636; color: white; border: none; padding: 10px 20px; 
            border-radius: 6px; cursor: pointer; margin: 5px; font-size: 14px;
            transition: background 0.2s;
        }
        .btn:hover { background: #2ea043; }
        .btn:disabled { background: #484f58; cursor: not-allowed; }
        .btn-secondary { background: #21262d; border: 1px solid #30363d; }
        .btn-secondary:hover { background: #30363d; }
        .log-output { 
            background: #0d1117; border: 1px solid #30363d; padding: 15px; 
            border-radius: 6px; font-family: 'Consolas', monospace; font-size: 12px;
            max-height: 200px; overflow-y: auto; margin-top: 10px;
        }
        .stats { display: flex; justify-content: space-between; margin: 15px 0; }
        .stat { text-align: center; }
        .stat-value { font-size: 1.8em; font-weight: bold; color: #58a6ff; }
        .stat-label { color: #8b949e; font-size: 0.9em; }
        .progress-bar { 
            background: #21262d; border-radius: 10px; height: 8px; overflow: hidden; margin: 10px 0;
        }
        .progress-fill { background: #2ea043; height: 100%; transition: width 0.3s ease; }
        .model-selector { margin: 10px 0; }
        .model-selector select { 
            background: #21262d; color: #e6edf3; border: 1px solid #30363d; 
            padding: 8px; border-radius: 6px; width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Gmail Spam Bot</h1>
            <p>LM Studio Powered Email Management System</p>
        </div>

        <div class="grid">
            <!-- System Status -->
            <div class="card">
                <h3>🏥 System Status</h3>
                <div class="status">
                    <div class="status-dot status-online"></div>
                    <span>Health Check Server: Online</span>
                </div>
                <div class="status" id="gmail-status">
                    <div class="status-dot status-unknown"></div>
                    <span>Gmail Connection: Checking...</span>
                </div>
                <div class="status" id="lmstudio-status">
                    <div class="status-dot status-unknown"></div>
                    <span>LM Studio: Checking...</span>
                </div>
                <div class="status" id="qml-status">
                    <div class="status-dot status-online"></div>
                    <span>QML Interface: Running (Offscreen)</span>
                </div>
            </div>

            <!-- LM Studio Control -->
            <div class="card">
                <h3>🧠 LM Studio Control</h3>
                <div id="current-model">Current Model: Loading...</div>
                <div class="model-selector">
                    <select id="model-select">
                        <option>Loading models...</option>
                    </select>
                </div>
                <button class="btn" onclick="switchModel()">Switch Model</button>
                <button class="btn btn-secondary" onclick="runAnalysis()">Run Analysis</button>
            </div>

            <!-- Email Statistics -->
            <div class="card">
                <h3>📊 Email Statistics</h3>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value" id="unread-count">-</div>
                        <div class="stat-label">Unread Emails</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="accuracy-rate">-</div>
                        <div class="stat-label">Accuracy</div>
                    </div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="processing-progress" style="width: 0%"></div>
                </div>
                <div id="processing-status">Ready to process emails</div>
            </div>

            <!-- Quick Actions -->
            <div class="card">
                <h3>⚡ Quick Actions</h3>
                <button class="btn" onclick="startProcessing()">🚀 Start Processing</button>
                <button class="btn" onclick="exportEmails()">📤 Export Emails</button>
                <button class="btn" onclick="cleanupOld()">🧹 Cleanup Old</button>
                <button class="btn btn-secondary" onclick="viewLogs()">📋 View Logs</button>
            </div>
        </div>

        <!-- Log Output -->
        <div class="card">
            <h3>📋 System Logs</h3>
            <div class="log-output" id="logs">Loading logs...</div>
            <button class="btn btn-secondary" onclick="refreshLogs()">Refresh Logs</button>
        </div>
    </div>

    <script>
        // Auto-refresh dashboard
        setInterval(updateDashboard, 5000);
        updateDashboard();

        async function updateDashboard() {
            // Update system status
            try {
                const statusResponse = await fetch('/status');
                const status = await statusResponse.json();
                
                // Update logs
                if (status.log_info && status.log_info.last_10_lines) {
                    document.getElementById('logs').textContent = 
                        status.log_info.last_10_lines.join('').slice(-1000) + '...';
                }
            } catch (e) {
                console.error('Failed to fetch status:', e);
            }

            // Update LM Studio status
            try {
                const lmResponse = await fetch('/api/lmstudio/status');
                const lmStatus = await lmResponse.json();
                const lmStatusEl = document.getElementById('lmstudio-status');
                
                if (lmStatus.status === 'running') {
                    lmStatusEl.innerHTML = `
                        <div class="status-dot status-online"></div>
                        <span>LM Studio: Online (${lmStatus.loaded_model || 'Unknown Model'})</span>
                    `;
                    document.getElementById('current-model').textContent = 
                        `Current Model: ${lmStatus.loaded_model || 'Unknown'}`;
                } else {
                    lmStatusEl.innerHTML = `
                        <div class="status-dot status-offline"></div>
                        <span>LM Studio: Offline</span>
                    `;
                }
            } catch (e) {
                console.error('Failed to fetch LM Studio status:', e);
            }

            // Update available models
            try {
                const modelsResponse = await fetch('/api/lmstudio/models');
                const models = await modelsResponse.json();
                const modelSelect = document.getElementById('model-select');
                modelSelect.innerHTML = '';
                
                Object.keys(models).forEach(key => {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = `${key}: ${models[key].name}`;
                    modelSelect.appendChild(option);
                });
            } catch (e) {
                console.error('Failed to fetch models:', e);
            }
        }

        async function switchModel() {
            const modelKey = document.getElementById('model-select').value;
            if (!modelKey) return;
            
            try {
                const response = await fetch('/api/lmstudio/switch-model', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model_key: modelKey })
                });
                
                const result = await response.json();
                if (response.ok) {
                    alert(`✅ Switched to model: ${modelKey}`);
                } else {
                    alert(`❌ Failed to switch model: ${result.error}`);
                }
                updateDashboard();
            } catch (e) {
                alert(`❌ Error switching model: ${e.message}`);
            }
        }

        async function runAnalysis() {
            try {
                document.getElementById('processing-status').textContent = 'Running LM Studio analysis...';
                const response = await fetch('/api/lmstudio/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ use_existing_export: true })
                });
                
                const result = await response.json();
                if (response.ok) {
                    alert('✅ Analysis completed successfully!');
                    document.getElementById('processing-status').textContent = 'Analysis completed';
                } else {
                    alert(`❌ Analysis failed: ${result.error}`);
                    document.getElementById('processing-status').textContent = 'Analysis failed';
                }
            } catch (e) {
                alert(`❌ Error running analysis: ${e.message}`);
                document.getElementById('processing-status').textContent = 'Ready to process emails';
            }
        }

        function startProcessing() {
            alert('🚀 Processing feature will be implemented in next update');
        }

        function exportEmails() {
            alert('📤 Export feature will be implemented in next update');
        }

        function cleanupOld() {
            alert('🧹 Cleanup feature will be implemented in next update');
        }

        function viewLogs() {
            window.open('/status', '_blank');
        }

        function refreshLogs() {
            updateDashboard();
        }
    </script>
</body>
</html>
    """
    return render_template_string(dashboard_html)

# --- API Documentation endpoint ---
@app.route("/api", methods=["GET"])
def api_docs():
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