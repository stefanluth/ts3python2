from threading import Event, Thread

from ts3client import TS3Client
from utils.logger import get_logger

from . import plugins
from .plugin import Plugin

logger = get_logger("main")


class PluginManager:
    def __init__(self, client: TS3Client, plugins: dict[str, dict]):
        logger.name = "PluginManager"
        self.plugins = plugins
        self.client = client
        self.threads: dict[int, tuple[Thread, Event]] = {}

    def run(self):
        for plugin_name, config in self.plugins.items():
            if plugin_name not in plugins.__all__:
                logger.info(f"Plugin {plugin_name} not found. Skipping...")
                continue

            stop = Event()
            plugin: Plugin = getattr(plugins, plugin_name)(stop)

            if not hasattr(plugin, "run"):
                logger.info(f"Plugin {plugin_name} does not have a run method. Skipping...")
                continue

            logger.info(f"Starting {plugin_name}...")
            thread = Thread(target=plugin.run, kwargs={"ts3_client": self.client, **config})
            thread.start()
            self.threads[thread.ident] = (thread, stop)

    def stop(self):
        logger.info("Stopping all plugins...")
        for thread, stop in self.threads.values():
            logger.debug(f"Stopping {thread.name}...")
            stop.set()
            thread.join()
