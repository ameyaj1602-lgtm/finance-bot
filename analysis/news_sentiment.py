"""
Phase 6: News & Sentiment Engine
Scrapes financial news and analyzes sentiment.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY, ANTHROPIC_API_KEY


class NewsSentimentEngine:
    """Scrapes financial news and analyzes market sentiment."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
        }

    def get_market_news(self, limit=10):
        """Get latest market news from multiple sources."""
        news = []
        news.extend(self._fetch_google_news_rss("Indian stock market", limit))
        news.extend(self._fetch_google_news_rss("Nifty Sensex", limit))
        # Deduplicate by title similarity
        seen = set()
        unique = []
        for n in news:
            title_key = n["title"][:50].lower()
            if title_key not in seen:
                seen.add(title_key)
                unique.append(n)
        return unique[:limit]

    def get_stock_news(self, symbol, limit=5):
        """Get news for a specific stock."""
        clean = symbol.replace(".NS", "").replace("_", " ")
        return self._fetch_google_news_rss(clean + " stock NSE", limit)

    def get_sector_news(self, sector, limit=5):
        """Get news for a sector."""
        return self._fetch_google_news_rss("India " + sector + " sector stocks", limit)

    def analyze_sentiment(self, news_items):
        """Analyze sentiment of news items."""
        if not news_items:
            return {"overall": "neutral", "score": 0, "details": []}

        # Keyword-based sentiment (works without AI)
        bullish_words = [
            "surge", "rally", "gains", "bullish", "record high", "breakout",
            "positive", "growth", "profit", "upgrade", "buy", "outperform",
            "strong", "boom", "recovery", "beat", "exceeds", "optimistic",
            "FII buying", "DII buying", "green", "up", "rises", "jumps",
        ]
        bearish_words = [
            "crash", "fall", "drops", "bearish", "selloff", "decline",
            "negative", "loss", "downgrade", "sell", "underperform",
            "weak", "slump", "correction", "recession", "misses", "fear",
            "FII selling", "red", "down", "sinks", "plunge", "tumble",
        ]

        details = []
        total_score = 0

        for item in news_items:
            title = item.get("title", "").lower()
            score = 0
            for word in bullish_words:
                if word in title:
                    score += 1
            for word in bearish_words:
                if word in title:
                    score -= 1

            sentiment = "bullish" if score > 0 else "bearish" if score < 0 else "neutral"
            details.append({
                "title": item["title"],
                "sentiment": sentiment,
                "score": score,
                "source": item.get("source", ""),
                "time": item.get("published", ""),
            })
            total_score += score

        avg_score = total_score / len(news_items) if news_items else 0
        overall = "bullish" if avg_score > 0.3 else "bearish" if avg_score < -0.3 else "neutral"

        return {
            "overall": overall,
            "score": round(avg_score, 2),
            "bullish_count": sum(1 for d in details if d["sentiment"] == "bullish"),
            "bearish_count": sum(1 for d in details if d["sentiment"] == "bearish"),
            "neutral_count": sum(1 for d in details if d["sentiment"] == "neutral"),
            "details": details,
        }

    def get_earnings_calendar(self):
        """Get upcoming earnings/results dates."""
        # Scrape from MoneyControl or similar
        try:
            url = "https://www.moneycontrol.com/earnings/results-calendar.html"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Basic extraction
                earnings = []
                tables = soup.find_all("table")
                for table in tables[:1]:
                    rows = table.find_all("tr")
                    for row in rows[1:10]:
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            earnings.append({
                                "company": cols[0].get_text(strip=True),
                                "date": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                            })
                return earnings
        except Exception:
            pass

        return [{"company": "Check moneycontrol.com for earnings calendar", "date": ""}]

    def format_news_report(self, news_items, sentiment=None):
        """Format news for Telegram display."""
        if not news_items:
            return "No news available right now."

        lines = ["📰 MARKET NEWS", "━" * 30]

        if sentiment:
            emoji_map = {"bullish": "🟢 BULLISH", "bearish": "🔴 BEARISH", "neutral": "⚪ NEUTRAL"}
            lines.append("Sentiment: " + emoji_map.get(sentiment["overall"], "NEUTRAL"))
            lines.append("Bullish: " + str(sentiment["bullish_count"]) +
                         " | Bearish: " + str(sentiment["bearish_count"]) +
                         " | Neutral: " + str(sentiment["neutral_count"]))
            lines.append("")

        for i, item in enumerate(news_items[:8]):
            emoji = ""
            if sentiment and i < len(sentiment.get("details", [])):
                s = sentiment["details"][i]["sentiment"]
                emoji = "🟢 " if s == "bullish" else "🔴 " if s == "bearish" else "⚪ "

            lines.append(emoji + item["title"])
            if item.get("source"):
                lines.append("  — " + item["source"])
            lines.append("")

        return "\n".join(lines)

    # ── Private Methods ──────────────────────────────────────────

    def _fetch_google_news_rss(self, query, limit=5):
        """Fetch news from Google News RSS."""
        news = []
        try:
            encoded = requests.utils.quote(query)
            url = "https://news.google.com/rss/search?q=" + encoded + "&hl=en-IN&gl=IN&ceid=IN:en"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "xml")
                items = soup.find_all("item")
                for item in items[:limit]:
                    title = item.find("title")
                    source = item.find("source")
                    pub_date = item.find("pubDate")
                    news.append({
                        "title": title.text if title else "",
                        "source": source.text if source else "",
                        "published": pub_date.text if pub_date else "",
                        "link": item.find("link").next_sibling.strip() if item.find("link") else "",
                    })
        except Exception as e:
            print("Google News RSS error: " + str(e))
        return news


# Quick test
if __name__ == "__main__":
    engine = NewsSentimentEngine()
    print("Fetching market news...")
    news = engine.get_market_news(10)
    sentiment = engine.analyze_sentiment(news)
    print(engine.format_news_report(news, sentiment))
