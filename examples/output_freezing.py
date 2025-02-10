import ell
from ell.stores.sql import SQLiteStore

# Define a base prompt for consistency
BASE_PROMPT = "You are an adept Python programmer. Your goal is to generate Python code. Only answer in Python code. Avoid markdown formatting."

# Improve function naming and parameter naming
@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=500)
def generate_python_class(user_spec: str):
    return [
        ell.system(f"{BASE_PROMPT}\nCreate a Python class based on the provided user specification."),
        ell.user(f"User specification: {user_spec}")
    ]

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=100)
def create_unit_test(class_def: str):
    return [
        ell.system(f"{BASE_PROMPT}\nWrite a single unit test for the provided class definition. Avoid using the `unittest` package."),
        ell.user(f"Class definition: {class_def}")
    ]

if __name__ == "__main__":
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    ell.config.verbose = True

    with store.freeze(generate_python_class):
        class_definition = generate_python_class("A class that represents a bank")
        unit_test = create_unit_test(class_definition)