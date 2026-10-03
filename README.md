# 🎮 Wordly - Telegram Word Guess Game Bot 📚🔤

Wordly is an addictive word scramble puzzle bot for Telegram groups and channels. Players scramble to create valid English words from 8 given letters and earn diamonds 💎 based on word length!

---

## 🚀 Features

- 🔡 **Word Scramble Gameplay**: 8 balanced letters with guaranteed 50–300+ valid words per round.
- 💎 **Progressive Curve Scoring**:
  - **3 letters**: +1 💎
  - **4 letters**: +2 💎
  - **5 letters**: +3 💎
  - **6 letters**: +5 💎
  - **7 letters**: +7 💎
  - **8–12 letters**: +10 💎 (Max reward)
- 🔠 **Letter Repetition**: Players can repeat available letters freely (e.g. `APPLE` from `[E, T, O, P, S, L, N, A]`).
- ⚠️ **Duplicate Detection**: Real-time alerts when a word has already been discovered (`⚠️ Slope is already found`).
- 🏆 **Group & Global Leaderboards**: Track total diamonds, words solved, and longest words with SQLite persistence.
- 👤 **Player Stats**: Individual profile view with `/stats` and `/me`.
- 🏁 **Game Over Summary**: Top 10 scoreboard and longest word attribution once 20 words are found or `/stop` is called.

---

## 🕹️ Commands

| Command | Description |
| :--- | :--- |
| `/start` | Welcome message and bot introduction. |
| `/help` | Explains rules, word limits, and points system. |
| `/new` | Starts a new round of 20 words in a group. |
| `/stop` / `/end` | Ends current game round and shows final scoreboard. |
| `/letters` / `/hint` | Re-displays current letters and found words progress. |
| `/top` / `/leaderboard` | View top diamond earners in the group/globally. |
| `/stats` / `/me` | View your personal diamonds, words, and record word. |

---

## ⚙️ Setup & Installation

### 1. Create your Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the instructions to choose a name and username.
3. Copy the HTTP API token provided by BotFather.
4. **Important Group Setting**: In BotFather, send `/setprivacy`, choose your bot, and set it to **`Disable`** (or make the bot an admin in your group) so the bot can read word guesses sent by group members.

### 2. Configure Token
Open the [`.env`](file:///c:/Users/Ayush%20Raj/Downloads/Telegram%20Desktop/wordly/.env) file and paste your bot token:
```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
WORDS_PER_ROUND=20
```

### 3. Run the Bot
Run the bot with:
```bash
python main.py
```

---

## 📁 Project Structure

```
wordly/
├── bot/
│   ├── __init__.py
│   ├── config.py         # Config variables & points calculation
│   ├── database.py       # SQLite database for points & leaderboard
│   ├── dictionary.py     # 83k+ English dictionary & letter generator
│   ├── game.py           # Active round manager & word processor
│   └── handlers.py       # Telegram command & message handlers
├── data/
│   ├── words.txt         # Curated standard English words
│   └── wordly.db         # SQLite persistent database (auto-created)
├── .env                  # Your Telegram bot token configuration
├── .env.example          # Environment template
├── main.py               # Main bot executable
├── requirements.txt      # Python dependencies
└── test_game.py          # Test suite simulating actual gameplay
```
