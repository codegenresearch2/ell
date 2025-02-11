import ell
import numpy as np
from typing import List

ell.init(store='./logdir', autocommit=True, verbose=True)

def get_random_length() -> int:
    return int(np.random.beta(2, 6) * 3000)

@ell.simple(model="gpt-4o-mini")
def generate_greeting(name: str) -> str:
    """Your goal is to be really meant to the other guy while saying hello"""
    capitalized_name = name.capitalize()
    char_limit = get_random_length()

    return f"Say hello to {capitalized_name} in {char_limit} characters or more!"

if __name__ == "__main__":
    while True:
        user_input = input("Enter a name (or 'exit' to quit): ")
        if user_input.lower() == 'exit':
            break

        greeting = generate_greeting(user_input)
        greeting_words = greeting.split(" ")
        last_word = greeting_words[-1]

        print(f"Generated greeting: {greeting}")
        print(f"Last word of the greeting: {last_word}")