"""
AI Analysis Layer — Multi-provider support.
Supports: Gemini (free tier), Claude (Anthropic), OpenAI, Groq.
Falls back to template-based reports if no API key is available.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, GEMINI_API_KEY

# ── Provider Detection ───────────────────────────────────────

AI_PROVIDER = None  # will be set to "gemini", "anthropic", or None

# Priority: Gemini first (free tier), then Anthropic
try:
    if GEMINI_API_KEY:
        from google import genai
        AI_PROVIDER = "gemini"
except ImportError:
    pass

if not AI_PROVIDER:
    try:
        if ANTHROPIC_API_KEY:
            import anthropic
            AI_PROVIDER = "anthropic"
    except ImportError:
        pass


class AIAnalyst:
    """Generates intelligent market analysis using any supported AI provider."""

    def __init__(self):
        self.provider = AI_PROVIDER
        self.client = None
        self.fallback_client = None
        self.fallback_provider = None

        if self.provider == "gemini":
            from google import genai
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.model = "gemini-2.0-flash"
            print("AI: Primary = Gemini (" + self.model + ")")
            # Set up Anthropic as fallback
            if ANTHROPIC_API_KEY:
                try:
                    import anthropic
                    self.fallback_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                    self.fallback_provider = "anthropic"
                    print("AI: Fallback = Claude (haiku)")
                except ImportError:
                    pass

        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            self.model = "claude-haiku-4-5-20251001"
            print("AI: Using Claude (" + self.model + ")")

        else:
            print("AI: No API key found. Using template-based analysis.")
            print("    Add GEMINI_API_KEY (free!) or ANTHROPIC_API_KEY to .env")

    def _ask_ai(self, prompt, max_tokens=500):
        """Route to the correct AI provider."""
        if not self.client:
            return None

        try:
            if self.provider == "gemini":
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        "max_output_tokens": max_tokens,
                        "temperature": 0.7,
                    }
                )
                return response.text

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

        except Exception as e:
            print("AI error (" + self.provider + "): " + str(e)[:100])
            # Try fallback
            if self.fallback_client and self.fallback_provider == "anthropic":
                try:
                    print("Falling back to Claude...")
                    response = self.fallback_client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
                except Exception as e2:
                    print("Fallback also failed: " + str(e2)[:100])
            return None

    @property
    def has_ai(self):
        return self.client is not None

    # ── Public Methods ───────────────────────────────────────────

    def analyze_market(self, market_data):
        """Generate overall market analysis."""
        prompt = self._build_market_prompt(market_data)
        result = self._ask_ai(prompt)
        return result if result else self._template_market_analysis(market_data)

    def analyze_stock(self, symbol, technical, fundamental):
        """Generate stock-specific analysis."""
        prompt = self._build_stock_prompt(symbol, technical, fundamental)
        result = self._ask_ai(prompt)
        return result if result else self._template_stock_analysis(symbol, technical, fundamental)

    def generate_trade_idea(self, symbol, technical, fundamental, trade_type="swing"):
        """Generate a trade idea with entry, SL, target."""
        if technical is None:
            return None

        ind = technical.get("indicators", {})
        sig = technical.get("overall_signal", {})
        sr = technical.get("support_resistance", {})
        price = ind.get("price", 0)
        atr = ind.get("atr", 0)

        if sig.get("signal") not in ("BUY", "STRONG BUY", "SELL", "STRONG SELL"):
            return None

        is_buy = "BUY" in sig.get("signal", "")

        if is_buy:
            entry = price
            if sr.get("support"):
                stop_loss = round(sr["support"][0], 2)
            else:
                stop_loss = round(price - (atr * 1.5 if atr else price * 0.02), 2)
            risk = entry - stop_loss
            target = round(entry + (risk * 2), 2)
            action = "BUY"
        else:
            entry = price
            if sr.get("resistance"):
                stop_loss = round(sr["resistance"][0], 2)
            else:
                stop_loss = round(price + (atr * 1.5 if atr else price * 0.02), 2)
            risk = stop_loss - entry
            target = round(entry - (risk * 2), 2)
            action = "SELL"

        idea = {
            "symbol": symbol.replace(".NS", ""),
            "action": action,
            "entry": entry,
            "stop_loss": stop_loss,
            "target": target,
            "risk_reward": "1:2",
            "confidence": sig.get("confidence", 0),
            "reasons": sig.get("reasons", []),
            "trade_type": trade_type,
        }

        if self.has_ai:
            prompt = (
                "You are an Indian stock market analyst. Given this trade setup, "
                "provide a 2-3 sentence rationale.\n\n"
                "Stock: {sym}\n"
                "Action: {act} at Rs.{entry}\n"
                "Stop Loss: Rs.{sl}\n"
                "Target: Rs.{tgt}\n"
                "Technical signals: {reasons}\n\n"
                "Be specific, mention the indicators, and explain why this setup "
                "looks good or risky. Keep it simple for a beginner."
            ).format(
                sym=idea['symbol'], act=idea['action'], entry=idea['entry'],
                sl=idea['stop_loss'], tgt=idea['target'],
                reasons=', '.join(idea['reasons'])
            )
            ai_result = self._ask_ai(prompt)
            if ai_result:
                idea["ai_rationale"] = ai_result

        return idea

    def explain_concept(self, concept):
        """Explain a trading/investing concept for a beginner."""
        prompt = (
            'Explain this stock market concept to a complete beginner in India: "' + concept + '"\n\n'
            "Rules:\n"
            "- Use simple Hindi-English (Hinglish) style — casual, friendly\n"
            "- Give a real Indian stock example\n"
            "- Maximum 5-6 sentences\n"
            "- End with one practical tip they can use today"
        )
        result = self._ask_ai(prompt)
        return result if result else self._template_concept(concept)

    def generate_daily_lesson(self, day_number):
        """Generate a daily learning lesson based on curriculum."""
        curriculum = self._get_curriculum()
        if day_number > len(curriculum):
            day_number = (day_number % len(curriculum)) + 1

        topic = curriculum[day_number - 1]

        prompt = (
            "You are a friendly Indian stock market tutor. Today is Day {day} of the learning journey.\n\n"
            "Topic: {topic}\n\n"
            "Create a short lesson (max 150 words):\n"
            "1. Start with a relatable analogy\n"
            "2. Explain the concept simply\n"
            "3. Show how it applies to Indian stocks (use Nifty 50 examples)\n"
            "4. One actionable tip\n"
            "5. End with a quiz question (with answer)\n\n"
            "Keep it fun and use some Hinglish naturally."
        ).format(day=day_number, topic=topic)

        result = self._ask_ai(prompt, max_tokens=600)
        if result:
            return {"day": day_number, "topic": topic, "lesson": result}
        return {"day": day_number, "topic": topic, "lesson": self._template_lesson(topic, day_number)}

    # ── Prompt Builders ──────────────────────────────────────────

    def _build_market_prompt(self, data):
        return (
            "You are an Indian stock market analyst writing a morning brief.\n\n"
            "Market Data:\n"
            + json.dumps(data, indent=2, default=str) + "\n\n"
            "Write a concise market analysis (max 200 words):\n"
            "1. Overall market mood (bullish/bearish/sideways)\n"
            "2. Key things to watch today\n"
            "3. Which sectors look strong/weak\n"
            "4. One actionable insight for a beginner investor\n\n"
            "Use clear language. Mention specific stocks or sectors from the data."
        )

    def _build_stock_prompt(self, symbol, technical, fundamental):
        ta_str = json.dumps(technical, indent=2, default=str) if technical else 'N/A'
        fa_str = json.dumps(fundamental, indent=2, default=str) if fundamental else 'N/A'
        return (
            "Analyze this Indian stock for a beginner investor:\n\n"
            "Stock: " + symbol + "\n"
            "Technical Analysis: " + ta_str + "\n"
            "Fundamental Analysis: " + fa_str + "\n\n"
            "Provide (max 150 words):\n"
            "1. Should they buy, sell, or wait?\n"
            "2. Why? (cite specific numbers)\n"
            "3. What's the risk?\n"
            "4. Simple next step"
        )

    # ── Fallback Templates ───────────────────────────────────────

    def _template_market_analysis(self, data):
        lines = []
        if "indices" in data:
            for name, info in data["indices"].items():
                pct = info.get('change_pct', 0)
                lines.append("{name}: {val} ({pct:+.2f}%)".format(
                    name=name, val=info.get('value', 'N/A'), pct=pct))

        if "movers" in data:
            gainers = data["movers"].get("gainers", [])
            losers = data["movers"].get("losers", [])
            if gainers:
                gainer_strs = [g['symbol'] + " (" + format(g['change_pct'], '+.1f') + "%)" for g in gainers[:3]]
                lines.append("\nTop Gainers: " + ", ".join(gainer_strs))
            if losers:
                loser_strs = [l['symbol'] + " (" + format(l['change_pct'], '+.1f') + "%)" for l in losers[:3]]
                lines.append("Top Losers: " + ", ".join(loser_strs))

        if "breadth" in data:
            b = data["breadth"]
            lines.append("\nMarket Breadth: {adv} advancing, {dec} declining".format(
                adv=b['advancing'], dec=b['declining']))
            if b["advance_decline_ratio"] > 1.5:
                mood = "Bullish"
            elif b["advance_decline_ratio"] < 0.7:
                mood = "Bearish"
            else:
                mood = "Mixed"
            lines.append("Overall Mood: " + mood)

        return "\n".join(lines) if lines else "Market data being fetched..."

    def _template_stock_analysis(self, symbol, technical, fundamental):
        lines = ["Analysis for " + symbol.replace('.NS', '') + ":"]
        if technical:
            sig = technical.get("overall_signal", {})
            lines.append("Signal: {s} (Confidence: {c}%)".format(
                s=sig.get('signal', 'N/A'), c=sig.get('confidence', 0)))
            for r in sig.get("reasons", []):
                lines.append("  * " + r)
        if fundamental:
            lines.append("Rating: " + fundamental.get('rating', 'N/A'))
        return "\n".join(lines)

    def _template_concept(self, concept):
        concepts = {
            "pe ratio": "PE Ratio = Stock Price / Earnings Per Share. If Reliance PE is 25, investors pay Rs.25 for every Rs.1 of profit. Lower PE can mean cheaper stock. Nifty average PE is ~22.",
            "stop loss": "Stop Loss is like a safety net. If you buy a stock at Rs.100, you set stop loss at Rs.95. If price falls to Rs.95, it auto-sells. You lose Rs.5 instead of potentially Rs.50. Always use it!",
            "support resistance": "Support = floor price where stock bounces up. Resistance = ceiling where it bounces down. Like a ball bouncing between floor and ceiling.",
            "rsi": "RSI (Relative Strength Index) ranges from 0-100. Above 70 = overbought (might fall), Below 30 = oversold (might rise). Like checking if a runner is tired (70+) or rested (30-).",
            "macd": "MACD shows momentum. When MACD line crosses above signal line = bullish. Below = bearish. Think of it as the 'speed' of price movement.",
            "sip": "SIP (Systematic Investment Plan) = investing a fixed amount monthly in mutual funds. Like a recurring deposit but in the stock market. Even Rs.500/month works!",
            "nifty": "Nifty 50 = Top 50 companies on NSE. It's like the 'average score' of the market. If Nifty is up, most stocks are doing well.",
            "intraday": "Intraday = Buy and sell on the SAME day. You don't keep stocks overnight. High risk, high reward. Not recommended for beginners!",
        }
        return concepts.get(concept.lower(),
            "Add GEMINI_API_KEY (free!) to your .env file for AI-powered explanations of any concept. "
            "Or search '" + concept + "' on varsity.zerodha.com — best free resource!")

    def _template_lesson(self, topic, day):
        return (
            "Day " + str(day) + ": " + topic + "\n\n"
            "Add GEMINI_API_KEY (free!) or ANTHROPIC_API_KEY to .env for AI-powered lessons.\n"
            "Meanwhile, check varsity.zerodha.com for excellent free lessons."
        )

    def _get_curriculum(self):
        return [
            "What is the Stock Market? (NSE, BSE, Nifty, Sensex)",
            "How to read a stock price (Open, High, Low, Close, Volume)",
            "What are indices? (Nifty 50, Bank Nifty, Sensex)",
            "Market participants: FII, DII, Retail — who moves the market?",
            "Types of orders: Market, Limit, Stop Loss",
            "What is a Demat account and how trading works",
            "Candlestick basics: Green vs Red, Body vs Wick",
            "Support and Resistance — the floor and ceiling of stocks",
            "Moving Averages: The trend is your friend",
            "RSI — Is the stock overbought or oversold?",
            "MACD — Spotting momentum shifts",
            "Bollinger Bands — Volatility and breakouts",
            "Volume: The fuel behind price moves",
            "PE Ratio — Is the stock cheap or expensive?",
            "EPS and Revenue Growth — Is the company growing?",
            "Debt-to-Equity — Is the company safe?",
            "ROE — How efficiently is the company using your money?",
            "Mutual Funds vs Direct Stock Investing",
            "SIP: The power of regular investing",
            "Intraday vs Swing vs Positional Trading",
            "Risk Management: Position sizing and stop losses",
            "Chart Patterns: Head & Shoulders, Double Top/Bottom",
            "Sector Rotation: Which sectors lead in bull/bear markets",
            "Reading an Annual Report (Basics)",
            "Dividends: Passive income from stocks",
            "IPOs: Should you invest in new listings?",
            "Options Trading Basics (Calls and Puts)",
            "Tax on stock market gains in India (STCG, LTCG)",
            "Building your first portfolio: Diversification",
            "Psychology of trading: Fear, Greed, and Discipline",
        ]
