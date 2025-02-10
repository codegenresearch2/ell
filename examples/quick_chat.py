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
    """You are backstoryGPT. You come up with a backstory for a character including name. Choose a completely random name from the list. Format as follows.

    Name: <name>
    Backstory: <3 sentence backstory>
    """
    return "Create a backstory about " + random.choice(names_list)

def format_message_history(messages: List[Tuple[str, str]]) -> str:
    return "\n".join([f"{name}: {message}" for name, message in messages])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(messages: List[Tuple[str, str]], *, personality: str) -> List[str]:
    """Generate a response to a chat based on the character's backstory.

    Format:
    System: <Character Backstory>
    User: <Chat History>
    """
    return [
        ell.system(f"""Here is your description.
{personality}.

Your goal is to come up with a response to a chat. Only respond in one sentence, using an informal tone. Never use Emojis."""),
        ell.user(format_message_history(messages)),
    ]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store('./logdir', autocommit=True)

    messages: List[Tuple[str, str]] = []
    personalities = [create_personality() for _ in range(100)]

    names = []
    backstories = []
    for personality in personalities:
        parts = list(filter(None, personality.split("\n")))
        names.append(parts[0].split(": ")[1])
        backstories.append(parts[1].split(": ")[1])
    print(names)

    whos_turn = 0
    for _ in range(100):
        personality_talking = personalities[whos_turn]
        response = chat(messages, personality=personality_talking)
        messages.append((names[whos_turn], response[1]))
        whos_turn = (whos_turn + 1) % len(personalities)
    print(messages)