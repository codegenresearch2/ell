import ell
import numpy as np

from ell.stores.sql import SQLiteStore

# Configure verbosity and store settings
ell.config.verbose = True
# Set the store to use SQLite and specify the database file path
# This line sets up the database connection for the application
ell.set_store('./logdir', autocommit=True)

def get_random_length():
    """
    Generate a random length between 0 and 3000.
    """
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def hello(world: str) -> str:
    """
    Greet the given name in a friendly manner with a random length.
    """
    if not isinstance(world, str):
        raise ValueError("Input 'world' must be a string.")

    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Hello {name}! Your name has {number_of_chars_in_name} characters or more. How's your day going?"

if __name__ == "__main__":
    greeting = hello("sam altman")
    # Print the last word of the greeting
    # This line prints the last word of the generated greeting
    print(greeting.split(" ")[-1])