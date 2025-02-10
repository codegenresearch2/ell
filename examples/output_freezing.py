import ell
from ell.stores.sql import SQLiteStore

# Improve code readability and clarity with descriptive function names
# Follow naming convention used in the gold code
BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

# Enhance code maintainability with consistent formatting and variable naming
# Use appropriate decorator for the function
@ell.lm(model="gpt-4o", temperature=0.7)
def generate_python_class(user_spec: str):
    return [
        ell.system(f"{BASE_PROMPT}\n\nYour goal is to generate a python class based on a user specification."),
        ell.user(f"Here is the user specification: {user_spec}")
    ]

# Use appropriate decorator for the function
@ell.lm(model="gpt-4o", temperature=0.7)
def create_unit_test_for_class(class_def: str):
    return [
        ell.system(f"{BASE_PROMPT}\n\nYour goal is to create a single unit test for a specific class definition. Avoid using the `unittest` package."),
        ell.user(f"Here is the class definition: {class_def}")
    ]

if __name__ == "__main__":
    # Simplify data access by using dot notation
    # Follow the code structure of the gold code
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    ell.config.verbose = True

    with store.freeze(generate_python_class):
        class_definition = generate_python_class("A class that represents a bank")
        unit_test = create_unit_test_for_class(class_definition)