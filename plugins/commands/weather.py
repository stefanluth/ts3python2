import json
import urllib.request

from ts3client import TS3Client
from ts3client.message import Message

from ..command import Command

API_URL = "http://api.weatherapi.com/v1"


class Weather(Command):
    """Get the weather for a location."""

    def __init__(self, client: TS3Client, trigger: str, api_key: str):
        super().__init__(client, trigger)
        self.api_key = api_key

    def run(self, message: Message):
        """Get the weather for a location.

        :param api_key: The API key for WeatherAPI.com.
        :type api_key: str
        """

        if not len(message.content.split(" ")) > 1:
            self.client.send_private_message(message.invokerid, "Please provide a location.")
            return

        self.logger.info(f"User {message.invokername} triggered the weather command.")
        location = message.content.split(" ", 1)[1]

        weather_data = self.get_weather_data(location)
        self.client.send_private_message(
            message.invokerid,
            f"Current weather for {weather_data['location']['name']}: {weather_data['current']['condition']['text']}, "
            f"{weather_data['current']['temp_c']}°C, feels like {weather_data['current']['feelslike_c']}°C, humidity "
            f"{weather_data['current']['humidity']}%, wind {weather_data['current']['wind_kph']} kph, "
            f"{weather_data['current']['wind_dir']}.",
        )

    def get_weather_data(self, location: str) -> dict:
        api_endpoint = f"{API_URL}/current.json?key={self.api_key}&q={location}"
        with urllib.request.urlopen(api_endpoint) as response:
            data = json.loads(response.read())
            return data
