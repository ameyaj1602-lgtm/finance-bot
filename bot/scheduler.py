"""
Phase 2: Scheduled Auto-Reports
Automatically sends market reports at fixed times IST.
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
import pytz

from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")

# Schedule configuration
SCHEDULES = {
    "morning_brief": {"time": time(8, 30), "days": "weekdays", "report": "morning"},
    "market_open": {"time": time(9, 20), "days": "weekdays", "report": "signals"},
    "mid_day": {"time": time(12, 30), "days": "weekdays", "report": "midday"},
    "eod_report": {"time": time(16, 5), "days": "weekdays", "report": "eod"},
    "weekly_digest": {"time": time(10, 0), "days": "sunday", "report": "weekly"},
}


def setup_scheduled_jobs(application, chat_id):
    """Register all scheduled jobs with the bot's job queue."""
    if not chat_id:
        logger.warning("No chat_id — scheduled reports disabled.")
        return

    job_queue = application.job_queue
    now_ist = datetime.now(IST)

    for name, config in SCHEDULES.items():
        target_time = config["time"]
        days = config["days"]
        report_type = config["report"]

        if days == "weekdays":
            # Monday=0 to Friday=4
            for day in range(5):
                job_queue.run_daily(
                    _send_report,
                    time=target_time,
                    days=(day,),
                    chat_id=int(chat_id),
                    name=name + "_" + str(day),
                    data={"report_type": report_type, "chat_id": chat_id},
                )
        elif days == "sunday":
            job_queue.run_daily(
                _send_report,
                time=target_time,
                days=(6,),
                chat_id=int(chat_id),
                name=name,
                data={"report_type": report_type, "chat_id": chat_id},
            )

    # Check paper trade SL/targets every 5 min during market hours
    job_queue.run_repeating(
        _check_paper_trades,
        interval=300,  # 5 minutes
        first=10,
        chat_id=int(chat_id),
        name="sl_target_check",
        data={"chat_id": chat_id},
    )

    # Check watchlist alerts every 3 min during market hours
    job_queue.run_repeating(
        _check_watchlist_alerts,
        interval=180,
        first=15,
        chat_id=int(chat_id),
        name="watchlist_alerts",
        data={"chat_id": chat_id},
    )

    logger.info("Scheduled jobs registered for chat_id: " + str(chat_id))
    print("Scheduled reports active:")
    for name, config in SCHEDULES.items():
        print("  " + name + ": " + str(config["time"]) + " IST (" + config["days"] + ")")


async def _send_report(context: ContextTypes.DEFAULT_TYPE):
    """Callback for scheduled reports."""
    data = context.job.data
    chat_id = data["chat_id"]
    report_type = data["report_type"]

    # Only send during market days
    now_ist = datetime.now(IST)
    if now_ist.weekday() > 4 and report_type != "weekly":
        return

    try:
        from reports.daily_report import DailyReportGenerator
        gen = DailyReportGenerator()

        if report_type == "morning":
            report = gen.generate_morning_brief()
        elif report_type == "signals":
            report = gen.generate_stock_signals()
        elif report_type == "midday":
            report = _generate_midday_update(gen)
        elif report_type == "eod":
            report = gen.generate_eod_report()
        elif report_type == "weekly":
            report = _generate_weekly_digest(gen)
        else:
            return

        await _send_long(context, chat_id, report)
        logger.info("Sent " + report_type + " report to " + str(chat_id))

    except Exception as e:
        logger.error("Failed to send " + report_type + ": " + str(e))


def _generate_midday_update(gen):
    """Quick midday check."""
    lines = ["🕐 MID-DAY UPDATE", "━" * 30, ""]
    from config import INDICES
    for name, symbol in INDICES.items():
        df = gen.data.get_stock_data(symbol, period="5d")
        if df is not None and len(df) >= 2:
            last = df["Close"].iloc[-1]
            prev = df["Close"].iloc[-2]
            pct = ((last - prev) / prev) * 100
            emoji = "🟢" if pct > 0 else "🔴"
            lines.append(emoji + " " + name.replace("_", " ") + ": " + format(last, ",.0f") + " (" + format(pct, "+.2f") + "%)")

    lines.append("\nHalf day done. Stay disciplined!")
    return "\n".join(lines)


