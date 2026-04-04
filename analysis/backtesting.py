"""
Phase 8: Backtesting Engine
Test trading strategies on historical data.
"""
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BacktestEngine:
    """Backtests trading strategies on historical data."""

    STRATEGIES = {
        "ema_crossover": "EMA 9/21 Crossover — Buy when 9 crosses above 21, sell when below",
        "rsi_reversal": "RSI Reversal — Buy when RSI < 30, sell when RSI > 70",
        "supertrend": "Supertrend — Follow the supertrend indicator direction",
        "golden_cross": "Golden Cross — Buy when 50 EMA crosses above 200 EMA",
        "mean_reversion": "Mean Reversion — Buy when price drops 3%+ below 20 EMA, sell at EMA",
        "breakout": "Breakout — Buy when price breaks 20-day high with volume",
    }

    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital

    def run(self, df, strategy, stop_loss_pct=2.0, target_pct=4.0):
        """Run a backtest on historical data."""
        if df is None or len(df) < 200:
            return {"error": "Need at least 200 days of data. Use period='2y'."}

        df = df.copy()
        df = df.reset_index(drop=True)

        # Generate signals based on strategy
        if strategy == "ema_crossover":
            signals = self._strategy_ema_crossover(df)
        elif strategy == "rsi_reversal":
            signals = self._strategy_rsi_reversal(df)
        elif strategy == "supertrend":
            signals = self._strategy_supertrend(df)
        elif strategy == "golden_cross":
            signals = self._strategy_golden_cross(df)
        elif strategy == "mean_reversion":
            signals = self._strategy_mean_reversion(df)
        elif strategy == "breakout":
            signals = self._strategy_breakout(df)
        else:
            return {"error": "Unknown strategy: " + strategy}

        # Execute trades
        return self._execute_backtest(df, signals, stop_loss_pct, target_pct)

    def _strategy_ema_crossover(self, df):
        """EMA 9/21 crossover strategy."""
        ema9 = EMAIndicator(close=df["Close"], window=9).ema_indicator()
        ema21 = EMAIndicator(close=df["Close"], window=21).ema_indicator()

        signals = pd.Series(0, index=df.index)
        for i in range(1, len(df)):
            if pd.notna(ema9.iloc[i]) and pd.notna(ema21.iloc[i]):
                if ema9.iloc[i] > ema21.iloc[i] and ema9.iloc[i-1] <= ema21.iloc[i-1]:
                    signals.iloc[i] = 1  # Buy
                elif ema9.iloc[i] < ema21.iloc[i] and ema9.iloc[i-1] >= ema21.iloc[i-1]:
                    signals.iloc[i] = -1  # Sell
        return signals

    def _strategy_rsi_reversal(self, df):
        """RSI reversal strategy."""
        rsi = RSIIndicator(close=df["Close"], window=14).rsi()

        signals = pd.Series(0, index=df.index)
        for i in range(1, len(df)):
            if pd.notna(rsi.iloc[i]):
                if rsi.iloc[i] < 30 and rsi.iloc[i-1] >= 30:
                    signals.iloc[i] = 1
                elif rsi.iloc[i] > 70 and rsi.iloc[i-1] <= 70:
                    signals.iloc[i] = -1
        return signals

    def _strategy_supertrend(self, df):
        """Supertrend strategy."""
        from ta.volatility import AverageTrueRange
        atr = AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"], window=10).average_true_range()

        hl2 = (df["High"] + df["Low"]) / 2
        upper = hl2 + (3 * atr)
        lower = hl2 - (3 * atr)

        direction = pd.Series(0, index=df.index)
        direction.iloc[0] = 1

        for i in range(1, len(df)):
            if df["Close"].iloc[i] > upper.iloc[i-1]:
                direction.iloc[i] = 1
            elif df["Close"].iloc[i] < lower.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1]

        signals = pd.Series(0, index=df.index)
        for i in range(1, len(df)):
            if direction.iloc[i] == 1 and direction.iloc[i-1] == -1:
                signals.iloc[i] = 1
            elif direction.iloc[i] == -1 and direction.iloc[i-1] == 1:
                signals.iloc[i] = -1
        return signals

    def _strategy_golden_cross(self, df):
        """50/200 EMA golden cross."""
        ema50 = EMAIndicator(close=df["Close"], window=50).ema_indicator()
        ema200 = EMAIndicator(close=df["Close"], window=200).ema_indicator()

        signals = pd.Series(0, index=df.index)
        for i in range(1, len(df)):
            if pd.notna(ema50.iloc[i]) and pd.notna(ema200.iloc[i]):
                if ema50.iloc[i] > ema200.iloc[i] and ema50.iloc[i-1] <= ema200.iloc[i-1]:
                    signals.iloc[i] = 1
                elif ema50.iloc[i] < ema200.iloc[i] and ema50.iloc[i-1] >= ema200.iloc[i-1]:
                    signals.iloc[i] = -1
        return signals

    def _strategy_mean_reversion(self, df):
        """Mean reversion — buy dips below 20 EMA."""
        ema20 = EMAIndicator(close=df["Close"], window=20).ema_indicator()

        signals = pd.Series(0, index=df.index)
        for i in range(1, len(df)):
            if pd.notna(ema20.iloc[i]):
                deviation = ((df["Close"].iloc[i] - ema20.iloc[i]) / ema20.iloc[i]) * 100
                if deviation < -3 and ((df["Close"].iloc[i-1] - ema20.iloc[i-1]) / ema20.iloc[i-1]) * 100 >= -3:
                    signals.iloc[i] = 1
                elif deviation > 0 and ((df["Close"].iloc[i-1] - ema20.iloc[i-1]) / ema20.iloc[i-1]) * 100 <= 0:
                    signals.iloc[i] = -1
        return signals

    def _strategy_breakout(self, df):
        """20-day high breakout with volume."""
        high_20 = df["High"].rolling(20).max()
        vol_avg = df["Volume"].rolling(20).mean()

        signals = pd.Series(0, index=df.index)
        for i in range(21, len(df)):
            if (df["Close"].iloc[i] > high_20.iloc[i-1] and
                df["Volume"].iloc[i] > vol_avg.iloc[i] * 1.5):
                signals.iloc[i] = 1
            low_20 = df["Low"].iloc[i-20:i].min()
            if df["Close"].iloc[i] < low_20:
                signals.iloc[i] = -1
        return signals

    def _execute_backtest(self, df, signals, sl_pct, target_pct):
        """Execute trades based on signals and compute results."""
        capital = self.initial_capital
        position = None
        trades = []
        equity_curve = [capital]

        for i in range(len(df)):
            price = df["Close"].iloc[i]

            # Check SL/Target if in position
            if position:
                if price <= position["stop_loss"]:
                    pnl = (position["stop_loss"] - position["entry"]) * position["qty"]
                    capital += position["stop_loss"] * position["qty"]
                    trades.append({
                        "entry": position["entry"], "exit": position["stop_loss"],
                        "qty": position["qty"], "pnl": round(pnl, 2),
                        "reason": "Stop Loss", "bars_held": i - position["bar"],
                    })
                    position = None
                elif price >= position["target"]:
                    pnl = (position["target"] - position["entry"]) * position["qty"]
                    capital += position["target"] * position["qty"]
                    trades.append({
                        "entry": position["entry"], "exit": position["target"],
                        "qty": position["qty"], "pnl": round(pnl, 2),
                        "reason": "Target Hit", "bars_held": i - position["bar"],
                    })
                    position = None

            # New signal
            if signals.iloc[i] == 1 and position is None:
                qty = max(1, int((capital * 0.1) / price))  # 10% of capital per trade
                cost = qty * price
                if cost <= capital:
                    capital -= cost
                    position = {
                        "entry": price, "qty": qty, "bar": i,
                        "stop_loss": round(price * (1 - sl_pct / 100), 2),
                        "target": round(price * (1 + target_pct / 100), 2),
                    }
            elif signals.iloc[i] == -1 and position is not None:
                pnl = (price - position["entry"]) * position["qty"]
                capital += price * position["qty"]
                trades.append({
                    "entry": position["entry"], "exit": price,
                    "qty": position["qty"], "pnl": round(pnl, 2),
                    "reason": "Signal Exit", "bars_held": i - position["bar"],
                })
                position = None

            # Track equity
            current_equity = capital
            if position:
                current_equity += price * position["qty"]
            equity_curve.append(current_equity)

        # Close any remaining position
        if position:
            price = df["Close"].iloc[-1]
            pnl = (price - position["entry"]) * position["qty"]
            capital += price * position["qty"]
            trades.append({
                "entry": position["entry"], "exit": price,
                "qty": position["qty"], "pnl": round(pnl, 2),
                "reason": "End of Data", "bars_held": len(df) - position["bar"],
            })

        # Compute statistics
        if not trades:
            return {"error": "No trades generated. Strategy had no signals in this period."}

        total_pnl = sum(t["pnl"] for t in trades)
        winners = [t for t in trades if t["pnl"] > 0]
        losers = [t for t in trades if t["pnl"] <= 0]

        max_equity = equity_curve[0]
        max_drawdown = 0
        for eq in equity_curve:
            if eq > max_equity:
                max_equity = eq
            dd = (max_equity - eq) / max_equity * 100
            if dd > max_drawdown:
                max_drawdown = dd

        avg_win = sum(t["pnl"] for t in winners) / len(winners) if winners else 0
        avg_loss = sum(t["pnl"] for t in losers) / len(losers) if losers else 0

        return {
            "total_trades": len(trades),
            "winning_trades": len(winners),
            "losing_trades": len(losers),
            "win_rate": round(len(winners) / len(trades) * 100, 1),
            "total_pnl": round(total_pnl, 2),
            "total_return_pct": round((total_pnl / self.initial_capital) * 100, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(abs(avg_win * len(winners)) / abs(avg_loss * len(losers)), 2) if losers and avg_loss != 0 else float("inf"),
            "max_drawdown_pct": round(max_drawdown, 2),
            "avg_bars_held": round(sum(t["bars_held"] for t in trades) / len(trades), 1),
            "final_capital": round(capital, 2),
            "trades": trades[-10:],  # Last 10 trades
        }

    def format_backtest_report(self, result, strategy, symbol):
        """Format backtest results for display."""
        if "error" in result:
            return "Backtest Error: " + result["error"]

        lines = [
            "📊 BACKTEST RESULTS",
            "━" * 32,
            "Strategy: " + self.STRATEGIES.get(strategy, strategy),
            "Stock: " + symbol.replace(".NS", ""),
            "",
            "📈 Performance:",
            "  Total P&L: Rs." + format(result["total_pnl"], "+,.2f") + " (" + format(result["total_return_pct"], "+.2f") + "%)",
            "  Final Capital: Rs." + format(result["final_capital"], ",.2f"),
            "",
            "📋 Trade Stats:",
            "  Total Trades: " + str(result["total_trades"]),
            "  Won: " + str(result["winning_trades"]) + " | Lost: " + str(result["losing_trades"]),
            "  Win Rate: " + str(result["win_rate"]) + "%",
            "  Avg Win: Rs." + format(result["avg_win"], "+,.2f"),
            "  Avg Loss: Rs." + format(result["avg_loss"], "+,.2f"),
            "  Profit Factor: " + str(result["profit_factor"]),
            "",
            "⚠️ Risk:",
            "  Max Drawdown: " + str(result["max_drawdown_pct"]) + "%",
            "  Avg Holding Period: " + str(result["avg_bars_held"]) + " days",
        ]

        if result["total_return_pct"] > 15:
            lines.append("\n✅ Strategy performed well! But past performance ≠ future results.")
        elif result["total_return_pct"] > 0:
            lines.append("\n⚠️ Modest returns. Consider combining with other indicators.")
        else:
            lines.append("\n🔴 Strategy lost money in this period. NOT recommended.")

        return "\n".join(lines)
