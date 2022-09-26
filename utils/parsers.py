from utils.formatters import query_to_string, string_to_query


def query_list_to_dict(keys_values: list[str]) -> dict:
    response_dict = dict()

    for key_value_pair in keys_values:
        key = key_value_pair.split("=")[0]
        value = key_value_pair[len(key) + 1 :]

        try:
            response_dict[key] = int(value)
        except ValueError:
            response_dict[key] = query_to_string(value)

    return response_dict


def dict_to_query_parameters(parameters: dict) -> list[str]:
    return [f"{key}={string_to_query(value)}" for key, value in parameters.items()]
