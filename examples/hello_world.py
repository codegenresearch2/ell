import ell
import numpy as np

from ell.stores.sql import SQLiteStore

# Configure verbosity and store settings
ell.config.verbose = True
# Set the store to SQLiteStore with the specified path and autocommit enabled
# Equivalent to: ell.init(store='./logdir', autocommit=True, verbose=True)
ell.set_store('./logdir', autocommit=True)

def get_random_length() -> int:
    """
    Generate a random length between 0 and 3000.
    """
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def hello(world: str) -> str:
    """
    Your goal is to be really friendly while saying hello.
    """
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name} characters or more!"

if __name__ == "__main__":
    greeting = hello("sam altman")
    # Extract the last word from the greeting
    print(greeting.split(" ")[-1])