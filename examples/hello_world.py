import ell
import numpy as np

from ell.stores.sql import SQLiteStore

def get_random_length():
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def hello(world: str):
    """Your goal is to be really kind to the person while saying hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name} characters or more!"

if __name__ == "__main__":
    ell.config.verbose = True
    ell.set_store('./logdir', autocommit=True)

    greeting = hello("sam altman")

    # List of strings
    last_word = greeting.split(" ")[-1]
    print([last_word])