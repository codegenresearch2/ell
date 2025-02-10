import random
from typing import List, Tuple
import ell

# Set verbose mode
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
    Generate a backstory for a character with a name chosen randomly from the provided list.
    Format the output as follows:

    Name: <name>
    Backstory: <3-sentence backstory>
    """
    name = random.choice(names_list)
    return f"Create a backstory for a character named {name}. Format the output as follows:\nName: {name}\nBackstory: <3-sentence backstory>"

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """
    Format the message history into a string for use in the chat function.
    """
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> str:
    """
    Generate a response to a chat based on the character's backstory.

    Format:
    System: <Character Backstory>
    User: <Chat History>
    """
    name, backstory = personality.split('\n')
    name = name.split(': ')[1]
    backstory = backstory.split(': ')[1]

    system_prompt = f"You are {name}. Your backstory: {backstory}. Your goal is to come up with a response to a chat. Only respond in one sentence, using an informal tone. Never use Emojis."
    user_prompt = format_message_history(message_history)

    return [
        ell.system(system_prompt),
        ell.user(user_prompt),
    ]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store('./logdir', autocommit=True)

    personalities = [create_personality() for _ in range(2)]
    names = [personality.split('\n')[0].split(': ')[1] for personality in personalities]
    backstories = [personality.split('\n')[1].split(': ')[1] for personality in personalities]

    messages: List[Tuple[str, str]] = []
    whos_turn = 0
    for _ in range(10):
        personality_talking = f"Name: {names[whos_turn]}\nBackstory: {backstories[whos_turn]}"
        response = chat(messages, personality=personality_talking)
        messages.append((names[whos_turn], response[1]))
        whos_turn = (whos_turn + 1) % len(names)
    print(messages)