import random
from typing import List, Tuple
import ell
ell.config.verbose = True

names_list = ["Alice", "Bob", "Charlie", "Diana", "Eve", "George", "Grace", "Hank", "Ivy", "Jack"]

@ell.lm(model="gpt-4o-2024-08-06", temperature=1.0)
def create_personality() -> str:
    name = random.choice(names_list)
    backstory = f"You are backstoryGPT. Come up with a 3-sentence backstory for a character named {name}."
    return f"Name: {name}\nBackstory: {backstory}"

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.lm(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], personality: str) -> str:
    system_prompt = f"Here is your description:\n{personality}\nYour goal is to come up with a response to a chat. Only respond in one sentence, using informal text message style. Never use Emojis."
    user_prompt = format_message_history(message_history)
    return system_prompt + "\n" + user_prompt

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    messages = []
    personalities = [create_personality(), create_personality()]

    names = [personality.split("\n")[0].split(": ")[1] for personality in personalities]
    backstories = [personality.split("\n")[1].split(": ")[1] for personality in personalities]
    print("Names:", names)

    whos_turn = 0
    for _ in range(10):
        personality_talking = personalities[whos_turn]
        response = chat(messages, personality_talking)
        messages.append((names[whos_turn], response))
        whos_turn = (whos_turn + 1) % len(personalities)
    print("Messages:", messages)