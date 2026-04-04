"""
Market Data Pipeline — fetches stock data from free sources.
Yahoo Finance for prices, NSE website for FII/DII and market breadth.
"""
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NIFTY_50_SYMBOLS, INDICES, DB_PATH


class MarketDataFetcher:
    """Fetches all market data from free sources."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for caching."""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS price_cache (
                symbol TEXT,
                date TEXT,
                open REAL, high REAL, low REAL, close REAL,
                volume INTEGER, adj_close REAL,
                PRIMARY KEY (symbol, date)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS fii_dii_data (
                date TEXT PRIMARY KEY,
                fii_buy REAL, fii_sell REAL, fii_net REAL,
                dii_buy REAL, dii_sell REAL, dii_net REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                action TEXT,
                price REAL,
                quantity INTEGER,
                stop_loss REAL,
                target REAL,
                status TEXT DEFAULT 'open',
                exit_price REAL,
                exit_timestamp TEXT,
                pnl REAL,
                reason TEXT
            )
        """)
        conn.commit()
        conn.close()

    # ── Price Data ───────────────────────────────────────────────

    def get_stock_data(self, symbol, period="6mo", interval="1d"):
        """Fetch historical OHLCV data for a single stock."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return None
            df.index = df.index.tz_localize(None)
            return df
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    def get_intraday_data(self, symbol, interval="15m"):
        """Fetch intraday data (last 5 days at 15m intervals)."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d", interval=interval)
            if df.empty:
                return None
            df.index = df.index.tz_localize(None)
            return df
        except Exception as e:
            print(f"Error fetching intraday {symbol}: {e}")
            return None

    def get_bulk_data(self, symbols=None, period="3mo"):
        """Fetch data for all Nifty 50 stocks."""
        symbols = symbols or NIFTY_50_SYMBOLS
        data = {}
        # Use yfinance download for bulk (faster)
        try:
            raw = yf.download(symbols, period=period, group_by="ticker", threads=True)
            for sym in symbols:
                try:
                    df = raw[sym].dropna()
                    if not df.empty:
                        data[sym] = df
                except (KeyError, TypeError):
                    pass
        except Exception as e:
            print(f"Bulk download failed, falling back to individual: {e}")
            for sym in symbols:
                df = self.get_stock_data(sym, period=period)
                if df is not None:
                    data[sym] = df
        return data

    def get_index_data(self, period="3mo"):
        """Fetch all major index data."""
        index_data = {}
        for name, symbol in INDICES.items():
            df = self.get_stock_data(symbol, period=period)
            if df is not None:
                index_data[name] = df
        return index_data

    def get_live_price(self, symbol):
        """Get current/last price for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            return {
                "price": info.get("lastPrice", info.get("regularMarketPrice", 0)),
                "change": info.get("regularMarketPrice", 0) - info.get("regularMarketPreviousClose", 0),
                "change_pct": ((info.get("regularMarketPrice", 0) - info.get("regularMarketPreviousClose", 0))
                              / info.get("regularMarketPreviousClose", 1)) * 100
                              if info.get("regularMarketPreviousClose", 0) else 0,
                "volume": info.get("lastVolume", 0),
                "day_high": info.get("dayHigh", 0),
                "day_low": info.get("dayLow", 0),
            }
        except Exception as e:
            print(f"Error getting live price for {symbol}: {e}")
            return None

    def get_stock_info(self, symbol):
        """Get fundamental info for a stock."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "name": info.get("longName", symbol),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "forward_pe": info.get("forwardPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "roe": info.get("returnOnEquity", 0),
                "debt_to_equity": info.get("debtToEquity", 0),
                "revenue_growth": info.get("revenueGrowth", 0),
                "profit_margins": info.get("profitMargins", 0),
                "52w_high": info.get("fiftyTwoWeekHigh", 0),
                "52w_low": info.get("fiftyTwoWeekLow", 0),
                "avg_volume": info.get("averageVolume", 0),
                "beta": info.get("beta", 0),
                "book_value": info.get("bookValue", 0),
                "eps": info.get("trailingEps", 0),
            }
        except Exception as e:
            print(f"Error fetching info for {symbol}: {e}")
            return None

    # ── FII/DII Data ─────────────────────────────────────────────

    def get_fii_dii_data(self):
        """Scrape FII/DII activity from NSE or MoneyControl."""
        try:
            url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/data.json"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data
        except Exception:
            pass

        # Fallback: try NSDL
        try:
            url = "https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return {"source": "nsdl", "note": "Check manually at fpi.nsdl.co.in"}
        except Exception:
            pass

        return {"fii_net": "N/A", "dii_net": "N/A", "note": "Data temporarily unavailable"}

    # ── Market Breadth ───────────────────────────────────────────

    def get_market_breadth(self, stock_data_dict):
        """Calculate market breadth from stock data."""
        advancing = 0
        declining = 0
        unchanged = 0

        for symbol, df in stock_data_dict.items():
            if df is not None and len(df) >= 2:
                last_close = df["Close"].iloc[-1]
                prev_close = df["Close"].iloc[-2]
                if last_close > prev_close:
                    advancing += 1
                elif last_close < prev_close:
                    declining += 1
                else:
                    unchanged += 1

        return {
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "advance_decline_ratio": round(advancing / max(declining, 1), 2),
        }

    # ── Top Movers ───────────────────────────────────────────────

    def get_top_movers(self, stock_data_dict, n=5):
        """Get top gainers and losers."""
        changes = []
        for symbol, df in stock_data_dict.items():
            if df is not None and len(df) >= 2:
                last = df["Close"].iloc[-1]
                prev = df["Close"].iloc[-2]
                pct = ((last - prev) / prev) * 100
                clean_name = symbol.replace(".NS", "")
                changes.append({"symbol": clean_name, "price": round(last, 2), "change_pct": round(pct, 2)})

        changes.sort(key=lambda x: x["change_pct"], reverse=True)
        return {
            "gainers": changes[:n],
            "losers": changes[-n:][::-1],
        }

    # ── Global Cues ──────────────────────────────────────────────

    def get_global_cues(self):
        """Fetch global market data."""
        global_symbols = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "Dow Jones": "^DJI",
            "Crude Oil": "CL=F",
            "Gold": "GC=F",
            "USD/INR": "INR=X",
            "US 10Y Yield": "^TNX",
        }
        cues = {}
        for name, sym in global_symbols.items():
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    last = hist["Close"].iloc[-1]
                    prev = hist["Close"].iloc[-2]
                    pct = ((last - prev) / prev) * 100
                    cues[name] = {"value": round(last, 2), "change_pct": round(pct, 2)}
                elif len(hist) == 1:
                    cues[name] = {"value": round(hist["Close"].iloc[-1], 2), "change_pct": 0}
            except Exception:
                pass
        return cues


# Quick test
if __name__ == "__main__":
    fetcher = MarketDataFetcher()
    print("Fetching Nifty 50 data...")
    nifty = fetcher.get_stock_data("^NSEI", period="1mo")
    if nifty is not None:
        print(f"Nifty Last Close: {nifty['Close'].iloc[-1]:.2f}")

    print("\nFetching global cues...")
    cues = fetcher.get_global_cues()
    for name, data in cues.items():
        print(f"  {name}: {data['value']} ({data['change_pct']:+.2f}%)")

    print("\nFetching top movers...")
    bulk = fetcher.get_bulk_data(NIFTY_50_SYMBOLS[:10], period="5d")
    movers = fetcher.get_top_movers(bulk)
    print("Top Gainers:")
    for g in movers["gainers"][:3]:
        print(f"  {g['symbol']}: {g['change_pct']:+.2f}%")
