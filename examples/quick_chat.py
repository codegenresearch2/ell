import random
from typing import List, Tuple
import ell
ell.config.verbose = True

names_list = [
    "Alice",
    "Bob",
    "Charlie",
    "Diana",
    "Eve",
    "George",
    "Grace",
    "Hank",
    "Ivy",
    "Jack",
]

@ell.simple(model="gpt-4o-2024-08-06", temperature=1.0)
def create_personality() -> str:
    """
    Generates a backstory for a character including their name.
    Chooses a random name from the provided list and constructs a backstory.
    Returns:
        str: A formatted string with the character's name and a backstory.
    """
    random_name = random.choice(names_list)
    backstory = f"Name: {random_name}\nBackstory: {random_name} has a fascinating past that shapes their current personality."
    return backstory

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """
    Formats a list of message tuples into a single string with each message separated by a newline.
    Args:
        message_history (List[Tuple[str, str]]): A list of tuples containing names and messages.
    Returns:
        str: A formatted string with each name and message pair on a new line.
    """
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> List[str]:
    """
    Generates a response based on the provided personality and message history.
    Args:
        message_history (List[Tuple[str, str]]): A list of tuples containing names and messages.
        personality (str): A string containing the personality description.
    Returns:
        List[str]: A list of strings containing the system and user prompts.
    """
    return [
        ell.system(f"""Here is your description.
{personality}. 

Your goal is to come up with a response to a chat. Only respond in one sentence (should be like a text message in informality.) Never use Emojis."""),
        ell.user(format_message_history(message_history)),
    ]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store('./logdir', autocommit=True)
        
    for _ in range(100):  # Loop runs 100 times to generate messages
        messages: List[Tuple[str, str]] = []  # Initialize messages for each iteration
        personalities = [create_personality() for _ in range(2)]  # Generate two personalities

        names = []
        backstories = []    
        for personality in personalities:
            parts = list(filter(None, personality.split("\n")))
            names.append(parts[0].split(": ")[1])
            backstories.append(parts[1].split(": ")[1])
        print(names)

        whos_turn = 0 
        for _ in range(10):  # Loop runs 10 times to generate messages
            personality_talking = personalities[whos_turn]
            messages.append((names[whos_turn], chat(messages, personality=personality_talking)))
            whos_turn = (whos_turn + 1) % len(personalities)
        print(messages)