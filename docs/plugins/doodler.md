# Doodler

The Doodler plugin replaces the server banner on given dates with custom images, similar to Google Doodles.

## Configuration

The following configuration options are available:

| Option     | Type         | Description                                                        |
| ---------- | ------------ | ------------------------------------------------------------------ |
| `default`* | `str`        | The URL of the default banner image.                               |
| `doodles`* | `list[dict]` | A list of dictionaries containing the date and URL of each doodle. |

Options marked with an asterisk (`*`) are required.

The `doodles` list contains dictionaries with the following keys:

| Key         | Type  | Description                                     |
| ----------- | ----- | ----------------------------------------------- |
| `date`      | `str` | The date on which the doodle will be displayed. |
| `startDate` | `str` | The start date of the doodle period.            |
| `endDate`   | `str` | The end date of the doodle period.              |
| `url`*      | `str` | The URL of the banner image.                    |

See the [Notes](#notes) for more information on the `date`, `startDate`, and `endDate` keys.

## Usage

To use this plugin, simply enable it by adding it to the `config.py` file.

```python
PLUGINS_CONFIG = {
    # Be sure to adjust the dates and URLs to your needs
    "Doodler": {
        "default": "https://mydomain.com/banner-default.png",
        "doodles": [
            {
                "date": "14-02-2024",
                "url": "https://mydomain.com/banner-valentines.png",
            },
            {
                "date": "01-04-2024",
                "url": "https://mydomain.com/banner-april-fools.png",
            },
            {
                "date": "31-10-2024",
                "url": "https://mydomain.com/banner-halloween.png",
            },
            {
                "startDate": "01-12-2024",
                "endDate": "30-12-2024",
                "url": "https://mydomain.com/banner-christmas.png",
            },
            {
                "startDate": "01-01-2025",
                "endDate": "07-01-2025",
                "url": "https://mydomain.com/banner-new-year.png",
            },
        ],
    },
}
```

## Notes

- The `date` key is used to specify a single date on which the doodle will be displayed. The `startDate` and `endDate` keys are used to specify a period during which the doodle will be displayed. Either `date` or `startDate` + `endDate` must be specified, but not both.
