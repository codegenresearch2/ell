import ell
from ell.stores.sql import SQLiteStore

# Define a base prompt for consistency
BASE_PROMPT = "You are an adept python programmer. Only answer in python code. Avoid markdown formatting."

# Improve function naming and parameter naming
@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=500)
def create_a_python_class(user_spec: str):
    return [
        ell.system(f"{BASE_PROMPT}\nYour goal is to create a python class based on a user specification."),
        ell.user(f"Here is the user specification: {user_spec}")
    ]

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=200)
def write_unit_for_a_class(class_def: str):
    return [
        ell.system(f"{BASE_PROMPT}\nYour goal is to write a single unit test for a specific class definition. Avoid using the `unittest` package."),
        ell.user(f"Here is the class definition: {class_def}")
    ]

if __name__ == "__main__":
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    ell.config.verbose = True

    with store.freeze(create_a_python_class):
        _class_def = create_a_python_class("A class that represents a bank")
        _unit_tests = write_unit_for_a_class(_class_def)