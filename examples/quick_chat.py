import random
from typing import List, Tuple
import ell
ell.config.verbose = True

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
    """You are backstoryGPT. You come up with a backstory for a character including name. Choose a completely random name from the list. Format the output as follows:

    Name: <name>
    Backstory: <3 sentence backstory>
    """
    chosen_name = random.choice(names_list)
    backstory = f"This is a backstory for {chosen_name}."
    return f"Name: {chosen_name}\nBackstory: {backstory}"

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> str:
    return [
        ell.system(f"""Here is your description.
{personality}. 

Your goal is to come up with a response to a chat. Only respond in one sentence (should be like a text message in informality.) Never use Emojis."""),
        ell.user(format_message_history(message_history)),
    ]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store('./logdir', autocommit=True)
    
    for _ in range(100):  # Adjusted loop count to match the gold code
        messages: List[Tuple[str, str]] = []
        personalities = [create_personality() for _ in range(2)]

        names = [personality.split(": ")[1].strip() for personality in personalities if ":" in personality]
        backstories = [personality.split(": ")[2].strip() for personality in personalities if ":" in personality]

        whos_turn = 0
        for __ in range(10):  # Adjusted loop count to match the gold code
            personality_talking = personalities[whos_turn]
            messages.append((names[whos_turn], chat(messages, personality=personality_talking)))
            whos_turn = (whos_turn + 1) % len(personalities)

        # Print the names after they have been populated
        print(names)
        print(messages)