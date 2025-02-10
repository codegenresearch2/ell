import ell
from ell.stores.sql import SQLiteStore

# Define a base prompt for consistency
BASE_PROMPT = "You are an adept Python programmer. Your goal is to generate Python code. Only answer in Python code. Avoid markdown formatting."

# Improve function naming and parameter naming
@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=4)
def create_a_python_class(specification: str):
    return [
        ell.system(f"{BASE_PROMPT}\n\nCreate a Python class based on the provided specification."),
        ell.user(f"Specification: {specification}")
    ]

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=100)
def write_unit_for_a_class(class_definition: str):
    return [
        ell.system(f"{BASE_PROMPT}\n\nWrite a single unit test for the provided class definition. Avoid using the `unittest` package."),
        ell.user(f"Class definition: {class_definition}")
    ]

if __name__ == "__main__":
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    ell.config.verbose = True

    with store.freeze(create_a_python_class):
        _class_def = create_a_python_class("A class that represents a bank")
        _unit_tests = write_unit_for_a_class(_class_def)