python\n    import ell\n    import openai\n                                    \n    ell.lm(model, client=openai.Client(api_key=my_key))\n    def {name}(...):\n        ...\n
python\n    ell.lm(model, client=openai.Client(api_key=my_key))(...)\n
python\nimport ell\nell.lm(model, client=my_client)\ndef {fn.__name__}(...):\n    ...\n
python\nell.lm(model, client=my_client)(...)\n