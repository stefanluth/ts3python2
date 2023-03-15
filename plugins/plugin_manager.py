from threading import Event, Thread

from ts3client import TS3Client
from utils.logger import create_logger

from . import plugins
from .plugin import Plugin

logger = create_logger("PluginManager", "main.log")


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
            if plugin_name not in plugins.__all__:
                logger.info(f"Plugin {plugin_name} not found. Skipping...")
                continue

            stop = Event()
            plugin: Plugin = getattr(plugins, plugin_name)(self.client, stop)

            if not hasattr(plugin, "run"):
                logger.info(f"Plugin {plugin_name} does not have a run method. Skipping...")
                continue

            logger.info(f"Starting {plugin_name}...")
            thread = Thread(target=plugin.run, kwargs=config)
            thread.start()
            thread.name = f"{plugin_name}-{thread.ident}"
            self.threads[thread.ident] = (thread, stop)
            logger.info(f"Started {plugin_name} with thread name {thread.name}")

    def stop(self):
        logger.info("Stopping all plugins...")
        for thread, stop in self.threads.values():
            logger.info(f"Stopping {thread.name}...")
            stop.set()
            thread.join()
            logger.info(f"Stopped {thread.name}.")
