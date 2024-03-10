from datetime import datetime, timedelta

from ..plugin import Plugin


def date_range(start_date, end_date) -> str:
    start_date = datetime.strptime(start_date, "%d-%m-%Y")
    end_date = datetime.strptime(end_date, "%d-%m-%Y")
    delta = timedelta(days=1)
    current_date = start_date
    while current_date <= end_date:
        yield current_date.strftime("%d-%m-%Y")
        current_date += delta


class Doodler(Plugin):
    def run(self, default: str, doodles: list[dict] = []):
        """Change the server banner on given dates.

        :param default: The default server banner to use.
        :type default: str
        :param doodles: The server banners to use on given dates, e.g. [{"date": "25-12-2025", "url": "https://myserver.net/christmas-banner.png"}, {"startDate": "01-01-2025", "endDate": "07-01-2025", "url": "https://myserver.net/new-year-banner.png"}], defaults to []
        :type doodles: list[dict]
        """

        transformed = {}
        # Transform doodles to a dict with the url as key and the date(s) as value
        for doodle in doodles:
            if "date" in doodle:
                transformed[doodle["url"]] = [doodle["date"]]
            elif "startDate" in doodle and "endDate" in doodle:
                transformed[doodle["url"]] = list(date_range(doodle["startDate"], doodle["endDate"]))

        self.ready()

        while not self.event.is_set():
            self.logger.debug("Checking doodles...")

            current_date = datetime.today().strftime("%d-%m-%Y")
            new_banner = default

            for url, dates in transformed.items():
                if current_date in dates:
                    new_banner = url
                    break

            server_info = self.client.query.commands.serverinfo().data[0]
            current_banner = server_info.get("virtualserver_hostbanner_gfx_url")
            if current_banner != new_banner:
                self.logger.info(f"Setting server banner to {new_banner}")
                self.client.query.commands.serveredit(
                    virtualserver_hostbanner_gfx_url=new_banner,
                    virtualserver_hostbanner_mode=2,
                )

            hours_until_midnight = 24 - datetime.today().hour
            self.event.wait(60 * 60 * hours_until_midnight)
