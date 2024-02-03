import inspect
from threading import Event, Thread

from ts3client import TS3Client
from ts3client.utils.logger import create_logger

from . import plugins as all_plugins
from .errors import ConfigurationError, ImplementationError
from .plugin import Plugin

logger = create_logger("PluginManager", "logs/main.log")


class PluginManager:
    def __init__(self, client: TS3Client, plugins: dict[str, dict]):
        logger.info("Initializing plugin manager...")
        self.plugins = plugins
        self.client = client
        self.threads: dict[int, tuple[Thread, Event]] = {}
        logger.info(f"Found {len(self.plugins)} plugins: {', '.join(self.plugins.keys())}")

    def run(self):
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
            thread.name = f"{plugin_name}-{thread.ident}"
            self.threads[thread.ident] = (thread, stop)
            logger.info(f"Started {plugin_name} with thread name {thread.name}")

    def stop(self, timeout: int = 5):
        logger.info("Stopping all plugins...")
        for thread, stop in self.threads.values():
            logger.info(f"Stopping {thread.name}...")
            stop.set()
            thread.join(timeout)
            logger.info(f"Stopped {thread.name}.")


def validate_config(plugin: Plugin, config: dict):
    signature = inspect.signature(plugin.run)

    for param_name, param in signature.parameters.items():
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

        if isinstance(param_value, param_type):
            continue

        raise ConfigurationError(
            plugin.__class__.__name__,
            f"Configuration parameter '{param_name}' should be of type {param_type.__name__}, but got {type(param_value).__name__}.",
        )
