class TS3Exception(Exception):
    def __init__(self, id: int, msg: str):
        self.id = id
        self.msg = msg

    def __str__(self):
        return f"Error {self.id}: {self.msg}"
