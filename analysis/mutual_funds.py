"""
Phase 5: Mutual Fund Tracker
Track NAVs, SIP calculations, MF comparison and recommendations.
Uses free MFAPI (api.mfapi.in) — no authentication needed.
"""
import requests
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MFAPI_BASE = "https://api.mfapi.in/mf"


class MutualFundTracker:
    """Tracks and analyzes Indian mutual funds using free MFAPI."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "FinanceWizBot/1.0"})

    def search_fund(self, query):
        """Search mutual funds by name."""
        try:
            resp = self.session.get(MFAPI_BASE, timeout=10)
            if resp.status_code == 200:
                all_funds = resp.json()
                query_lower = query.lower()
                matches = [f for f in all_funds if query_lower in f.get("schemeName", "").lower()]
                return matches[:10]
        except Exception as e:
            print("MF search error: " + str(e))
        return []

    def get_fund_nav(self, scheme_code):
        """Get latest NAV and history for a fund."""
        try:
            resp = self.session.get(MFAPI_BASE + "/" + str(scheme_code), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                meta = data.get("meta", {})
                nav_data = data.get("data", [])

                if not nav_data:
                    return None

                latest = nav_data[0]
                prev = nav_data[1] if len(nav_data) > 1 else latest

                # Calculate returns
                returns = {}
                for period, days in [("1D", 1), ("1W", 7), ("1M", 30), ("3M", 90), ("6M", 180), ("1Y", 365), ("3Y", 1095)]:
                    if len(nav_data) > days:
                        old_nav = float(nav_data[days]["nav"])
                        current_nav = float(latest["nav"])
                        if old_nav > 0:
                            ret = ((current_nav - old_nav) / old_nav) * 100
                            if days > 365:
                                # Annualize
                                years = days / 365
                                ret = ((current_nav / old_nav) ** (1 / years) - 1) * 100
                            returns[period] = round(ret, 2)

                return {
                    "scheme_code": scheme_code,
                    "name": meta.get("scheme_name", "Unknown"),
                    "fund_house": meta.get("fund_house", "Unknown"),
                    "category": meta.get("scheme_category", "Unknown"),
                    "type": meta.get("scheme_type", "Unknown"),
                    "nav": float(latest["nav"]),
                    "nav_date": latest["date"],
                    "prev_nav": float(prev["nav"]),
                    "change_pct": round(((float(latest["nav"]) - float(prev["nav"])) / float(prev["nav"])) * 100, 2),
                    "returns": returns,
                }
        except Exception as e:
            print("MF NAV error: " + str(e))
        return None

    def calculate_sip(self, monthly_amount, annual_return_pct, years):
        """Calculate SIP returns."""
        monthly_rate = annual_return_pct / 12 / 100
        months = years * 12
        total_invested = monthly_amount * months

        if monthly_rate == 0:
            future_value = total_invested
        else:
            future_value = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)

        wealth_gained = future_value - total_invested

        return {
            "monthly_sip": monthly_amount,
            "annual_return": annual_return_pct,
            "years": years,
            "total_invested": round(total_invested, 0),
            "future_value": round(future_value, 0),
            "wealth_gained": round(wealth_gained, 0),
            "returns_pct": round((wealth_gained / total_invested) * 100, 1),
        }

    def calculate_lumpsum(self, amount, annual_return_pct, years):
        """Calculate lumpsum investment returns."""
        future_value = amount * ((1 + annual_return_pct / 100) ** years)
        return {
            "invested": amount,
            "annual_return": annual_return_pct,
            "years": years,
            "future_value": round(future_value, 0),
            "wealth_gained": round(future_value - amount, 0),
        }

    def compare_funds(self, scheme_codes):
        """Compare multiple mutual funds."""
        results = []
        for code in scheme_codes:
            data = self.get_fund_nav(code)
            if data:
                results.append(data)
        return results

    def get_popular_funds(self):
        """Return popular fund scheme codes for quick access."""
        return {
            "Nifty 50 Index": [
                {"name": "UTI Nifty 50 Index Fund", "code": 120716},
                {"name": "HDFC Index Fund Nifty 50", "code": 101525},
                {"name": "SBI Nifty Index Fund", "code": 119598},
            ],
            "Large Cap": [
                {"name": "Mirae Asset Large Cap Fund", "code": 118834},
                {"name": "Axis Bluechip Fund", "code": 120503},
                {"name": "ICICI Pru Bluechip Fund", "code": 120586},
            ],
            "Flexi Cap": [
                {"name": "Parag Parikh Flexi Cap Fund", "code": 122639},
                {"name": "HDFC Flexi Cap Fund", "code": 118989},
            ],
            "Small Cap": [
                {"name": "SBI Small Cap Fund", "code": 125497},
                {"name": "Nippon India Small Cap Fund", "code": 113177},
            ],
            "ELSS (Tax Saving)": [
                {"name": "Mirae Asset ELSS Tax Saver", "code": 118835},
                {"name": "Axis Long Term Equity Fund", "code": 112323},
            ],
        }

    def format_fund_report(self, fund_data):
        """Format fund data for display."""
        if not fund_data:
            return "Fund data unavailable."

        lines = []
        lines.append("📊 " + fund_data["name"])
        lines.append("━" * 30)
        lines.append("Fund House: " + fund_data["fund_house"])
        lines.append("Category: " + fund_data["category"])
        lines.append("NAV: Rs." + format(fund_data["nav"], ",.4f") + " (" + fund_data["nav_date"] + ")")

        emoji = "🟢" if fund_data["change_pct"] > 0 else "🔴"
        lines.append(emoji + " Day Change: " + format(fund_data["change_pct"], "+.2f") + "%")

        if fund_data["returns"]:
            lines.append("\nReturns:")
            for period, ret in fund_data["returns"].items():
                emoji = "🟢" if ret > 0 else "🔴"
                lines.append("  " + emoji + " " + period + ": " + format(ret, "+.2f") + "%")

        return "\n".join(lines)

    def format_sip_report(self, sip_data):
        """Format SIP calculation."""
        lines = [
            "💰 SIP CALCULATOR",
            "━" * 30,
            "Monthly SIP: Rs." + format(sip_data["monthly_sip"], ","),
            "Expected Return: " + str(sip_data["annual_return"]) + "% p.a.",
            "Duration: " + str(sip_data["years"]) + " years",
            "",
            "Total Invested:  Rs." + format(sip_data["total_invested"], ",.0f"),
            "Future Value:    Rs." + format(sip_data["future_value"], ",.0f"),
            "Wealth Gained:   Rs." + format(sip_data["wealth_gained"], ",.0f"),
            "Returns:         " + str(sip_data["returns_pct"]) + "%",
            "",
        ]

        # Add comparison table
        lines.append("What if you invest more?")
        for multiplier in [2, 5, 10]:
            amt = sip_data["monthly_sip"] * multiplier
            calc = self.calculate_sip(amt, sip_data["annual_return"], sip_data["years"])
            lines.append("  Rs." + format(amt, ",") + "/mo -> Rs." + format(calc["future_value"], ",.0f"))

        return "\n".join(lines)
