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


# ─── Indian Company Universe ───────────────────────────────────

@app.route("/api/companies/search", methods=["GET"])
def search_companies():
    """
    Search Indian NSE companies by name or ticker.
    ?q=<query>&sector=<sector>

    - If q is empty and sector is given → return all companies in that sector
    - If q is provided → text search, optionally filtered by sector
    - Returns: { results: [...], total: N, sector: str, query: str }
    """
    from backtest.universe_india import IndiaUniverse
    q      = request.args.get("q", "").strip()
    sector = request.args.get("sector", "").strip()

    u = IndiaUniverse()

    if not q and sector:
        # Browse mode: return all companies in a sector (sorted by name)
        companies = u.browse_sector(sector)
    elif not q:
        # No query and no sector → return empty so search box stays clean
        return jsonify({"results": [], "total": 0, "sector": sector, "query": q})
    else:
        # Text search with optional sector filter
        companies = u.search(q, sector=sector)

    return jsonify({
        "results": companies,
        "total":   len(companies),
        "sector":  sector,
        "query":   q,
    })


@app.route("/api/companies/sectors", methods=["GET"])
def get_sectors():
    """List all sector names with company count."""
    from backtest.universe_india import IndiaUniverse
    u = IndiaUniverse()
    sector_names = u.sectors()
    counts = {s: 0 for s in sector_names}
    for stock in u.stocks:
        counts[stock["sector"]] = counts.get(stock["sector"], 0) + 1
    return jsonify({
        "sectors": sector_names,
        "counts":  counts,
    })


@app.route("/api/companies/by-sector/<sector>", methods=["GET"])
def companies_by_sector(sector: str):
    """Return all companies in a given sector."""
    from backtest.universe_india import IndiaUniverse
    u = IndiaUniverse()
    stocks = [s for s in u.stocks if s["sector"].lower() == sector.lower()]
    return jsonify(stocks)


@app.route("/api/companies/all", methods=["GET"])
def get_all_companies():
    """Return all 500 NSE companies (ticker, name, sector)."""
    from backtest.universe_india import IndiaUniverse
    return jsonify(IndiaUniverse().stocks)


@app.route("/api/companies/info/<ticker>", methods=["GET"])
def company_info(ticker: str):
    """Return metadata for a single ticker."""
    from backtest.universe_india import IndiaUniverse, normalise_ticker
    t = normalise_ticker(ticker)
    u = IndiaUniverse()
    info = u.info(t)
    if info is None:
        # Not in universe — still return basic info
        return jsonify({
            "ticker":    t,
            "name":      t.replace(".NS", ""),
            "sector":    "Unknown",
            "in_universe": False,
        })
    info["in_universe"] = True
    return jsonify(info)


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


# ─── Portfolio Allocations ────────────────────────────────────

@app.route("/api/portfolio/allocations", methods=["GET"])
def get_portfolio_allocations():
    """Return INR-denominated per-ticker allocation plan."""
    return jsonify(trading_api.get_portfolio_allocations())


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


# ─── Backtesting ──────────────────────────────────────────────

_bt_job_lock = threading.Lock()
_bt_job = {
    "status":  "idle",   # idle | running | complete | error
    "progress": "",
    "error":    None,
    "run_id":   None,
}


def _run_backtest_bg(params: dict):
    """Background thread for running backtest (same async pattern as analysis)."""
    global _bt_job
    try:
        from backtest.runner import run_backtest

        with _bt_job_lock:
            _bt_job["progress"] = "Loading price data…"

        result = run_backtest(
            tickers            = params.get("tickers") or None,
            sector             = params.get("sector") or None,
            start              = params.get("start",  "2022-01-01"),
            end                = params.get("end",    "2024-01-01"),
            strategy_variant   = params.get("strategy_variant",  "threshold"),
            risk_level         = params.get("risk_level",        "Medium"),
            sentiment_mode     = params.get("sentiment_mode",    "price_momentum"),
            buy_threshold      = float(params.get("buy_threshold",  0.10)),
            sell_threshold     = float(params.get("sell_threshold", -0.10)),
            max_position_pct   = float(params.get("max_position_pct", 0.05)),
            initial_capital    = float(params.get("initial_capital",  100_000)),
            benchmark_ticker   = params.get("benchmark_ticker", "SPY"),
            slippage_bps       = float(params.get("slippage_bps", 5.0)),
            allow_shorts       = bool(params.get("allow_shorts", False)),
            max_open_positions = int(params.get("max_open_positions", 20)),
            save_results       = True,
            run_id             = params.get("run_id") or None,
            verbose            = False,
        )

        with _bt_job_lock:
            _bt_job["status"]   = "complete"
            _bt_job["progress"] = "Backtest complete"
            _bt_job["run_id"]   = result.to_dict().get("_run_id", "")
            _bt_job["result"]   = result.to_dict()
            _bt_job["error"]    = None

    except Exception as e:
        import traceback
        with _bt_job_lock:
            _bt_job["status"]   = "error"
            _bt_job["progress"] = ""
            _bt_job["error"]    = str(e)
            _bt_job["run_id"]   = None


