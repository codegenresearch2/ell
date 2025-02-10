import ell
import numpy as np

from ell.stores.sql import SQLiteStore

def initialize_store():
    ell.config.verbose = True
    ell.set_store('./logdir', autocommit=True)

def calculate_random_length():
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def generate_greeting(name: str):
    """Your goal is to be really kind to the person while saying hello"""
    capitalized_name = name.capitalize()
    char_limit = calculate_random_length()

    return f"Say hello to {capitalized_name} in {char_limit} characters or more!"

if __name__ == "__main__":
    initialize_store()
    greeting = generate_greeting("sam altman")

    # Extract the last word from the greeting
    last_word = greeting.split(" ")[-1]
    print(last_word)