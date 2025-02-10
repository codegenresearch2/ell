import random
from typing import List, Tuple
import ell
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define names list
names_list = ["Alice", "Bob", "Charlie", "Diana", "Eve", "George", "Grace", "Hank", "Ivy", "Jack"]

# Cache for create_personality function
personality_cache = {}

@ell.lm(model="gpt-4o-2024-08-06", temperature=1.0)
def create_personality(name: str) -> str:
    """You are backstoryGPT. You come up with a backstory for a character. Format as follows.
    Name: <name>
    Backstory: <3 sentence backstory>"""
    if name in personality_cache:
        logging.info(f"Using cached personality for {name}")
        return personality_cache[name]
    else:
        logging.info(f"Creating new personality for {name}")
        personality = f"Name: {name}\nBackstory: {generate_backstory(name)}"
        personality_cache[name] = personality
        return personality

def generate_backstory(name: str) -> str:
    """Generate a backstory for a given name."""
    return f"{name} is a mysterious character with a hidden past."

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """Format the message history into a string."""
    return "\n".join([f"{name}: {message}" for name, message in message_history])

# Cache for chat function
chat_cache = {}

@ell.lm(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], personality: str) -> str:
    """Generate a response to the chat based on the message history and personality."""
    cache_key = (tuple(message_history), personality)
    if cache_key in chat_cache:
        logging.info("Using cached chat response")
        return chat_cache[cache_key]
    else:
        logging.info("Generating new chat response")
        response = generate_chat_response(message_history, personality)
        chat_cache[cache_key] = response
        return response

def generate_chat_response(message_history: List[Tuple[str, str]], personality: str) -> str:
    """Generate a chat response based on the message history and personality."""
    return "A quick response based on the chat history and personality."

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    messages = []
    personalities = [create_personality(random.choice(names_list)), create_personality(random.choice(names_list))]

    names = [personality.split("\n")[0].split(": ")[1] for personality in personalities]
    backstories = [personality.split("\n")[1].split(": ")[1] for personality in personalities]
    logging.info(f"Names: {names}")

    whos_turn = 0
    for _ in range(10):
        personality_talking = personalities[whos_turn]
        response = chat(messages, personality_talking)
        messages.append((names[whos_turn], response))
        whos_turn = (whos_turn + 1) % len(personalities)
    logging.info(f"Messages: {messages}")