def _generate_weekly_digest(gen):
    """Sunday weekly summary."""
    lines = ["📊 WEEKLY DIGEST", "━" * 30, ""]

    from config import INDICES, NIFTY_50_SYMBOLS
    # Weekly index performance
    lines.append("INDEX WEEKLY PERFORMANCE:")
    for name, symbol in INDICES.items():
        df = gen.data.get_stock_data(symbol, period="1mo")
        if df is not None and len(df) >= 5:
            week_close = df["Close"].iloc[-1]
            week_open = df["Close"].iloc[-5] if len(df) >= 5 else df["Close"].iloc[0]
            pct = ((week_close - week_open) / week_open) * 100
            emoji = "🟢" if pct > 0 else "🔴"
            lines.append("  " + emoji + " " + name.replace("_", " ") + ": " + format(pct, "+.2f") + "% this week")

    # Top weekly movers
    lines.append("\nBIGGEST WEEKLY MOVERS:")
    bulk = gen.data.get_bulk_data(NIFTY_50_SYMBOLS, period="1mo")
    if bulk:
        changes = []
        for sym, df in bulk.items():
            if len(df) >= 5:
                pct = ((df["Close"].iloc[-1] - df["Close"].iloc[-5]) / df["Close"].iloc[-5]) * 100
                changes.append({"symbol": sym.replace(".NS", ""), "pct": round(pct, 2)})
        changes.sort(key=lambda x: x["pct"], reverse=True)
        lines.append("  Top Gainers:")
        for g in changes[:3]:
            lines.append("    🟢 " + g["symbol"] + ": " + format(g["pct"], "+.2f") + "%")
        lines.append("  Top Losers:")
        for l in changes[-3:]:
            lines.append("    🔴 " + l["symbol"] + ": " + format(l["pct"], "+.2f") + "%")

    # Paper trading summary
    from trading.paper_trader import PaperTrader
    trader = PaperTrader()
    p = trader.get_portfolio_summary()
    lines.append("\n💼 YOUR PAPER PORTFOLIO:")
    lines.append("  Capital: " + format(p["current_capital"], ",.0f"))
    lines.append("  Total P&L: " + format(p["total_pnl"], "+,.0f"))
    lines.append("  Win Rate: " + str(p["win_rate"]) + "%")

    # Lesson reminder
    from datetime import datetime
    day = (datetime.now().timetuple().tm_yday % 30) + 1
    from education.lessons import get_lesson
    lesson = get_lesson(day)
    lines.append("\n📚 This week's lesson: Day " + str(day) + " — " + lesson["topic"])
    lines.append("Type /learn " + str(day) + " to read it!")

    return "\n".join(lines)


async def _check_paper_trades(context: ContextTypes.DEFAULT_TYPE):
    """Check SL/targets during market hours."""
    now_ist = datetime.now(IST)
    # Only during market hours (9:15 to 15:30) on weekdays
    if now_ist.weekday() > 4:
        return
    market_open = time(9, 15)
    market_close = time(15, 30)
    current_time = now_ist.time()
    if current_time < market_open or current_time > market_close:
        return

    data = context.job.data
    chat_id = data["chat_id"]

    try:
        from trading.paper_trader import PaperTrader
        from data.market_data import MarketDataFetcher

        trader = PaperTrader()
        fetcher = MarketDataFetcher()
        open_trades = trader.get_open_trades()

        if not open_trades:
            return

        prices = {}
        for t in open_trades:
            sym = t["symbol"]
            full = sym + ".NS" if not sym.endswith(".NS") else sym
            live = fetcher.get_live_price(full)
            if live and live["price"]:
                prices[sym] = live["price"]

        triggered = trader.check_stop_loss_targets(prices)
        for t in triggered:
            emoji = "🎯" if t.get("trigger") == "TARGET" else "🛑"
            msg = (emoji + " " + t["trigger"] + " HIT!\n"
                   + t["symbol"] + ": Rs." + format(t["entry_price"], ",.2f")
                   + " -> Rs." + format(t["exit_price"], ",.2f") + "\n"
                   + "P&L: Rs." + format(t["pnl"], "+,.2f"))
            await context.bot.send_message(chat_id=int(chat_id), text=msg)

    except Exception as e:
        logger.error("SL/Target check error: " + str(e))


async def _check_watchlist_alerts(context: ContextTypes.DEFAULT_TYPE):
    """Check watchlist price alerts."""
    now_ist = datetime.now(IST)
    if now_ist.weekday() > 4:
        return
    if now_ist.time() < time(9, 15) or now_ist.time() > time(15, 30):
        return

    data = context.job.data
    chat_id = data["chat_id"]

    try:
        from bot.watchlist import check_alerts
        alerts = check_alerts()
        for alert in alerts:
            await context.bot.send_message(chat_id=int(chat_id), text=alert)
    except Exception:
        pass  # Watchlist module may not exist yet


async def _send_long(context, chat_id, text):
    """Send long messages in chunks."""
    max_len = 4000
    while text:
        if len(text) <= max_len:
            await context.bot.send_message(chat_id=int(chat_id), text=text)
            break
        break_at = text.rfind("\n", 0, max_len)
        if break_at == -1:
            break_at = max_len
        await context.bot.send_message(chat_id=int(chat_id), text=text[:break_at])
        text = text[break_at:].lstrip("\n")
