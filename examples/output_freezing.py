import ell
from ell.stores.sql import SQLiteStore

# Set verbose mode
ell.config.verbose = True

# Define base prompt
BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=500)
def create_a_python_class(user_spec: str):
    """
    This function creates a python class based on a user specification.

    Args:
    user_spec (str): The user's specification for the class.

    Returns:
    list: A list containing the system message and user message for the language model.
    """
    return [
        ell.system(
            f"{BASE_PROMPT}\n\nYour goal is to make a python class for a user based a user spec."
        ),
        ell.user(
            f"Here is the user spec: {user_spec}"
        )
    ]

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=500)
def write_unit_for_a_class(class_def: str):
    """
    This function writes a single unit test for a specific class definition.

    Args:
    class_def (str): The definition of the class.

    Returns:
    list: A list containing the system message and user message for the language model.
    """
    return [
        ell.system(
            f"{BASE_PROMPT}\n\nYour goal is to write only a single unit test for a specific class definition. Don't use `unittest` package"
        ),
        ell.user(
            f"Here is the class definition: {class_def}"
        )
    ]

if __name__ == "__main__":
    # Define the store
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    # Create a python class
    with store.freeze(create_a_python_class):
        _class_def = create_a_python_class("A class that represents a bank")
        # Write a unit test for the class
        _unit_tests = write_unit_for_a_class(_class_def)