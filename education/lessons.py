"""
Educational Module — Daily lessons to teach stock market basics.
30-day curriculum from zero to comfortable investor.
"""


LESSON_LIBRARY = {
    1: {
        "topic": "What is the Stock Market?",
        "lesson": """🎓 DAY 1: What is the Stock Market?

Think of it like a sabzi mandi (vegetable market), but instead of vegetables, people buy and sell tiny pieces of companies.

📌 Key Points:
• A "stock" = a tiny piece of ownership in a company
• If you buy 1 share of Reliance, you literally own a small part of Reliance
• NSE (National Stock Exchange) and BSE (Bombay Stock Exchange) are the two markets in India
• Nifty 50 = Top 50 companies on NSE (like the "popular kids" of the market)
• Sensex = Top 30 companies on BSE

💡 Real Example:
If TCS has 100 crore shares and you buy 100, you own 0.0000001% of TCS. Tiny, but real ownership!

🎯 Tip: You don't need lakhs to start. You can buy 1 share of many companies for under ₹500.

❓ Quiz: What does "Nifty 50" represent?
Answer: The top 50 companies listed on NSE by market value.""",
    },

    2: {
        "topic": "Reading Stock Prices (OHLCV)",
        "lesson": """🎓 DAY 2: How to Read a Stock Price

Every stock has 5 key numbers each day — think of it as a daily report card:

📌 OHLCV:
• O = Open: Price when market opened (9:15 AM)
• H = High: Highest price during the day
• L = Low: Lowest price during the day
• C = Close: Price when market closed (3:30 PM)
• V = Volume: How many shares were traded

💡 Example:
RELIANCE today: O=2840, H=2870, L=2825, C=2860, V=50 lakh shares
This means: Opened at ₹2840, went as high as ₹2870, as low as ₹2825, and ended at ₹2860.

🔑 Pro tip: Close price is the MOST important. It's what everyone refers to as "the price."

High Volume = lots of interest (big news?)
Low Volume = nobody cares (boring day)

❓ Quiz: If a stock opened at ₹100 and closed at ₹105, did it go up or down?
Answer: UP by ₹5 (5%)! Green day! 🟢""",
    },

    3: {
        "topic": "Market Indices (Nifty, Sensex, Bank Nifty)",
        "lesson": """🎓 DAY 3: Market Indices — The Market's Mood Ring

Instead of checking all 5000+ stocks, we check indices. It's like checking the class average instead of every student's marks.

📌 Key Indices:
• Nifty 50: Average of top 50 NSE stocks → Overall market health
• Sensex: Average of top 30 BSE stocks → Same thing, older index
• Bank Nifty: Only banking stocks → Shows how banks are doing
• Nifty IT: Only IT stocks (TCS, Infosys, etc.)

💡 When people say "market is up":
They mean Nifty/Sensex is up. If Nifty goes from 24,000 to 24,500, market went up ~2%.

🔑 Why it matters:
If Nifty is crashing, even good stocks usually fall. "A rising tide lifts all boats" — and a falling tide sinks them.

📊 Current Nifty levels to remember:
• Above 25,000 = Bull territory (strong)
• 22,000-25,000 = Normal range
• Below 22,000 = Bear territory (weak)

❓ Quiz: If Bank Nifty falls 3% but Nifty only falls 0.5%, which sector is weak?
Answer: Banking! Banks are dragging, rest of market is fine.""",
    },

    4: {
        "topic": "FII, DII, Retail — Who Moves the Market?",
        "lesson": """🎓 DAY 4: Who Are the Players?

Three groups trade in the Indian market:

📌 The Players:
• FII (Foreign Institutional Investors): Big foreign funds (Goldman Sachs, BlackRock, etc.)
  - They bring HUGE money. When FIIs buy, market usually goes UP
  - When FIIs sell, market usually goes DOWN
  - Think of them as the "whales" 🐋

• DII (Domestic Institutional Investors): Indian mutual funds, LIC, SBI MF
  - They often BUY when FIIs sell (supporting the market)
  - Your SIP money goes here!

• Retail: That's YOU and me
  - We're the smallest fish 🐟
  - Often buy at highs (FOMO) and sell at lows (panic)

💡 Daily check:
FII bought ₹2000 Cr + DII bought ₹1500 Cr = VERY bullish day
FII sold ₹3000 Cr + DII sold ₹500 Cr = VERY bearish day

🎯 Tip: Always check FII/DII data. It tells you what the "smart money" is doing.

❓ Quiz: If FIIs sold ₹5000 Cr today, what's likely to happen to the market?
Answer: Market will likely fall. FII selling = big pressure.""",
    },

    5: {
        "topic": "Types of Orders",
        "lesson": """🎓 DAY 5: Types of Orders — How to Actually Buy/Sell

When you want to buy a stock, you can't just say "I want it." You need to place an ORDER:

📌 Order Types:
• Market Order: "Buy RIGHT NOW at whatever the current price is"
  - Fast but you might get a slightly different price
  - Use when: You NEED to buy/sell immediately

• Limit Order: "Buy only at ₹500 or less"
  - You set YOUR price. Trade only happens if price reaches it
  - Use when: You want a specific price (most common)

• Stop Loss (SL): "If price falls to ₹480, SELL automatically"
  - This is your SAFETY NET. It prevents big losses
  - ALWAYS use this. Non-negotiable. 🛡️

💡 Example:
You buy Infosys at ₹1500 (Limit Order)
You set Stop Loss at ₹1450
If Infosys drops to ₹1450 → auto-sold, you lose ₹50/share
If Infosys goes to ₹1600 → you manually sell, profit ₹100/share

🎯 Golden Rule: NEVER buy without a stop loss. Ever.

❓ Quiz: You want to buy a stock only if it falls to ₹200. Which order type?
Answer: Limit Order at ₹200!""",
    },

    6: {
        "topic": "Demat Account and How Trading Works",
        "lesson": """🎓 DAY 6: Demat Account — Your Stock Wallet

Just like you need a bank account for money, you need a Demat account for stocks.

📌 What you need:
• Demat Account: Stores your stocks (like a locker)
• Trading Account: Used to buy/sell (like a counter)
• Bank Account: Your regular bank account (linked for money transfer)

Most brokers give you all three together!

📌 Top Brokers in India:
• Zerodha: Most popular, ₹0 for delivery, ₹20/trade for intraday
• Groww: Super simple app, good for beginners
• Angel One: Free trades, good research
• Upstox: Low cost, decent platform

💡 How a trade works:
1. You deposit ₹10,000 from bank → Trading account
2. You buy 5 shares of ITC at ₹450 each = ₹2,250
3. Shares appear in your Demat account (T+1 day)
4. Money left in trading account: ₹7,750

🎯 Start with: Open a Zerodha or Groww account. It's free and takes 15 minutes with Aadhaar.

❓ Quiz: Where are your stocks stored?
Answer: In your Demat account!""",
    },

    7: {
        "topic": "Candlestick Basics",
        "lesson": """🎓 DAY 7: Candlestick Charts — Reading the Market's Body Language

Candlesticks are the most popular way to see stock prices on a chart. Each candle = one time period.

📌 Anatomy of a Candle:
• Body (thick part): Difference between Open and Close
  - Green/White body = Close > Open (price went UP) 🟢
  - Red/Black body = Close < Open (price went DOWN) 🔴
• Wicks (thin lines): Show High and Low

📌 What candle shapes tell you:
• Long green body = Strong buying (bulls in control)
• Long red body = Strong selling (bears in control)
• Small body, long wicks = Confusion (nobody's sure)
• Doji (cross shape) = Perfect indecision, possible reversal

💡 Example:
If you see 5 green candles in a row → Strong uptrend
If you see a doji after those 5 greens → "Hmm, trend might be tired"

🎯 Tip: Don't trade based on ONE candle. Look at the pattern of 3-5 candles.

❓ Quiz: A candle is green with a very long body and tiny wicks. What does it mean?
Answer: Strong buying! Buyers controlled the entire day.""",
    },

    8: {
        "topic": "Support and Resistance",
        "lesson": """🎓 DAY 8: Support & Resistance — Floor and Ceiling

📌 Support: A price level where the stock STOPS FALLING and bounces up
  - Think of it as a floor. The stock "rests" here.
  - More times it bounces off, STRONGER the support

📌 Resistance: A price level where the stock STOPS RISING and falls back
  - Think of it as a ceiling. The stock hits its head here.
  - More times it fails here, STRONGER the resistance

💡 Real Example:
RELIANCE keeps bouncing between ₹2800 (support) and ₹2900 (resistance)
→ Buy near ₹2800, sell near ₹2900 (range trading!)

📌 What happens when they BREAK?
• Stock breaks ABOVE resistance → It often ROCKETS up (breakout!)
  Old resistance becomes NEW support
• Stock breaks BELOW support → It often CRASHES down (breakdown!)
  Old support becomes NEW resistance

🎯 Tip: Never buy a stock right at resistance. Wait for it to break above, or buy near support.

❓ Quiz: A stock has bounced off ₹500 three times and then breaks below it. What happens?
Answer: ₹500 was support, now it becomes resistance. Stock likely falls further.""",
    },

    9: {
        "topic": "Moving Averages",
        "lesson": """🎓 DAY 9: Moving Averages — The Trend is Your Friend

A Moving Average (MA) smooths out price data to show the TREND clearly.

📌 Types:
• EMA 9 (9-day): Short-term trend (this week)
• EMA 21 (21-day): Medium-term trend (this month)
• EMA 50 (50-day): Long-term trend (last 2 months)
• EMA 200 (200-day): MAJOR trend (almost a year)

📌 How to use:
• Price ABOVE EMA → Uptrend (bullish)
• Price BELOW EMA → Downtrend (bearish)
• Short EMA crosses ABOVE long EMA → "Golden Cross" = BUY signal
• Short EMA crosses BELOW long EMA → "Death Cross" = SELL signal

💡 Example:
If TCS price is above its 200 EMA → Long-term trend is UP
If 9 EMA just crossed above 21 EMA → Short-term buying started

🎯 Simplest strategy ever: Only buy stocks that are ABOVE their 200 EMA. Ignore everything below it.

❓ Quiz: Stock price is below 9 EMA but above 200 EMA. What's happening?
Answer: Short-term dip in a long-term uptrend. Could be a buying opportunity!""",
    },

    10: {
        "topic": "RSI — Overbought or Oversold?",
        "lesson": """🎓 DAY 10: RSI (Relative Strength Index)

RSI is a number from 0 to 100 that tells you if a stock has been bought too much or sold too much.

📌 The Rules:
• RSI > 70 = OVERBOUGHT → Stock went up too fast, might fall soon
• RSI < 30 = OVERSOLD → Stock fell too much, might bounce soon
• RSI 30-70 = NEUTRAL → Normal zone

📌 Think of it like this:
Imagine running. RSI measures how tired you are.
• RSI 80 = You're exhausted, need to rest (stock needs to cool down)
• RSI 20 = You've been resting too long, ready to run again

💡 Example:
HDFC Bank RSI = 75 → "Hmm, it's been running up a lot. Maybe wait before buying."
Tata Steel RSI = 25 → "It's been beaten down. Could bounce from here."

⚠️ WARNING: RSI can STAY overbought/oversold for days in strong trends.
RSI 80 doesn't mean "SELL NOW." It means "be careful if buying."

🎯 Best use: Combine RSI with Support levels. RSI oversold + at support = Strong buy signal.

❓ Quiz: A stock's RSI is 28 and it's sitting right on strong support. What might you do?
Answer: This is a potential buy! Oversold + support = good combo.""",
    },
}

