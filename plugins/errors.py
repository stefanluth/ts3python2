class ConfigurationError(Exception):
    def __init__(self, plugin: str, message: str):
        self.plugin = plugin
        self.message = message

    def __str__(self):
        return f"Plugin '{self.plugin}': {self.message}"


class ImplementationError(Exception):
    def __init__(self, plugin: str, message: str):
        self.plugin = plugin
        self.message = message

    def __str__(self):
        return f"Plugin '{self.plugin}': {self.message}"
