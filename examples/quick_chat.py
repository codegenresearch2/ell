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

@ell.lm(model="gpt-4o-2024-08-06", temperature=1.0)
def create_personality() -> str:
    """You are backstoryGPT. You come up with a backstory for a character including name. Choose a completely random name from the list. Format as follows.

Name: <name>
Backstory: <3 sentence backstory>"""
    name = random.choice(names_list)
    return f"Name: {name}\nBackstory: A character with a unique background and personality."

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.lm(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> List[str]:
    system_prompt = ell.system(f"""Here is your description.
{personality}. 

Your goal is to come up with a response to a chat. Only respond in one sentence (should be like a text message in informality.) Never use Emojis.""")
    user_prompt = ell.user(format_message_history(message_history))
    return [system_prompt, user_prompt]

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
    
    whos_turn = 0 
    for _ in range(10):
        personality_talking = personalities[whos_turn]
        messages.append((names[whos_turn], chat(messages, personality=personality_talking)))
        whos_turn = (whos_turn + 1) % len(personalities)
    
    print(messages)