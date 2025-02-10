import ell
from ell.stores.sql import SQLiteStore

# Improve code readability and clarity
BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

# Enhance code maintainability with consistent formatting
def create_python_class(user_spec: str):
    return [
        ell.system(f"{BASE_PROMPT}\n\nYour goal is to make a python class for a user based on a user spec."),
        ell.user(f"Here is the user spec: {user_spec}")
    ]

def write_unit_test_for_class(class_def: str):
    return [
        ell.system(f"{BASE_PROMPT}\n\nYour goal is to write only a single unit test for a specific class definition. Don't use `unittest` package"),
        ell.user(f"Here is the class definition: {class_def}")
    ]

if __name__ == "__main__":
    # Simplify data access by using dot notation
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    ell.config.verbose = True

    with store.freeze(create_python_class):
        class_def = create_python_class("A class that represents a bank")
        unit_tests = write_unit_test_for_class(class_def)