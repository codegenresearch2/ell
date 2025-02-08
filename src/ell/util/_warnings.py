import logging\\nfrom colorama import Fore, Style\\nfrom ell.configurator import config\\n\\ndef _no_api_key_warning(model, name, client_to_use, long=False, error=False):\\n    color = Fore.RED if error else Fore.LIGHTYELLOW_EX\\n    prefix = "ERROR" if error else "WARNING"\\n    return f"{color}{prefix}: No API key found for model `{model}` used by LMP `{name}` using client `{client_to_use}`" + (f"\\n\\nTo fix this:\\n* Or, set your API key in the environment variable `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.\\n* Or, specify a client explicitly in the decorator:\\n    \\\"\\n    import ell\\n    import openai\\n                                    \\\"\\n    ell.lm(model, client=openai.Client(api_key=my_key))\\n    def {name}(...):\\n        ...\\n    \\\"\\n* Or explicitly specify the client when calling the LMP:\\n\\n    \\\"\\n    ell.lm(model, client=openai.Client(api_key=my_key))(...)\\"\\n" if long else " at time of definition. Can be okay if custom client specified later! <TODO: add link to docs> ") + f"{Style.RESET_ALL}""