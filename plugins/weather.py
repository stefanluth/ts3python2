import json
import time
from .plugin import Plugin
import urllib.request


class Weather(Plugin):
    def run(self, api_key: str, command: str):
        """Get the weather for a location.

        :param api_key: The API key for WeatherAPI.com.
        :type api_key: str
        :param command: The command to trigger the weather command.
        :type command: str
        """

        while not self.event.is_set():
            for message in self.client.get_unread_messages():
                if not message.content.startswith(command):
                    continue

                message.mark_as_used()

                if not len(message.content.split(" ")) > 1:
                    self.client.send_private_message(
                        message.invokerid,
                        "Please provide a location.",
                    )

                    continue

                self.logger.info(f"User {message.invokername} triggered the weather command.")
                location = message.content.split(" ", 1)[1]

                data = self.get_weather(api_key, location)
                self.client.send_private_message(
                    message.invokerid,
                    f"Current weather for {data['location']['name']}: {data['current']['condition']['text']}, "
                    f"{data['current']['temp_c']}°C, feels like {data['current']['feelslike_c']}°C, humidity "
                    f"{data['current']['humidity']}%, wind {data['current']['wind_kph']} kph, "
                    f"{data['current']['wind_dir']}.",
                )
            time.sleep(1)

    def get_weather(self, api_key: str, location: str) -> dict:
        api_endpoint = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"

        with urllib.request.urlopen(api_endpoint) as response:
            data = json.loads(response.read())
            return data
