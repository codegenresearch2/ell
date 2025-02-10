import ell
import numpy as np
from typing import List

from ell.stores.sql import SQLiteStore

# Initialize the store and set verbose mode
ell.init(store='./logdir', autocommit=True, verbose=True)

def get_random_length() -> int:
    """
    Generate a random length between 0 and 3000.

    Returns:
        int: A random length.
    """
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def hello(world: str) -> str:
    """
    Generate a friendly greeting to the given name with a random length.

    Args:
        world (str): The name to greet.

    Returns:
        str: A friendly greeting.
    """
    if not isinstance(world, str):
        raise ValueError("Input 'world' must be a string.")

    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name} characters or more!"

def main_loop(iterations: int = 100) -> List[str]:
    """
    Run the main loop for a given number of iterations.

    Args:
        iterations (int): The number of iterations to run the loop.

    Returns:
        List[str]: A list of the last words in each greeting.
    """
    greetings = []
    for _ in range(iterations):
        greeting = hello("sam altman")
        greetings.append(greeting.split(" ")[-1])
    return greetings

if __name__ == "__main__":
    last_words = main_loop()
    print(last_words)