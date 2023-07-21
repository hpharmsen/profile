import os


class PromptReader:
    _instance = None
    # def __new__(cls, *args, **kwargs):
    #     """ To make it a singleton """
    #     if not cls._instance:
    #         cls._instance = super(PromptReader, cls).__new__(
    #             cls, *args, **kwargs)
    #     return cls._instance

    def __init__(self, variables: dict = None, path: str = None):
        if not path:
            path = os.path.join(os.path.dirname(__file__), 'prompts')
        self.variables = {} if variables is None else variables
        self.path = path
        self.data = {}
        self.read()

    def read(self):
        with open(self.path, 'r') as file:
            for item in file.read().split('\n\n\n'):
                key, text = item.split('\n', 1)
                self.data[key] = text.format(**self.variables)

    def __getitem__(self, key):
        return self.data[key]
