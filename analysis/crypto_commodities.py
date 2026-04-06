"""
Crypto, Gold, Silver, Crude, Currency Tracker
All free via Yahoo Finance.
"""
import yfinance as yf
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


CRYPTO_SYMBOLS = {
    "Bitcoin": "BTC-INR",
    "Ethereum": "ETH-INR",
    "Solana": "SOL-INR",
    "XRP": "XRP-INR",
    "Dogecoin": "DOGE-INR",
    "Cardano": "ADA-INR",
    "Polygon": "MATIC-INR",
}

COMMODITY_SYMBOLS = {
    "Gold (MCX)": "GC=F",
    "Silver": "SI=F",
    "Crude Oil": "CL=F",
    "Natural Gas": "NG=F",
    "Copper": "HG=F",
}

CURRENCY_SYMBOLS = {
    "USD/INR": "USDINR=X",
    "EUR/INR": "EURINR=X",
    "GBP/INR": "GBPINR=X",
    "JPY/INR": "JPYINR=X",
}


class CryptoCommodityTracker:
    """Tracks crypto, commodities, and currencies."""

    def get_crypto_prices(self):
        """Get all crypto prices in INR."""
        results = []
        for name, symbol in CRYPTO_SYMBOLS.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if hist is not None and len(hist) >= 1:
                    price = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
                    pct = ((price - prev) / prev) * 100 if prev > 0 else 0
                    results.append({
                        "name": name, "symbol": symbol,
                        "price": round(price, 2), "change_pct": round(pct, 2),
                    })
            except Exception:
                pass
        return results

    def get_commodity_prices(self):
        """Get commodity prices (USD)."""
        results = []
        for name, symbol in COMMODITY_SYMBOLS.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if hist is not None and len(hist) >= 1:
                    price = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
                    pct = ((price - prev) / prev) * 100 if prev > 0 else 0
                    results.append({
                        "name": name, "symbol": symbol,
                        "price": round(price, 2), "change_pct": round(pct, 2),
                    })
            except Exception:
                pass
        return results

    def get_currency_rates(self):
        """Get currency exchange rates."""
        results = []
        for name, symbol in CURRENCY_SYMBOLS.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if hist is not None and len(hist) >= 1:
                    price = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
                    pct = ((price - prev) / prev) * 100 if prev > 0 else 0
                    results.append({
                        "name": name, "symbol": symbol,
                        "rate": round(price, 4), "change_pct": round(pct, 2),
                    })
            except Exception:
                pass
        return results

    def format_crypto_report(self):
        """Format crypto prices for Telegram."""
        cryptos = self.get_crypto_prices()
        if not cryptos:
            return "Could not fetch crypto prices."

        lines = ["₿ CRYPTO PRICES (INR)", "━" * 30]
        for c in cryptos:
            emoji = "🟢" if c["change_pct"] > 0 else "🔴" if c["change_pct"] < 0 else "⚪"
            pct_str = ("+" if c["change_pct"] > 0 else "") + format(c["change_pct"], ".2f") + "%"
            lines.append(emoji + " " + c["name"] + ": Rs." + format(c["price"], ",.2f") + " (" + pct_str + ")")
        return "\n".join(lines)

    def format_commodity_report(self):
        """Format commodity prices."""
        commodities = self.get_commodity_prices()
        if not commodities:
            return "Could not fetch commodity prices."

        lines = ["🏆 COMMODITIES", "━" * 30]
        for c in commodities:
            emoji = "🟢" if c["change_pct"] > 0 else "🔴" if c["change_pct"] < 0 else "⚪"
            pct_str = ("+" if c["change_pct"] > 0 else "") + format(c["change_pct"], ".2f") + "%"
            lines.append(emoji + " " + c["name"] + ": $" + format(c["price"], ",.2f") + " (" + pct_str + ")")
        return "\n".join(lines)

    def format_currency_report(self):
        """Format currency rates."""
        currencies = self.get_currency_rates()
        if not currencies:
            return "Could not fetch currency rates."

        lines = ["💱 CURRENCY RATES", "━" * 30]
        for c in currencies:
            emoji = "🟢" if c["change_pct"] > 0 else "🔴" if c["change_pct"] < 0 else "⚪"
            pct_str = ("+" if c["change_pct"] > 0 else "") + format(c["change_pct"], ".2f") + "%"
            lines.append(emoji + " " + c["name"] + ": Rs." + format(c["rate"], ",.4f") + " (" + pct_str + ")")
        return "\n".join(lines)

    def format_full_report(self):
        """Full crypto + commodity + currency report."""
        parts = [
            self.format_crypto_report(),
            "",
            self.format_commodity_report(),
            "",
            self.format_currency_report(),
        ]
        return "\n".join(parts)
