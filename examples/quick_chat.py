import random
from typing import List, Tuple
import ell

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

@ell.lm(model="gpt-4o-2024-08-06", temperature=1.0, max_tokens=50)
def create_personality() -> str:
    """
    Generate a backstory for a character with a random name from the provided list.
    The output should be formatted as follows:

    Name: <name>
    Backstory: <3 sentence backstory>
    """
    name = random.choice(names_list)
    return f"Create a backstory for a character named {name}. Format the output as specified."

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """Format the message history into a string for the chat function."""
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.lm(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> List[str]:
    """
    Generate a chat response based on the message history and the character's personality.
    Returns a list containing the system and user prompts.
    """
    formatted_history = format_message_history(message_history)
    return [
        ell.system(f"""
        Here is your description:
        {personality}

        Your goal is to come up with a response to a chat. Only respond in one sentence, using informal language similar to a text message. Never use Emojis.

        Chat History:
        {formatted_history}
        """),
        ell.user(formatted_history)  # Include the chat history in the user prompt
    ]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    messages: List[Tuple[str, str]] = []
    personalities = [create_personality() for _ in range(2)]

    names = []
    backstories = []
    for personality in personalities:
        parts = personality.split("\n")
        names.append(parts[0].split(": ")[1])
        backstories.append(parts[1].split(": ")[1])
    print(f"Character names: {names}")

    whos_turn = 0
    for _ in range(10):
        personality_talking = personalities[whos_turn]
        response = chat(messages, personality=personality_talking)
        messages.append((names[whos_turn], response[0]))  # Append the system response to the messages list
        whos_turn = (whos_turn + 1) % len(personalities)

    print(f"Final chat messages: {messages}")