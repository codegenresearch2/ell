import ell
from ell.stores.sql import SQLiteStore
from functools import lru_cache
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define base prompt
BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

# Define the store
store = SQLiteStore("sqlite_example")
ell.set_store(store, autocommit=True)

@lru_cache(maxsize=128)
@ell.lm(model="gpt-4o", temperature=0.7)
def create_a_python_class(user_spec: str):
    """
    This function creates a python class based on a user specification.

    Args:
    user_spec (str): The user's specification for the class.

    Returns:
    str: The definition of the created class.
    """
    try:
        return [
            ell.system(
                f"{BASE_PROMPT}\n\nYour goal is to make a python class for a user based on a user spec."
            ),
            ell.user(
                f"Here is the user spec: {user_spec}"
            )
        ]
    except Exception as e:
        logging.error(f"Error creating class: {e}")
        return None

@lru_cache(maxsize=128)
@ell.lm(model="gpt-4o", temperature=0.7)
def write_unit_for_a_class(class_def: str):
    """
    This function writes a single unit test for a specific class definition.

    Args:
    class_def (str): The definition of the class.

    Returns:
    str: The definition of the unit test.
    """
    try:
        return [
            ell.system(
                f"{BASE_PROMPT}\n\nYour goal is to write only a single unit test for a specific class definition. Don't use `unittest` package"
            ),
            ell.user(
                f"Here is the class definition: {class_def}"
            )
        ]
    except Exception as e:
        logging.error(f"Error writing unit test: {e}")
        return None

if __name__ == "__main__":
    ell.config.verbose = True

    # Create a python class
    class_def = create_a_python_class("A class that represents a bank")
    if class_def is not None:
        # Write a unit test for the class
        unit_tests = write_unit_for_a_class(class_def)
        if unit_tests is not None:
            logging.info("Class and unit test created successfully.")
        else:
            logging.warning("Failed to create unit test.")
    else:
        logging.warning("Failed to create class.")


In this rewritten code, I have added clearer function definitions and comments to improve readability. I have also added caching mechanisms using `functools.lru_cache` to improve performance. Additionally, I have enhanced error handling and logging capabilities using the `logging` module to provide more detailed information about any errors that occur.