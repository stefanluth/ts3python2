class TS3Error(Exception):
    def __init__(self, id: int, message: str):
        self.id = id
        self.msg = message

    def __str__(self):
        return f"Error {self.id}: {self.msg}"
