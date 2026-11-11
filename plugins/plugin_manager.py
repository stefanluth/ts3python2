import inspect
import types
import typing
from threading import Event, Thread
from typing import Any

from ts3client import TS3Client
from ts3client.utils.logger import create_logger

from . import plugins as all_plugins
from .errors import ConfigurationError, ImplementationError
from .plugin import Plugin

logger = create_logger("PluginManager", "logs/main.log")


class PluginManager:
    def __init__(self, client: TS3Client, plugins: dict[str, dict[str, Any]]) -> None:
        logger.info("Initializing plugin manager...")
        self.plugins = plugins
        self.client = client
        self.threads: dict[int, tuple[Thread, Event]] = {}
        logger.info(f"Found {len(self.plugins)} plugins: {', '.join(self.plugins.keys())}")

    def run(self) -> None:
        logger.info("Starting plugins...")
        for plugin_name, config in self.plugins.items():
            if plugin_name not in all_plugins.__all__:
                raise ImplementationError(
                    plugin_name,
                    f"Plugin {plugin_name} was listed in the configuration, but not found in the plugins directory.",
                )

            stop = Event()
            plugin: Plugin = getattr(all_plugins, plugin_name)(self.client, stop)

            if not hasattr(plugin, "run"):
                raise ImplementationError(
                    plugin_name,
                    f"Plugin {plugin_name} does not have a run() method.",
                )

            validate_config(plugin, config)

            logger.info(f"Starting {plugin_name}...")
            thread = Thread(target=plugin.run, kwargs=config)
            thread.start()
            ident = thread.ident
            if ident is None:
                raise ImplementationError(plugin_name, f"Plugin {plugin_name} did not start.")
            thread.name = f"{plugin_name}-{ident}"
            self.threads[ident] = (thread, stop)
            logger.info(f"Started {plugin_name} with thread name {thread.name}")

    def stop(self, timeout: int = 5) -> None:
        logger.info("Stopping all plugins...")
        for thread, stop in self.threads.values():
            logger.info(f"Stopping {thread.name}...")
            stop.set()
            thread.join(timeout)
            logger.info(f"Stopped {thread.name}.")


def _matches_type(value: object, annotation: object) -> bool:
    if annotation is inspect.Parameter.empty or annotation is typing.Any:
        return True

    origin = typing.get_origin(annotation)
    if origin is typing.Union or origin is types.UnionType:
        return any(_matches_type(value, arg) for arg in typing.get_args(annotation))
    if origin is typing.Literal:
        return value in typing.get_args(annotation)
    if origin is typing.Annotated:
        return _matches_type(value, typing.get_args(annotation)[0])
    if origin is not None:
        return isinstance(value, origin) if isinstance(origin, type) else True

    if annotation is None:
        annotation = type(None)

    return isinstance(value, annotation) if isinstance(annotation, type) else True


def validate_config(plugin: Plugin, config: dict[str, Any]) -> None:
    try:
        signature = inspect.signature(plugin.run, eval_str=True)
    except (NameError, TypeError):
        signature = inspect.signature(plugin.run)

    for param_name, param in signature.parameters.items():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue

        is_mandatory = param.default == param.empty
        if param_name not in config and is_mandatory:
            raise ConfigurationError(
                plugin.__class__.__name__,
                f"Parameter '{param_name}' is missing from the configuration.",
            )
        elif param_name not in config and not is_mandatory:
            continue

        param_value = config[param_name]
        param_type = param.annotation

        if _matches_type(param_value, param_type):
            continue

        type_name = getattr(param_type, "__name__", str(param_type))
        raise ConfigurationError(
            plugin.__class__.__name__,
            f"Configuration parameter '{param_name}' should be of type {type_name}, but got {type(param_value).__name__}.",
        )

    parameters = signature.parameters
    accepts_extra = any(param.kind is inspect.Parameter.VAR_KEYWORD for param in parameters.values())
    if not accepts_extra:
        unknown = sorted(set(config) - set(parameters))
        if unknown:
            raise ConfigurationError(
                plugin.__class__.__name__,
                f"Unknown configuration parameter(s): {', '.join(unknown)}.",
            )
