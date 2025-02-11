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
    System prompt:
    You are backstoryGPT. You come up with a backstory for a character including name.
    Choose a completely random name from the provided list.

    User prompt:
    Come up with a backstory about <name>. Format as follows:
    Name: <name>
    Backstory: <3 sentence backstory>
    """
    # Validate that the names list is not empty
    if not names_list:
        raise ValueError("Names list is empty")

    # Choose a random name from the list
    name = random.choice(names_list)

    # Return the prompt for the AI model
    return "Come up with a backstory about " + name

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
    return [
        ell.system(f"""Here is your description.
{personality}.

Your goal is to come up with a response to a chat. Only respond in one sentence (should be like a text message in informality.) Never use Emojis."""),
        ell.user(format_message_history(message_history)),
    ]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore

    # Set the store for the AI model
    ell.set_store('./logdir', autocommit=True)

    # Initialize the message history and personalities
    messages = []
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

    # Simulate the chat for 10 turns
    for _ in range(10):
        personality_talking = personalities[whos_turn]
        messages.append(
            (names[whos_turn], chat(messages, personality=personality_talking)))
        whos_turn = (whos_turn + 1) % len(personalities)

    print(messages)