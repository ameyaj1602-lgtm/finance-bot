"""
Phase 10: Portfolio Intelligence
Advanced portfolio analysis, allocation, and rebalancing.
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SECTOR_MAP


class PortfolioIntelligence:
    """Advanced portfolio analysis and recommendations."""

    def analyze_portfolio(self, holdings, stock_infos):
        """Full portfolio analysis given holdings and stock info.
        holdings: list of {"symbol": "RELIANCE", "quantity": 10, "avg_price": 2800}
        stock_infos: dict of symbol -> stock_info from MarketDataFetcher
        """
        if not holdings:
            return {"error": "No holdings to analyze."}

        total_value = 0
        total_invested = 0
        sector_allocation = defaultdict(float)
        stock_analysis = []

        for h in holdings:
            symbol = h["symbol"]
            qty = h["quantity"]
            avg_price = h["avg_price"]
            full_sym = symbol + ".NS" if not symbol.endswith(".NS") else symbol

            info = stock_infos.get(full_sym, stock_infos.get(symbol, {}))
            current_price = info.get("current_price", avg_price)  # fallback
            market_value = current_price * qty
            invested = avg_price * qty
            pnl = market_value - invested
            pnl_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0

            total_value += market_value
            total_invested += invested

            # Find sector
            clean = symbol.replace(".NS", "") + ".NS"
            sector = "Other"
            for sec, symbols in SECTOR_MAP.items():
                if clean in symbols:
                    sector = sec
                    break
            sector_allocation[sector] += market_value

            stock_analysis.append({
                "symbol": symbol.replace(".NS", ""),
                "qty": qty,
                "avg_price": avg_price,
                "current_price": current_price,
                "market_value": round(market_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "weight_pct": 0,  # calculated below
                "sector": sector,
            })

        # Calculate weights
        for s in stock_analysis:
            s["weight_pct"] = round((s["market_value"] / total_value) * 100, 1) if total_value > 0 else 0

        # Sector weights
        sector_weights = {}
        for sec, val in sector_allocation.items():
            sector_weights[sec] = round((val / total_value) * 100, 1) if total_value > 0 else 0

        # Warnings
        warnings = []
        # Concentration risk
        for s in stock_analysis:
            if s["weight_pct"] > 25:
                warnings.append("HIGH CONCENTRATION: " + s["symbol"] + " is " + str(s["weight_pct"]) + "% of portfolio. Consider diversifying.")
        for sec, wt in sector_weights.items():
            if wt > 40:
                warnings.append("SECTOR OVERWEIGHT: " + sec + " is " + str(wt) + "% of portfolio. Too much exposure to one sector.")

        # Too few stocks
        if len(stock_analysis) < 5:
            warnings.append("UNDER-DIVERSIFIED: Only " + str(len(stock_analysis)) + " stocks. Aim for at least 8-10 across different sectors.")

        # Losers held too long
        for s in stock_analysis:
            if s["pnl_pct"] < -15:
                warnings.append("BIG LOSER: " + s["symbol"] + " is down " + format(s["pnl_pct"], ".1f") + "%. Review if thesis still holds.")

        # Rebalancing suggestions
        rebalance = []
        stock_analysis.sort(key=lambda x: x["weight_pct"], reverse=True)
        for s in stock_analysis:
            if s["weight_pct"] > 20:
                rebalance.append("TRIM: " + s["symbol"] + " (" + str(s["weight_pct"]) + "%) — sell some to reduce concentration")
            if s["pnl_pct"] > 50:
                rebalance.append("BOOK PROFITS: " + s["symbol"] + " is up " + format(s["pnl_pct"], ".1f") + "%. Consider partial profit booking.")

        total_pnl = total_value - total_invested

        return {
            "total_invested": round(total_invested, 2),
            "current_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_return_pct": round((total_pnl / total_invested) * 100, 2) if total_invested > 0 else 0,
            "num_stocks": len(stock_analysis),
            "stocks": stock_analysis,
            "sector_allocation": dict(sorted(sector_weights.items(), key=lambda x: x[1], reverse=True)),
            "warnings": warnings,
            "rebalance_suggestions": rebalance,
        }

    def suggest_diversification(self, current_sectors):
        """Suggest sectors to add for better diversification."""
        all_sectors = set(SECTOR_MAP.keys())
        held_sectors = set(current_sectors.keys())
        missing = all_sectors - held_sectors

        suggestions = []
        if "Banking" not in held_sectors:
            suggestions.append("Add Banking: HDFCBANK or ICICIBANK — backbone of Indian economy")
        if "IT" not in held_sectors:
            suggestions.append("Add IT: TCS or INFY — global revenue, hedge against rupee weakness")
        if "FMCG" not in held_sectors:
            suggestions.append("Add FMCG: ITC or HINDUNILVR — defensive, steady growers")
        if "Pharma" not in held_sectors:
            suggestions.append("Add Pharma: SUNPHARMA or CIPLA — defensive sector")

        return {"missing_sectors": list(missing), "suggestions": suggestions}

    def format_portfolio_report(self, analysis):
        """Format portfolio analysis for display."""
        if "error" in analysis:
            return analysis["error"]

        lines = [
            "💼 PORTFOLIO INTELLIGENCE",
            "━" * 32,
            "Total Invested: Rs." + format(analysis["total_invested"], ",.0f"),
            "Current Value:  Rs." + format(analysis["current_value"], ",.0f"),
        ]

        emoji = "🟢" if analysis["total_pnl"] > 0 else "🔴"
        lines.append(emoji + " P&L: Rs." + format(analysis["total_pnl"], "+,.0f") +
                     " (" + format(analysis["total_return_pct"], "+.2f") + "%)")
        lines.append("")

        # Holdings
        lines.append("📋 HOLDINGS (" + str(analysis["num_stocks"]) + " stocks):")
        for s in analysis["stocks"]:
            emoji = "🟢" if s["pnl"] > 0 else "🔴"
            lines.append("  " + emoji + " " + s["symbol"] + ": Rs." + format(s["current_price"], ",.2f") +
                        " | " + format(s["pnl_pct"], "+.1f") + "% | " + str(s["weight_pct"]) + "% of portfolio")

        # Sector allocation
        lines.append("\n🏭 SECTOR ALLOCATION:")
        for sec, wt in analysis["sector_allocation"].items():
            bar = "█" * min(int(wt / 5), 10)
            lines.append("  " + sec + ": " + str(wt) + "% " + bar)

        # Warnings
        if analysis["warnings"]:
            lines.append("\n⚠️ WARNINGS:")
            for w in analysis["warnings"]:
                lines.append("  ⚠️ " + w)

        # Rebalancing
        if analysis["rebalance_suggestions"]:
            lines.append("\n🔄 REBALANCING:")
            for r in analysis["rebalance_suggestions"]:
                lines.append("  → " + r)

        return "\n".join(lines)
