import random
from typing import List, Tuple
import ell

# Enable verbose mode
ell.config.verbose = True

# List of names to choose from
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
    You are backstoryGPT. Your task is to create a backstory for a character, including their name.
    Choose a name randomly from the provided list and format the output as follows:

    Name: <name>
    Backstory: <3-sentence backstory>
    """
    # Validate that the names list is not empty
    if not names_list:
        raise ValueError("Names list is empty")

    # Choose a random name from the list and return the prompt for the AI model
    return f"Create a backstory for a character named {random.choice(names_list)}."

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """
    Format the message history into a string for the AI model.
    """
    # Format the message history into a string
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> List[str]:
    """
    Generate a chat response based on the message history and personality.
    """
    # Validate that the message history and personality are not empty
    if not message_history:
        raise ValueError("Message history is empty")
    if not personality:
        raise ValueError("Personality is empty")

    # Generate the chat response
    system_prompt = f"""You are a character with the following personality:
{personality}.

Your goal is to respond to a chat in one sentence, using informal language and avoiding emojis.
"""
    user_prompt = format_message_history(message_history)

    return [ell.system(system_prompt), ell.user(user_prompt)]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore

    # Set the store for the AI model
    ell.set_store('./logdir', autocommit=True)

    # Simulate multiple conversations
    for _ in range(100):
        # Initialize the message history and personalities
        messages: List[Tuple[str, str]] = []
        personalities = [create_personality(), create_personality()]

        # Extract the names and backstories from the personalities
        names = []
        backstories = []
        for personality in personalities:
            parts = list(filter(None, personality.split("\n")))
            names.append(parts[0].split(": ")[1])
            backstories.append(parts[1].split(": ")[1])
        print(names)

        # Initialize the turn counter
        whos_turn = 0

        # Simulate the chat
        for _ in range(10):
            personality_talking = personalities[whos_turn]
            messages.append(
                (names[whos_turn], chat(messages, personality=personality_talking)))
            whos_turn = (whos_turn + 1) % len(personalities)

        print(messages)