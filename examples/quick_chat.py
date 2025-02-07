import random
from typing import List, Tuple
import ell
ell.config.verbose = True

names_list = [
    'Alice',
    'Bob',
    'Charlie',
    'Diana',
    'Eve',
    'George',
    'Grace',
    'Hank',
    'Ivy',
    'Jack',
]

@ell.lm(model='gpt-4o-2024-08-06', temperature=1.0)
def create_personality() -> str:
    """You are backstoryGPT. You come up with a backstory for a character including name. Choose a completely random name from the list. Format as follows.\n\nName: <name>\nBackstory: <3 sentence backstory>"""
    name = random.choice(names_list)
    return f'Name: {name}\nBackstory: A brief backstory about {name}.'