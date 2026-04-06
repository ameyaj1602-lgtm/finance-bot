"""
Goal Planner + Tax Calculator for Indian investors.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GoalPlanner:
    """Plan financial goals and calculate required SIP."""

    def plan_goal(self, target_amount, years, expected_return_pct=12):
        """Calculate monthly SIP needed to reach a goal."""
        monthly_rate = expected_return_pct / 12 / 100
        months = years * 12

        if monthly_rate == 0:
            monthly_sip = target_amount / months
        else:
            monthly_sip = target_amount / (((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate))

        total_invested = monthly_sip * months
        wealth_gained = target_amount - total_invested

        return {
            "target": target_amount,
            "years": years,
            "expected_return": expected_return_pct,
            "monthly_sip": round(monthly_sip, 0),
            "total_invested": round(total_invested, 0),
            "wealth_gained": round(wealth_gained, 0),
        }

    def retirement_plan(self, current_age, retire_age, monthly_expense, inflation=7):
        """Calculate retirement corpus needed."""
        years_to_retire = retire_age - current_age
        years_in_retirement = 85 - retire_age  # Assume 85 life expectancy

        # Future monthly expense at retirement (with inflation)
        future_expense = monthly_expense * ((1 + inflation / 100) ** years_to_retire)

        # Total corpus needed (simplified: 25x annual expense)
        annual_expense = future_expense * 12
        corpus_needed = annual_expense * 25  # 4% withdrawal rule

        # SIP needed
        goal = self.plan_goal(corpus_needed, years_to_retire, 12)

        return {
            "current_age": current_age,
            "retire_age": retire_age,
            "years_to_retire": years_to_retire,
            "current_monthly_expense": monthly_expense,
            "future_monthly_expense": round(future_expense, 0),
            "corpus_needed": round(corpus_needed, 0),
            "monthly_sip_needed": goal["monthly_sip"],
        }

    def format_goal_report(self, goal):
        """Format goal plan for display."""
        lines = [
            "🎯 GOAL PLANNER",
            "━" * 30,
            "Target: Rs." + format(goal["target"], ",.0f"),
            "Timeline: " + str(goal["years"]) + " years",
            "Expected Return: " + str(goal["expected_return"]) + "% p.a.",
            "",
            "💰 Monthly SIP Needed: Rs." + format(goal["monthly_sip"], ",.0f"),
            "Total You'll Invest:   Rs." + format(goal["total_invested"], ",.0f"),
            "Market Will Add:       Rs." + format(goal["wealth_gained"], ",.0f"),
            "",
        ]

        # Show at different return rates
        lines.append("What if returns differ?")
        for ret in [8, 10, 12, 15]:
            alt = self.plan_goal(goal["target"], goal["years"], ret)
            lines.append("  At " + str(ret) + "%: Rs." + format(alt["monthly_sip"], ",.0f") + "/month")

        return "\n".join(lines)

    def format_retirement_report(self, plan):
        """Format retirement plan."""
        lines = [
            "🏖️ RETIREMENT PLANNER",
            "━" * 30,
            "Current Age: " + str(plan["current_age"]),
            "Retire At: " + str(plan["retire_age"]),
            "Years to Retire: " + str(plan["years_to_retire"]),
            "",
            "Current Monthly Expense: Rs." + format(plan["current_monthly_expense"], ",.0f"),
            "Expense at Retirement:   Rs." + format(plan["future_monthly_expense"], ",.0f") + " (after inflation)",
            "",
            "💰 Corpus Needed: Rs." + format(plan["corpus_needed"], ",.0f"),
            "📊 Monthly SIP:   Rs." + format(plan["monthly_sip_needed"], ",.0f"),
            "",
            "Based on: 12% returns, 7% inflation, 4% withdrawal rule",
        ]
        return "\n".join(lines)


class TaxCalculator:
    """Calculate Indian stock market taxes."""

    # FY 2024-25 rates (updated as per budget)
    STCG_RATE = 20  # Short Term Capital Gains (equity, held < 1 year)
    LTCG_RATE = 12.5  # Long Term Capital Gains (equity, held > 1 year)
    LTCG_EXEMPTION = 125000  # Rs. 1.25 lakh exemption per year
    INTRADAY_TAX = "slab"  # Taxed as business income (slab rates)
    STT_DELIVERY = 0.1  # STT on delivery (both buy and sell)
    STT_INTRADAY = 0.025  # STT on intraday (sell side only)

    def calculate_equity_tax(self, buy_price, sell_price, quantity, holding_days):
        """Calculate tax on equity trade."""
        buy_value = buy_price * quantity
        sell_value = sell_price * quantity
        profit = sell_value - buy_value

        if profit <= 0:
            return {
                "profit": round(profit, 2),
                "tax": 0,
                "type": "LOSS",
                "note": "Losses can be set off against gains. Short-term loss against any capital gains. Long-term loss against long-term gains only.",
                "stt": round(sell_value * self.STT_DELIVERY / 100, 2),
            }

        is_long_term = holding_days >= 365

        if is_long_term:
            taxable = max(0, profit - self.LTCG_EXEMPTION)
            tax = taxable * self.LTCG_RATE / 100
            tax_type = "LTCG"
            note = "Long-term: Held > 1 year. First Rs." + format(self.LTCG_EXEMPTION, ",") + " exempt. " + str(self.LTCG_RATE) + "% on rest."
        else:
            tax = profit * self.STCG_RATE / 100
            tax_type = "STCG"
            taxable = profit
            note = "Short-term: Held < 1 year. Flat " + str(self.STCG_RATE) + "% tax."

        stt = sell_value * self.STT_DELIVERY / 100

        return {
            "buy_value": round(buy_value, 2),
            "sell_value": round(sell_value, 2),
            "profit": round(profit, 2),
            "holding_days": holding_days,
            "type": tax_type,
            "taxable_amount": round(taxable, 2),
            "tax": round(tax, 2),
            "stt": round(stt, 2),
            "total_charges": round(tax + stt, 2),
            "net_profit": round(profit - tax - stt, 2),
            "note": note,
        }

    def calculate_intraday_tax(self, profit, tax_slab_rate=30):
        """Calculate tax on intraday trading."""
        if profit <= 0:
            return {
                "profit": profit,
                "tax": 0,
                "type": "INTRADAY LOSS",
                "note": "Intraday losses can only be set off against intraday/speculative income.",
            }

        tax = profit * tax_slab_rate / 100

        return {
            "profit": round(profit, 2),
            "type": "INTRADAY",
            "tax_rate": str(tax_slab_rate) + "% (your slab rate)",
            "tax": round(tax, 2),
            "net_profit": round(profit - tax, 2),
            "note": "Intraday profits are taxed as speculative business income at your income tax slab rate.",
        }

    def format_tax_report(self, result):
        """Format tax calculation."""
        lines = [
            "🧾 TAX CALCULATOR",
            "━" * 30,
            "Type: " + result["type"],
        ]

        if result.get("buy_value"):
            lines.append("Buy Value: Rs." + format(result["buy_value"], ",.2f"))
            lines.append("Sell Value: Rs." + format(result["sell_value"], ",.2f"))

        emoji = "🟢" if result["profit"] > 0 else "🔴"
        lines.append(emoji + " Profit: Rs." + format(result["profit"], "+,.2f"))

        if result.get("holding_days"):
            lines.append("Held: " + str(result["holding_days"]) + " days")

        if result.get("taxable_amount"):
            lines.append("Taxable Amount: Rs." + format(result["taxable_amount"], ",.2f"))

        lines.append("Tax: Rs." + format(result["tax"], ",.2f"))

        if result.get("stt"):
            lines.append("STT: Rs." + format(result["stt"], ",.2f"))

        if result.get("net_profit"):
            lines.append("Net Profit (after tax): Rs." + format(result["net_profit"], "+,.2f"))

        lines.append("")
        lines.append("ℹ️ " + result["note"])

        return "\n".join(lines)
