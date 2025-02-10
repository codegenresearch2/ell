import ell
from ell.stores.sql import SQLiteStore

# Improve function naming and add decorator parameters
@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=500)
def generate_class_definition(user_spec: str):
    return [
        ell.system(f"You are an adept python programmer. Your goal is to generate a python class definition based on a user specification. Only answer in python code."),
        ell.user(f"Here is the user specification: {user_spec}")
    ]

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=200)
def create_unit_test(class_def: str):
    return [
        ell.system(f"You are an adept python programmer. Your goal is to create a single unit test for a specific class definition. Avoid using the `unittest` package. Only answer in python code."),
        ell.user(f"Here is the class definition: {class_def}")
    ]

if __name__ == "__main__":
    # Follow the code structure of the gold code and improve variable naming
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    ell.config.verbose = True

    with store.freeze(generate_class_definition):
        class_definition = generate_class_definition("A class that represents a bank")
        unit_test = create_unit_test(class_definition)