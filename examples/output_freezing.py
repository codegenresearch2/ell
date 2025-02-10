import ell
from ell.stores.sql import SQLiteStore

# Define a base prompt for consistency
BASE_PROMPT = "You are an adept Python programmer. Your goal is to generate Python code. Only answer in Python code. Avoid markdown formatting."

# Improve function naming and parameter naming
@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=300)
def create_python_class(specification: str):
    return [
        ell.system(f"{BASE_PROMPT}\nCreate a Python class based on the provided specification."),
        ell.user(f"Specification: {specification}")
    ]

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=100)
def generate_unit_test(class_definition: str):
    return [
        ell.system(f"{BASE_PROMPT}\nWrite a single unit test for the provided class definition. Avoid using the `unittest` package."),
        ell.user(f"Class definition: {class_definition}")
    ]

if __name__ == "__main__":
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    ell.config.verbose = True

    with store.freeze(create_python_class):
        bank_class = create_python_class("A class that represents a bank")
        bank_unit_test = generate_unit_test(bank_class)