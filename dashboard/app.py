"""
Finance Bot Web Dashboard
Indian Stock Market — Dark theme, responsive, TradingView-style.
"""
import os
import sys
import json
import traceback
from datetime import datetime

# Allow imports from the finance-bot root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request

from data.market_data import MarketDataFetcher
from analysis.technical import TechnicalAnalyzer
from analysis.fundamental import FundamentalAnalyzer
from trading.paper_trader import PaperTrader
from education.lessons import get_lesson, get_all_topics
from config import NIFTY_50_SYMBOLS, INDICES, SECTOR_MAP

app = Flask(__name__)

# Shared instances
fetcher = MarketDataFetcher()
tech_analyzer = TechnicalAnalyzer()
fund_analyzer = FundamentalAnalyzer()
trader = PaperTrader()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val, default=0.0):
    """Safely convert to float."""
    try:
        if val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _pct_change(current, previous):
    """Return percentage change or 0.0."""
    try:
        if previous and previous != 0:
            return round(((current - previous) / previous) * 100, 2)
    except (TypeError, ZeroDivisionError):
        pass
    return 0.0


def _format_symbol(symbol):
    """Remove .NS suffix for display."""
    return symbol.replace(".NS", "")


def _get_index_snapshot():
    """Fetch latest index values."""
    snapshots = []
    for name, symbol in INDICES.items():
        try:
            df = fetcher.get_stock_data(symbol, period="5d")
            display_name = name.replace("_", " ")
            price_val = 0.0
            change_pct = 0.0
            if df is not None and len(df) >= 2:
                price_val = _safe_float(df["Close"].iloc[-1])
                prev = _safe_float(df["Close"].iloc[-2])
                change_pct = _pct_change(price_val, prev)
            snapshots.append({
                "name": display_name,
                "symbol": symbol,
                "price": price_val,
                "change_pct": change_pct,
            })
        except Exception:
            snapshots.append({
                "name": name.replace("_", " "),
                "symbol": symbol,
                "price": 0.0,
                "change_pct": 0.0,
            })
    return snapshots


def _get_sector_heatmap(stock_data):
    """Build sector performance from bulk stock data."""
    heatmap = {}
    for sector, symbols in SECTOR_MAP.items():
        changes = []
        for sym in symbols:
            if sym in stock_data and stock_data[sym] is not None and len(stock_data[sym]) >= 2:
                df = stock_data[sym]
                last = _safe_float(df["Close"].iloc[-1])
                prev = _safe_float(df["Close"].iloc[-2])
                pct = _pct_change(last, prev)
                changes.append(pct)
        avg = round(sum(changes) / len(changes), 2) if changes else 0.0
        heatmap[sector] = avg
    return heatmap


# ---------------------------------------------------------------------------
# Page Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Main dashboard — market overview."""
    return render_template("index.html")


@app.route("/stock/<symbol>")
def stock_detail(symbol):
    """Stock detail page."""
    display = _format_symbol(symbol)
    if not symbol.endswith(".NS"):
        symbol = symbol + ".NS"
    return render_template("stock.html", symbol=symbol, display_name=display)


@app.route("/portfolio")
def portfolio():
    """Paper trading portfolio."""
    return render_template("portfolio.html")


@app.route("/signals")
def signals():
    """Today's trading signals."""
    return render_template("signals.html")


@app.route("/learn")
def learn():
    """Learning curriculum."""
    topics = get_all_topics()
    return render_template("learn.html", topics=topics)


@app.route("/learn/<int:day>")
def lesson_detail(day):
    """Individual lesson."""
    lesson = get_lesson(day)
    topics = get_all_topics()
    return render_template("lesson.html", lesson=lesson, day=day, topics=topics)


# ---------------------------------------------------------------------------
# JSON API Routes
# ---------------------------------------------------------------------------

