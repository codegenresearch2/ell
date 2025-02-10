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
    """Your goal is to be genuinely friendly and expressive while saying hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Hello {name}! I'm thrilled to meet you. Let's make this conversation at least {number_of_chars_in_name} characters long to ensure we have plenty of time to connect."

if __name__ == "__main__":
    greeting = hello("sam altman")  # Expected output: "Hello Sam! I'm thrilled to meet you. Let's make this conversation at least ..."

    # Print the last word of the greeting
    print(greeting.split(" ")[-1])