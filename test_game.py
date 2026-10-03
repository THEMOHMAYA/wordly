import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Test imports
from bot.config import get_points, WORDS_PER_ROUND
from bot.dictionary import dictionary
from bot.database import db
from bot.game import game_manager

print("1. Testing Dictionary...")
assert dictionary.is_valid_word('APPLE'), 'APPLE should be valid'
assert dictionary.is_valid_word('SLOPE'), 'SLOPE should be valid'
assert dictionary.is_valid_word('XYZABCQQ') is False, 'Invalid word should be False'
print(f"   -> Dictionary has {len(dictionary.words)} words")

print("2. Testing Letter Generator...")
letters = dictionary.generate_balanced_letters(count=8)
possible = dictionary.get_possible_words(letters)
print(f"   -> Generated letters: {letters}")
print(f"   -> Total possible words found: {len(possible)}")
assert len(possible) >= 30, 'Should have plenty of valid words'

print("3. Testing Points Curve...")
assert get_points(3) == 1, '3 letter word should be 1'
assert get_points(4) == 2, '4 letter word should be 2'
assert get_points(5) == 3, '5 letter word should be 3'
assert get_points(6) == 5, '6 letter word should be 5'
assert get_points(7) == 7, '7 letter word should be 7'
assert get_points(8) == 10, '8 letter word should be 10'
assert get_points(12) == 10, '12 letter word should be 10'
print("   -> Points system verified!")

print("4. Simulating Game Round from transcript...")
chat_id = -100123456789
user_id = 999
user_name = "𝆺𝅥اـ꯭ـ꯭𝞂⃕𝝲𝝴꯭•⚚𝆺𝅥𝗦͟𝗛͟𝗔͟𝗗͟❍֟፝͢͠𝗪͟𝆺꯭꯭꯭꯭𝅥𝆬─𝄄꯭꯭𝄄꯭꯭꯭ ̶꯭𝅥ͦ𝆬😈"

# Force transcript letters: E, T, O, P, S, L, N, A
game = game_manager.start_game(chat_id, target_words=20)
game.letters = ['E', 'T', 'O', 'P', 'S', 'L', 'N', 'A']
game.letter_set = set(game.letters)

transcript_words = [
    'top', 'slope', 'apple', 'pot', 'plane', 'slope', # duplicate
    'STONE', 'PLATE', 'NOTES', 'PETAL', 'STOP', 'SLOT',
    'SALT', 'LOAN', 'LATE', 'PANTS', 'PASTE', 'LEAST',
    'POLE', 'TONE', 'NOTE'
]

words_found_count = 0
for w in transcript_words:
    status, res = game.process_word(w, user_id=user_id, user_name=user_name)
    if status == 'SUCCESS':
        words_found_count += 1
        print(f"   [+] Found \"{res['word']}\" (+{res['points']} 💎) - Total: {res['total_found']}/{res['target']}")
        if res['is_game_over']:
            print("   🎉 Game over triggered! Summary:")
            summary = res['game_over_data']
            for rank, u in enumerate(summary['rankings'], 1):
                print(f"      {rank}. {u['name']} - {u['points']} points 💎")
            print(f"      Longest words: {summary['longest_word']} - {summary['longest_word_user']}")
    elif status == 'ALREADY_FOUND':
        print(f"   [!] Handled duplicate: ⚠️ {res['word']} is already found")

assert words_found_count == 20, f"Expected 20 words found, got {words_found_count}"

print("5. Testing Database Leaderboards...")
top_players = db.get_top_players(5)
print(f"   -> Top players globally: {len(top_players)}")
print(f"   -> Player score: {top_players[0]['total_points']} diamonds!")

print("\n🚀 ALL TESTS PASSED PERFECTLY!")
