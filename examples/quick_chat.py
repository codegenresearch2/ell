import random
from typing import List, Tuple
import ell

# Set verbose mode for ell
ell.config.verbose = True

# List of names for character generation
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
    You are backstoryGPT. Choose a completely random name from the provided list and generate a backstory.
    Format the output as follows:

    Name: <name>
    Backstory: <3 sentence backstory>
    """
    # Validate that names_list is not empty
    if not names_list:
        raise ValueError("The names_list is empty. Please provide a list of names.")

    # Choose a random name from the list
    name = random.choice(names_list)

    # Generate a backstory for the character
    backstory = f"{name} is a character with a unique background. They have a passion for adventure and a love for the outdoors. They are known for their quick wit and their ability to solve problems."

    # Return the formatted name and backstory
    return f"Name: {name}\nBackstory: {backstory}"

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """
    Format the message history into a string for the chat function.

    Args:
    message_history (List[Tuple[str, str]]): A list of tuples containing the name and message.

    Returns:
    str: A formatted string of the message history.
    """
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> List[str]:
    """
    Generate a chat response based on the message history and personality.

    Args:
    message_history (List[Tuple[str, str]]): A list of tuples containing the name and message.
    personality (str): The personality of the character.

    Returns:
    List[str]: A list containing the system and user prompts.
    """
    # Format the system prompt
    system_prompt = f"""
    You are {personality}. Your goal is to come up with a response to a chat. Only respond in one sentence, in an informal manner, similar to a text message. Never use Emojis.
    """

    # Format the user prompt
    user_prompt = format_message_history(message_history)

    # Return the chat response
    return [ell.system(system_prompt), ell.user(user_prompt)]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store('./logdir', autocommit=True)

    # Initialize personalities
    personalities = [create_personality(), create_personality()]

    # Extract names and backstories from personalities
    names = []
    backstories = []
    for personality in personalities:
        parts = list(filter(None, personality.split("\n")))
        names.append(parts[0].split(": ")[1])
        backstories.append(parts[1].split(": ")[1])
    print(names)

    # Simulate a chat between the characters for 100 turns
    for _ in range(100):
        # Initialize messages for each turn
        messages = []
        for i in range(len(personalities)):
            personality_talking = personalities[i]
            name_talking = names[i]
            response = chat(messages, personality=personality_talking)
            messages.append((name_talking, response))

    print(messages)