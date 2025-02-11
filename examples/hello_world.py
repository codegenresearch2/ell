import ell
import numpy as np
from ell.stores.sql import SQLiteStore

# Set verbose mode and initialize the store
ell.config.verbose = True
ell.set_store(SQLiteStore('./logdir'), autocommit=True)

def get_random_length():
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def hello(world: str):
    """Your goal is to be really kind to the other guy while saying hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Hello {name}, hope you're having a great day! This message is at least {number_of_chars_in_name} characters long."

if __name__ == "__main__":
    # Generate a greeting
    greeting = hello("sam altman")

    # Extract the last word of the greeting
    last_word = greeting.split()[-1]

    # Print the last word of the greeting
    print(f"The last word of the greeting is: {last_word}")