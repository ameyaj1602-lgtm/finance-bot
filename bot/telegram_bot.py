"""
Telegram Bot — Full-featured Finance Bot with ALL phases.
"""
import os
import sys
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, NIFTY_50_SYMBOLS
from reports.daily_report import DailyReportGenerator
from trading.paper_trader import PaperTrader
from education.lessons import get_lesson, get_all_topics
from analysis.ai_analyst import AIAnalyst
from analysis.charts import ChartGenerator
from analysis.predictor import MarketPredictor
from analysis.mutual_funds import MutualFundTracker
from analysis.news_sentiment import NewsSentimentEngine
from analysis.backtesting import BacktestEngine
from analysis.intraday import IntradayScanner
from analysis.options import OptionsAnalyzer
from analysis.portfolio_intel import PortfolioIntelligence
from bot.watchlist import Watchlist, format_watchlist
from data.market_data import MarketDataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize
report_gen = DailyReportGenerator()
paper_trader = PaperTrader()
ai_analyst = AIAnalyst()
chart_gen = ChartGenerator()
mf_tracker = MutualFundTracker()
news_engine = NewsSentimentEngine()
backtest_engine = BacktestEngine()
intraday_scanner = IntradayScanner()
options_analyzer = OptionsAnalyzer()
portfolio_intel = PortfolioIntelligence()
watchlist = Watchlist()
data_fetcher = MarketDataFetcher()
predictor = MarketPredictor()


async def send_long(update_or_id, text, context):
    max_len = 4000
    while text:
        chunk = text[:max_len] if len(text) > max_len else text
        if len(text) > max_len:
            br = text.rfind("\n", 0, max_len)
            if br > 0:
                chunk = text[:br]
        if isinstance(update_or_id, Update):
            await update_or_id.message.reply_text(chunk)
        else:
            await context.bot.send_message(chat_id=update_or_id, text=chunk)
        text = text[len(chunk):].lstrip("\n")
        if not text:
            break


# ── Core Commands ────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    # Save chat ID
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    try:
        with open(env_path, "r") as f:
            content = f.read()
        if "TELEGRAM_CHAT_ID=" in content:
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                if line.startswith("TELEGRAM_CHAT_ID="):
                    new_lines.append("TELEGRAM_CHAT_ID=" + str(chat_id))
                else:
                    new_lines.append(line)
            with open(env_path, "w") as f:
                f.write("\n".join(new_lines))
    except Exception:
        pass

    welcome = """🚀 Welcome to Finance Wiz, """ + (user.first_name or "Investor") + """!

📊 MARKET REPORTS:
/morning — Morning brief
/signals — Buy/sell signals (Nifty 50)
/sectors — Sector heatmap
/eod — End of day report
/news — Market news + sentiment
/intraday — Intraday scanner

🔎 STOCK ANALYSIS:
/analyze RELIANCE — Deep analysis
/price INFY — Quick price
/compare TCS INFY — Compare stocks
/chart RELIANCE — Chart with indicators
/options NIFTY — Option chain analysis

📚 LEARNING:
/learn — Today's lesson
/learn 5 — Specific lesson
/topics — All 30 topics
/explain PE ratio — Explain anything

💼 PAPER TRADING:
/portfolio — Your portfolio
/buy RELIANCE 2850 — Paper buy
/sell 1 — Close trade
/history — Trade history
/performance — P&L chart

👁 WATCHLIST:
/watch RELIANCE — Add to watchlist
/unwatch RELIANCE — Remove
/watchlist — View watchlist
/alert RELIANCE above 2900 — Price alert
/alerts — View active alerts

📈 MUTUAL FUNDS:
/mf search Nifty index — Search funds
/mf nav 120716 — Fund NAV + returns
/sip 5000 12 10 — SIP calculator
/mf popular — Popular funds

🧪 BACKTESTING:
/backtest RELIANCE ema_crossover — Test strategy
/strategies — List all strategies

🔮 PREDICTIONS:
/predict — Tomorrow's market prediction
/predict RELIANCE — Stock prediction

📰 FINANCE NEWS:
/financenews — Top finance/market news
/financenews RELIANCE — Stock-specific news

💡 Type any stock name to get a quick summary!"""

    await update.message.reply_text(welcome)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


