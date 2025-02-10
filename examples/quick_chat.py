import random
from typing import List, Tuple
import ell
import logging

ell.config.verbose = True
logging.basicConfig(level=logging.INFO)

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
def create_personality(name: str) -> str:
    """You are backstoryGPT. You come up with a backstory for a character. Format as follows.

Name: <name>
Backstory: <3 sentence backstory>"""

    logging.info(f"Creating personality for: {name}")
    return f"Name: {name}\nBackstory: "

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.lm(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], personality: str) -> str:
    logging.info(f"Generating chat response for: {personality}")
    return ell.system(f"""Here is your description.
{personality}.

Your goal is to come up with a response to a chat. Only respond in one sentence (should be like a text message in informality.) Never use Emojis.

Chat History:
{format_message_history(message_history)}""")

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    messages: List[Tuple[str, str]] = []
    personalities = [create_personality(random.choice(names_list)) for _ in range(2)]

    names = [personality.split("\n")[0].split(": ")[1] for personality in personalities]
    backstories = [personality.split("\n")[1].split(": ")[1] for personality in personalities]
    logging.info(f"Names: {names}")

    whos_turn = 0
    for _ in range(10):
        personality_talking = personalities[whos_turn]
        response = chat(messages, personality_talking)
        messages.append((names[whos_turn], response))
        whos_turn = (whos_turn + 1) % len(personalities)

    logging.info(f"Final chat messages: {messages}")