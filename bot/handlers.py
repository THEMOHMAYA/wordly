import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatType

from .config import WORDS_PER_ROUND, INACTIVITY_TIMEOUT_SECONDS
from .game import game_manager
from .database import db

logger = logging.getLogger(__name__)

def get_new_game_keyboard() -> InlineKeyboardMarkup:
    """Returns the inline keyboard button for starting a new game."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 New Game", callback_data="btn_new_game")]
    ])

def reset_inactivity_timer(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Schedules or resets the 5-minute inactivity timer for a chat."""
    if not context.job_queue:
        return
    job_name = f"inactivity_{chat_id}"
    # Cancel existing jobs for this chat
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()

    # Schedule new 5-minute timer
    context.job_queue.run_once(
        inactivity_timeout_callback,
        when=INACTIVITY_TIMEOUT_SECONDS,
        chat_id=chat_id,
        name=job_name,
        data={"chat_id": chat_id}
    )

def cancel_inactivity_timer(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the inactivity timer when a game finishes or is stopped."""
    if not context.job_queue:
        return
    job_name = f"inactivity_{chat_id}"
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()

async def inactivity_timeout_callback(context: ContextTypes.DEFAULT_TYPE):
    """Fires when no words have been guessed for 5 minutes."""
    chat_id = context.job.chat_id
    game = game_manager.get_game(chat_id)
    if not game:
        return

    summary = game_manager.end_game(chat_id)
    cancel_inactivity_timer(chat_id, context)

    if summary and summary["rankings"]:
        scores_lines = []
        for i, user in enumerate(summary["rankings"][:10], start=1):
            scores_lines.append(f"{i}. {user['name']} - {user['points']} points 💎")
        scores_text = "\n".join(scores_lines)
    else:
        scores_text = "No words found."

    longest_info = ""
    if summary and summary["longest_word"]:
        longest_info = f"\n\nLongest words:\n{summary['longest_word']} - {summary['longest_word_user']}"

    text = (
        "🎉 Game over 🎉\n"
        "Nobody guessed a new word in last 5 minutes ⏰\n\n"
        "🏆 Scores\n\n"
        f"{scores_text}"
        f"{longest_info}\n\n"
        "/new - Start new game"
    )

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=get_new_game_keyboard()
        )
    except Exception as e:
        logger.error(f"Failed to send timeout message in chat {chat_id}: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    text = (
        "🎉 Welcome to Wordly Bot! 🧠✨\n\n"
        "An addictive word-guess game where you create words using the given letters 📚🔤\n\n"
        "🎮 /new — Start a game and challenge yourself\n"
        "📖 /help — View all available commands and how to play\n\n"
        "🚀 Sharpen your vocabulary, think fast, and climb the leaderboard! 🏆🔥"
    )
    
    bot_info = await context.bot.get_me()
    keyboard = None
    if update.effective_chat.type == ChatType.PRIVATE:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add me to a Group", url=f"https://t.me/{bot_info.username}?startgroup=true")]
        ])

    await update.message.reply_text(text, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    text = (
        "🔖 How to Play\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔹 Send /new to start a round.\n"
        "🔹 Create valid English words using the letters provided.\n"
        "🔹 Words must be between 3 to 12 letters long.\n"
        "🔹 Pro Tip: Letter repetition is completely allowed!\n\n"
        "⚽ Points System\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "We use a Progressive Curve scoring system to keep gameplay fair and rewarding. The longer the word, the bigger the payout!\n\n"
        "🔸 3 letters: 1 point\n"
        "🔸 4 letters: 2 points\n"
        "🔸 5 letters: 3 points\n"
        "🔸 6 letters: 5 points\n"
        "🔸 7 letters: 7 points\n"
        "🎯 8 to 12 letters: 10 points (Max reward)\n\n"
        "📌 Other Commands:\n"
        "🏆 /top — View leaderboard\n"
        "📊 /stats — View your profile stats\n"
        "🔤 /letters — Show current round letters\n"
        "🛑 /stop — End active round"
    )
    await update.message.reply_text(text)


async def new_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /new command."""
    chat = update.effective_chat
    
    # Check if in private chat
    if chat.type == ChatType.PRIVATE:
        bot_info = await context.bot.get_me()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_info.username}?startgroup=true")]
        ])
        await update.message.reply_text("🔥 Add me in a group to start playing!", reply_markup=keyboard)
        return

    # In group chat
    existing_game = game_manager.get_game(chat.id)
    if existing_game:
        # Prompt active round
        msg = (
            "⚠️ A game is already in progress!\n\n"
            f"✍🏻 WORD SCRAMBLE\n\n"
            f"🔡 Make words using these letters\n\n"
            f"{existing_game.get_letters_display()}\n\n"
            "👌 3–12 letter words are accepted\n"
            f"Total: {len(existing_game.found_words)}/{existing_game.target_words}"
        )
        await update.message.reply_text(msg)
        return

    # Start a brand new game
    game = game_manager.start_game(chat.id, target_words=WORDS_PER_ROUND)
    reset_inactivity_timer(chat.id, context)

    msg = (
        "✍🏻 WORD SCRAMBLE\n\n"
        "🔡 Make words using these letters\n\n"
        f"{game.get_letters_display()}\n\n"
        "👌 3–12 letter words are accepted\n"
        f"Total: 0/{game.target_words}"
    )
    await update.message.reply_text(msg)


