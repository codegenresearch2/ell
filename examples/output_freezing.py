import ell\nfrom ell.stores.sql import SQLiteStore\nell.config.verbose = True\n\nBASE_PROMPT = '''You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs.'''\\\n\n@ell.lm(model=\"gpt-4o\", temperature=0.7, max_tokens=4)\\\\\\ndef create_a_python_class(user_spec : str):\\\\\n    return [\\\n        ell.system(\\\"${BASE_PROMPT}\n\nYour goal to make a python class for a user based a user spec.\\\")\\\\\n        ,\\\n        ell.user(\\\"Here is the user spec: ${user_spec}\\\")\\\\\n    ]\\\\\n\n@ell.lm(model=\"gpt-4o\", temperature=0.7)\\\\n\\\ndef write_unit_for_a_class(class_def : str):\\\\\n    return [\\\n        ell.system(\\\"${BASE_PROMPT}\n\nYour goal is to write only a single unit test for a specific class definition. Don't use `unittest` package.\\\")\\\\\n        ,\\\n        ell.user(\\\"Here is the class definition: ${class_def}\\\")\\\\\n    ]\\\\\n\n\nif __name__ == \"__main__\":\\\\\n    store = SQLiteStore(\"sqlite_example\")\\\\\n    ell.set_store(store, autocommit=True)\\\\\n\n    with store.freeze(create_a_python_class):\\\\\n        _class_def = create_a_python_class(\"A class that represents a bank\")\\\\\n        _unit_tests = write_unit_for_a_class(_class_def)\\\\\n