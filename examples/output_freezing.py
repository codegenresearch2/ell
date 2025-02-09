import ell
from ell.stores.sql import SQLiteStore

BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=4)
def create_a_python_class(user_spec : str):
    """
    Generates a Python class based on the user's specific requirements.
    Returns a list containing the system message and the user specification.
    """
    return [
        ell.system(
            f"{BASE_PROMPT}\n\nCreate a Python class according to the user's specific requirements provided in the specification."
        ),
        ell.user(
            f"User's specific requirements: {user_spec}"
        )
    ]

@ell.lm(model="gpt-4o", temperature=0.7)
def write_unit_for_a_class(class_def : str):
    """
    Writes a single unit test for the specified class definition.
    Do not use the `unittest` package.
    """
    return [
        ell.system(
            f"{BASE_PROMPT}\n\nWrite a unit test for the given class definition provided."
        ),
        ell.user(
            f"Class definition to be tested: {class_def}"
        )
    ]

if __name__ == "__main__":
    ell.config.verbose = True
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    with store.freeze(create_a_python_class):
        _class_def = create_a_python_class("A class that represents a bank")
        _unit_tests = write_unit_for_a_class(_class_def)