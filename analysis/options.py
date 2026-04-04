"""
Phase 11: Options Module
Basic options analysis — option chain, IV, max pain, simple strategies.
Uses NSE data (free).
"""
import requests
import math
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class OptionsAnalyzer:
    """Options chain analysis and strategy suggestions."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # Hit NSE homepage first for cookies
        try:
            self.session.get("https://www.nseindia.com", timeout=5)
        except Exception:
            pass

    def get_option_chain(self, symbol="NIFTY"):
        """Fetch option chain from NSE."""
        try:
            url = "https://www.nseindia.com/api/option-chain-indices?symbol=" + symbol
            if symbol not in ("NIFTY", "BANKNIFTY", "FINNIFTY"):
                url = "https://www.nseindia.com/api/option-chain-equities?symbol=" + symbol

            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", {})
                return {
                    "symbol": symbol,
                    "spot_price": records.get("underlyingValue", 0),
                    "expiry_dates": records.get("expiryDates", []),
                    "data": records.get("data", []),
                    "timestamp": records.get("timestamp", ""),
                }
        except Exception as e:
            print("Option chain error: " + str(e))

        return None

    def calculate_max_pain(self, chain_data):
        """Calculate max pain strike price."""
        if not chain_data or not chain_data.get("data"):
            return None

        strike_pain = {}
        for record in chain_data["data"]:
            strike = record.get("strikePrice", 0)
            ce_oi = record.get("CE", {}).get("openInterest", 0) or 0
            pe_oi = record.get("PE", {}).get("openInterest", 0) or 0

            # Pain for CE writers if price goes above strike
            # Pain for PE writers if price goes below strike
            total_pain = 0
            for r in chain_data["data"]:
                s = r.get("strikePrice", 0)
                ce = r.get("CE", {}).get("openInterest", 0) or 0
                pe = r.get("PE", {}).get("openInterest", 0) or 0

                if strike > s:
                    total_pain += (strike - s) * ce
                elif strike < s:
                    total_pain += (s - strike) * pe

            strike_pain[strike] = total_pain

        if not strike_pain:
            return None

        max_pain_strike = min(strike_pain, key=strike_pain.get)
        return {
            "max_pain": max_pain_strike,
            "spot": chain_data["spot_price"],
            "difference": round(chain_data["spot_price"] - max_pain_strike, 2),
            "difference_pct": round(((chain_data["spot_price"] - max_pain_strike) / chain_data["spot_price"]) * 100, 2),
        }

    def analyze_pcr(self, chain_data):
        """Calculate Put-Call Ratio."""
        if not chain_data or not chain_data.get("data"):
            return None

        total_ce_oi = 0
        total_pe_oi = 0
        total_ce_vol = 0
        total_pe_vol = 0

        for record in chain_data["data"]:
            ce = record.get("CE", {})
            pe = record.get("PE", {})
            total_ce_oi += ce.get("openInterest", 0) or 0
            total_pe_oi += pe.get("openInterest", 0) or 0
            total_ce_vol += ce.get("totalTradedVolume", 0) or 0
            total_pe_vol += pe.get("totalTradedVolume", 0) or 0

        pcr_oi = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0
        pcr_vol = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol > 0 else 0

        # Interpretation
        if pcr_oi > 1.2:
            sentiment = "BULLISH (heavy put writing = support)"
        elif pcr_oi < 0.8:
            sentiment = "BEARISH (heavy call writing = resistance)"
        else:
            sentiment = "NEUTRAL"

        return {
            "pcr_oi": pcr_oi,
            "pcr_volume": pcr_vol,
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "sentiment": sentiment,
        }

    def find_key_strikes(self, chain_data):
        """Find strikes with highest OI (support/resistance)."""
        if not chain_data or not chain_data.get("data"):
            return None

        ce_oi = []
        pe_oi = []

        for record in chain_data["data"]:
            strike = record.get("strikePrice", 0)
            ce = record.get("CE", {}).get("openInterest", 0) or 0
            pe = record.get("PE", {}).get("openInterest", 0) or 0
            if ce > 0:
                ce_oi.append({"strike": strike, "oi": ce})
            if pe > 0:
                pe_oi.append({"strike": strike, "oi": pe})

        ce_oi.sort(key=lambda x: x["oi"], reverse=True)
        pe_oi.sort(key=lambda x: x["oi"], reverse=True)

        return {
            "resistance": ce_oi[:3],  # Highest CE OI = resistance
            "support": pe_oi[:3],     # Highest PE OI = support
        }

    def calculate_premium(self, spot, strike, days_to_expiry, volatility=20, rate=7, option_type="CE"):
        """Simple Black-Scholes approximation for option premium."""
        S = spot
        K = strike
        T = days_to_expiry / 365
        r = rate / 100
        sigma = volatility / 100

        if T <= 0:
            # Expired
            if option_type == "CE":
                return max(S - K, 0)
            else:
                return max(K - S, 0)

        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        from math import erf
        def norm_cdf(x):
            return 0.5 * (1 + erf(x / math.sqrt(2)))

        if option_type == "CE":
            return round(S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2), 2)
        else:
            return round(K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1), 2)

    def suggest_strategies(self, spot, trend="neutral", view_days=7):
        """Suggest simple option strategies based on view."""
        strategies = []

        if trend == "bullish":
            strategies.append({
                "name": "Buy Call (CE)",
                "desc": "Buy ATM or slightly OTM Call",
                "risk": "Premium paid (limited loss)",
                "reward": "Unlimited upside",
                "best_for": "Strong bullish view",
                "strike": round(spot * 1.01, -2),  # Slightly OTM
            })
            strategies.append({
                "name": "Bull Call Spread",
                "desc": "Buy ATM Call + Sell OTM Call",
                "risk": "Net premium (very limited)",
                "reward": "Limited but defined",
                "best_for": "Moderately bullish",
            })
        elif trend == "bearish":
            strategies.append({
                "name": "Buy Put (PE)",
                "desc": "Buy ATM or slightly OTM Put",
                "risk": "Premium paid (limited loss)",
                "reward": "Large downside profit",
                "best_for": "Strong bearish view",
                "strike": round(spot * 0.99, -2),
            })
        else:
            strategies.append({
                "name": "Iron Condor",
                "desc": "Sell OTM Call + Put, Buy further OTM Call + Put",
                "risk": "Defined, limited",
                "reward": "Premium collected if market stays in range",
                "best_for": "Sideways/range-bound market",
            })
            strategies.append({
                "name": "Straddle",
                "desc": "Buy ATM Call + ATM Put",
                "risk": "Total premium of both",
                "reward": "Profit if big move in either direction",
                "best_for": "Expecting big move, unsure of direction",
                "strike": round(spot, -2),
            })

        return strategies

    def format_options_report(self, symbol, chain_data):
        """Format options analysis for display."""
        if not chain_data:
            return "Could not fetch option chain for " + symbol + ". NSE may be blocking requests."

        lines = ["📊 OPTIONS ANALYSIS: " + symbol, "━" * 32]
        lines.append("Spot: Rs." + format(chain_data["spot_price"], ",.2f"))

        if chain_data.get("expiry_dates"):
            lines.append("Next Expiry: " + chain_data["expiry_dates"][0])

        # PCR
        pcr = self.analyze_pcr(chain_data)
        if pcr:
            lines.append("\nPut-Call Ratio (OI): " + str(pcr["pcr_oi"]))
            lines.append("Sentiment: " + pcr["sentiment"])

        # Max Pain
        mp = self.calculate_max_pain(chain_data)
        if mp:
            lines.append("\nMax Pain: " + str(mp["max_pain"]))
            lines.append("Spot vs Max Pain: " + format(mp["difference"], "+,.0f") +
                        " (" + format(mp["difference_pct"], "+.2f") + "%)")

        # Key Strikes
        ks = self.find_key_strikes(chain_data)
        if ks:
            lines.append("\nKey Resistance (highest CE OI):")
            for s in ks["resistance"][:3]:
                lines.append("  " + str(s["strike"]) + " — OI: " + format(s["oi"], ","))
            lines.append("Key Support (highest PE OI):")
            for s in ks["support"][:3]:
                lines.append("  " + str(s["strike"]) + " — OI: " + format(s["oi"], ","))

        lines.append("\n⚠️ Options are complex. Start with learning before trading.")
        return "\n".join(lines)