@app.route("/api/backtest/run", methods=["POST"])
def start_backtest():
    """Start a backtest in a background thread (non-blocking)."""
    global _bt_job
    params = request.get_json() or {}

    with _bt_job_lock:
        if _bt_job["status"] == "running":
            return jsonify({"status": "running", "message": "Backtest already in progress"})
        _bt_job["status"]   = "running"
        _bt_job["progress"] = "Queued…"
        _bt_job["error"]    = None
        _bt_job["run_id"]   = None
        _bt_job.pop("result", None)

    t = threading.Thread(target=_run_backtest_bg, args=(params,), daemon=True)
    t.start()
    return jsonify({"status": "started"})


@app.route("/api/backtest/status", methods=["GET"])
def backtest_status():
    """Poll for backtest completion."""
    with _bt_job_lock:
        snapshot = {k: v for k, v in _bt_job.items() if k != "result"}
    return jsonify(snapshot)


@app.route("/api/backtest/latest", methods=["GET"])
def backtest_latest_result():
    """Return the full result of the most-recently-completed backtest."""
    with _bt_job_lock:
        r = _bt_job.get("result")
    if not r:
        return jsonify({"error": "No completed backtest in memory. Call /api/backtest/result/<run_id> instead."}), 404
    return jsonify(r)


@app.route("/api/backtest/results", methods=["GET"])
def list_backtest_results():
    """List all saved backtest runs."""
    from backtest.report import list_runs
    return jsonify(list_runs())


@app.route("/api/backtest/result/<run_id>", methods=["GET"])
def get_backtest_result(run_id: str):
    """Load a saved backtest result by run_id."""
    from backtest.report import load_result
    try:
        return jsonify(load_result(run_id))
    except FileNotFoundError:
        return jsonify({"error": f"run_id '{run_id}' not found"}), 404


@app.route("/api/backtest/compare", methods=["POST"])
def compare_backtest_results():
    """Compare multiple saved runs side by side."""
    from backtest.report import compare_runs
    run_ids = (request.get_json() or {}).get("run_ids", [])
    if not run_ids:
        return jsonify({"error": "provide run_ids list"}), 400
    return jsonify(compare_runs(run_ids))


@app.route("/api/backtest/result/<run_id>", methods=["DELETE"])
def delete_backtest_result(run_id: str):
    """Delete a saved run."""
    from backtest.report import delete_result
    deleted = delete_result(run_id)
    return jsonify({"deleted": deleted})


@app.route("/api/backtest/run-ticker", methods=["POST"])
def start_backtest_for_ticker():
    """
    Silent auto-backtest for a single NSE ticker using Indian market defaults.
    Called automatically by the Dashboard when a company is selected.
    User never sees this — result is injected as a Performance Summary card.
    """
    global _bt_job
    data   = request.get_json() or {}
    ticker = data.get("ticker", "").strip()
    if not ticker:
        return jsonify({"error": "ticker required"}), 400

    # Read user capital + risk preference from current settings
    try:
        settings = trading_api.get_settings()
        capital  = float(settings.get("cash", 50_000))
        risk     = settings.get("risk_preference", "Medium")
    except Exception:
        capital = 50_000.0
        risk    = "Medium"

    params = {
        "tickers":            [ticker],
        "start":              "2023-01-31",
        "end":                "2026-01-31",
        "benchmark_ticker":   "^NSEI",
        "initial_capital":    capital,
        "risk_level":         risk,
        "strategy_variant":   "threshold",
        "sentiment_mode":     "price_momentum",
        "buy_threshold":      0.10,
        "sell_threshold":    -0.10,
        "max_position_pct":   0.20,
        "slippage_bps":       5.0,
        "allow_shorts":       False,
        "max_open_positions": 5,
        "save_results":       True,
    }

    with _bt_job_lock:
        if _bt_job["status"] == "running":
            # A backtest is already running — client can poll /api/backtest/status
            return jsonify({"status": "running", "message": "Already in progress"})
        _bt_job["status"]   = "running"
        _bt_job["progress"] = "Queued…"
        _bt_job["error"]    = None
        _bt_job["run_id"]   = None
        _bt_job.pop("result", None)

    t = threading.Thread(target=_run_backtest_bg, args=(params,), daemon=True)
    t.start()
    return jsonify({"status": "started"})


# ─── Run Server ───────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  SentXStock API Server")
    print("  http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, port=5000)
