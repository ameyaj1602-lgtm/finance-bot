"""
Market Predictor — Predicts next day's market direction using
technical indicators, sentiment, global cues, and FII/DII data.
Gives clear reasoning for every prediction.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import INDICES, NIFTY_50_SYMBOLS, SECTOR_MAP


class MarketPredictor:
    """Predicts market direction with reasoning."""

    def __init__(self):
        from data.market_data import MarketDataFetcher
        from analysis.technical import TechnicalAnalyzer
        from analysis.news_sentiment import NewsSentimentEngine
        from analysis.ai_analyst import AIAnalyst
        self.fetcher = MarketDataFetcher()
        self.ta = TechnicalAnalyzer()
        self.news = NewsSentimentEngine()
        self.ai = AIAnalyst()

    def predict_market(self):
        """Full market prediction with reasoning."""
        signals = []
        bullish_reasons = []
        bearish_reasons = []
        score = 0  # positive = bullish, negative = bearish

        # 1. Nifty Technical Analysis
        nifty_df = self.fetcher.get_stock_data("^NSEI", period="6mo")
        nifty_ta = None
        if nifty_df is not None and len(nifty_df) >= 50:
            nifty_ta = self.ta.analyze(nifty_df, "NIFTY")
            if nifty_ta:
                overall = nifty_ta["overall_signal"]
                ind = nifty_ta["indicators"]

                if "BUY" in overall["signal"]:
                    score += 2
                    bullish_reasons.append("Nifty technical signal: " + overall["signal"] + " (" + str(overall["confidence"]) + "% confidence)")
                elif "SELL" in overall["signal"]:
                    score -= 2
                    bearish_reasons.append("Nifty technical signal: " + overall["signal"] + " (" + str(overall["confidence"]) + "% confidence)")

                # RSI
                rsi = ind.get("rsi")
                if rsi:
                    if rsi < 35:
                        score += 1
                        bullish_reasons.append("Nifty RSI oversold at " + str(rsi) + " — bounce likely")
                    elif rsi > 65:
                        score -= 1
                        bearish_reasons.append("Nifty RSI overbought at " + str(rsi) + " — correction possible")

                # Supertrend
                st = ind.get("supertrend_direction")
                if st == 1:
                    score += 1
                    bullish_reasons.append("Nifty Supertrend is BULLISH")
                elif st == -1:
                    score -= 1
                    bearish_reasons.append("Nifty Supertrend is BEARISH")

                # EMA alignment
                trend = nifty_ta.get("trend", {})
                if trend.get("short") == "bullish" and trend.get("medium") == "bullish":
                    score += 1
                    bullish_reasons.append("Short and medium term trends are UP")
                elif trend.get("short") == "bearish" and trend.get("medium") == "bearish":
                    score -= 1
                    bearish_reasons.append("Short and medium term trends are DOWN")

        # 2. Global Cues
        global_cues = self.fetcher.get_global_cues()
        global_score = 0
        for name, data in global_cues.items():
            if name in ("S&P 500", "NASDAQ", "Dow Jones"):
                if data["change_pct"] > 0.5:
                    global_score += 1
                elif data["change_pct"] < -0.5:
                    global_score -= 1
            elif name == "Crude Oil":
                if data["change_pct"] > 2:
                    global_score -= 1  # Rising crude = bearish for India
                elif data["change_pct"] < -2:
                    global_score += 1
            elif name == "USD/INR":
                if data["change_pct"] > 0.5:
                    global_score -= 1  # Rupee weakening
                elif data["change_pct"] < -0.3:
                    global_score += 1  # Rupee strengthening

        if global_score > 0:
            score += 1
            bullish_reasons.append("Global cues are POSITIVE (US markets green, rupee stable)")
        elif global_score < 0:
            score -= 1
            bearish_reasons.append("Global cues are NEGATIVE (US markets red / crude rising / rupee weak)")

        # 3. FII/DII
        fii_dii = self.fetcher.get_fii_dii_data()
        if isinstance(fii_dii, dict) and fii_dii.get("fii_net"):
            try:
                fii = float(str(fii_dii["fii_net"]).replace(",", ""))
                if fii > 500:
                    score += 1
                    bullish_reasons.append("FII buying (Rs." + str(int(fii)) + " Cr) — foreign money flowing in")
                elif fii < -500:
                    score -= 1
                    bearish_reasons.append("FII selling (Rs." + str(int(fii)) + " Cr) — foreign money pulling out")
            except (ValueError, TypeError):
                pass

        # 4. Market Breadth
        bulk = self.fetcher.get_bulk_data(NIFTY_50_SYMBOLS[:20], period="5d")
        if bulk:
            breadth = self.fetcher.get_market_breadth(bulk)
            ratio = breadth["advance_decline_ratio"]
            if ratio > 1.5:
                score += 1
                bullish_reasons.append("Market breadth strong: " + str(breadth["advancing"]) + " advancing vs " + str(breadth["declining"]) + " declining")
            elif ratio < 0.7:
                score -= 1
                bearish_reasons.append("Market breadth weak: " + str(breadth["declining"]) + " declining vs " + str(breadth["advancing"]) + " advancing")

        # 5. News Sentiment
        news_items = self.news.get_market_news(10)
        sentiment = self.news.analyze_sentiment(news_items)
        if sentiment["overall"] == "bullish":
            score += 1
            bullish_reasons.append("News sentiment is BULLISH (" + str(sentiment["bullish_count"]) + " positive headlines)")
        elif sentiment["overall"] == "bearish":
            score -= 1
            bearish_reasons.append("News sentiment is BEARISH (" + str(sentiment["bearish_count"]) + " negative headlines)")

        # 6. Sector Strength
        strong_sectors = []
        weak_sectors = []
        for sector, symbols in SECTOR_MAP.items():
            changes = []
            for sym in symbols[:3]:
                if sym in bulk and bulk[sym] is not None and len(bulk[sym]) >= 2:
                    df = bulk[sym]
                    pct = ((df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2]) * 100
                    changes.append(pct)
            if changes:
                avg = sum(changes) / len(changes)
                if avg > 1:
                    strong_sectors.append(sector)
                elif avg < -1:
                    weak_sectors.append(sector)

        if strong_sectors:
            bullish_reasons.append("Strong sectors: " + ", ".join(strong_sectors))
        if weak_sectors:
            bearish_reasons.append("Weak sectors: " + ", ".join(weak_sectors))

        # ── Final Prediction ─────────────────────────────────

        if score >= 3:
            prediction = "STRONG BULLISH"
            emoji = "🟢🟢"
            action = "Market likely to go UP. Good day to look for buying opportunities."
        elif score >= 1:
            prediction = "MILDLY BULLISH"
            emoji = "🟢"
            action = "Slight upward bias. Selective buying in strong stocks."
        elif score <= -3:
            prediction = "STRONG BEARISH"
            emoji = "🔴🔴"
            action = "Market likely to fall. Avoid fresh buying. Protect your positions with stop losses."
        elif score <= -1:
            prediction = "MILDLY BEARISH"
            emoji = "🔴"
            action = "Slight downward bias. Be cautious. Don't chase rallies."
        else:
            prediction = "SIDEWAYS / UNCERTAIN"
            emoji = "⚪"
            action = "No clear direction. Wait for a clearer setup. Cash is also a position."

        confidence = min(abs(score) * 15, 90)

        # Support/Resistance for Nifty
        nifty_levels = ""
        if nifty_ta:
            sr = nifty_ta["support_resistance"]
            if sr["support"]:
                nifty_levels += "Support: " + ", ".join(str(s) for s in sr["support"][:2])
            if sr["resistance"]:
                nifty_levels += " | Resistance: " + ", ".join(str(r) for r in sr["resistance"][:2])

        return {
            "prediction": prediction,
            "emoji": emoji,
            "score": score,
            "confidence": confidence,
            "action": action,
            "bullish_reasons": bullish_reasons,
            "bearish_reasons": bearish_reasons,
            "nifty_levels": nifty_levels,
            "global_cues": global_cues,
            "sentiment": sentiment["overall"],
        }

    def predict_stock(self, symbol):
        """Predict direction for a single stock."""
        full = symbol + ".NS" if not symbol.endswith(".NS") else symbol
        clean = symbol.replace(".NS", "")

        df = self.fetcher.get_stock_data(full, period="6mo")
        if df is None or len(df) < 50:
            return {"error": "Not enough data for " + clean}

        ta_result = self.ta.analyze(df, full)
        if not ta_result:
            return {"error": "Analysis failed for " + clean}

        overall = ta_result["overall_signal"]
        ind = ta_result["indicators"]
        trend = ta_result["trend"]
        sr = ta_result["support_resistance"]
        patterns = ta_result["pattern"]

        reasons = []
        score = 0

        # Signal
        if "BUY" in overall["signal"]:
            score += 2
            reasons.append("Technical signal: " + overall["signal"] + " (" + str(overall["confidence"]) + "%)")
        elif "SELL" in overall["signal"]:
            score -= 2
            reasons.append("Technical signal: " + overall["signal"] + " (" + str(overall["confidence"]) + "%)")

        # Trend alignment
        if trend["short"] == "bullish" and trend["medium"] == "bullish" and trend["long"] == "bullish":
            score += 2
            reasons.append("All trends aligned BULLISH (short + medium + long)")
        elif trend["short"] == "bearish" and trend["medium"] == "bearish":
            score -= 2
            reasons.append("Short and medium trends BEARISH")

        # RSI
        rsi = ind.get("rsi")
        if rsi and rsi < 30:
            score += 1
            reasons.append("RSI oversold at " + str(rsi) + " — bounce expected")
        elif rsi and rsi > 70:
            score -= 1
            reasons.append("RSI overbought at " + str(rsi) + " — pullback possible")

        # Patterns
        for p in patterns:
            if p["type"] == "bullish":
                score += 1
                reasons.append("Pattern: " + p["name"] + " — " + p["desc"])
            elif p["type"] == "bearish":
                score -= 1
                reasons.append("Pattern: " + p["name"] + " — " + p["desc"])

        # Volume
        vol_ratio = ind.get("volume_ratio", 1)
        if vol_ratio > 2:
            reasons.append("High volume (" + format(vol_ratio, ".1f") + "x avg) — strong conviction")

        # Prediction
        if score >= 3:
            prediction = "BULLISH"
            action = "Looks good for buying. Entry near Rs." + str(ind["price"])
            if sr["support"]:
                action += ", SL at Rs." + str(sr["support"][0])
        elif score <= -3:
            prediction = "BEARISH"
            action = "Avoid buying or consider exiting. Weakness expected."
        elif score >= 1:
            prediction = "MILDLY BULLISH"
            action = "Slight positive bias. Wait for pullback to support for better entry."
        elif score <= -1:
            prediction = "MILDLY BEARISH"
            action = "Caution. Don't add new positions here."
        else:
            prediction = "NEUTRAL"
            action = "No clear direction. Wait."

        return {
            "symbol": clean,
            "prediction": prediction,
            "score": score,
            "confidence": min(abs(score) * 15, 90),
            "price": ind["price"],
            "action": action,
            "reasons": reasons,
            "support": sr["support"][:2],
            "resistance": sr["resistance"][:2],
            "rsi": rsi,
            "trend": trend,
        }

    def format_market_prediction(self, pred):
        """Format market prediction for Telegram."""
        lines = [
            "🔮 MARKET PREDICTION — Tomorrow",
            "━" * 32,
            "",
            pred["emoji"] + " " + pred["prediction"],
            "Confidence: " + str(pred["confidence"]) + "%",
            "",
            "📌 " + pred["action"],
        ]

        if pred["nifty_levels"]:
            lines.append("\n📊 Nifty Levels: " + pred["nifty_levels"])

        if pred["bullish_reasons"]:
            lines.append("\n🟢 BULLISH FACTORS:")
            for r in pred["bullish_reasons"]:
                lines.append("  + " + r)

        if pred["bearish_reasons"]:
            lines.append("\n🔴 BEARISH FACTORS:")
            for r in pred["bearish_reasons"]:
                lines.append("  - " + r)

        # Global cues summary
        if pred["global_cues"]:
            lines.append("\n🌍 GLOBAL CUES:")
            for name, data in pred["global_cues"].items():
                emoji = "🟢" if data["change_pct"] > 0 else "🔴"
                lines.append("  " + emoji + " " + name + ": " + format(data["change_pct"], "+.2f") + "%")

        lines.append("\n📰 News Sentiment: " + pred["sentiment"].upper())

        lines.append("\n⚠️ This is an AI-assisted prediction based on technical indicators,")
        lines.append("global cues, FII/DII data, and news sentiment. NOT financial advice.")
        lines.append("The market can always do the opposite. Always use stop losses.")

        return "\n".join(lines)

    def format_stock_prediction(self, pred):
        """Format stock prediction for Telegram."""
        if "error" in pred:
            return pred["error"]

        emoji = "🟢" if pred["score"] > 0 else "🔴" if pred["score"] < 0 else "⚪"

        lines = [
            "🔮 PREDICTION: " + pred["symbol"],
            "━" * 32,
            "",
            emoji + " " + pred["prediction"] + " (Confidence: " + str(pred["confidence"]) + "%)",
            "Price: Rs." + format(pred["price"], ",.2f"),
            "",
            "📌 " + pred["action"],
        ]

        if pred["reasons"]:
            lines.append("\n📊 REASONS:")
            for r in pred["reasons"]:
                lines.append("  → " + r)

        if pred["support"]:
            lines.append("\nSupport: " + ", ".join("Rs." + str(s) for s in pred["support"]))
        if pred["resistance"]:
            lines.append("Resistance: " + ", ".join("Rs." + str(r) for r in pred["resistance"]))

        trend = pred["trend"]
        lines.append("\nTrend: Short=" + trend["short"] + " | Medium=" + trend["medium"] + " | Long=" + trend["long"])

        lines.append("\n⚠️ Prediction, not advice. Always use stop losses.")
        return "\n".join(lines)

    def get_ai_prediction(self, pred):
        """Enhance prediction with AI reasoning."""
        if not self.ai.has_ai:
            return None

        prompt = (
            "You are an Indian stock market analyst. Based on this data, give a 3-4 sentence "
            "prediction for tomorrow's market in simple language a beginner would understand.\n\n"
            "Prediction: " + pred["prediction"] + " (score: " + str(pred["score"]) + ")\n"
            "Bullish factors: " + ", ".join(pred["bullish_reasons"][:3]) + "\n"
            "Bearish factors: " + ", ".join(pred["bearish_reasons"][:3]) + "\n"
            "Sentiment: " + pred["sentiment"] + "\n\n"
            "Be specific. Mention Nifty levels. Give one clear actionable tip."
        )
        return self.ai._ask_ai(prompt, max_tokens=300)
