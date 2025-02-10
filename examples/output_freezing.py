import ell
from ell.stores.sql import SQLiteStore

ell.config.verbose = True

BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

def create_class_prompt(user_spec: str):
    """
    Generate a system prompt for creating a Python class based on the user specification.
    """
    return [
        ell.system(f"{BASE_PROMPT}\n\nTask: Create a Python class based on the user specification."),
        ell.user(f"User specification: {user_spec}")
    ]

def write_unit_test_prompt(class_def: str):
    """
    Generate a system prompt for writing a unit test for the provided class definition.
    """
    return [
        ell.system(f"{BASE_PROMPT}\n\nTask: Write a single unit test for the provided class definition. Avoid using the `unittest` package."),
        ell.user(f"Class definition: {class_def}")
    ]

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=4)
def create_a_python_class(user_spec: str):
    """
    Create a Python class based on the user specification.
    """
    return create_class_prompt(user_spec)

@ell.lm(model="gpt-4o", temperature=0.7)
def write_unit_for_a_class(class_def: str):
    """
    Write a single unit test for the provided class definition.
    """
    return write_unit_test_prompt(class_def)

if __name__ == "__main__":
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    with store.freeze(create_a_python_class):
        _class_def = create_a_python_class("A class that represents a bank")
        _unit_tests = write_unit_for_a_class(_class_def)