async def stop_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /stop command to end current game."""
    chat = update.effective_chat
    game = game_manager.get_game(chat.id)
    if not game:
        await update.message.reply_text("ℹ️ No active game in this group. Send /new to start one!")
        return

    summary = game_manager.end_game(chat.id)
    cancel_inactivity_timer(chat.id, context)

    if summary and summary["rankings"]:
        scores_lines = []
        for i, user in enumerate(summary["rankings"][:10], start=1):
            scores_lines.append(f"{i}. {user['name']} - {user['points']} points 💎")
        scores_text = "\n".join(scores_lines)

        longest_info = ""
        if summary["longest_word"]:
            longest_info = f"\n\nLongest words:\n{summary['longest_word']} - {summary['longest_word_user']}"

        text = (
            "🎉 Game over 🎉\n\n"
            "🏆 Scores\n\n"
            f"{scores_text}"
            f"{longest_info}\n\n"
            "/new - Start new game"
        )
    else:
        text = "🛑 Game stopped.\n\n/new - Start new game"

    await update.message.reply_text(text, reply_markup=get_new_game_keyboard())


async def callback_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for inline button '🎮 New Game' click."""
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    if not chat:
        return

    existing_game = game_manager.get_game(chat.id)
    if existing_game:
        await query.message.reply_text(
            "⚠️ A game is already in progress!\n\n"
            f"✍🏻 WORD SCRAMBLE\n\n"
            f"🔡 Make words using these letters\n\n"
            f"{existing_game.get_letters_display()}\n\n"
            "👌 3–12 letter words are accepted\n"
            f"Total: {len(existing_game.found_words)}/{existing_game.target_words}"
        )
        return

    # Start new game
    game = game_manager.start_game(chat.id, target_words=WORDS_PER_ROUND)
    reset_inactivity_timer(chat.id, context)

    msg = (
        "✍🏻 WORD SCRAMBLE\n\n"
        "🔡 Make words using these letters\n\n"
        f"{game.get_letters_display()}\n\n"
        "👌 3–12 letter words are accepted\n"
        f"Total: 0/{game.target_words}"
    )
    await query.message.reply_text(msg)


