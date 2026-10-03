import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Game Settings
WORDS_PER_ROUND = int(os.getenv("WORDS_PER_ROUND", "20"))
INACTIVITY_TIMEOUT_SECONDS = int(os.getenv("INACTIVITY_TIMEOUT", "300")) # 5 minutes
MIN_WORD_LENGTH = 3
MAX_WORD_LENGTH = 12
LETTERS_COUNT = 8

# Progressive Curve Points System
POINT_SYSTEM = {
    3: 1,
    4: 2,
    5: 3,
    6: 5,
    7: 7,
    8: 10,
    9: 10,
    10: 10,
    11: 10,
    12: 10
}

def get_points(word_len: int) -> int:
    """Returns the diamond points for a word of given length."""
    if word_len >= 8:
        return 10
    return POINT_SYSTEM.get(word_len, 0)
