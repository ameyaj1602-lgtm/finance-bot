"""
Fundamental Analysis Engine
Evaluates stocks based on financial health, valuation, and growth.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NIFTY_50_SYMBOLS, SECTOR_MAP


class FundamentalAnalyzer:
    """Runs fundamental analysis on stock data."""

    # Benchmark values for Indian market
    BENCHMARKS = {
        "pe_good": 25,        # PE below this is reasonable
        "pe_expensive": 40,   # PE above this is expensive
        "pb_good": 3,
        "roe_good": 15,       # ROE above 15% is good
        "debt_equity_safe": 1.0,
        "dividend_good": 1.5,  # > 1.5% yield is decent
        "revenue_growth_good": 10,
        "profit_margin_good": 10,
    }

    def analyze(self, stock_info):
        """Run fundamental analysis on stock info dict (from MarketDataFetcher.get_stock_info)."""
        if not stock_info:
            return None

        scores = {}
        reasons = []

        # Valuation Score (PE, PB)
        pe = stock_info.get("pe_ratio", 0)
        pb = stock_info.get("pb_ratio", 0)
        val_score = 0
        if pe and pe > 0:
            if pe < self.BENCHMARKS["pe_good"]:
                val_score += 2
                reasons.append(f"PE of {pe:.1f} is reasonable (below {self.BENCHMARKS['pe_good']})")
            elif pe < self.BENCHMARKS["pe_expensive"]:
                val_score += 1
                reasons.append(f"PE of {pe:.1f} is fair")
            else:
                val_score -= 1
                reasons.append(f"PE of {pe:.1f} is expensive")
        if pb and pb > 0:
            if pb < self.BENCHMARKS["pb_good"]:
                val_score += 1
        scores["valuation"] = val_score

        # Profitability Score (ROE, Margins)
        roe = stock_info.get("roe", 0)
        margin = stock_info.get("profit_margins", 0)
        prof_score = 0
        if roe and roe > 0:
            roe_pct = roe * 100 if roe < 1 else roe
            if roe_pct > self.BENCHMARKS["roe_good"]:
                prof_score += 2
                reasons.append(f"ROE of {roe_pct:.1f}% is strong")
            elif roe_pct > 10:
                prof_score += 1
            else:
                reasons.append(f"ROE of {roe_pct:.1f}% is weak")
        if margin and margin > 0:
            margin_pct = margin * 100 if margin < 1 else margin
            if margin_pct > self.BENCHMARKS["profit_margin_good"]:
                prof_score += 1
        scores["profitability"] = prof_score

        # Growth Score
        rev_growth = stock_info.get("revenue_growth", 0)
        growth_score = 0
        if rev_growth and rev_growth > 0:
            rev_pct = rev_growth * 100 if rev_growth < 1 else rev_growth
            if rev_pct > self.BENCHMARKS["revenue_growth_good"]:
                growth_score += 2
                reasons.append(f"Revenue growing at {rev_pct:.1f}%")
            elif rev_pct > 5:
                growth_score += 1
        scores["growth"] = growth_score

        # Safety Score (Debt, Beta)
        debt = stock_info.get("debt_to_equity", 0)
        beta = stock_info.get("beta", 1)
        safety_score = 0
        if debt is not None and debt >= 0:
            if debt < self.BENCHMARKS["debt_equity_safe"]:
                safety_score += 2
                reasons.append(f"Low debt (D/E: {debt:.2f})")
            elif debt < 2:
                safety_score += 1
            else:
                safety_score -= 1
                reasons.append(f"High debt (D/E: {debt:.2f}) — risky")
        if beta and beta > 0:
            if beta < 1.2:
                safety_score += 1
            elif beta > 1.5:
                reasons.append(f"High beta ({beta:.2f}) — very volatile")
        scores["safety"] = safety_score

        # Dividend Score
        div_yield = stock_info.get("dividend_yield", 0)
        div_score = 0
        if div_yield and div_yield > 0:
            div_pct = div_yield * 100 if div_yield < 1 else div_yield
            if div_pct > self.BENCHMARKS["dividend_good"]:
                div_score += 2
                reasons.append(f"Good dividend yield ({div_pct:.1f}%)")
            elif div_pct > 0.5:
                div_score += 1
        scores["dividend"] = div_score

        # 52-week position
        high_52 = stock_info.get("52w_high", 0)
        low_52 = stock_info.get("52w_low", 0)
        if high_52 and low_52 and high_52 > low_52:
            range_52 = high_52 - low_52
            # Can't determine current price from info alone, but we note the range
            reasons.append(f"52W range: ₹{low_52:.0f} — ₹{high_52:.0f}")

        # Overall Rating
        total = sum(scores.values())
        max_possible = 10  # rough max
        if total >= 7:
            rating = "EXCELLENT"
        elif total >= 5:
            rating = "GOOD"
        elif total >= 3:
            rating = "AVERAGE"
        elif total >= 1:
            rating = "BELOW AVERAGE"
        else:
            rating = "POOR"

        return {
            "name": stock_info.get("name", "Unknown"),
            "sector": stock_info.get("sector", "Unknown"),
            "rating": rating,
            "total_score": total,
            "scores": scores,
            "reasons": reasons,
            "key_metrics": {
                "pe": pe,
                "pb": pb,
                "roe": round((roe or 0) * 100, 1) if roe and roe < 1 else roe,
                "debt_to_equity": debt,
                "revenue_growth": round((rev_growth or 0) * 100, 1) if rev_growth and rev_growth < 1 else rev_growth,
                "dividend_yield": round((div_yield or 0) * 100, 2) if div_yield and div_yield < 1 else div_yield,
                "market_cap_cr": round(stock_info.get("market_cap", 0) / 1e7, 0),
                "eps": stock_info.get("eps", 0),
                "beta": beta,
            },
        }

    def screen_stocks(self, stock_infos):
        """Screen multiple stocks and rank them."""
        results = []
        for symbol, info in stock_infos.items():
            analysis = self.analyze(info)
            if analysis:
                analysis["symbol"] = symbol.replace(".NS", "")
                results.append(analysis)

        # Sort by total score
        results.sort(key=lambda x: x["total_score"], reverse=True)
        return results

    def get_sector_summary(self, stock_infos):
        """Summarize fundamentals by sector."""
        sector_data = {}
        for sector, symbols in SECTOR_MAP.items():
            sector_scores = []
            for sym in symbols:
                if sym in stock_infos:
                    analysis = self.analyze(stock_infos[sym])
                    if analysis:
                        sector_scores.append(analysis["total_score"])

            if sector_scores:
                sector_data[sector] = {
                    "avg_score": round(sum(sector_scores) / len(sector_scores), 1),
                    "stocks_analyzed": len(sector_scores),
                    "best_score": max(sector_scores),
                }

        return dict(sorted(sector_data.items(), key=lambda x: x[1]["avg_score"], reverse=True))

    def format_report(self, analysis):
        """Format fundamental analysis into readable text."""
        if not analysis:
            return "No data available"

        lines = []
        lines.append(f"📊 {analysis.get('name', analysis.get('symbol', 'Unknown'))}")
        lines.append(f"Rating: {analysis['rating']} (Score: {analysis['total_score']}/10)")
        lines.append("")

        km = analysis["key_metrics"]
        lines.append("Key Metrics:")
        if km.get("pe"): lines.append(f"  PE Ratio: {km['pe']:.1f}")
        if km.get("roe"): lines.append(f"  ROE: {km['roe']}%")
        if km.get("debt_to_equity") is not None: lines.append(f"  Debt/Equity: {km['debt_to_equity']:.2f}")
        if km.get("revenue_growth"): lines.append(f"  Revenue Growth: {km['revenue_growth']}%")
        if km.get("market_cap_cr"): lines.append(f"  Market Cap: ₹{km['market_cap_cr']:,.0f} Cr")
        if km.get("dividend_yield"): lines.append(f"  Dividend Yield: {km['dividend_yield']}%")

        if analysis["reasons"]:
            lines.append("")
            lines.append("Analysis:")
            for r in analysis["reasons"]:
                lines.append(f"  • {r}")

        return "\n".join(lines)
