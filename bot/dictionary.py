import os
import random
from typing import List, Set

DICTIONARY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "words.txt")

class WordDictionary:
    def __init__(self, dict_path: str = DICTIONARY_PATH):
        self.words: Set[str] = set()
        self.load_words(dict_path)

    def load_words(self, dict_path: str):
        if os.path.exists(dict_path):
            with open(dict_path, "r", encoding="utf-8") as f:
                self.words = {line.strip().upper() for line in f if line.strip()}
        else:
            print(f"Warning: Dictionary file not found at {dict_path}")

    def is_valid_word(self, word: str) -> bool:
        """Check if the word is a valid English word in our dictionary."""
        return word.upper() in self.words

    def get_possible_words(self, letters: List[str], min_len: int = 3, max_len: int = 12) -> List[str]:
        """Find all valid dictionary words that can be made from the given letters (repetition allowed)."""
        letter_set = set(l.upper() for l in letters)
        possible = []
        for w in self.words:
            if min_len <= len(w) <= max_len:
                if set(w).issubset(letter_set):
                    possible.append(w)
        return possible

    def generate_balanced_letters(self, count: int = 8, min_possible_words: int = 60) -> List[str]:
        """
        Generate a balanced set of letters containing 2-3 vowels and balanced consonants,
        ensuring there are at least min_possible_words possible.
        """
        vowels = ['A', 'E', 'I', 'O', 'U']
        consonants = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T', 'V', 'W', 'Y']
        # Weighted consonant choices for common letters
        common_consonants = ['T', 'N', 'S', 'R', 'H', 'L', 'D', 'C', 'M', 'P', 'G', 'B', 'W', 'Y', 'F']

        for _ in range(50):
            num_vowels = random.choice([2, 3])
            num_cons = count - num_vowels
            
            chosen_vowels = random.sample(vowels, num_vowels)
            # Sample consonants from common pool
            if len(common_consonants) >= num_cons:
                chosen_cons = random.sample(common_consonants, num_cons)
            else:
                chosen_cons = random.sample(consonants, num_cons)
                
            candidate = chosen_vowels + chosen_cons
            random.shuffle(candidate)

            possible = self.get_possible_words(candidate)
            if len(possible) >= min_possible_words:
                return candidate

        # Fallback preset letters if random generation took too many tries
        fallback_sets = [
            ['E', 'T', 'O', 'P', 'S', 'L', 'N', 'A'],
            ['A', 'E', 'I', 'R', 'S', 'T', 'L', 'N'],
            ['E', 'O', 'U', 'R', 'S', 'T', 'P', 'L'],
            ['A', 'E', 'O', 'M', 'P', 'L', 'S', 'T'],
            ['A', 'I', 'E', 'C', 'R', 'T', 'S', 'P']
        ]
        return random.choice(fallback_sets)

# Global singleton
dictionary = WordDictionary()
