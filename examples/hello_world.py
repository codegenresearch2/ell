import ell
import numpy as np
from ell.stores.sql import SQLiteStore

# Set configuration settings for ELL
ell.config.verbose = True

# Initialize the store
ell.set_store('./logdir', autocommit=True)

def get_random_length():
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def hello(world: str):
    """Your goal is to be really meant to the other guy while saying hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()
    return f"Say hello to {name} in {number_of_chars_in_name} characters or more!"

if __name__ == "__main__":
    # Generate a greeting and print the last word of the greeting
    greeting = hello("sam altman")
    print(greeting.split(" ")[-1])