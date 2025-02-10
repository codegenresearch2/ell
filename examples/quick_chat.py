import random
from typing import List, Tuple
import ell

# Set verbose configuration
ell.config.verbose = True

# Define names list
names_list = ["Alice", "Bob", "Charlie", "Diana", "Eve", "George", "Grace", "Hank", "Ivy", "Jack"]

@ell.lm(model="gpt-4o-2024-08-06", temperature=1.0)
def create_personality() -> str:
    """
    You are backstoryGPT. Come up with a backstory for a character including name.
    Choose a completely random name from the list. Format as follows:

    System Prompt:
    You are backstoryGPT. Come up with a 3-sentence backstory for a character named {name}.

    User Prompt:
    Name: {name}
    Backstory: <3 sentence backstory>
    """
    name = random.choice(names_list)
    system_prompt = f"You are backstoryGPT. Come up with a 3-sentence backstory for a character named {name}."
    user_prompt = f"Name: {name}\nBackstory: <3 sentence backstory>"
    return ell.system(system_prompt) + ell.user(user_prompt)

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """Format the message history into a string."""
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.lm(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> str:
    """Generate a response to the chat based on the message history and personality."""
    system_message = f"Here is your description.\n{personality}\nYour goal is to come up with a response to a chat. Only respond in one sentence (should be like a text message in informality.) Never use Emojis."
    user_message = format_message_history(message_history)
    return ell.system(system_message) + ell.user(user_message)

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    messages: List[Tuple[str, str]] = []
    personalities = [create_personality(), create_personality()]

    names = []
    backstories = []
    for personality in personalities:
        parts = personality.split("\n")
        names.append(parts[1].split(": ")[1])
        backstories.append(parts[2].split(": ")[1])
    print(names)

    whos_turn = 0
    for _ in range(10):
        personality_talking = personalities[whos_turn]
        response = chat(messages, personality=personality_talking)
        messages.append((names[whos_turn], response.split("\n")[-1]))
        whos_turn = (whos_turn + 1) % len(personalities)
    print(messages)