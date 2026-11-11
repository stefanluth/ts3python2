import re

_QUERY_UNESCAPES = {
    "\\": "\\",
    "/": "/",
    "s": " ",
    "p": "|",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "f": "\f",
}


def string_to_query(string: str | int | float) -> str:
    return (
        str(string)
        .replace("\\", r"\\")
        .replace("/", r"\/")
        .replace(" ", r"\s")
        .replace("|", r"\p")
        .replace("\n", r"\n")
        .replace("\r", r"\r")
        .replace("\t", r"\t")
    )


def query_to_string(string: str | int | float) -> str:
    return re.sub(r"\\(.)", lambda match: _QUERY_UNESCAPES.get(match.group(1), match.group(0)), str(string))
