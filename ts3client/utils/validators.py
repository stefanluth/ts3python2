from typing import Any

from ..constants import *


def _validate_kwargs(args: dict[str, Any]) -> None:
    """
    Validates the arguments passed to a query command.

    :param args: Arguments to validate.
    :type args: dict
    :raises ValueError: Raised if any argument value is not a string, integer or float.
    """
    if not all([isinstance(arg, (str, int, float)) for arg in args.values()]):
        raise ValueError("All argument values must be strings, integers or floats.")


def _validate_changeable_kwargs(args: dict[str, Any], changeables: list[str]) -> dict[str, Any]:
    """
    Validates the arguments passed to a query command that changes properties. This
    function validates that the arguments are valid changeable properties and returns
    them with their property names lowercased, which is the format the server expects.

    :param args: Arguments to validate.
    :type args: dict
    :param changeables: List of changeable properties.
    :type changeables: list[str]
    :return: The validated arguments with lowercased property names.
    :rtype: dict
    :raises ValueError: Raised if any argument is not a valid changeable property.
    """
    _validate_kwargs(args)

    validated: dict[str, Any] = {}
    for key, value in args.items():
        normalized_key = key.lower()
        if normalized_key not in changeables:
            raise ValueError(
                f"Invalid argument: {key}\n\
                \rValid arguments: {changeables}"
            )
        if normalized_key in validated:
            raise ValueError(f"Duplicate argument: {normalized_key}")
        validated[normalized_key] = value

    return validated


def _validate_server_instance_kwargs(args: dict[str, Any]) -> dict[str, Any]:
    """
    Validates the arguments passed to a server instance query command.

    :param args: Arguments to validate.
    :type args: dict
    :return: The validated arguments with lowercased property names.
    :rtype: dict
    :raises ValueError: Raised if any argument is not a valid changeable server instance property.
    """
    return _validate_changeable_kwargs(args, ChangeableServerInstanceProperties)


def _validate_channel_kwargs(args: dict[str, Any]) -> dict[str, Any]:
    """
    Validates the arguments passed to a channel query command.

    :param args: Arguments to validate.
    :type args: dict
    :return: The validated arguments with lowercased property names.
    :rtype: dict
    :raises ValueError: Raised if any argument is not a valid changeable channel property.
    """
    return _validate_changeable_kwargs(args, ChangeableChannelProperties)


def _validate_client_kwargs(args: dict[str, Any]) -> dict[str, Any]:
    """
    Validates the arguments passed to a client query command.

    :param args: Arguments to validate.
    :type args: dict
    :return: The validated arguments with lowercased property names.
    :rtype: dict
    :raises ValueError: Raised if any argument is not a valid changeable client property.
    """
    return _validate_changeable_kwargs(args, ChangeableClientProperties)


def _validate_virtual_server_kwargs(args: dict[str, Any]) -> dict[str, Any]:
    """
    Validates the arguments passed to a virtual server query command.

    :param args: Arguments to validate.
    :type args: dict
    :return: The validated arguments with lowercased property names.
    :rtype: dict
    :raises ValueError: Raised if any argument is not a valid changeable virtual server property.
    """
    return _validate_changeable_kwargs(args, ChangeableVirtualServerProperties)
