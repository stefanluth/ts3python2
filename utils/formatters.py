def string_to_query(string: str | int | float) -> str:
    return (
        str(string)
        .replace("\n", r"\n")
        .replace(" ", r"\s")
        .replace("|", r"\p")
        .replace("\t", r"\t")
        .strip()
    )


def query_to_string(string: str | int | float):
    return (
        str(string)
        .replace(r"\n", "\n")
        .replace(r"\s", " ")
        .replace(r"\p", "|")
        .replace(r"\t", "\t")
        .strip()
    )