# ── Market Reports ───────────────────────────────────────────

async def morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching market data... (30-60 sec)")
    try:
        report = report_gen.generate_morning_brief()
        await send_long(update, report, context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Scanning Nifty 50... (1-2 min)")
    try:
        report = report_gen.generate_stock_signals()
        await send_long(update, report, context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


async def sectors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Calculating sectors...")
    try:
        report = report_gen.generate_sector_heatmap()
        await send_long(update, report, context)
        # Also send chart image
        sector_data = {}
        from config import SECTOR_MAP
        for sector, symbols in SECTOR_MAP.items():
            changes = []
            for sym in symbols[:3]:
                df = data_fetcher.get_stock_data(sym, period="5d")
                if df is not None and len(df) >= 2:
                    pct = ((df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2]) * 100
                    changes.append(pct)
            if changes:
                sector_data[sector] = sum(changes) / len(changes)
        img = chart_gen.generate_sector_heatmap(sector_data)
        if img:
            await update.message.reply_photo(photo=open(img, "rb"))
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Generating EOD report...")
    try:
        report = report_gen.generate_eod_report()
        await send_long(update, report, context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


# ── Stock Analysis ───────────────────────────────────────────

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /analyze RELIANCE")
        return
    symbol = context.args[0].upper()
    await update.message.reply_text("Analyzing " + symbol + "...")
    try:
        report = report_gen.generate_stock_analysis(symbol)
        await send_long(update, report, context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price RELIANCE")
        return
    symbol = context.args[0].upper()
    full = symbol + ".NS" if not symbol.endswith(".NS") else symbol
    try:
        p = data_fetcher.get_live_price(full)
        if p:
            emoji = "🟢" if p["change_pct"] > 0 else "🔴"
            await update.message.reply_text(
                emoji + " " + symbol + "\n"
                "Price: Rs." + format(p["price"], ",.2f") + "\n"
                "Change: " + format(p["change_pct"], "+.2f") + "%\n"
                "Range: Rs." + format(p["day_low"], ",.2f") + " - Rs." + format(p["day_high"], ",.2f"))
        else:
            await update.message.reply_text("Could not fetch price for " + symbol)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /compare TCS INFY")
        return
    s1, s2 = context.args[0].upper(), context.args[1].upper()
    await update.message.reply_text("Comparing " + s1 + " vs " + s2 + "...")
    try:
        report = report_gen.generate_stock_analysis(s1) + "\n\n" + "━" * 30 + "\n\n" + report_gen.generate_stock_analysis(s2)
        await send_long(update, report, context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /chart RELIANCE [1mo/3mo/6mo]")
        return
    symbol = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "3mo"
    full = symbol + ".NS" if not symbol.endswith(".NS") else symbol

    await update.message.reply_text("Generating chart for " + symbol + "...")
    try:
        df = data_fetcher.get_stock_data(full, period=period)
        if df is not None:
            img = chart_gen.generate_candlestick_chart(df, full, period, ["ema", "volume", "rsi", "sr"])
            if img:
                await update.message.reply_photo(photo=open(img, "rb"), caption=symbol + " (" + period + ")")
            else:
                await update.message.reply_text("Could not generate chart.")
        else:
            await update.message.reply_text("No data for " + symbol)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


# ── News & Sentiment ─────────────────────────────────────────

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.reply_text("Fetching news...")
    try:
        if query:
            items = news_engine.get_stock_news(query)
        else:
            items = news_engine.get_market_news(10)
        sentiment = news_engine.analyze_sentiment(items)
        report = news_engine.format_news_report(items, sentiment)
        await send_long(update, report, context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


# ── Intraday Scanner ─────────────────────────────────────────

async def intraday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Scanning for intraday setups... (1-2 min)")
    try:
        results = intraday_scanner.scan_all()
        report = intraday_scanner.format_intraday_report(results)
        await send_long(update, report, context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


# ── Options ──────────────────────────────────────────────────

async def options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0].upper() if context.args else "NIFTY"
    await update.message.reply_text("Fetching option chain for " + symbol + "...")
    try:
        chain = options_analyzer.get_option_chain(symbol)
        report = options_analyzer.format_options_report(symbol, chain)
        await send_long(update, report, context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


# ── Learning ─────────────────────────────────────────────────

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        try:
            day = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Usage: /learn or /learn 5")
            return
    else:
        day = (datetime.now().timetuple().tm_yday % 30) + 1
    lesson = get_lesson(day)
    await send_long(update, lesson["lesson"], context)


async def topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_t = get_all_topics()
    lines = ["📚 30-DAY CURRICULUM", "━" * 30, ""]
    for d, t in all_t.items():
        lines.append("  Day " + str(d) + ": " + t)
    lines.append("\nUse /learn <day> to read any lesson.")
    await send_long(update, "\n".join(lines), context)


async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /explain PE ratio")
        return
    concept = " ".join(context.args)
    await update.message.reply_text("Explaining '" + concept + "'...")
    explanation = ai_analyst.explain_concept(concept)
    await send_long(update, explanation, context)


# ── Paper Trading ────────────────────────────────────────────

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(paper_trader.format_portfolio())


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /buy SYMBOL [price] [stop_loss] [target]")
        return
    symbol = context.args[0].upper()
    full = symbol + ".NS" if not symbol.endswith(".NS") else symbol
    if len(context.args) >= 2:
        try:
            p = float(context.args[1])
        except ValueError:
            await update.message.reply_text("Invalid price.")
            return
    else:
        live = data_fetcher.get_live_price(full)
        if live and live["price"]:
            p = live["price"]
        else:
            await update.message.reply_text("Could not fetch price. Specify: /buy " + symbol + " 2850")
            return
    sl = float(context.args[2]) if len(context.args) >= 3 else None
    tgt = float(context.args[3]) if len(context.args) >= 4 else None
    result = paper_trader.buy(symbol, p, sl, tgt)
    if "error" in result:
        await update.message.reply_text("Error: " + result["error"])
    else:
        await update.message.reply_text(
            "BUY " + result["symbol"] + "\n"
            "Price: Rs." + format(result["price"], ",.2f") + "\n"
            "Qty: " + str(result["quantity"]) + "\n"
            "SL: Rs." + format(result["stop_loss"], ",.2f") + "\n"
            "Target: Rs." + format(result["target"], ",.2f") + "\n"
            "Trade #" + str(result["trade_id"]) + "\n"
            "Use /sell " + str(result["trade_id"]) + " to close.")


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /sell <trade_id> [price]")
        return
    try:
        tid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Trade ID must be a number.")
        return
    if len(context.args) >= 2:
        ep = float(context.args[1])
    else:
        trades = paper_trader.get_open_trades()
        trade = next((t for t in trades if t["id"] == tid), None)
        if not trade:
            await update.message.reply_text("No open trade #" + str(tid))
            return
        full = trade["symbol"] + ".NS"
        live = data_fetcher.get_live_price(full)
        ep = live["price"] if live and live["price"] else 0
        if not ep:
            await update.message.reply_text("Could not fetch price. Use: /sell " + str(tid) + " 2900")
            return
    result = paper_trader.sell(tid, ep)
    if "error" in result:
        await update.message.reply_text("Error: " + result["error"])
    else:
        emoji = "🟢" if result["pnl"] > 0 else "🔴"
        await update.message.reply_text(
            emoji + " TRADE CLOSED\n"
            + result["symbol"] + ": Rs." + format(result["entry_price"], ",.2f")
            + " -> Rs." + format(result["exit_price"], ",.2f") + "\n"
            "P&L: Rs." + format(result["pnl"], "+,.2f")
            + " (" + format(result["pnl_pct"], "+.2f") + "%)")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trades = paper_trader.get_trade_history(10)
    if not trades:
        await update.message.reply_text("No trades yet. Start with /buy RELIANCE")
        return
    lines = ["Trade History (Last 10)", "━" * 30]
    for t in trades:
        emoji = "🟢" if t["pnl"] > 0 else "🔴"
        lines.append(emoji + " #" + str(t["id"]) + " " + t["symbol"] +
                     ": Rs." + format(t["pnl"], "+,.0f"))
    await send_long(update, "\n".join(lines), context)


async def performance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trades = paper_trader.get_trade_history(50)
    if not trades:
        await update.message.reply_text("No trades yet.")
        return
    img = chart_gen.generate_portfolio_chart(trades)
    if img:
        await update.message.reply_photo(photo=open(img, "rb"), caption="Portfolio P&L")
    await update.message.reply_text(paper_trader.format_portfolio())


# ── Watchlist ────────────────────────────────────────────────

async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /watch RELIANCE")
        return
    symbol = context.args[0].upper()
    full = symbol + ".NS"
    live = data_fetcher.get_live_price(full)
    p = live["price"] if live else 0
    watchlist.add(symbol, p)
    await update.message.reply_text("Added " + symbol + " to watchlist" + (" at Rs." + format(p, ",.2f") if p else ""))


async def unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /unwatch RELIANCE")
        return
    symbol = context.args[0].upper()
    if watchlist.remove(symbol):
        await update.message.reply_text("Removed " + symbol + " from watchlist.")
    else:
        await update.message.reply_text(symbol + " not in watchlist.")


async def show_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = watchlist.get_all()
    prices = {}
    for item in items:
        full = item["symbol"] + ".NS"
        live = data_fetcher.get_live_price(full)
        if live and live["price"]:
            prices[item["symbol"]] = live["price"]
    report = format_watchlist(items, prices)
    await send_long(update, report, context)


async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /alert RELIANCE above 2900\n"
            "       /alert TCS below 3500")
        return
    symbol = context.args[0].upper()
    direction = context.args[1].lower()
    try:
        target = float(context.args[2])
    except ValueError:
        await update.message.reply_text("Invalid price.")
        return
    alert_type = "price_above" if direction == "above" else "price_below"
    result = watchlist.add_alert(symbol, alert_type, target)
    await update.message.reply_text(
        "Alert set: " + symbol + " " + direction + " Rs." + format(target, ",.2f") +
        "\nAlert ID: #" + str(result["id"]))


async def show_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active = watchlist.get_active_alerts()
    if not active:
        await update.message.reply_text("No active alerts. Set one: /alert RELIANCE above 2900")
        return
    lines = ["🔔 ACTIVE ALERTS", "━" * 30]
    for a in active:
        direction = "above" if a["type"] == "price_above" else "below"
        lines.append("#" + str(a["id"]) + " " + a["symbol"] + " " + direction + " Rs." + format(a["target"], ",.2f"))
    await send_long(update, "\n".join(lines), context)


# ── Mutual Funds ─────────────────────────────────────────────

async def mf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n/mf search Nifty index\n/mf nav 120716\n/mf popular")
        return
    cmd = context.args[0].lower()
    if cmd == "search" and len(context.args) > 1:
        query = " ".join(context.args[1:])
        results = mf_tracker.search_fund(query)
        if results:
            lines = ["🔍 MF Search: " + query, ""]
            for f in results[:8]:
                lines.append(str(f.get("schemeCode", "")) + " — " + f.get("schemeName", ""))
            lines.append("\nUse /mf nav <code> for details")
            await send_long(update, "\n".join(lines), context)
        else:
            await update.message.reply_text("No funds found for '" + query + "'")
    elif cmd == "nav" and len(context.args) > 1:
        try:
            code = int(context.args[1])
        except ValueError:
            await update.message.reply_text("Invalid scheme code.")
            return
        await update.message.reply_text("Fetching fund data...")
        data = mf_tracker.get_fund_nav(code)
        report = mf_tracker.format_fund_report(data)
        await send_long(update, report, context)
    elif cmd == "popular":
        popular = mf_tracker.get_popular_funds()
        lines = ["📊 POPULAR MUTUAL FUNDS", "━" * 30]
        for category, funds in popular.items():
            lines.append("\n" + category + ":")
            for f in funds:
                lines.append("  " + str(f["code"]) + " — " + f["name"])
        lines.append("\nUse /mf nav <code> for details")
        await send_long(update, "\n".join(lines), context)
    else:
        await update.message.reply_text("Usage: /mf search <query> | /mf nav <code> | /mf popular")


async def sip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /sip <monthly_amount> <return_%> <years>\n"
            "Example: /sip 5000 12 10 — Rs.5000/mo at 12% for 10 years")
        return
    try:
        amount = float(context.args[0])
        ret = float(context.args[1])
        years = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Invalid numbers. Example: /sip 5000 12 10")
        return
    result = mf_tracker.calculate_sip(amount, ret, years)
    report = mf_tracker.format_sip_report(result)
    await send_long(update, report, context)


# ── Backtesting ──────────────────────────────────────────────

async def backtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /backtest RELIANCE ema_crossover\n\n"
            "Strategies: /strategies")
        return
    symbol = context.args[0].upper()
    strategy = context.args[1].lower()
    full = symbol + ".NS" if not symbol.endswith(".NS") else symbol

    if strategy not in BacktestEngine.STRATEGIES:
        await update.message.reply_text(
            "Unknown strategy. Available:\n" +
            "\n".join("  " + k + " — " + v for k, v in BacktestEngine.STRATEGIES.items()))
        return

    await update.message.reply_text("Backtesting " + symbol + " with " + strategy + "... (30 sec)")
    try:
        import yfinance as yf
        df = yf.Ticker(full).history(period="2y")
        result = backtest_engine.run(df, strategy)
        report = backtest_engine.format_backtest_report(result, strategy, symbol)
        await send_long(update, report, context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


async def strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["📊 AVAILABLE STRATEGIES", "━" * 30, ""]
    for name, desc in BacktestEngine.STRATEGIES.items():
        lines.append("  " + name)
        lines.append("  " + desc)
        lines.append("")
    lines.append("Use: /backtest RELIANCE <strategy_name>")
    await send_long(update, "\n".join(lines), context)


# ── Free Text Handler ────────────────────────────────────────

# ── Predictions ──────────────────────────────────────────────

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        # Stock prediction
        symbol = context.args[0].upper()
        await update.message.reply_text("Predicting " + symbol + "... (30 sec)")
        try:
            pred = predictor.predict_stock(symbol)
            report = predictor.format_stock_prediction(pred)
            await send_long(update, report, context)
        except Exception as e:
            await update.message.reply_text("Error: " + str(e))
    else:
        # Market prediction
        await update.message.reply_text("Analyzing market for prediction... (1-2 min)")
        try:
            pred = predictor.predict_market()
            report = predictor.format_market_prediction(pred)

            # Try to add AI commentary
            ai_take = predictor.get_ai_prediction(pred)
            if ai_take:
                report += "\n\n🤖 AI TAKE:\n" + ai_take

            await send_long(update, report, context)
        except Exception as e:
            await update.message.reply_text("Error: " + str(e))


# ── Finance News ─────────────────────────────────────────────

async def financenews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching finance news...")
    try:
        if context.args:
            symbol = context.args[0].upper()
            items = news_engine.get_stock_news(symbol, limit=8)
            title = "📰 FINANCE NEWS: " + symbol
        else:
            # Finance-specific news
            items = []
            for query in ["Indian stock market today", "Nifty Sensex", "RBI economy India"]:
                items.extend(news_engine._fetch_google_news_rss(query, 5))
            # Deduplicate
            seen = set()
            unique = []
            for n in items:
                key = n["title"][:40].lower()
                if key not in seen:
                    seen.add(key)
                    unique.append(n)
            items = unique[:12]
            title = "📰 FINANCE NEWS"

        sentiment = news_engine.analyze_sentiment(items)

        lines = [title, "━" * 32]

        # Sentiment summary
        if sentiment:
            emoji_map = {"bullish": "🟢 BULLISH", "bearish": "🔴 BEARISH", "neutral": "⚪ NEUTRAL"}
            lines.append("Market Mood: " + emoji_map.get(sentiment["overall"], "NEUTRAL"))
            lines.append("")

        for i, item in enumerate(items):
            s_emoji = ""
            if i < len(sentiment.get("details", [])):
                s = sentiment["details"][i]["sentiment"]
                s_emoji = "🟢 " if s == "bullish" else "🔴 " if s == "bearish" else "⚪ "

            lines.append(s_emoji + item["title"])
            if item.get("source"):
                lines.append("  — " + item["source"])
            if item.get("published"):
                lines.append("  " + item["published"][:25])
            lines.append("")

        lines.append("Sentiment Score: " + str(sentiment.get("score", 0)))
        lines.append("Bullish: " + str(sentiment.get("bullish_count", 0)) +
                     " | Bearish: " + str(sentiment.get("bearish_count", 0)) +
                     " | Neutral: " + str(sentiment.get("neutral_count", 0)))

        await send_long(update, "\n".join(lines), context)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


# ── Free Text Handler ────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    if len(text) <= 20 and text.replace("&", "").isalpha():
        full = text + ".NS"
        if full in NIFTY_50_SYMBOLS or any(text in s for s in NIFTY_50_SYMBOLS):
            await update.message.reply_text("Looking up " + text + "...")
            try:
                p = data_fetcher.get_live_price(full)
                if p and p["price"]:
                    emoji = "🟢" if p["change_pct"] > 0 else "🔴"
                    await update.message.reply_text(
                        emoji + " " + text + ": Rs." + format(p["price"], ",.2f") +
                        " (" + format(p["change_pct"], "+.2f") + "%)\n\n"
                        "Commands:\n/analyze " + text + "\n/chart " + text + "\n/news " + text)
                    return
            except Exception:
                pass
    await update.message.reply_text("Try /help to see all commands.")


# ── Main ─────────────────────────────────────────────────────

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: No TELEGRAM_BOT_TOKEN in .env!")
        return

    print("Starting Finance Wiz Bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Core
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # Market Reports
    app.add_handler(CommandHandler("morning", morning))
    app.add_handler(CommandHandler("signals", signals))
    app.add_handler(CommandHandler("sectors", sectors))
    app.add_handler(CommandHandler("eod", eod))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("intraday", intraday))

    # Stock Analysis
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("compare", compare))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("options", options))

    # Learning
    app.add_handler(CommandHandler("learn", learn))
    app.add_handler(CommandHandler("topics", topics))
    app.add_handler(CommandHandler("explain", explain))

    # Paper Trading
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("performance", performance))

    # Watchlist
    app.add_handler(CommandHandler("watch", watch))
    app.add_handler(CommandHandler("unwatch", unwatch))
    app.add_handler(CommandHandler("watchlist", show_watchlist))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("alerts", show_alerts))

    # Mutual Funds
    app.add_handler(CommandHandler("mf", mf))
    app.add_handler(CommandHandler("sip", sip))

    # Backtesting
    app.add_handler(CommandHandler("backtest", backtest))
    app.add_handler(CommandHandler("strategies", strategies))

    # Predictions
    app.add_handler(CommandHandler("predict", predict))

    # Finance News
    app.add_handler(CommandHandler("financenews", financenews))

    # Free text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Setup scheduled jobs
    try:
        from bot.scheduler import setup_scheduled_jobs
        chat_id = TELEGRAM_CHAT_ID
        if chat_id:
            setup_scheduled_jobs(app, chat_id)
        else:
            print("No TELEGRAM_CHAT_ID — send /start to the bot first for scheduled reports")
    except Exception as e:
        print("Scheduler setup error (non-fatal): " + str(e))

    print("Bot is LIVE! Send /start on Telegram.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
