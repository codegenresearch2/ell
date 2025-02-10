import random
from typing import List, Tuple
import ell

# Set verbose mode
ell.config.verbose = True

# List of names for character generation
CHARACTER_NAMES = [
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
def generate_character_backstory() -> str:
    """Generate a backstory for a character including a random name from the list.

    Format:
    Name: <name>
    Backstory: <3 sentence backstory>
    """
    return "Create a backstory about " + random.choice(CHARACTER_NAMES)

def format_conversation_history(conversation_history: List[Tuple[str, str]]) -> str:
    return "\n".join([f"{name}: {message}" for name, message in conversation_history])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def generate_response(conversation_history: List[Tuple[str, str]], *, character_backstory: str) -> str:
    """Generate a response to a chat based on the character's backstory.

    Format:
    <Character Name>: <Response>
    """
    return [
        ell.system(f"""Here is your description.
{character_backstory}.

Your goal is to come up with a response to a chat. Only respond in one sentence, using an informal tone. Never use Emojis."""),
        ell.user(format_conversation_history(conversation_history)),
    ]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store('./logdir', autocommit=True)

    conversation_history: List[Tuple[str, str]] = []
    character_backstories = [generate_character_backstory(), generate_character_backstory()]

    character_names = []
    character_backstories_text = []
    for backstory in character_backstories:
        parts = list(filter(None, backstory.split("\n")))
        character_names.append(parts[0].split(": ")[1])
        character_backstories_text.append(parts[1].split(": ")[1])
    print(character_names)

    current_turn = 0
    for _ in range(10):
        current_character_backstory = character_backstories[current_turn]
        response = generate_response(conversation_history, character_backstory=current_character_backstory)
        conversation_history.append((character_names[current_turn], response))
        current_turn = (current_turn + 1) % len(character_backstories)
    print(conversation_history)