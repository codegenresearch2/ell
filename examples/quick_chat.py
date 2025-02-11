import random
from typing import List, Tuple
import ell

# Enable verbose mode
ell.config.verbose = True

# List of names to choose from
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
    System prompt:
    You are backstoryGPT. You come up with a backstory for a character including name.
    Choose a completely random name from the provided list. Format as follows:

    Name: <name>
    Backstory: <3 sentence backstory>

    User prompt:
    Come up with a backstory about <name>
    """
    # Validate that the names list is not empty
    if not names_list:
        raise ValueError("Names list is empty")

    # Choose a random name from the list
    name = random.choice(names_list)

    # Return the prompt for the AI model
    return f"Come up with a backstory about {name}"

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    """
    Format the message history into a string for the AI model.
    """
    # Format the message history into a string
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history: List[Tuple[str, str]], *, personality: str) -> str:
    """
    Generate a chat response based on the message history and personality.
    """
    # Validate that the message history and personality are not empty
    if not message_history:
        raise ValueError("Message history is empty")
    if not personality:
        raise ValueError("Personality is empty")

    # Generate the chat response
    return ell.system(f"""Here is your description.
{personality}.

Your goal is to come up with a response to a chat. Only respond in one sentence (should be like a text message in informality.) Never use Emojis.""") + ell.user(format_message_history(message_history))

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore

    # Set the store for the AI model
    ell.set_store('./logdir', autocommit=True)

    # Initialize the message history and personalities
    messages = []
    personalities = [create_personality(), create_personality()]

    # Extract the names and backstories from the personalities
    names = []
    backstories = []
    for personality in personalities:
        parts = list(filter(None, personality.split("\n")))
        names.append(parts[0].split(": ")[1])
        backstories.append(parts[1].split(": ")[1])
    print(names)

    # Initialize the turn counter
    whos_turn = 0

    # Simulate the chat for 100 turns
    for _ in range(100):
        personality_talking = personalities[whos_turn]
        messages.append(
            (names[whos_turn], chat(messages, personality=personality_talking)))
        whos_turn = (whos_turn + 1) % len(personalities)

    print(messages)


The oracle has provided feedback that there was a "Bad Request" error. This could be due to a variety of reasons, such as invalid input data, missing headers, or incorrect API usage. However, without more specific details about the error, it's difficult to determine the exact cause.

The code provided is a simulation of a chat between two characters, with each character having a randomly generated backstory. The code uses the `ell` library to interact with an AI model to generate the backstories and chat responses. The code appears to be well-structured and follows the provided rules.

To address the "Bad Request" error, I would need more specific details about the error message and the context in which it occurred. Without this information, it's difficult to suggest a specific solution. However, some general steps that could be taken to troubleshoot the error include:

* Checking the input data to ensure that it is in the expected format and within the acceptable range of values.
* Checking the API documentation to ensure that the correct headers are being sent with the request.
* Checking the API usage to ensure that it is being used correctly, including any necessary authentication or authorization steps.
* Checking the error message for any additional details that could provide more clues about the cause of the error.

Without more information, it's not possible to provide a more specific solution.