import sys
import os
import logging

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from bot.config import BOT_TOKEN
from bot.handlers import (
    start_command,
    help_command,
    new_game_command,
    stop_game_command,
    letters_command,
    leaderboard_command,
    stats_command,
    handle_word_message,
    callback_new_game,
)

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("WordlyBot")

def main():
    if not BOT_TOKEN or BOT_TOKEN.strip() == "YOUR_BOT_TOKEN_HERE":
        print("=" * 60)
        print("⚠️  ERROR: BOT_TOKEN is not configured!")
        print("Please open the '.env' file and add your Telegram Bot Token:")
        print("BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        print("You can get a token for free from @BotFather on Telegram.")
        print("=" * 60)
        sys.exit(1)

    logger.info("Initializing Wordly Bot...")

    # Build Telegram Bot Application
    app = Application.builder().token(BOT_TOKEN).build()

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_game_command))
    app.add_handler(CommandHandler("newgame", new_game_command))
    app.add_handler(CommandHandler("stop", stop_game_command))
    app.add_handler(CommandHandler("end", stop_game_command))
    app.add_handler(CommandHandler("letters", letters_command))
    app.add_handler(CommandHandler("hint", letters_command))
    app.add_handler(CommandHandler("top", leaderboard_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("me", stats_command))

    # Register Callback Query Handler for Inline Buttons
    app.add_handler(CallbackQueryHandler(callback_new_game, pattern="^btn_new_game$"))

    # Register Message Handler for word guesses (filter for text without commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_word_message))

    logger.info("Wordly Bot is now polling for messages...")
    print("✨ Wordly Bot started successfully! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
