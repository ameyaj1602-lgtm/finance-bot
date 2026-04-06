"""
Email Reports — Send daily market reports via email.
Uses Gmail SMTP (free, no API needed).
Requires an App Password from Google (not your regular Gmail password).
"""
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NIFTY_50_SYMBOLS, INDICES, SECTOR_MAP


# Config
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "ameya.j@growthx.club")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")  # Your Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Gmail App Password
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


def send_email(subject, html_body, recipient=None):
    """Send an HTML email."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("Email not configured. Set SMTP_EMAIL and SMTP_PASSWORD in .env")
        return False

    recipient = recipient or RECIPIENT_EMAIL

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "Finance Wiz <" + SMTP_EMAIL + ">"
    msg["To"] = recipient

    html_part = MIMEText(html_body, "html")
    msg.attach(html_part)

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, recipient, msg.as_string())
        server.quit()
        print("Email sent to " + recipient)
        return True
    except Exception as e:
        print("Email error: " + str(e))
        return False


def generate_morning_email():
    """Generate full HTML morning report email."""
    from reports.daily_report import DailyReportGenerator
    from analysis.predictor import MarketPredictor
    from analysis.news_sentiment import NewsSentimentEngine

    gen = DailyReportGenerator()
    predictor = MarketPredictor()
    news_engine = NewsSentimentEngine()

    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y")

    # Gather data
    index_data = {}
    for name, symbol in INDICES.items():
        df = gen.data.get_stock_data(symbol, period="5d")
        if df is not None and len(df) >= 2:
            last = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])
            pct = ((last - prev) / prev) * 100
            index_data[name.replace("_", " ")] = {"price": last, "change_pct": round(pct, 2)}

    # Top movers
    bulk = gen.data.get_bulk_data(NIFTY_50_SYMBOLS, period="5d")
    movers = gen.data.get_top_movers(bulk, n=5) if bulk else {"gainers": [], "losers": []}
    breadth = gen.data.get_market_breadth(bulk) if bulk else {"advancing": 0, "declining": 0, "advance_decline_ratio": 1}

    # Global cues
    global_cues = gen.data.get_global_cues()

    # Prediction
    try:
        prediction = predictor.predict_market()
    except Exception:
        prediction = {"prediction": "N/A", "emoji": "", "bullish_reasons": [], "bearish_reasons": [], "confidence": 0, "action": ""}

    # News
    try:
        news_items = news_engine.get_market_news(8)
        sentiment = news_engine.analyze_sentiment(news_items)
    except Exception:
        news_items = []
        sentiment = {"overall": "neutral"}

    # Sector performance
    sector_perf = {}
    for sector, symbols in SECTOR_MAP.items():
        changes = []
        for sym in symbols[:3]:
            if sym in bulk and bulk[sym] is not None and len(bulk[sym]) >= 2:
                df = bulk[sym]
                pct = ((float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-2])) / float(df["Close"].iloc[-2])) * 100
                changes.append(pct)
        if changes:
            sector_perf[sector] = round(sum(changes) / len(changes), 2)

    # Build HTML
    html = _build_html_email(
        date_str=date_str,
        index_data=index_data,
        movers=movers,
        breadth=breadth,
        global_cues=global_cues,
        prediction=prediction,
        news_items=news_items,
        sentiment=sentiment,
        sector_perf=sector_perf,
    )

    subject = prediction.get("emoji", "") + " Market Brief — " + date_str

    return subject, html


def _build_html_email(**data):
    """Build a beautiful HTML email."""
    date_str = data["date_str"]
    index_data = data["index_data"]
    movers = data["movers"]
    breadth = data["breadth"]
    global_cues = data["global_cues"]
    prediction = data["prediction"]
    news_items = data["news_items"]
    sentiment = data["sentiment"]
    sector_perf = data["sector_perf"]

    green = "#26a69a"
    red = "#ef5350"
    bg = "#1a1a2e"
    card_bg = "#16213e"
    text = "#e0e0e0"
    muted = "#888888"

    def color_pct(pct):
        if pct > 0:
            return green
        elif pct < 0:
            return red
        return muted

    def format_pct(pct):
        prefix = "+" if pct > 0 else ""
        return prefix + format(pct, ".2f") + "%"

    # Indices rows
    index_rows = ""
    for name, d in index_data.items():
        c = color_pct(d["change_pct"])
        index_rows += (
            '<tr>'
            '<td style="padding:8px 12px;border-bottom:1px solid #2a2a4a;font-weight:600;">' + name + '</td>'
            '<td style="padding:8px 12px;border-bottom:1px solid #2a2a4a;text-align:right;">Rs.' + format(d["price"], ",.0f") + '</td>'
            '<td style="padding:8px 12px;border-bottom:1px solid #2a2a4a;text-align:right;color:' + c + ';font-weight:700;">' + format_pct(d["change_pct"]) + '</td>'
            '</tr>'
        )

    # Gainers
    gainer_rows = ""
    for g in movers.get("gainers", [])[:5]:
        gainer_rows += (
            '<tr>'
            '<td style="padding:6px 12px;border-bottom:1px solid #2a2a4a;">' + g["symbol"] + '</td>'
            '<td style="padding:6px 12px;border-bottom:1px solid #2a2a4a;text-align:right;">Rs.' + format(g["price"], ",.2f") + '</td>'
            '<td style="padding:6px 12px;border-bottom:1px solid #2a2a4a;text-align:right;color:' + green + ';font-weight:700;">' + format_pct(g["change_pct"]) + '</td>'
            '</tr>'
        )

    # Losers
    loser_rows = ""
    for l in movers.get("losers", [])[:5]:
        loser_rows += (
            '<tr>'
            '<td style="padding:6px 12px;border-bottom:1px solid #2a2a4a;">' + l["symbol"] + '</td>'
            '<td style="padding:6px 12px;border-bottom:1px solid #2a2a4a;text-align:right;">Rs.' + format(l["price"], ",.2f") + '</td>'
            '<td style="padding:6px 12px;border-bottom:1px solid #2a2a4a;text-align:right;color:' + red + ';font-weight:700;">' + format_pct(l["change_pct"]) + '</td>'
            '</tr>'
        )

    # Global cues
    global_rows = ""
    for name, d in global_cues.items():
        c = color_pct(d["change_pct"])
        global_rows += (
            '<tr>'
            '<td style="padding:6px 12px;border-bottom:1px solid #2a2a4a;">' + name + '</td>'
            '<td style="padding:6px 12px;border-bottom:1px solid #2a2a4a;text-align:right;">' + format(d["value"], ",.2f") + '</td>'
            '<td style="padding:6px 12px;border-bottom:1px solid #2a2a4a;text-align:right;color:' + c + ';">' + format_pct(d["change_pct"]) + '</td>'
            '</tr>'
        )

    # Prediction section
    pred_color = green if "BULLISH" in prediction.get("prediction", "") else red if "BEARISH" in prediction.get("prediction", "") else muted
    bullish_html = ""
    for r in prediction.get("bullish_reasons", []):
        bullish_html += '<div style="color:' + green + ';padding:2px 0;">+ ' + r + '</div>'
    bearish_html = ""
    for r in prediction.get("bearish_reasons", []):
        bearish_html += '<div style="color:' + red + ';padding:2px 0;">- ' + r + '</div>'

    # Sector heatmap
    sector_rows = ""
    for sector, pct in sorted(sector_perf.items(), key=lambda x: x[1], reverse=True):
        c = color_pct(pct)
        bar_width = min(abs(pct) * 30, 200)
        sector_rows += (
            '<div style="display:flex;align-items:center;padding:4px 0;">'
            '<span style="width:100px;font-size:13px;">' + sector + '</span>'
            '<div style="flex:1;height:18px;background:#2a2a4a;border-radius:3px;overflow:hidden;">'
            '<div style="width:' + str(bar_width) + 'px;height:100%;background:' + c + ';border-radius:3px;"></div>'
            '</div>'
            '<span style="width:60px;text-align:right;font-size:13px;color:' + c + ';font-weight:700;">' + format_pct(pct) + '</span>'
            '</div>'
        )

    # News
    news_html = ""
    for item in news_items[:6]:
        news_html += '<div style="padding:6px 0;border-bottom:1px solid #2a2a4a;font-size:13px;">' + item["title"]
        if item.get("source"):
            news_html += ' <span style="color:' + muted + ';">— ' + item["source"] + '</span>'
        news_html += '</div>'

    # Breadth
    adv = breadth.get("advancing", 0)
    dec = breadth.get("declining", 0)
    ratio = breadth.get("advance_decline_ratio", 1)
    mood = "Bullish" if ratio > 1.5 else "Bearish" if ratio < 0.7 else "Mixed"
    mood_color = green if ratio > 1.5 else red if ratio < 0.7 else muted

    html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:""" + bg + """;color:""" + text + """;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:20px;">

<!-- Header -->
<div style="text-align:center;padding:20px 0;">
<h1 style="margin:0;font-size:24px;color:""" + green + """;">Finance Wiz</h1>
<p style="margin:5px 0 0;color:""" + muted + """;font-size:14px;">""" + date_str + """</p>
</div>

<!-- Prediction Banner -->
<div style="background:""" + card_bg + """;border-radius:12px;padding:20px;margin-bottom:16px;border-left:4px solid """ + pred_color + """;">
<div style="font-size:12px;color:""" + muted + """;text-transform:uppercase;letter-spacing:1px;">Tomorrow's Prediction</div>
<div style="font-size:22px;font-weight:700;color:""" + pred_color + """;margin:8px 0;">""" + prediction.get("emoji", "") + " " + prediction.get("prediction", "N/A") + """</div>
<div style="font-size:14px;color:""" + text + """;">""" + prediction.get("action", "") + """</div>
<div style="font-size:12px;color:""" + muted + """;margin-top:8px;">Confidence: """ + str(prediction.get("confidence", 0)) + """%</div>
</div>

<!-- Indices -->
<div style="background:""" + card_bg + """;border-radius:12px;padding:16px;margin-bottom:16px;">
<h2 style="margin:0 0 12px;font-size:16px;">Indices</h2>
<table style="width:100%;border-collapse:collapse;font-size:14px;">
""" + index_rows + """
</table>
<div style="margin-top:10px;font-size:13px;">
Breadth: <span style="color:""" + green + "";">""" + str(adv) + """ advancing</span> / <span style="color:""" + red + "";">""" + str(dec) + """ declining</span>
<span style="color:""" + mood_color + """;font-weight:700;"> — """ + mood + """</span>
</div>
</div>

<!-- Top Movers -->
<div style="display:flex;gap:12px;margin-bottom:16px;">
<div style="flex:1;background:""" + card_bg + """;border-radius:12px;padding:16px;">
<h2 style="margin:0 0 10px;font-size:14px;color:""" + green + """;">Top Gainers</h2>
<table style="width:100%;border-collapse:collapse;font-size:13px;">""" + gainer_rows + """</table>
</div>
<div style="flex:1;background:""" + card_bg + """;border-radius:12px;padding:16px;">
<h2 style="margin:0 0 10px;font-size:14px;color:""" + red + """;">Top Losers</h2>
<table style="width:100%;border-collapse:collapse;font-size:13px;">""" + loser_rows + """</table>
</div>
</div>

<!-- Prediction Reasoning -->
<div style="background:""" + card_bg + """;border-radius:12px;padding:16px;margin-bottom:16px;">
<h2 style="margin:0 0 10px;font-size:16px;">Why This Prediction?</h2>
""" + bullish_html + bearish_html + """
</div>

<!-- Sector Heatmap -->
<div style="background:""" + card_bg + """;border-radius:12px;padding:16px;margin-bottom:16px;">
<h2 style="margin:0 0 10px;font-size:16px;">Sector Heatmap</h2>
""" + sector_rows + """
</div>

<!-- Global Cues -->
<div style="background:""" + card_bg + """;border-radius:12px;padding:16px;margin-bottom:16px;">
<h2 style="margin:0 0 10px;font-size:16px;">Global Cues</h2>
<table style="width:100%;border-collapse:collapse;font-size:13px;">""" + global_rows + """</table>
</div>

<!-- News -->
<div style="background:""" + card_bg + """;border-radius:12px;padding:16px;margin-bottom:16px;">
<h2 style="margin:0 0 10px;font-size:16px;">Market News <span style="font-size:12px;color:""" + muted + """;">(Sentiment: """ + sentiment.get("overall", "neutral").upper() + """)</span></h2>
""" + news_html + """
</div>

<!-- Footer -->
<div style="text-align:center;padding:20px 0;color:""" + muted + """;font-size:12px;">
Finance Wiz Bot — For educational purposes only. Not financial advice.<br>
<a href="https://finance-bot-yr7k.onrender.com" style="color:""" + green + """;">Open Dashboard</a>
</div>

</div>
</body>
</html>"""

    return html


def send_morning_report():
    """Generate and send the morning email report."""
    subject, html = generate_morning_email()
    return send_email(subject, html)


# Test
if __name__ == "__main__":
    subject, html = generate_morning_email()
    print("Subject:", subject)
    # Save HTML for preview
    with open("/tmp/finance_email_preview.html", "w") as f:
        f.write(html)
    print("Preview saved to /tmp/finance_email_preview.html")

    if SMTP_EMAIL and SMTP_PASSWORD:
        send_email(subject, html)
    else:
        print("Set SMTP_EMAIL and SMTP_PASSWORD in .env to send emails")