# Lessons 11-30 follow the same pattern
for i in range(11, 31):
    topics = [
        "MACD — Spotting Momentum Shifts",
        "Bollinger Bands — Volatility Breakouts",
        "Volume Analysis — The Fuel Behind Moves",
        "PE Ratio — Is It Cheap or Expensive?",
        "EPS and Revenue Growth",
        "Debt-to-Equity Ratio",
        "ROE — Return on Equity",
        "Mutual Funds vs Direct Stocks",
        "SIP: Power of Regular Investing",
        "Intraday vs Swing vs Positional",
        "Risk Management & Position Sizing",
        "Chart Patterns (Head & Shoulders)",
        "Sector Rotation Strategy",
        "Reading Annual Reports (Basics)",
        "Dividends: Passive Income",
        "IPOs: Should You Invest?",
        "Options Basics (Calls & Puts)",
        "Tax on Stock Gains (STCG/LTCG)",
        "Building Your First Portfolio",
        "Trading Psychology: Fear & Greed",
    ]
    idx = i - 11
    LESSON_LIBRARY[i] = {
        "topic": topics[idx],
        "lesson": f"🎓 DAY {i}: {topics[idx]}\n\n[AI-powered lesson will be generated when ANTHROPIC_API_KEY is configured]\n\nFor now, search '{topics[idx]}' on Varsity by Zerodha (varsity.zerodha.com) — it's the BEST free resource for learning Indian stock markets.",
    }


def get_lesson(day_number):
    """Get lesson for a specific day."""
    if day_number in LESSON_LIBRARY:
        return LESSON_LIBRARY[day_number]
    return LESSON_LIBRARY.get(((day_number - 1) % 30) + 1)


def get_all_topics():
    """Get list of all topics."""
    return {day: info["topic"] for day, info in sorted(LESSON_LIBRARY.items())}
