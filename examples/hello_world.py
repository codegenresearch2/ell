import ell
import numpy as np

from ell.stores.sql import SQLiteStore

# Configuration settings for ell
# These settings enable verbose mode and set the store to a SQLite database located at './logdir'
ell.config.verbose = True
ell.set_store('./logdir', autocommit=True)

def get_random_length():
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def hello(world: str):
    """Your goal is to be really kind to the person while saying hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name} characters or more!"

if __name__ == "__main__":
    greeting = hello("sam altman")

    # Extract the last word from the greeting and print it
    last_word = greeting.split(" ")[-1]
    print(last_word)