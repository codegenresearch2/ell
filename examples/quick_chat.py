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
    You are backstoryGPT. You come up with a backstory for a character including name.
    Choose a completely random name from the provided list. Format as follows:

    Name: <name>
    Backstory: <3 sentence backstory>
    """
    # Validate that names_list is not empty
    if not names_list:
        raise ValueError("The names_list is empty. Please provide a list of names.")

    # Choose a random name from the list
    name = random.choice(names_list)

    # Generate a backstory for the character
    backstory = f"{name} is a mysterious and enigmatic individual with a past shrouded in mystery. They have a unique talent for solving complex problems and a knack for getting into trouble. Despite their rough exterior, {name} has a soft spot for animals and often spends time volunteering at a local shelter."

    # Return the formatted backstory
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
    system_prompt = f"You are {personality}. Your goal is to respond to a chat in one sentence, using an informal tone. Keep your response concise and engaging."

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

    # Simulate a chat between the characters
    for _ in range(100):
        messages: List[Tuple[str, str]] = []
        for i in range(len(personalities)):
            personality_talking = personalities[i]
            messages.append(
                (names[i], chat(messages, personality=personality_talking)))
        print(messages)