"""
Finance Wiz Bot — Main Entry Point
Run this to start the Telegram bot.
"""
import sys
import os

# Ensure the finance-bot directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_bot import main

if __name__ == "__main__":
    main()
