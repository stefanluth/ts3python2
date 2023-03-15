from threading import Thread

from ts3client import TS3Client
from .afk_mover import afk_mover


class PluginManager:
    def __init__(self, client: TS3Client, plugins: dict):
        self.plugins = plugins
        self.client = client

    def run(self):
        for plugin, config in self.plugins.items():
            Thread(target=eval(plugin), kwargs={"ts3_client": self.client, **config}).start()
