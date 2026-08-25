#!/usr/bin/env python3
"""Minimal OpenWeatherMap current-weather collector.

Reads a city name from the command line and appends one row to
weather_realtime.csv.  No data is invented — every value comes directly
from the OpenWeatherMap Current Weather API response.
"""

import csv
import os
import sys
from datetime import datetime

import requests

CSV_FILE = "weather_realtime.csv"
FIELDNAMES = [
    "Timestamp",
    "City",
    "Latitude",
    "Longitude",
    "Temperature_C",
    "Feels_Like_C",
    "Humidity_Percent",
    "Pressure_hPa",
    "Wind_Speed_mps",
    "Cloud_Cover_Percent",
    "Weather_Condition",
    "Weather_Description",
    "Visibility_m",
]


def fetch_weather(city: str) -> dict:
    """Call the OpenWeatherMap Current Weather API and return a flat dict."""
    api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    if not api_key:
        print("Error: OPENWEATHER_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Error fetching weather for '{city}': {exc}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()

    return {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "City": data.get("name", city),
        "Latitude": data["coord"]["lat"],
        "Longitude": data["coord"]["lon"],
        "Temperature_C": data["main"]["temp"],
        "Feels_Like_C": data["main"]["feels_like"],
        "Humidity_Percent": data["main"]["humidity"],
        "Pressure_hPa": data["main"]["pressure"],
        "Wind_Speed_mps": data["wind"]["speed"],
        "Cloud_Cover_Percent": data["clouds"]["all"],
        "Weather_Condition": data["weather"][0]["main"],
        "Weather_Description": data["weather"][0]["description"],
        "Visibility_m": data.get("visibility", ""),
    }


def append_row(row: dict) -> None:
    """Append one row to the CSV.  Create the file (with header) if needed.

    Duplicate detection: skip if a row with the same City + Timestamp
    already exists.
    """
    file_exists = os.path.isfile(CSV_FILE)

    if file_exists:
        with open(CSV_FILE, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for existing in reader:
                if (existing.get("City", "") == row["City"]
                        and existing.get("Timestamp", "") == row["Timestamp"]):
                    print(
                        f"Duplicate observation skipped: {row['City']} @ {row['Timestamp']}"
                    )
                    return

    write_header = not file_exists or os.path.getsize(CSV_FILE) == 0

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    print(f"Wrote row: {row['City']} — {row['Temperature_C']}°C, {row['Weather_Condition']}")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <city>", file=sys.stderr)
        print("Example: python weather_collector.py Jatani", file=sys.stderr)
        sys.exit(1)

    city = sys.argv[1]
    row = fetch_weather(city)
    append_row(row)


if __name__ == "__main__":
    main()
