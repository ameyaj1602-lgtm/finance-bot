"""
Phase 7: Watchlist & Price Alerts
Personal watchlist with configurable alerts.
"""
import sqlite3
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


class Watchlist:
    """Manages personal watchlist and price alerts."""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                symbol TEXT PRIMARY KEY,
                added_at TEXT,
                added_price REAL,
                notes TEXT DEFAULT ''
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                alert_type TEXT,
                target_value REAL,
                condition TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                triggered_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add(self, symbol, price=None, notes=""):
        """Add a stock to watchlist."""
        symbol = symbol.upper().replace(".NS", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO watchlist (symbol, added_at, added_price, notes) VALUES (?, ?, ?, ?)",
            (symbol, datetime.now().isoformat(), price or 0, notes)
        )
        conn.commit()
        conn.close()
        return {"symbol": symbol, "price": price}

    def remove(self, symbol):
        """Remove from watchlist."""
        symbol = symbol.upper().replace(".NS", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def get_all(self):
        """Get all watchlist items."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM watchlist ORDER BY added_at DESC")
        rows = c.fetchall()
        conn.close()
        return [{"symbol": r[0], "added_at": r[1], "added_price": r[2], "notes": r[3]} for r in rows]

    def add_alert(self, symbol, alert_type, target_value, condition="crosses"):
        """Add a price alert.
        alert_type: 'price_above', 'price_below', 'rsi_above', 'rsi_below', 'volume_spike'
        """
        symbol = symbol.upper().replace(".NS", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO price_alerts (symbol, alert_type, target_value, condition, created_at) VALUES (?, ?, ?, ?, ?)",
            (symbol, alert_type, target_value, condition, datetime.now().isoformat())
        )
        alert_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"id": alert_id, "symbol": symbol, "type": alert_type, "target": target_value}

    def remove_alert(self, alert_id):
        """Remove an alert."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM price_alerts WHERE id = ?", (alert_id,))
        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def get_active_alerts(self):
        """Get all active alerts."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM price_alerts WHERE status = 'active' ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "symbol": r[1], "type": r[2], "target": r[3],
                 "condition": r[4], "status": r[5]} for r in rows]

    def trigger_alert(self, alert_id):
        """Mark alert as triggered."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE price_alerts SET status = 'triggered', triggered_at = ? WHERE id = ?",
                  (datetime.now().isoformat(), alert_id))
        conn.commit()
        conn.close()


def check_alerts():
    """Check all active alerts against current prices. Returns list of alert messages."""
    from data.market_data import MarketDataFetcher

    watchlist = Watchlist()
    fetcher = MarketDataFetcher()
    alerts = watchlist.get_active_alerts()
    triggered_messages = []

    for alert in alerts:
        symbol = alert["symbol"]
        full_sym = symbol + ".NS"

        try:
            live = fetcher.get_live_price(full_sym)
            if not live or not live.get("price"):
                continue

            price = live["price"]
            triggered = False

            if alert["type"] == "price_above" and price >= alert["target"]:
                triggered = True
                msg = "🔔 ALERT: " + symbol + " crossed ABOVE Rs." + format(alert["target"], ",.2f") + " (now Rs." + format(price, ",.2f") + ")"
            elif alert["type"] == "price_below" and price <= alert["target"]:
                triggered = True
                msg = "🔔 ALERT: " + symbol + " fell BELOW Rs." + format(alert["target"], ",.2f") + " (now Rs." + format(price, ",.2f") + ")"

            if triggered:
                watchlist.trigger_alert(alert["id"])
                triggered_messages.append(msg)

        except Exception:
            pass

    return triggered_messages


def format_watchlist(watchlist_items, current_prices=None):
    """Format watchlist for display."""
    if not watchlist_items:
        return "Your watchlist is empty. Add stocks with /watch RELIANCE"

    lines = ["👁 YOUR WATCHLIST", "━" * 30]

    for item in watchlist_items:
        symbol = item["symbol"]
        added_price = item["added_price"]

        line = "  " + symbol
        if current_prices and symbol in current_prices:
            price = current_prices[symbol]
            line += ": Rs." + format(price, ",.2f")
            if added_price and added_price > 0:
                change = ((price - added_price) / added_price) * 100
                emoji = "🟢" if change > 0 else "🔴"
                line += " " + emoji + " " + format(change, "+.2f") + "% since added"
        elif added_price and added_price > 0:
            line += " (added at Rs." + format(added_price, ",.2f") + ")"

        if item.get("notes"):
            line += " — " + item["notes"]

        lines.append(line)

    return "\n".join(lines)
