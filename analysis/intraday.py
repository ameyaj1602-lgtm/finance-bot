"""
Phase 9: Intraday Scanner
Real-time scanning for intraday trading opportunities.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, time

from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NIFTY_50_SYMBOLS


class IntradayScanner:
    """Scans for intraday trading setups."""

    STRATEGIES = {
        "orb": "Opening Range Breakout — trade breakout of first 15/30 min range",
        "vwap_bounce": "VWAP Bounce — buy/sell when price bounces off VWAP",
        "gap": "Gap Play — trade stocks with significant gap up/down",
        "momentum": "Momentum — stocks with strong directional move + volume",
        "ema_pullback": "EMA Pullback — pullback to 9 EMA in trending stock",
    }

    def __init__(self):
        from data.market_data import MarketDataFetcher
        self.fetcher = MarketDataFetcher()

    def scan_all(self, symbols=None):
        """Run all intraday scans."""
        symbols = symbols or NIFTY_50_SYMBOLS[:20]  # Top 20 for speed
        results = {
            "gap_ups": [],
            "gap_downs": [],
            "momentum_buys": [],
            "momentum_sells": [],
            "vwap_setups": [],
            "volume_spikes": [],
        }

        for symbol in symbols:
            try:
                df = self.fetcher.get_intraday_data(symbol, interval="15m")
                daily = self.fetcher.get_stock_data(symbol, period="5d")
                if df is None or daily is None or len(df) < 5:
                    continue

                clean = symbol.replace(".NS", "")
                current = df["Close"].iloc[-1]

                # Gap analysis
                if len(daily) >= 2:
                    prev_close = daily["Close"].iloc[-2]
                    today_open = daily["Open"].iloc[-1]
                    gap_pct = ((today_open - prev_close) / prev_close) * 100

                    if gap_pct > 1:
                        results["gap_ups"].append({
                            "symbol": clean, "gap_pct": round(gap_pct, 2),
                            "open": round(today_open, 2), "current": round(current, 2),
                            "prev_close": round(prev_close, 2),
                        })
                    elif gap_pct < -1:
                        results["gap_downs"].append({
                            "symbol": clean, "gap_pct": round(gap_pct, 2),
                            "open": round(today_open, 2), "current": round(current, 2),
                            "prev_close": round(prev_close, 2),
                        })

                # Momentum scan
                if len(df) >= 10:
                    change = ((df["Close"].iloc[-1] - df["Close"].iloc[-5]) / df["Close"].iloc[-5]) * 100
                    vol_ratio = df["Volume"].iloc[-1] / df["Volume"].rolling(20).mean().iloc[-1] if df["Volume"].rolling(20).mean().iloc[-1] > 0 else 1

                    if change > 1.5 and vol_ratio > 1.3:
                        results["momentum_buys"].append({
                            "symbol": clean, "change_pct": round(change, 2),
                            "volume_ratio": round(vol_ratio, 2), "price": round(current, 2),
                        })
                    elif change < -1.5 and vol_ratio > 1.3:
                        results["momentum_sells"].append({
                            "symbol": clean, "change_pct": round(change, 2),
                            "volume_ratio": round(vol_ratio, 2), "price": round(current, 2),
                        })

                # VWAP setup
                if len(df) >= 10:
                    typical = (df["High"] + df["Low"] + df["Close"]) / 3
                    vwap = (typical * df["Volume"]).cumsum() / df["Volume"].cumsum()
                    vwap_val = vwap.iloc[-1]
                    distance = ((current - vwap_val) / vwap_val) * 100

                    if abs(distance) < 0.3:  # Near VWAP
                        results["vwap_setups"].append({
                            "symbol": clean, "price": round(current, 2),
                            "vwap": round(vwap_val, 2), "distance_pct": round(distance, 2),
                        })

                # Volume spike
                if len(df) >= 20:
                    vol_ratio = df["Volume"].iloc[-1] / df["Volume"].rolling(20).mean().iloc[-1] if df["Volume"].rolling(20).mean().iloc[-1] > 0 else 1
                    if vol_ratio > 2.5:
                        results["volume_spikes"].append({
                            "symbol": clean, "volume_ratio": round(vol_ratio, 2),
                            "price": round(current, 2),
                        })

            except Exception as e:
                continue

        # Sort results
        results["gap_ups"].sort(key=lambda x: x["gap_pct"], reverse=True)
        results["gap_downs"].sort(key=lambda x: x["gap_pct"])
        results["momentum_buys"].sort(key=lambda x: x["change_pct"], reverse=True)
        results["momentum_sells"].sort(key=lambda x: x["change_pct"])
        results["volume_spikes"].sort(key=lambda x: x["volume_ratio"], reverse=True)

        return results

    def format_intraday_report(self, results):
        """Format intraday scan results."""
        lines = ["⚡ INTRADAY SCANNER", "━" * 32,
                 "⚠️ Intraday = HIGH RISK. Use strict stop losses.\n"]

        if results["gap_ups"]:
            lines.append("📈 GAP UP STOCKS:")
            for g in results["gap_ups"][:5]:
                lines.append("  🟢 " + g["symbol"] + ": Gap +" + format(g["gap_pct"], ".2f") +
                            "% (Open: " + str(g["open"]) + ", Now: " + str(g["current"]) + ")")

        if results["gap_downs"]:
            lines.append("\n📉 GAP DOWN STOCKS:")
            for g in results["gap_downs"][:5]:
                lines.append("  🔴 " + g["symbol"] + ": Gap " + format(g["gap_pct"], ".2f") +
                            "% (Open: " + str(g["open"]) + ", Now: " + str(g["current"]) + ")")

        if results["momentum_buys"]:
            lines.append("\n🚀 MOMENTUM BUYS:")
            for m in results["momentum_buys"][:5]:
                lines.append("  🟢 " + m["symbol"] + ": +" + format(m["change_pct"], ".2f") +
                            "% | Vol: " + format(m["volume_ratio"], ".1f") + "x | Rs." + str(m["price"]))

        if results["momentum_sells"]:
            lines.append("\n💨 MOMENTUM SELLS:")
            for m in results["momentum_sells"][:5]:
                lines.append("  🔴 " + m["symbol"] + ": " + format(m["change_pct"], ".2f") +
                            "% | Vol: " + format(m["volume_ratio"], ".1f") + "x | Rs." + str(m["price"]))

        if results["vwap_setups"]:
            lines.append("\n📊 NEAR VWAP (Bounce Possible):")
            for v in results["vwap_setups"][:5]:
                lines.append("  " + v["symbol"] + ": Rs." + str(v["price"]) +
                            " (VWAP: " + str(v["vwap"]) + ")")

        if results["volume_spikes"]:
            lines.append("\n🔊 VOLUME SPIKES:")
            for v in results["volume_spikes"][:5]:
                lines.append("  " + v["symbol"] + ": " + format(v["volume_ratio"], ".1f") +
                            "x avg volume | Rs." + str(v["price"]))

        if not any(results.values()):
            lines.append("No strong intraday setups right now. Wait for better opportunities.")

        return "\n".join(lines)
