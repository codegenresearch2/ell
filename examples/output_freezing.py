import ell
from ell.stores.sql import SQLiteStore

ell.config.verbose = True

BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=4)
def create_a_python_class(user_spec: str) -> list:
    """
    Create a Python class based on the user specification.

    Args:
    user_spec (str): The user specification for the class.

    Returns:
    list: A list containing the system prompt and user prompt.
    """
    return [
        ell.system(f"{BASE_PROMPT}\n\nTask: Develop a Python class that meets the user's specifications."),
        ell.user(f"User's class specifications: {user_spec}")
    ]

@ell.lm(model="gpt-4o", temperature=0.7)
def write_unit_for_a_class(class_def: str) -> list:
    """
    Write a single unit test for the provided class definition.

    Args:
    class_def (str): The class definition for which to write a unit test.

    Returns:
    list: A list containing the system prompt and user prompt.
    """
    return [
        ell.system(f"{BASE_PROMPT}\n\nTask: Write a single unit test for the given class definition. Avoid using the `unittest` package."),
        ell.user(f"Class definition: {class_def}")
    ]

if __name__ == "__main__":
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    with store.freeze(create_a_python_class):
        _class_def = create_a_python_class("A class that represents a bank")
        _unit_tests = write_unit_for_a_class(_class_def)