@app.route("/api/market")
def api_market():
    """Market overview data as JSON."""
    try:
        indices = _get_index_snapshot()
        stock_data = fetcher.get_bulk_data(NIFTY_50_SYMBOLS[:20], period="5d")
        movers = fetcher.get_top_movers(stock_data, n=5)
        heatmap = _get_sector_heatmap(stock_data)

        top_gainers = []
        top_losers = []
        if movers:
            for item in movers.get("gainers", []):
                top_gainers.append({"symbol": item["symbol"], "change_pct": item["change_pct"]})
            for item in movers.get("losers", []):
                top_losers.append({"symbol": item["symbol"], "change_pct": item["change_pct"]})

        return jsonify({
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "indices": indices,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "sector_heatmap": heatmap,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stock/<symbol>")
def api_stock(symbol):
    """Full analysis for a single stock."""
    try:
        if not symbol.endswith(".NS"):
            symbol = symbol + ".NS"

        df = fetcher.get_stock_data(symbol, period="6mo")
        info = fetcher.get_stock_info(symbol)
        price = fetcher.get_live_price(symbol)

        technical = None
        if df is not None and len(df) >= 50:
            technical = tech_analyzer.analyze(df, symbol)

        fundamental = None
        if info:
            fundamental = fund_analyzer.analyze(info)

        # Serialise technical result — filter out non-JSON-safe fields
        tech_json = None
        if technical:
            tech_json = {}
            for k, v in technical.items():
                if k == "signals":
                    tech_json["signals"] = v
                elif k == "summary":
                    tech_json["summary"] = v
                elif k == "indicators":
                    indicators = {}
                    for ik, iv in v.items():
                        try:
                            indicators[ik] = float(iv) if iv is not None else None
                        except (TypeError, ValueError):
                            indicators[ik] = str(iv)
                    tech_json["indicators"] = indicators
                elif k in ("trend", "pattern", "support", "resistance"):
                    try:
                        tech_json[k] = float(v) if isinstance(v, (int, float)) else str(v)
                    except (TypeError, ValueError):
                        tech_json[k] = str(v)

        return jsonify({
            "success": True,
            "symbol": symbol,
            "display_name": _format_symbol(symbol),
            "price": _safe_float(price),
            "info": {
                "name": info.get("shortName", "") if info else "",
                "sector": info.get("sector", "") if info else "",
                "industry": info.get("industry", "") if info else "",
                "market_cap": info.get("marketCap", 0) if info else 0,
                "pe_ratio": _safe_float(info.get("trailingPE")) if info else 0,
                "pb_ratio": _safe_float(info.get("priceToBook")) if info else 0,
                "dividend_yield": _safe_float(info.get("dividendYield")) if info else 0,
                "52w_high": _safe_float(info.get("fiftyTwoWeekHigh")) if info else 0,
                "52w_low": _safe_float(info.get("fiftyTwoWeekLow")) if info else 0,
            },
            "technical": tech_json,
            "fundamental": fundamental,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/portfolio")
def api_portfolio():
    """Portfolio and trade data."""
    try:
        summary = trader.get_portfolio_summary()
        open_trades = trader.get_open_trades()
        history = trader.get_trade_history(limit=30)
        return jsonify({
            "success": True,
            "summary": summary,
            "open_trades": open_trades,
            "history": history,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/signals")
def api_signals():
    """Generate signals for top stocks."""
    try:
        stock_data = fetcher.get_bulk_data(NIFTY_50_SYMBOLS[:20], period="6mo")
        signals_list = []
        for sym, df in stock_data.items():
            if df is None or len(df) < 50:
                continue
            result = tech_analyzer.analyze(df, sym)
            if result and result.get("overall_signal"):
                overall = result["overall_signal"]
                indicators = result.get("indicators", {})
                signals_list.append({
                    "symbol": _format_symbol(sym),
                    "signal": overall.get("signal", "HOLD"),
                    "confidence": overall.get("confidence", 0),
                    "price": indicators.get("price", 0),
                    "change_pct": indicators.get("change_pct", 0),
                    "rsi": indicators.get("rsi"),
                    "reasons": overall.get("reasons", []),
                    "trend_short": result.get("trend", {}).get("short", ""),
                    "trend_medium": result.get("trend", {}).get("medium", ""),
                })

        signals_list.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return jsonify({
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "signals": signals_list[:20],
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/lesson/<int:day>")
def api_lesson(day):
    """Get lesson content."""
    try:
        lesson = get_lesson(day)
        return jsonify({"success": True, "day": day, "topic": lesson["topic"], "lesson": lesson["lesson"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)
