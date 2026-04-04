"""
Daily Report Generator
Creates formatted market reports for Telegram delivery.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.market_data import MarketDataFetcher
from analysis.technical import TechnicalAnalyzer
from analysis.fundamental import FundamentalAnalyzer
from analysis.ai_analyst import AIAnalyst
from config import NIFTY_50_SYMBOLS, SECTOR_MAP, INDICES


class DailyReportGenerator:
    """Generates all daily reports."""

    def __init__(self):
        self.data = MarketDataFetcher()
        self.technical = TechnicalAnalyzer()
        self.fundamental = FundamentalAnalyzer()
        self.ai = AIAnalyst()

    def generate_morning_brief(self):
        """Pre-market morning brief (8:30 AM)."""
        lines = []
        now = datetime.now()
        lines.append(f"☀️ GOOD MORNING — Market Brief")
        lines.append(f"📅 {now.strftime('%A, %d %B %Y')}")
        lines.append("━" * 32)

        # Index Data
        lines.append("\n📊 INDICES:")
        for name, symbol in INDICES.items():
            df = self.data.get_stock_data(symbol, period="5d")
            if df is not None and len(df) >= 2:
                last = df["Close"].iloc[-1]
                prev = df["Close"].iloc[-2]
                pct = ((last - prev) / prev) * 100
                emoji = "🟢" if pct > 0 else "🔴" if pct < 0 else "⚪"
                display_name = name.replace("_", " ")
                lines.append(f"  {emoji} {display_name}: {last:,.0f} ({pct:+.2f}%)")

        # Global Cues
        lines.append("\n🌍 GLOBAL CUES:")
        global_cues = self.data.get_global_cues()
        for name, info in global_cues.items():
            emoji = "🟢" if info["change_pct"] > 0 else "🔴" if info["change_pct"] < 0 else "⚪"
            lines.append(f"  {emoji} {name}: {info['value']:,.2f} ({info['change_pct']:+.2f}%)")

        # FII/DII
        lines.append("\n💰 FII/DII ACTIVITY:")
        fii_dii = self.data.get_fii_dii_data()
        if isinstance(fii_dii, dict):
            if "note" in fii_dii:
                lines.append(f"  {fii_dii['note']}")
            else:
                lines.append(f"  FII Net: {fii_dii.get('fii_net', 'N/A')}")
                lines.append(f"  DII Net: {fii_dii.get('dii_net', 'N/A')}")

        # Top movers from a quick scan
        lines.append("\n📈📉 TOP MOVERS (Nifty 50):")
        bulk = self.data.get_bulk_data(NIFTY_50_SYMBOLS, period="5d")
        if bulk:
            movers = self.data.get_top_movers(bulk, n=3)
            if movers["gainers"]:
                lines.append("  Gainers:")
                for g in movers["gainers"]:
                    lines.append(f"    🟢 {g['symbol']}: ₹{g['price']} ({g['change_pct']:+.2f}%)")
            if movers["losers"]:
                lines.append("  Losers:")
                for l in movers["losers"]:
                    lines.append(f"    🔴 {l['symbol']}: ₹{l['price']} ({l['change_pct']:+.2f}%)")

            # Market breadth
            breadth = self.data.get_market_breadth(bulk)
            lines.append(f"\n📊 BREADTH: {breadth['advancing']}⬆ / {breadth['declining']}⬇ / {breadth['unchanged']}➡")
            ratio = breadth["advance_decline_ratio"]
            if ratio > 1.5:
                lines.append("  Market Mood: BULLISH 🐂")
            elif ratio < 0.7:
                lines.append("  Market Mood: BEARISH 🐻")
            else:
                lines.append("  Market Mood: MIXED 🤷")

        return "\n".join(lines)

    def generate_stock_signals(self, top_n=5):
        """Generate buy/sell signals for top opportunities."""
        lines = []
        lines.append("🎯 TODAY'S SIGNALS")
        lines.append("━" * 32)
        lines.append("⚠️ Educational only. NOT financial advice.\n")

        bulk = self.data.get_bulk_data(NIFTY_50_SYMBOLS, period="6mo")
        signals = []

        for symbol, df in bulk.items():
            analysis = self.technical.analyze(df, symbol)
            if analysis and analysis["overall_signal"]["confidence"] > 40:
                sig = analysis["overall_signal"]
                if sig["signal"] in ("BUY", "STRONG BUY", "SELL", "STRONG SELL"):
                    signals.append({
                        "symbol": symbol.replace(".NS", ""),
                        "signal": sig["signal"],
                        "confidence": sig["confidence"],
                        "price": analysis["indicators"]["price"],
                        "reasons": sig["reasons"],
                        "support": analysis["support_resistance"]["support"][:1],
                        "resistance": analysis["support_resistance"]["resistance"][:1],
                        "rsi": analysis["indicators"].get("rsi"),
                        "trend": analysis["trend"],
                    })

        # Sort by confidence
        signals.sort(key=lambda x: x["confidence"], reverse=True)

        buy_signals = [s for s in signals if "BUY" in s["signal"]][:top_n]
        sell_signals = [s for s in signals if "SELL" in s["signal"]][:top_n]

        if buy_signals:
            lines.append("🟢 BUY SIGNALS:")
            for s in buy_signals:
                lines.append(f"\n  {s['symbol']} — {s['signal']} ({s['confidence']}% confidence)")
                lines.append(f"  Price: ₹{s['price']}")
                if s["support"]: lines.append(f"  Support: ₹{s['support'][0]}")
                if s["resistance"]: lines.append(f"  Resistance: ₹{s['resistance'][0]}")
                if s["rsi"]: lines.append(f"  RSI: {s['rsi']}")
                for r in s["reasons"][:2]:
                    lines.append(f"  → {r}")

        if sell_signals:
            lines.append("\n🔴 SELL/EXIT SIGNALS:")
            for s in sell_signals:
                lines.append(f"\n  {s['symbol']} — {s['signal']} ({s['confidence']}% confidence)")
                lines.append(f"  Price: ₹{s['price']}")
                if s["rsi"]: lines.append(f"  RSI: {s['rsi']}")
                for r in s["reasons"][:2]:
                    lines.append(f"  → {r}")

        if not buy_signals and not sell_signals:
            lines.append("No strong signals today. Market is sideways/uncertain.")
            lines.append("Best to wait for clearer setups. Patience is a superpower!")

        return "\n".join(lines)

    def generate_sector_heatmap(self):
        """Generate sector performance heatmap."""
        lines = ["🏭 SECTOR PERFORMANCE", "━" * 32]

        for sector, symbols in SECTOR_MAP.items():
            changes = []
            for sym in symbols:
                df = self.data.get_stock_data(sym, period="5d")
                if df is not None and len(df) >= 2:
                    pct = ((df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2]) * 100
                    changes.append(pct)

            if changes:
                avg = sum(changes) / len(changes)
                emoji = "🟢" if avg > 0.5 else "🔴" if avg < -0.5 else "⚪"
                bar = "█" * min(int(abs(avg) * 2), 10)
                direction = "+" if avg > 0 else ""
                lines.append(f"  {emoji} {sector:12s} {direction}{avg:.2f}% {bar}")

        return "\n".join(lines)

    def generate_stock_analysis(self, symbol):
        """Deep analysis of a single stock."""
        if not symbol.endswith(".NS"):
            symbol += ".NS"

        lines = []
        clean = symbol.replace(".NS", "")
        lines.append(f"🔎 DEEP ANALYSIS: {clean}")
        lines.append("━" * 32)

        # Technical
        df = self.data.get_stock_data(symbol, period="6mo")
        if df is None:
            return f"Could not fetch data for {clean}. Check the symbol."

        ta_result = self.technical.analyze(df, symbol)
        if ta_result:
            lines.append("\n📈 TECHNICAL ANALYSIS:")
            lines.append(ta_result["summary"])

            if ta_result["pattern"]:
                lines.append("\n🕯️ Patterns:")
                for p in ta_result["pattern"]:
                    lines.append(f"  {p['name']} ({p['type']}) — {p['desc']}")

        # Fundamental
        info = self.data.get_stock_info(symbol)
        if info:
            fa_result = self.fundamental.analyze(info)
            if fa_result:
                lines.append(f"\n📊 FUNDAMENTAL ANALYSIS:")
                lines.append(self.fundamental.format_report(fa_result))

        # Trade idea
        if ta_result:
            idea = self.ai.generate_trade_idea(symbol, ta_result, info)
            if idea:
                lines.append(f"\n🎯 TRADE IDEA:")
                lines.append(f"  Action: {idea['action']}")
                lines.append(f"  Entry: ₹{idea['entry']}")
                lines.append(f"  Stop Loss: ₹{idea['stop_loss']}")
                lines.append(f"  Target: ₹{idea['target']}")
                lines.append(f"  Risk:Reward = {idea['risk_reward']}")
                if idea.get("ai_rationale"):
                    lines.append(f"\n  💡 {idea['ai_rationale']}")

        lines.append("\n⚠️ This is educational analysis, not financial advice.")
        return "\n".join(lines)

    def generate_eod_report(self):
        """End of day report (4 PM)."""
        lines = []
        now = datetime.now()
        lines.append(f"🌙 END OF DAY REPORT")
        lines.append(f"📅 {now.strftime('%A, %d %B %Y')}")
        lines.append("━" * 32)

        # Index closing
        lines.append("\n📊 CLOSING LEVELS:")
        for name, symbol in INDICES.items():
            df = self.data.get_stock_data(symbol, period="5d")
            if df is not None and len(df) >= 2:
                last = df["Close"].iloc[-1]
                prev = df["Close"].iloc[-2]
                pct = ((last - prev) / prev) * 100
                emoji = "🟢" if pct > 0 else "🔴" if pct < 0 else "⚪"
                lines.append(f"  {emoji} {name.replace('_', ' ')}: {last:,.0f} ({pct:+.2f}%)")

        # Sector heatmap
        lines.append("")
        lines.append(self.generate_sector_heatmap())

        # Top movers
        bulk = self.data.get_bulk_data(NIFTY_50_SYMBOLS, period="5d")
        if bulk:
            movers = self.data.get_top_movers(bulk, n=5)
            lines.append("\n📈 TOP 5 GAINERS:")
            for g in movers["gainers"]:
                lines.append(f"  🟢 {g['symbol']}: ₹{g['price']} ({g['change_pct']:+.2f}%)")
            lines.append("\n📉 TOP 5 LOSERS:")
            for l in movers["losers"]:
                lines.append(f"  🔴 {l['symbol']}: ₹{l['price']} ({l['change_pct']:+.2f}%)")

        lines.append("\n💤 Markets closed. Review, learn, prepare for tomorrow!")
        return "\n".join(lines)


if __name__ == "__main__":
    gen = DailyReportGenerator()
    print("Generating morning brief...")
    print(gen.generate_morning_brief())
