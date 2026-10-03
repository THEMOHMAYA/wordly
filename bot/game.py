from typing import List, Dict, Set, Optional, Tuple
from .config import WORDS_PER_ROUND, MIN_WORD_LENGTH, MAX_WORD_LENGTH, get_points
from .dictionary import dictionary
from .database import db

class GameRound:
    def __init__(self, chat_id: int, target_words: int = WORDS_PER_ROUND):
        self.chat_id = chat_id
        self.target_words = target_words
        self.letters: List[str] = dictionary.generate_balanced_letters(count=8)
        self.letter_set: Set[str] = set(l.upper() for l in self.letters)
        self.found_words: Dict[str, Dict] = {} # word -> {user_id, user_name, points}
        self.user_scores: Dict[int, Dict] = {} # user_id -> {name, points, words: []}
        self.longest_word: str = ""
        self.longest_word_user: str = ""
        self.is_active: bool = True

    def get_letters_display(self) -> str:
        """Returns format: ▶️ E, T, O, P, S, L, N, A"""
        return "▶️ " + ", ".join(self.letters)

    def get_stars_letters_display(self) -> str:
        """Returns format: ⭐  E T O P S L N A"""
        return "⭐  " + " ".join(self.letters)

    def process_word(self, raw_word: str, user_id: int, user_name: str) -> Tuple[str, Optional[Dict]]:
        """
        Process a word attempt from a user.
        Returns:
            ("IGNORED", None) -> Not matching length/letters or not a valid dictionary word
            ("ALREADY_FOUND", {"word": title_word}) -> Already found previously
            ("SUCCESS", {
                "word": title_word,
                "points": points,
                "total_found": count,
                "target": target,
                "is_game_over": bool,
                "game_over_data": dict (if game over)
            })
        """
        if not self.is_active:
            return "IGNORED", None

        word = raw_word.strip().upper()

        # Check word length
        if not (MIN_WORD_LENGTH <= len(word) <= MAX_WORD_LENGTH):
            return "IGNORED", None

        # Check only alpha
        if not word.isalpha():
            return "IGNORED", None

        # Check if all letters are in the round's letter set (letter repetition is allowed)
        if not set(word).issubset(self.letter_set):
            return "IGNORED", None

        # Check if word is in valid English dictionary
        if not dictionary.is_valid_word(word):
            return "IGNORED", None

        title_word = word.capitalize()

        # Check if already found
        if word in self.found_words:
            return "ALREADY_FOUND", {"word": title_word}

        # Calculate points
        points = get_points(len(word))

        # Record word
        self.found_words[word] = {
            "user_id": user_id,
            "user_name": user_name,
            "points": points
        }

        # Update round scores
        if user_id not in self.user_scores:
            self.user_scores[user_id] = {
                "name": user_name,
                "points": 0,
                "words": []
            }
        self.user_scores[user_id]["points"] += points
        self.user_scores[user_id]["words"].append(word)
        self.user_scores[user_id]["name"] = user_name

        # Update longest word in this game
        if len(word) > len(self.longest_word):
            self.longest_word = title_word
            self.longest_word_user = user_name

        # Record to persistent database
        db.record_word_found(
            user_id=user_id,
            first_name=user_name,
            username=None,
            points=points,
            word=word,
            chat_id=self.chat_id
        )

        total_found = len(self.found_words)
        is_game_over = total_found >= self.target_words

        game_over_data = None
        if is_game_over:
            self.is_active = False
            game_over_data = self.get_game_over_summary()

        return "SUCCESS", {
            "word": title_word,
            "points": points,
            "total_found": total_found,
            "target": self.target_words,
            "is_game_over": is_game_over,
            "game_over_data": game_over_data
        }

    def get_game_over_summary(self) -> Dict:
        """Generates the leaderboard and longest word data for Game Over."""
        # Sort users by points descending
        sorted_users = sorted(
            self.user_scores.values(),
            key=lambda x: x["points"],
            reverse=True
        )

        return {
            "rankings": sorted_users,
            "longest_word": self.longest_word,
            "longest_word_user": self.longest_word_user
        }


class GameManager:
    def __init__(self):
        self.active_games: Dict[int, GameRound] = {}

    def get_game(self, chat_id: int) -> Optional[GameRound]:
        game = self.active_games.get(chat_id)
        if game and game.is_active:
            return game
        return None

    def start_game(self, chat_id: int, target_words: int = WORDS_PER_ROUND) -> GameRound:
        game = GameRound(chat_id=chat_id, target_words=target_words)
        self.active_games[chat_id] = game
        return game

    def end_game(self, chat_id: int) -> Optional[Dict]:
        game = self.active_games.get(chat_id)
        if game and game.is_active:
            game.is_active = False
            summary = game.get_game_over_summary()
            del self.active_games[chat_id]
            return summary
        return None

game_manager = GameManager()
