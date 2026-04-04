"""
Run both the Telegram bot and the web dashboard.
For cloud deployment — runs everything in one process.
"""
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_dashboard():
    """Run Flask dashboard in a separate thread."""
    try:
        from dashboard.app import app
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        print("Dashboard error: " + str(e))


def run_bot():
    """Run Telegram bot."""
    try:
        from bot.telegram_bot import main
        main()
    except Exception as e:
        print("Bot error: " + str(e))


if __name__ == "__main__":
    print("Starting Finance Wiz...")
    print("Dashboard: http://localhost:" + str(os.environ.get("PORT", 8080)))
    print("Telegram: @finanacewiz_bot")

    # Start dashboard in background thread
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()

    # Run bot in main thread (blocking)
    run_bot()
