import ell
from ell.stores.sql import SQLiteStore

ell.config.verbose = True

BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=4)
def create_a_python_class(user_spec):
    """Develop a Python class that meets the user's specifications."""
    return [
        ell.system(f"{BASE_PROMPT}\n\nTask: Create a Python class based on the provided user specification."),
        ell.user(f"User's class specifications: {user_spec}")
    ]

@ell.lm(model="gpt-4o", temperature=0.7)
def write_unit_for_a_class(class_def):
    """Write a single unit test for the given class definition."""
    return [
        ell.system(f"{BASE_PROMPT}\n\nTask: Write a unit test for the provided class definition. Avoid using the `unittest` package."),
        ell.user(f"Class definition: {class_def}")
    ]

if __name__ == "__main__":
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    with store.freeze(create_a_python_class):
        _class_def = create_a_python_class("A class that represents a bank")
        _unit_tests = write_unit_for_a_class(_class_def)