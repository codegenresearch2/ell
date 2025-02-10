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
def hello(world: str):
    """Your goal is to be really kind to the other person while saying hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Hello {name}! I hope this heartfelt greeting is at least {number_of_chars_in_name} characters long to truly express my kindness."

if __name__ == "__main__":
    greeting = hello("sam altman")  # Expected output: "Hello Sam! I hope this heartfelt greeting is at least ..."

    # Print the last word of the greeting
    print(greeting.split(" ")[-1])