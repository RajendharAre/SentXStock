"""
Flask API server — bridges React frontend to Python backend.
Run: python server.py
Serves at: http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from api import TradingAPI
import threading

app = Flask(__name__)
CORS(app)  # Allow React dev server (localhost:5173) to call this

# Singleton API instance (persists across requests)
trading_api = TradingAPI()

# ─── Async Analysis Job Tracker ───────────────────────────────
_job_lock = threading.Lock()
_job = {
    "status": "idle",      # idle | running | complete | error
    "progress": "",
    "error": None,
}


def _run_analysis_bg(use_mock: bool):
    """Background thread: run analysis + update _job on finish."""
    global _job
    try:
        with _job_lock:
            _job["progress"] = "Fetching news & social data…"
        result = trading_api.run_analysis(use_mock=use_mock)
        with _job_lock:
            _job["status"] = "complete"
            _job["progress"] = "Analysis complete"
            _job["error"] = None
    except Exception as e:
        with _job_lock:
            _job["status"] = "error"
            _job["progress"] = ""
            _job["error"] = str(e)


# ─── Health Check ─────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "SentXStock API is running"})


# ─── User Settings ────────────────────────────────────────────

@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(trading_api.get_settings())


@app.route("/api/settings/tickers", methods=["POST"])
def set_tickers():
    data = request.get_json()
    tickers = data.get("tickers", [])
    if isinstance(tickers, str):
        tickers = [t.strip() for t in tickers.split(",") if t.strip()]
    result = trading_api.set_user_tickers(tickers)
    return jsonify(result)


@app.route("/api/settings/portfolio", methods=["POST"])
def set_portfolio():
    data = request.get_json()
    cash = data.get("cash", 50000)
    risk = data.get("risk", "Moderate")
    result = trading_api.set_user_portfolio(cash=float(cash), risk=risk)
    return jsonify(result)


# ─── Analysis ─────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST"])
def run_analysis():
    """Start the analysis pipeline in a background thread (non-blocking)."""
    global _job
    data = request.get_json() or {}
    use_mock = data.get("mock", False)

    with _job_lock:
        if _job["status"] == "running":
            return jsonify({"status": "running", "message": "Analysis already in progress"})
        _job["status"] = "running"
        _job["progress"] = "Starting pipeline…"
        _job["error"] = None

    t = threading.Thread(target=_run_analysis_bg, args=(use_mock,), daemon=True)
    t.start()
    return jsonify({"status": "started"})


@app.route("/api/analyze/status", methods=["GET"])
def analyze_status():
    """Poll this endpoint to check if analysis has finished."""
    with _job_lock:
        snapshot = dict(_job)
    return jsonify(snapshot)


@app.route("/api/analyze/ticker", methods=["POST"])
def analyze_ticker():
    """Deep-dive analysis on a specific ticker."""
    data = request.get_json()
    ticker = data.get("ticker", "")
    if not ticker:
        return jsonify({"error": "Please provide a ticker"}), 400
    result = trading_api.analyze_ticker(ticker)
    return jsonify(result)


@app.route("/api/result", methods=["GET"])
def get_latest_result():
    """Get the most recent analysis result (cached)."""
    return jsonify(trading_api.get_latest_result())


# ─── Dashboard ────────────────────────────────────────────────

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    """Get all dashboard data in one call."""
    return jsonify(trading_api.get_dashboard_data())


# ─── Chatbot ──────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    """Ask the AI trading advisor a question."""
    data = request.get_json()
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "Please provide a question"}), 400
    result = trading_api.chat(question)
    return jsonify(result)


@app.route("/api/chat/history", methods=["GET"])
def chat_history():
    """Get conversation history."""
    return jsonify(trading_api.get_chat_history())


@app.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    """Clear conversation history."""
    trading_api.clear_chat()
    return jsonify({"success": True})


# ─── Run Server ───────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  SentXStock API Server")
    print("  http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, port=5000)
