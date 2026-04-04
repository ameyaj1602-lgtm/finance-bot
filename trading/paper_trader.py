"""
Paper Trading System
Track virtual trades without real money to test strategies.
"""
import sqlite3
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, RISK_CONFIG


class PaperTrader:
    """Manages paper (virtual) trades."""

    def __init__(self, starting_capital=100000):
        self.starting_capital = starting_capital
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS paper_portfolio (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                action TEXT,
                price REAL,
                quantity INTEGER,
                stop_loss REAL,
                target REAL,
                status TEXT DEFAULT 'open',
                exit_price REAL,
                exit_timestamp TEXT,
                pnl REAL,
                reason TEXT,
                trade_type TEXT DEFAULT 'swing'
            )
        """)
        # Initialize capital if not exists
        c.execute("INSERT OR IGNORE INTO paper_portfolio VALUES ('capital', ?)", (str(self.starting_capital),))
        c.execute("INSERT OR IGNORE INTO paper_portfolio VALUES ('total_trades', '0')")
        c.execute("INSERT OR IGNORE INTO paper_portfolio VALUES ('winning_trades', '0')")
        conn.commit()
        conn.close()

    def _get_value(self, key):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM paper_portfolio WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

    def _set_value(self, key, value):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO paper_portfolio VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()

    def get_capital(self):
        return float(self._get_value("capital") or self.starting_capital)

    def buy(self, symbol, price, stop_loss=None, target=None, trade_type="swing", reason=""):
        """Open a paper buy trade."""
        capital = self.get_capital()
        risk_per_trade = capital * (RISK_CONFIG["max_risk_per_trade_pct"] / 100)

        if stop_loss is None:
            stop_loss = round(price * (1 - RISK_CONFIG["default_stop_loss_pct"] / 100), 2)
        if target is None:
            target = round(price * (1 + RISK_CONFIG["default_target_pct"] / 100), 2)

        risk_per_share = price - stop_loss
        if risk_per_share <= 0:
            return {"error": "Stop loss must be below entry price"}

        quantity = max(1, int(risk_per_trade / risk_per_share))
        trade_value = quantity * price

        if trade_value > capital:
            quantity = max(1, int(capital / price))
            trade_value = quantity * price

        # Check max open positions
        open_trades = self.get_open_trades()
        if len(open_trades) >= RISK_CONFIG["max_open_positions"]:
            return {"error": f"Max {RISK_CONFIG['max_open_positions']} open positions allowed. Close some first."}

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO paper_trades (timestamp, symbol, action, price, quantity, stop_loss, target, reason, trade_type)
            VALUES (?, ?, 'BUY', ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), symbol, price, quantity, stop_loss, target, reason, trade_type))
        trade_id = c.lastrowid

        # Deduct capital
        new_capital = capital - trade_value
        c.execute("INSERT OR REPLACE INTO paper_portfolio VALUES ('capital', ?)", (str(new_capital),))
        conn.commit()
        conn.close()

        return {
            "trade_id": trade_id,
            "symbol": symbol,
            "action": "BUY",
            "price": price,
            "quantity": quantity,
            "value": trade_value,
            "stop_loss": stop_loss,
            "target": target,
            "remaining_capital": round(new_capital, 2),
        }

    def sell(self, trade_id, exit_price, reason="Manual exit"):
        """Close a paper trade."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM paper_trades WHERE id = ? AND status = 'open'", (trade_id,))
        trade = c.fetchone()

        if not trade:
            conn.close()
            return {"error": f"No open trade found with ID {trade_id}"}

        # trade columns: id, timestamp, symbol, action, price, quantity, stop_loss, target, status, exit_price, exit_timestamp, pnl, reason, trade_type
        entry_price = trade[4]
        quantity = trade[5]
        pnl = (exit_price - entry_price) * quantity

        c.execute("""
            UPDATE paper_trades
            SET status = 'closed', exit_price = ?, exit_timestamp = ?, pnl = ?, reason = ?
            WHERE id = ?
        """, (exit_price, datetime.now().isoformat(), pnl, reason, trade_id))

        # Return capital + PnL
        capital = self.get_capital()
        returned = (exit_price * quantity)
        new_capital = capital + returned
        c.execute("INSERT OR REPLACE INTO paper_portfolio VALUES ('capital', ?)", (str(new_capital),))

        # Update stats
        total = int(self._get_value("total_trades") or 0) + 1
        wins = int(self._get_value("winning_trades") or 0) + (1 if pnl > 0 else 0)
        c.execute("INSERT OR REPLACE INTO paper_portfolio VALUES ('total_trades', ?)", (str(total),))
        c.execute("INSERT OR REPLACE INTO paper_portfolio VALUES ('winning_trades', ?)", (str(wins),))

        conn.commit()
        conn.close()

        return {
            "trade_id": trade_id,
            "symbol": trade[2],
            "entry_price": entry_price,
            "exit_price": exit_price,
            "quantity": quantity,
            "pnl": round(pnl, 2),
            "pnl_pct": round((pnl / (entry_price * quantity)) * 100, 2),
            "capital": round(new_capital, 2),
        }

    def check_stop_loss_targets(self, current_prices):
        """Check if any open trades hit SL or target."""
        triggered = []
        open_trades = self.get_open_trades()

        for trade in open_trades:
            trade_id, symbol = trade["id"], trade["symbol"]
            price = current_prices.get(symbol) or current_prices.get(symbol + ".NS")
            if not price:
                continue

            if price <= trade["stop_loss"]:
                result = self.sell(trade_id, trade["stop_loss"], "Stop Loss Hit")
                result["trigger"] = "STOP LOSS"
                triggered.append(result)
            elif price >= trade["target"]:
                result = self.sell(trade_id, trade["target"], "Target Hit")
                result["trigger"] = "TARGET"
                triggered.append(result)

        return triggered

    def get_open_trades(self):
        """Get all open trades."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM paper_trades WHERE status = 'open' ORDER BY timestamp DESC")
        rows = c.fetchall()
        conn.close()

        trades = []
        for r in rows:
            trades.append({
                "id": r[0], "timestamp": r[1], "symbol": r[2], "action": r[3],
                "price": r[4], "quantity": r[5], "stop_loss": r[6], "target": r[7],
                "trade_type": r[13] if len(r) > 13 else "swing",
            })
        return trades

    def get_trade_history(self, limit=20):
        """Get closed trades."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM paper_trades WHERE status = 'closed' ORDER BY exit_timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()

        trades = []
        for r in rows:
            trades.append({
                "id": r[0], "symbol": r[2], "entry_price": r[4], "quantity": r[5],
                "exit_price": r[9], "pnl": r[11], "reason": r[12],
                "entry_time": r[1], "exit_time": r[10],
            })
        return trades

    def get_portfolio_summary(self):
        """Get overall portfolio performance."""
        capital = self.get_capital()
        total = int(self._get_value("total_trades") or 0)
        wins = int(self._get_value("winning_trades") or 0)
        open_trades = self.get_open_trades()

        # Calculate total PnL from closed trades
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COALESCE(SUM(pnl), 0) FROM paper_trades WHERE status = 'closed'")
        total_pnl = c.fetchone()[0]
        conn.close()

        return {
            "starting_capital": self.starting_capital,
            "current_capital": round(capital, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round((total_pnl / self.starting_capital) * 100, 2),
            "total_trades": total,
            "winning_trades": wins,
            "losing_trades": total - wins,
            "win_rate": round((wins / total) * 100, 1) if total > 0 else 0,
            "open_positions": len(open_trades),
            "open_trades": open_trades,
        }

    def format_portfolio(self):
        """Format portfolio for display."""
        p = self.get_portfolio_summary()
        lines = [
            "💼 PAPER TRADING PORTFOLIO",
            "━" * 30,
            f"Starting Capital: ₹{p['starting_capital']:,.0f}",
            f"Current Capital:  ₹{p['current_capital']:,.0f}",
            f"Total P&L:        ₹{p['total_pnl']:+,.0f} ({p['total_pnl_pct']:+.1f}%)",
            f"",
            f"Total Trades:  {p['total_trades']}",
            f"Won: {p['winning_trades']} | Lost: {p['losing_trades']}",
            f"Win Rate:      {p['win_rate']}%",
            f"Open Positions: {p['open_positions']}",
        ]

        if p["open_trades"]:
            lines.append("\nOpen Trades:")
            for t in p["open_trades"]:
                lines.append(f"  #{t['id']} {t['symbol']} @ ₹{t['price']} (SL: ₹{t['stop_loss']}, T: ₹{t['target']})")

        return "\n".join(lines)
