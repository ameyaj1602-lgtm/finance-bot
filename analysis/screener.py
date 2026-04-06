"""
Stock Screener — Filter stocks by fundamental and technical criteria.
Usage: /screen pe<25 roe>15 debt<1
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NIFTY_50_SYMBOLS


class StockScreener:
    """Screen stocks based on filters."""

    AVAILABLE_FILTERS = {
        "pe": "PE Ratio (e.g., pe<25)",
        "pb": "Price to Book (e.g., pb<3)",
        "roe": "Return on Equity % (e.g., roe>15)",
        "debt": "Debt to Equity (e.g., debt<1)",
        "div": "Dividend Yield % (e.g., div>1)",
        "mcap": "Market Cap in Cr (e.g., mcap>100000)",
        "growth": "Revenue Growth % (e.g., growth>10)",
        "margin": "Profit Margin % (e.g., margin>10)",
        "beta": "Beta (e.g., beta<1.5)",
        "rsi": "RSI (e.g., rsi<30)",
        "price": "Price in Rs (e.g., price<500)",
    }

    def __init__(self):
        from data.market_data import MarketDataFetcher
        from analysis.technical import TechnicalAnalyzer
        self.fetcher = MarketDataFetcher()
        self.ta = TechnicalAnalyzer()

    def parse_filters(self, filter_string):
        """Parse filter string like 'pe<25 roe>15 debt<1'."""
        import re
        filters = []
        parts = filter_string.strip().split()
        for part in parts:
            match = re.match(r'(\w+)([<>]=?)([\d.]+)', part)
            if match:
                field = match.group(1).lower()
                operator = match.group(2)
                value = float(match.group(3))
                if field in self.AVAILABLE_FILTERS:
                    filters.append({"field": field, "op": operator, "value": value})
        return filters

    def _check_filter(self, actual_value, operator, target_value):
        """Check if a value passes a filter."""
        if actual_value is None:
            return False
        if operator == "<":
            return actual_value < target_value
        elif operator == "<=":
            return actual_value <= target_value
        elif operator == ">":
            return actual_value > target_value
        elif operator == ">=":
            return actual_value >= target_value
        return False

    def screen(self, filter_string, symbols=None):
        """Screen stocks based on filter string."""
        symbols = symbols or NIFTY_50_SYMBOLS
        filters = self.parse_filters(filter_string)

        if not filters:
            return {"error": "No valid filters. Use format: pe<25 roe>15 debt<1\n\nAvailable filters:\n" +
                    "\n".join("  " + k + " — " + v for k, v in self.AVAILABLE_FILTERS.items())}

        results = []

        for symbol in symbols:
            try:
                info = self.fetcher.get_stock_info(symbol)
                if not info:
                    continue

                # Map fields to info values
                field_map = {
                    "pe": info.get("pe_ratio", 0) or 0,
                    "pb": info.get("pb_ratio", 0) or 0,
                    "roe": (info.get("roe", 0) or 0) * 100 if (info.get("roe", 0) or 0) < 1 else (info.get("roe", 0) or 0),
                    "debt": info.get("debt_to_equity", 0) or 0,
                    "div": (info.get("dividend_yield", 0) or 0) * 100 if (info.get("dividend_yield", 0) or 0) < 1 else (info.get("dividend_yield", 0) or 0),
                    "mcap": (info.get("market_cap", 0) or 0) / 1e7,  # Convert to Crores
                    "growth": (info.get("revenue_growth", 0) or 0) * 100 if (info.get("revenue_growth", 0) or 0) < 1 else (info.get("revenue_growth", 0) or 0),
                    "margin": (info.get("profit_margins", 0) or 0) * 100 if (info.get("profit_margins", 0) or 0) < 1 else (info.get("profit_margins", 0) or 0),
                    "beta": info.get("beta", 0) or 0,
                    "price": 0,
                    "rsi": 0,
                }

                # Get price
                live = self.fetcher.get_live_price(symbol)
                if live and live.get("price"):
                    field_map["price"] = live["price"]

                # Get RSI if needed
                rsi_needed = any(f["field"] == "rsi" for f in filters)
                if rsi_needed:
                    df = self.fetcher.get_stock_data(symbol, period="3mo")
                    if df is not None and len(df) >= 50:
                        ta_result = self.ta.analyze(df, symbol)
                        if ta_result:
                            field_map["rsi"] = ta_result["indicators"].get("rsi", 0) or 0

                # Check all filters
                passes = True
                for f in filters:
                    val = field_map.get(f["field"])
                    if val is None or val == 0:
                        # Skip stocks with missing data for this field
                        if f["field"] not in ("div", "growth"):  # These can legitimately be 0
                            passes = False
                            break
                    if not self._check_filter(val, f["op"], f["value"]):
                        passes = False
                        break

                if passes:
                    clean = symbol.replace(".NS", "")
                    results.append({
                        "symbol": clean,
                        "name": info.get("name", clean),
                        "price": field_map.get("price", 0),
                        "pe": round(field_map.get("pe", 0), 1),
                        "roe": round(field_map.get("roe", 0), 1),
                        "debt": round(field_map.get("debt", 0), 2),
                        "mcap_cr": round(field_map.get("mcap", 0), 0),
                        "growth": round(field_map.get("growth", 0), 1),
                    })

            except Exception:
                continue

        return {"filters": filters, "results": results, "total_scanned": len(symbols)}

    def format_screen_report(self, screen_result):
        """Format screening results."""
        if "error" in screen_result:
            return screen_result["error"]

        filters = screen_result["filters"]
        results = screen_result["results"]
        total = screen_result["total_scanned"]

        filter_desc = " & ".join(f["field"] + f["op"] + str(f["value"]) for f in filters)

        lines = [
            "🔍 STOCK SCREENER",
            "━" * 30,
            "Filters: " + filter_desc,
            "Found: " + str(len(results)) + " / " + str(total) + " stocks",
            "",
        ]

        if not results:
            lines.append("No stocks match your filters. Try relaxing the criteria.")
        else:
            for r in results[:15]:
                lines.append(
                    r["symbol"] + " — Rs." + format(r["price"], ",.2f") +
                    " | PE:" + str(r["pe"]) +
                    " | ROE:" + str(r["roe"]) + "%" +
                    " | D/E:" + str(r["debt"])
                )

        return "\n".join(lines)
