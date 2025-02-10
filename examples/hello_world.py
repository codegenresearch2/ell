import ell
import numpy as np

from ell.stores.sql import SQLiteStore

# Initialize the store directly in the global scope
# Equivalent to ell.init(store='./logdir', autocommit=True, verbose=True)
ell.set_store('./logdir', autocommit=True)
ell.config.verbose = True

def calculate_greeting_length():
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def greet(person: str):
    """Your goal is to be warm and welcoming while saying hello"""
    name = person.capitalize()
    min_chars_in_greeting = calculate_greeting_length()

    return f"Hello {name}! I'm delighted to meet you. Let's make this conversation at least {min_chars_in_greeting} characters long to ensure we have plenty of time to connect and get to know each other."

if __name__ == "__main__":
    greeting = greet("sam altman")  # Expected output: "Hello Sam! I'm delighted to meet you. Let's make this conversation at least ..."

    # Print the last word of the greeting
    print(greeting.split(" ")[-1])