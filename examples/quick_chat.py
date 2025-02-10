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
    """Generates a backstory for a character including name.
    
    The function chooses a random name from the list and generates a backstory for that character.
    The backstory includes the name and a 3-sentence backstory.
    
    Returns:
        str: A string containing the name and backstory.
    """
    chosen_name = random.choice(names_list)
    backstory = f"Name: {chosen_name}\nBackstory: {chosen_name} is a person with a fascinating past."
    return backstory

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """Formats the message history for display.
    
    Args:
        message_history (List[Tuple[str, str]]): A list of tuples containing name and message pairs.
    
    Returns:
        str: A string formatted with each message prefixed by the name.
    """
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str):
    """Generates a response based on the message history and personality.
    
    Args:
        message_history (List[Tuple[str, str]]): A list of tuples containing name and message pairs.
        personality (str): A string containing the personality description.
    
    Returns:
        List[ell.system or ell.user]: A list containing system and user messages formatted according to the gold code's style.
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
    
    for __ in range(100):  # Using double underscore for unused variable
        messages: List[Tuple[str, str]] = []
        personalities = [create_personality(), create_personality()]

        names: List[str] = []  # List to store names
        backstories: List[str] = []  # List to store backstories
        for personality in personalities:
            parts = list(filter(None, personality.split("\n")))
            names.append(parts[0].split(": ")[1])
            backstories.append(parts[1].split(": ")[1])

        print(names)  # Printing names for debugging purposes

        whos_turn = 0
        for _ in range(10):
            personality_talking = personalities[whos_turn]
            messages.append((names[whos_turn], chat(messages, personality=personality_talking)))
            whos_turn = (whos_turn + 1) % len(personalities)

    print(messages)