import ell
import numpy as np

from ell.stores.sql import SQLiteStore

# Initialize the store directly in the global scope
# Equivalent to ell.init(store='./logdir', autocommit=True, verbose=True)
ell.set_store('./logdir', autocommit=True)
ell.config.verbose = True

def get_random_length():
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def greet(world: str):
    """Your goal is to be really meant to the other guy while saying hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name} characters or more!"

if __name__ == "__main__":
    greeting = greet("sam altman")  # Expected output: "Say hello to Sam in ... characters or more!"

    # Print the last word of the greeting
    print(greeting.split(" ")[-1])