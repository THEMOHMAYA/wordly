import sqlite3
import os
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "wordly.db")

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    username TEXT,
                    total_points INTEGER DEFAULT 0,
                    total_words INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    longest_word TEXT DEFAULT '',
                    longest_word_len INTEGER DEFAULT 0,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_stats (
                    chat_id INTEGER,
                    user_id INTEGER,
                    first_name TEXT,
                    username TEXT,
                    points INTEGER DEFAULT 0,
                    words_count INTEGER DEFAULT 0,
                    PRIMARY KEY (chat_id, user_id)
                )
            """)
            conn.commit()

    def record_word_found(self, user_id: int, first_name: str, username: Optional[str], points: int, word: str, chat_id: Optional[int] = None):
        word = word.upper()
        word_len = len(word)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Update Global User Table
            cursor.execute("SELECT total_points, total_words, longest_word_len FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row is None:
                cursor.execute("""
                    INSERT INTO users (user_id, first_name, username, total_points, total_words, longest_word, longest_word_len)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                """, (user_id, first_name, username, points, word, word_len))
            else:
                new_longest_word = word if word_len > (row["longest_word_len"] or 0) else None
                if new_longest_word:
                    cursor.execute("""
                        UPDATE users
                        SET first_name = ?, username = ?, total_points = total_points + ?, total_words = total_words + 1,
                            longest_word = ?, longest_word_len = ?, last_active = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (first_name, username, points, new_longest_word, word_len, user_id))
                else:
                    cursor.execute("""
                        UPDATE users
                        SET first_name = ?, username = ?, total_points = total_points + ?, total_words = total_words + 1,
                            last_active = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (first_name, username, points, user_id))

            # 2. Update Group Chat Stats if chat_id is provided
            if chat_id:
                cursor.execute("""
                    INSERT INTO chat_stats (chat_id, user_id, first_name, username, points, words_count)
                    VALUES (?, ?, ?, ?, ?, 1)
                    ON CONFLICT(chat_id, user_id) DO UPDATE SET
                        first_name = excluded.first_name,
                        username = excluded.username,
                        points = chat_stats.points + excluded.points,
                        words_count = chat_stats.words_count + 1
                """, (chat_id, user_id, first_name, username, points))
            conn.commit()

    def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_top_players(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, first_name, username, total_points, total_words, longest_word
                FROM users
                ORDER BY total_points DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_chat_top_players(self, chat_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, first_name, username, points, words_count
                FROM chat_stats
                WHERE chat_id = ?
                ORDER BY points DESC
                LIMIT ?
            """, (chat_id, limit))
            return [dict(row) for row in cursor.fetchall()]

db = Database()