async def letters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /letters or /hint command to re-display current game letters."""
    chat = update.effective_chat
    game = game_manager.get_game(chat.id)
    if not game:
        await update.message.reply_text("ℹ️ No active game. Send /new to start!")
        return

    msg = (
        "✍🏻 CURRENT ROUND\n\n"
        "🔡 Make words using these letters\n\n"
        f"{game.get_letters_display()}\n\n"
        f"Total words found: {len(game.found_words)}/{game.target_words}"
    )
    await update.message.reply_text(msg)


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /top and /leaderboard command."""
    chat = update.effective_chat
    # Fetch group top players if in a group
    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        top_players = db.get_chat_top_players(chat.id, limit=10)
        title = "🏆 Group Leaderboard"
    else:
        top_players = db.get_top_players(limit=10)
        title = "🏆 Global Leaderboard"

    if not top_players:
        await update.message.reply_text("📊 No scores recorded yet. Play a game with /new to get on the board!")
        return

    lines = [f"{title}\n━━━━━━━━━━━━━━━━━━"]
    for i, p in enumerate(top_players, start=1):
        name = p.get("first_name") or p.get("username") or f"Player {p['user_id']}"
        pts = p.get("points") if "points" in p else p.get("total_points", 0)
        words = p.get("words_count") if "words_count" in p else p.get("total_words", 0)
        lines.append(f"{i}. {name} — {pts} 💎 ({words} words)")

    await update.message.reply_text("\n".join(lines))


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /stats command."""
    user = update.effective_user
    user_stats = db.get_user_stats(user.id)
    
    if not user_stats or user_stats["total_words"] == 0:
        await update.message.reply_text(f"👤 {user.full_name}\n\nYou haven't found any words yet! Join a game with /new.")
        return

    longest = user_stats["longest_word"] or "None"
    text = (
        f"👤 Stats for {user.full_name}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💎 Total Diamonds: {user_stats['total_points']}\n"
        f"📚 Total Words Found: {user_stats['total_words']}\n"
        f"🌟 Longest Word: {longest} ({user_stats['longest_word_len']} letters)\n"
    )
    await update.message.reply_text(text)


async def handle_word_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming text messages in chat during active game."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    
    # If it's a command, let command handlers process it
    if text.startswith("/"):
        return

    chat_id = update.effective_chat.id
    game = game_manager.get_game(chat_id)
    if not game:
        return

    user = update.effective_user
    user_name = user.full_name or user.first_name or "Player"
    user_id = user.id

    status, result = game.process_word(text, user_id=user_id, user_name=user_name)

    if status == "ALREADY_FOUND":
        found_word = result["word"]
        await update.message.reply_text(f"⚠️ {found_word} is already found")

    elif status == "SUCCESS":
        # Reset 5-minute inactivity timer because new activity happened
        reset_inactivity_timer(chat_id, context)

        word = result["word"]
        points = result["points"]
        total_found = result["total_found"]
        target = result["target"]
        is_game_over = result["is_game_over"]

        # Word found notification format
        response_text = (
            f"{user_name} found \"{word}\"\n"
            f"+{points} 💎\n\n"
            f"{game.get_stars_letters_display()}\n\n"
            f"Total words found: {total_found}/{target}"
        )
        await update.message.reply_text(response_text)

        # If game is completed (20/20 words found)
        if is_game_over:
            cancel_inactivity_timer(chat_id, context)
            summary = result["game_over_data"]
            scores_lines = []
            for i, p in enumerate(summary["rankings"][:10], start=1):
                scores_lines.append(f"{i}. {p['name']} - {p['points']} points 💎")
            scores_text = "\n".join(scores_lines)

            longest_info = ""
            if summary["longest_word"]:
                longest_info = f"\n\nLongest words:\n{summary['longest_word']} - {summary['longest_word_user']}"

            game_over_text = (
                "🎉 Game over 🎉\n\n"
                "🏆 Scores\n\n"
                f"{scores_text}"
                f"{longest_info}\n\n"
                "/new - Start new game"
            )
            # Remove completed game from active games
            game_manager.end_game(chat_id)
            await update.message.reply_text(game_over_text, reply_markup=get_new_game_keyboard())
