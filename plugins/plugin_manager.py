from threading import Event, Thread

from ts3client import TS3Client
from utils.logger import get_logger

from . import plugins

logger = get_logger("main")


class PluginManager:
    def __init__(self, client: TS3Client, plugins: dict):
        self.plugins = plugins
        self.client = client
        self.threads: dict[int, tuple[Thread, Event]] = {}

    def run(self):
        for plugin_name, config in self.plugins.items():
            if plugin_name not in plugins.__all__:
                logger.info(f"Plugin {plugin_name} not found. Skipping...")
                continue

            stop = Event()
            plugin = getattr(plugins, plugin_name)(stop)

            if not hasattr(plugin, "run"):
                logger.info(f"Plugin {plugin_name} does not have a run method. Skipping...")
                continue

            thread = Thread(target=plugin.run, kwargs={"ts3_client": self.client, **config})
            thread.start()
            self.threads[thread.ident] = (thread, stop)

    def stop(self):
        for thread, stop in self.threads.values():
            stop.set()
            thread.join()
