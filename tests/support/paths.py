import hashlib
from pathlib import Path


def hashed_path(directory, uid):
    digest = hashlib.sha256(uid.encode("utf-8")).hexdigest()
    return Path(directory) / f"{digest}.json"
