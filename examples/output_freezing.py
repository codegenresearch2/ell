import ell
from ell.stores.sql import SQLiteStore

BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

@ell.lm(model="gpt-4o", temperature=0.7, max_tokens=4)
def create_a_python_class(user_spec: str):
    return [
        ell.system(
            f"{BASE_PROMPT}\n\nCreate a Python class based on the user specification provided."
        ),
        ell.user(
            f"User specification: {user_spec}"
        )
    ]

@ell.lm(model="gpt-4o", temperature=0.7)
def write_unit_for_a_class(class_def: str):
    return [
        ell.system(
            f"{BASE_PROMPT}\n\nWrite a single unit test for the given class definition without using the `unittest` package."
        ),
        ell.user(
            f"Class definition: {class_def}"
        )
    ]

if __name__ == "__main__":
    ell.config.verbose = True
    store = SQLiteStore("sqlite_example")
    ell.set_store(store, autocommit=True)

    with store.freeze(create_a_python_class):
        _class_def = create_a_python_class("A class that represents a bank")
        _unit_tests = write_unit_for_a_class(_class_def)