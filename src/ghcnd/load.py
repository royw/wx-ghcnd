from __future__ import annotations

from io import SEEK_SET, StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

_DATA_PATH = Path(__file__).parent.parent.parent / "data"  # local path to the NCIE/GHCND data
_CSV_SEPARATOR = "|"  # some of the NCIE data contains commas with a value, so use an alternative separator.


@st.cache_data
def load_countries() -> pd.DataFrame:
    """
    Loads the ghcnd-countries.txt file and converts to CSV so pandas can read it into a DataFrame.
    See https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt file for ghcnd-countries.txt file format.
    """
    data: StringIO = StringIO()
    data.write(f"code{_CSV_SEPARATOR}country\n")
    with (_DATA_PATH / "ghcnd-countries.txt").open() as infile:
        for line in infile.readlines():
            code: str = line[0:2]
            country: str = line[3:]
            new_row = f"{code}{_CSV_SEPARATOR}{country}\n"
            data.write(new_row)
    data.seek(0, SEEK_SET)
    return pd.read_csv(filepath_or_buffer=data, sep=_CSV_SEPARATOR)


@st.cache_data
def load_states() -> pd.DataFrame:
    """
    Loads the ghcnd-states.txt file and converts to CSV so pandas can read it into a DataFrame.
    See https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt file for ghcnd-states.txt file format.
    """
    data: StringIO = StringIO()
    data.write(f"code{_CSV_SEPARATOR}name\n")
    with (_DATA_PATH / "ghcnd-states.txt").open() as infile:
        for line in infile.readlines():
            code: str = line[0:2]
            name: str = line[3:]
            new_row = f"{code}{_CSV_SEPARATOR}{name}\n"
            data.write(new_row)
    data.seek(0, SEEK_SET)
    return pd.read_csv(filepath_or_buffer=data, sep=_CSV_SEPARATOR)


def find_daily_path(station_id: str) -> Path | None:
    """
    Find the daily file for the station (station_id.dly).  The daily files
    can be in either the data/ghcnd_gsn or data/ghcnd_hcn directories.
    returns None if not found.
    """
    gsn_daily_path = _DATA_PATH / "ghcnd_gsn" / f"{station_id}.dly"
    if gsn_daily_path.exists():
        return gsn_daily_path
    hcn_daily_path = _DATA_PATH / "ghcnd_hcn" / f"{station_id}.dly"
    if hcn_daily_path.exists():
        return hcn_daily_path
    return None


def _is_station_in_country(station_id: str, country_code: str) -> bool:
    return station_id[0:2] == country_code


@st.cache_data
def load_stations(country_code: str) -> pd.DataFrame:
    """
    Loads the ghcnd-stations.txt file and converts to CSV so pandas can read it into a DataFrame.
    See https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt file for ghcnd-stations.txt file format.
    """
    data: StringIO = StringIO()
    data.write(
        f"station_id{_CSV_SEPARATOR}latitude{_CSV_SEPARATOR}longitude{_CSV_SEPARATOR}elevation{_CSV_SEPARATOR}state"
        f"{_CSV_SEPARATOR}name{_CSV_SEPARATOR}gsn_flag{_CSV_SEPARATOR}hcn_crn_flag{_CSV_SEPARATOR}wmo_id\n"
    )
    with (_DATA_PATH / "ghcnd-stations.txt").open() as infile:
        for line in infile.readlines():
            station_id: str = line[0:11]
            if _is_station_in_country(station_id, country_code) and find_daily_path(station_id):
                latitude: str = line[12:20]
                longitude: str = line[21:30]
                elevation: str = line[31:37]
                state: str = line[38:40]
                name: str = line[41:71]
                gsn_flag: str = line[72:75]
                hcn_crn_flag: str = line[76:79]
                wmo_id: str = line[80:85]
                new_row = (
                    f"{station_id}{_CSV_SEPARATOR}{latitude}{_CSV_SEPARATOR}{longitude}{_CSV_SEPARATOR}"
                    f"{elevation}{_CSV_SEPARATOR}{state}{_CSV_SEPARATOR}{name}{_CSV_SEPARATOR}{gsn_flag}"
                    f"{_CSV_SEPARATOR}{hcn_crn_flag}{_CSV_SEPARATOR}{wmo_id}\n"
                )
                data.write(new_row)
    data.seek(0, SEEK_SET)
    return pd.read_csv(filepath_or_buffer=data, sep=_CSV_SEPARATOR)


# @st.cache
def load_dly_file(file_path: Path, celsius: bool) -> pd.DataFrame:
    """
    Loads a daily file (*.dly) and converts to CSV so pandas can read it into a DataFrame.
    See https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt file for dly file format.
    """
    data: StringIO = StringIO()
    with file_path.open() as infile:
        data.write(f"date{_CSV_SEPARATOR}station{_CSV_SEPARATOR}element{_CSV_SEPARATOR}value\n")
        for line in infile.readlines():
            station_id: str = line[0:11]
            yyyy: str = line[11:15]
            mm: str = line[15:17]
            element: str = line[17:21]
            for day_of_month in range(1, 32):
                index: int = (day_of_month - 1) * 8 + 21
                value: str | None = _convert_temperature(line[index : index + 5], celsius, element)
                if value:
                    new_row: str = (
                        f"{yyyy}-{mm}-{day_of_month:02d}{_CSV_SEPARATOR}{station_id}{_CSV_SEPARATOR}"
                        f"{element}{_CSV_SEPARATOR}{value}\n"
                    )
                    data.write(new_row)
    data.seek(0, SEEK_SET)
    # noinspection PyTypeChecker
    return pd.read_csv(filepath_or_buffer=data, na_values=[-9999], thousands=",", sep=_CSV_SEPARATOR)


def _convert_temperature(value: str | None, celsius: bool, element: str) -> str | None:
    """
    Temperature is stored as tenths of a degree C
    Scale the temperature to degrees C or F (depending on if the celsius parameter is asserted)
    """
    if element not in ("TMIN", "TAVG", "TMAX"):
        return value
    if value is None or value == "-9999":
        return None
    # convert from tenths of a degree of celsius to degree celsius
    temperature: float = float(value) / 10.0
    if celsius:
        return f"{temperature:3.1f}"
    # convert to fahrenheit
    return f"{(temperature * 1.8) + 32:3.1f}"
