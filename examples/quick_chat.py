import random
from typing import List, Tuple
import ell
ell.config.verbose = True

names_list = ["Alice", "Bob", "Charlie", "Diana", "Eve", "George", "Grace", "Hank", "Ivy", "Jack"]

@ell.lm(model="gpt-4o-2024-08-06", temperature=1.0)
def create_personality() -> str:
    """
    Generate a backstory for a character with a random name from the names_list.

    System Prompt:
    You are backstoryGPT. Your task is to create a 3-sentence backstory for a character with a random name from the names_list.

    Returns:
        str: A formatted string containing the character's name and backstory.
              The format should be: "Name: <name>\nBackstory: <3-sentence backstory>"
    """
    name = random.choice(names_list)
    backstory = f"Create a 3-sentence backstory for a character named {name}."
    return f"Name: {name}\nBackstory: {backstory}"

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """
    Format the message history into a single string for the chat function.

    Args:
        message_history (List[Tuple[str, str]]): A list of tuples containing the sender's name and message.

    Returns:
        str: A formatted string containing the message history.
    """
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.lm(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> str:
    """
    Generate a response to a chat based on the message history and the character's personality.

    Args:
        message_history (List[Tuple[str, str]]): A list of tuples containing the sender's name and message.
        personality (str): The character's personality and backstory.

    Returns:
        str: A response to the chat in one sentence, using informal text message style.
    """
    system_prompt = f"You are {personality}. Your goal is to respond to a chat in one sentence, using informal text message style. Never use Emojis. Here is the chat history:\n{format_message_history(message_history)}"
    user_prompt = "Based on the chat history and your personality, respond to the last message in one sentence."
    return ell.system(system_prompt) + ell.user(user_prompt)

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    messages: List[Tuple[str, str]] = []
    personalities = [create_personality() for _ in range(2)]

    names = [personality.split("\n")[0].split(": ")[1] for personality in personalities]
    backstories = [personality.split("\n")[1].split(": ")[1] for personality in personalities]
    print("Names:", names)

    whos_turn = 0
    for _ in range(10):
        personality_talking = personalities[whos_turn]
        response = chat(messages, personality=personality_talking)
        messages.append((names[whos_turn], response))
        whos_turn = (whos_turn + 1) % len(personalities)
    print("Messages:", messages)