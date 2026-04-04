"""
Finance Bot Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# AI APIs (use either or both — Gemini has a free tier)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Zerodha (Phase 3)
KITE_API_KEY = os.getenv("KITE_API_KEY", "")
KITE_API_SECRET = os.getenv("KITE_API_SECRET", "")
KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN", "")

# Market Settings
NIFTY_50_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS",
    "SUNPHARMA.NS", "BAJFINANCE.NS", "WIPRO.NS", "ULTRACEMCO.NS", "NESTLEIND.NS",
    "NTPC.NS", "TATAMOTORS.NS", "M&M.NS", "POWERGRID.NS", "ADANIENT.NS",
    "TATASTEEL.NS", "ONGC.NS", "JSWSTEEL.NS", "HCLTECH.NS", "TECHM.NS",
    "INDUSINDBK.NS", "COALINDIA.NS", "BAJAJFINSV.NS", "GRASIM.NS", "ADANIPORTS.NS",
    "BPCL.NS", "CIPLA.NS", "DRREDDY.NS", "EICHERMOT.NS", "DIVISLAB.NS",
    "APOLLOHOSP.NS", "HEROMOTOCO.NS", "TATACONSUM.NS", "SBILIFE.NS", "BRITANNIA.NS",
    "HINDALCO.NS", "BAJAJ-AUTO.NS", "HDFCLIFE.NS", "LTIM.NS", "SHRIRAMFIN.NS"
]

# Index symbols
INDICES = {
    "NIFTY_50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK_NIFTY": "^NSEBANK",
    "NIFTY_IT": "^CNXIT",
    "NIFTY_PHARMA": "^CNXPHARMA",
}

# Sector mapping
SECTOR_MAP = {
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "LTIM.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "INDUSINDBK.NS"],
    "Auto": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", "HEROMOTOCO.NS"],
    "Pharma": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS"],
    "Metal": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS"],
    "Energy": ["RELIANCE.NS", "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "BPCL.NS", "COALINDIA.NS", "ADANIENT.NS"],
    "Finance": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "SBILIFE.NS", "HDFCLIFE.NS", "SHRIRAMFIN.NS"],
    "Infra": ["LT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "GRASIM.NS"],
    "Consumer": ["ASIANPAINT.NS", "TITAN.NS"],
}

# Technical Analysis Settings
TA_CONFIG = {
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2,
    "ema_short": 9,
    "ema_medium": 21,
    "ema_long": 50,
    "ema_trend": 200,
    "supertrend_period": 10,
    "supertrend_multiplier": 3,
    "vwap_period": 14,
}

# Risk Management (conservative for beginners)
RISK_CONFIG = {
    "max_risk_per_trade_pct": 1.0,   # max 1% of capital per trade
    "max_daily_loss_pct": 3.0,        # stop trading if down 3% in a day
    "default_stop_loss_pct": 2.0,     # 2% stop loss
    "default_target_pct": 4.0,        # 4% target (2:1 risk-reward)
    "max_open_positions": 3,          # max 3 trades at once for beginners
    "paper_trading_default": True,    # start with paper trading
}

# Report Schedule (IST)
SCHEDULE = {
    "pre_market": "08:30",
    "market_open_check": "09:20",
    "mid_day": "12:30",
    "post_market": "16:00",
    "weekly_deep_dive": "sunday_10:00",
}

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "finance.db")
