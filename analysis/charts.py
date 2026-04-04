"""
Phase 4: Chart Image Generator
Creates candlestick charts with indicators and sends via Telegram.
"""
import os
import sys
import tempfile
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ta.trend import EMAIndicator
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CHART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "charts")
os.makedirs(CHART_DIR, exist_ok=True)


class ChartGenerator:
    """Generates stock chart images."""

    def __init__(self):
        plt.style.use("dark_background")

    def generate_candlestick_chart(self, df, symbol, period="3mo", indicators=None):
        """Generate a candlestick chart with indicators."""
        if df is None or len(df) < 10:
            return None

        if indicators is None:
            indicators = ["ema", "volume", "rsi"]

        # Limit to last N candles based on period
        period_map = {"1mo": 22, "3mo": 66, "6mo": 132, "1y": 252}
        n_candles = period_map.get(period, 66)
        df = df.tail(n_candles).copy()

        clean_symbol = symbol.replace(".NS", "")
        has_rsi = "rsi" in indicators
        n_panels = 2 if has_rsi else 1
        height_ratios = [3, 1] if has_rsi else [1]

        fig, axes = plt.subplots(n_panels, 1, figsize=(14, 8 if has_rsi else 6),
                                  gridspec_kw={"height_ratios": height_ratios},
                                  sharex=True)
        if n_panels == 1:
            axes = [axes]

        ax_price = axes[0]
        ax_rsi = axes[1] if has_rsi else None

        # Plot candlesticks manually
        dates = np.arange(len(df))
        opens = df["Open"].values
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        volumes = df["Volume"].values

        colors = ["#26a69a" if c >= o else "#ef5350" for o, c in zip(opens, closes)]

        # Wicks
        for i in range(len(df)):
            ax_price.plot([dates[i], dates[i]], [lows[i], highs[i]], color=colors[i], linewidth=0.8)

        # Bodies
        body_width = 0.6
        for i in range(len(df)):
            bottom = min(opens[i], closes[i])
            height = abs(closes[i] - opens[i])
            if height < 0.01:
                height = 0.01
            ax_price.bar(dates[i], height, bottom=bottom, width=body_width, color=colors[i], edgecolor=colors[i])

        # EMAs
        if "ema" in indicators:
            close_series = df["Close"]
            for period_val, color, label in [(9, "#FFD700", "EMA 9"), (21, "#00BFFF", "EMA 21"), (50, "#FF69B4", "EMA 50")]:
                if len(df) > period_val:
                    ema = EMAIndicator(close=close_series, window=period_val).ema_indicator()
                    ax_price.plot(dates, ema.values, color=color, linewidth=1, label=label, alpha=0.8)

        # Bollinger Bands
        if "bollinger" in indicators and len(df) > 20:
            bb = BollingerBands(close=df["Close"], window=20, window_dev=2)
            ax_price.fill_between(dates, bb.bollinger_hband().values, bb.bollinger_lband().values,
                                   alpha=0.1, color="#888888", label="BB")
            ax_price.plot(dates, bb.bollinger_hband().values, color="#888888", linewidth=0.5, linestyle="--")
            ax_price.plot(dates, bb.bollinger_lband().values, color="#888888", linewidth=0.5, linestyle="--")

        # Support/Resistance lines
        if "sr" in indicators:
            from analysis.technical import TechnicalAnalyzer
            ta = TechnicalAnalyzer()
            sr = ta._find_support_resistance(df)
            for s in sr["support"][:2]:
                ax_price.axhline(y=s, color="#26a69a", linestyle="--", linewidth=0.8, alpha=0.6)
                ax_price.text(dates[-1] + 1, s, "S: " + str(s), color="#26a69a", fontsize=8, va="center")
            for r in sr["resistance"][:2]:
                ax_price.axhline(y=r, color="#ef5350", linestyle="--", linewidth=0.8, alpha=0.6)
                ax_price.text(dates[-1] + 1, r, "R: " + str(r), color="#ef5350", fontsize=8, va="center")

        # Volume on price chart (as bars at bottom)
        if "volume" in indicators:
            ax_vol = ax_price.twinx()
            max_vol = max(volumes) if max(volumes) > 0 else 1
            vol_normalized = volumes / max_vol * (max(highs) - min(lows)) * 0.2
            ax_vol.bar(dates, vol_normalized, width=body_width, color=colors, alpha=0.3)
            ax_vol.set_ylim(0, max(vol_normalized) * 5)
            ax_vol.set_yticks([])

        # RSI Panel
        if ax_rsi is not None:
            rsi = RSIIndicator(close=df["Close"], window=14).rsi()
            ax_rsi.plot(dates, rsi.values, color="#FFD700", linewidth=1.2)
            ax_rsi.axhline(y=70, color="#ef5350", linestyle="--", linewidth=0.8, alpha=0.5)
            ax_rsi.axhline(y=30, color="#26a69a", linestyle="--", linewidth=0.8, alpha=0.5)
            ax_rsi.fill_between(dates, 30, 70, alpha=0.05, color="white")
            ax_rsi.set_ylim(0, 100)
            ax_rsi.set_ylabel("RSI", fontsize=10)
            ax_rsi.text(dates[-1] + 1, rsi.iloc[-1], str(round(rsi.iloc[-1], 1)), color="#FFD700", fontsize=8, va="center")

        # Formatting
        last_price = closes[-1]
        prev_price = closes[-2] if len(closes) > 1 else closes[-1]
        change_pct = ((last_price - prev_price) / prev_price) * 100
        emoji = "+" if change_pct > 0 else ""

        ax_price.set_title(clean_symbol + "  |  Rs." + format(last_price, ",.2f") + "  (" + emoji + format(change_pct, ".2f") + "%)",
                           fontsize=14, fontweight="bold", pad=15)
        ax_price.legend(loc="upper left", fontsize=8, framealpha=0.3)
        ax_price.set_ylabel("Price (Rs.)", fontsize=10)
        ax_price.grid(True, alpha=0.1)

        # X-axis dates
        date_labels = df.index.strftime("%d %b")
        tick_positions = np.linspace(0, len(dates) - 1, min(10, len(dates))).astype(int)
        for ax in axes:
            ax.set_xticks(tick_positions)
            ax.set_xticklabels([date_labels[i] for i in tick_positions], rotation=45, fontsize=8)
            ax.grid(True, alpha=0.1)

        fig.tight_layout()

        # Save
        filepath = os.path.join(CHART_DIR, clean_symbol + "_chart.png")
        fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
        plt.close(fig)

        return filepath

    def generate_sector_heatmap(self, sector_data):
        """Generate a visual sector heatmap image."""
        if not sector_data:
            return None

        sectors = list(sector_data.keys())
        values = [sector_data[s] for s in sectors]

        fig, ax = plt.subplots(figsize=(10, 6))

        colors = []
        for v in values:
            if v > 1:
                colors.append("#26a69a")
            elif v > 0:
                colors.append("#4db6ac")
            elif v > -1:
                colors.append("#ef9a9a")
            else:
                colors.append("#ef5350")

        bars = ax.barh(sectors, values, color=colors, edgecolor="none", height=0.6)

        for bar, val in zip(bars, values):
            x_pos = bar.get_width()
            ax.text(x_pos + 0.1 if x_pos >= 0 else x_pos - 0.1,
                    bar.get_y() + bar.get_height() / 2,
                    format(val, "+.2f") + "%",
                    va="center", ha="left" if x_pos >= 0 else "right",
                    fontsize=10, color="white")

        ax.set_title("Sector Performance Heatmap", fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Change %", fontsize=10)
        ax.axvline(x=0, color="white", linewidth=0.5, alpha=0.3)
        ax.grid(True, axis="x", alpha=0.1)

        fig.tight_layout()
        filepath = os.path.join(CHART_DIR, "sector_heatmap.png")
        fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
        plt.close(fig)

        return filepath

    def generate_portfolio_chart(self, trade_history):
        """Generate portfolio P&L curve."""
        if not trade_history:
            return None

        fig, ax = plt.subplots(figsize=(12, 5))

        cumulative_pnl = []
        total = 0
        dates = []
        for t in reversed(trade_history):
            total += t.get("pnl", 0)
            cumulative_pnl.append(total)
            dates.append(t.get("exit_time", "")[:10])

        color = "#26a69a" if total >= 0 else "#ef5350"
        ax.fill_between(range(len(cumulative_pnl)), cumulative_pnl, alpha=0.3, color=color)
        ax.plot(cumulative_pnl, color=color, linewidth=2)
        ax.axhline(y=0, color="white", linewidth=0.5, alpha=0.3)

        ax.set_title("Portfolio P&L Curve", fontsize=14, fontweight="bold")
        ax.set_ylabel("Cumulative P&L (Rs.)", fontsize=10)
        ax.set_xlabel("Trades", fontsize=10)
        ax.grid(True, alpha=0.1)

        fig.tight_layout()
        filepath = os.path.join(CHART_DIR, "portfolio_pnl.png")
        fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
        plt.close(fig)

        return filepath
