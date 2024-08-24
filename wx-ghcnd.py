# SPDX-FileCopyrightText: 2024 Roy Wright
#
# SPDX-License-Identifier: MIT

"""
This script is ran by "streamlit run wx-ghcnd.py" and lets the user plot
historical weather data (https://www.ncei.noaa.gov/pub/data/ghcn/daily/).
Why? To play with streamlit and pandas.

Usage, running the program launches your default browser to the apps page.
Simply choose the country, state, and weather station.  The TMAX plot
should appear.  Other interesting elements are: TMIN, TAVG, PRCP, SNOW

The init-data.sh script will create and download the following data directory:

    data/
    data/ghcnd-countries.txt
    data/ghcnd-states.txt
    data/ghcnd-stations.txt
    data/ghcnd_gsn.tar.gz
    data/ghcnd_hcn.tar.gz
    data/ghcnd_gsn/*.dly
    data/ghcnd_hcn/*.dly
    data/readme.txt

You may delete the data/*.tar.gz files after the *.dly files have been extracted.

Also, the init-data.sh script will:
* create a .venv/ virtual directory if one does not exists
* install streamlit and pandas into to virtual environment
* emit the run command you will need to use.

Pandas is not as flexible as I had hoped and I didn't see a direct technique for
loading the NCEI files, so added a translation layer (load_* methods) that converts
the NCEI formats to CSV, albeit using a pipe ('|') character instead of a comma as
some of the NCEI values contain commas.
"""

from __future__ import annotations

from io import StringIO, SEEK_SET
from pathlib import Path

import pandas as pd
import streamlit as st
from pandas import DataFrame

DATA_PATH = Path(__file__).parent / "data"  # local path to the NCIE data
CSV_SEPARATOR = "|"  # some of the NCIE data contains commas with a value, so use an alternative separator.


@st.cache_data
def load_ghcnd_countries() -> pd.DataFrame:
    """
    Loads the ghcnd-countries.txt file and converts to CSV so pandas can read it into a DataFrame.
    See https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt file for ghcnd-countries.txt file format.
    """
    data: StringIO = StringIO()
    data.write(f"code{CSV_SEPARATOR}country\n")
    with (DATA_PATH / "ghcnd-countries.txt").open() as infile:
        for line in infile.readlines():
            code: str = line[0: 2]
            country: str = line[3:]
            new_row = f"{code}{CSV_SEPARATOR}{country}\n"
            data.write(new_row)
    data.seek(0, SEEK_SET)
    return pd.read_csv(filepath_or_buffer=data, sep=CSV_SEPARATOR)


@st.cache_data
def load_ghcnd_states() -> pd.DataFrame:
    """
    Loads the ghcnd-states.txt file and converts to CSV so pandas can read it into a DataFrame.
    See https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt file for ghcnd-states.txt file format.
    """
    data: StringIO = StringIO()
    data.write(f"code{CSV_SEPARATOR}name\n")
    with (DATA_PATH / "ghcnd-states.txt").open() as infile:
        for line in infile.readlines():
            code: str = line[0: 2]
            name: str = line[3:]
            new_row = f"{code}{CSV_SEPARATOR}{name}\n"
            data.write(new_row)
    data.seek(0, SEEK_SET)
    return pd.read_csv(filepath_or_buffer=data, sep=CSV_SEPARATOR)


def find_daily_path(station_id: str) -> Path | None:
    """
    Find the daily file for the station (station_id.dly).  The daily files
    can be in either the data/ghcnd_gsn or data/ghcnd_hcn directories.
    returns None if not found.
    """
    gsn_daily_path = DATA_PATH / "ghcnd_gsn" / f"{station_id}.dly"
    if gsn_daily_path.exists():
        return gsn_daily_path
    hcn_daily_path = DATA_PATH / "ghcnd_hcn" / f"{station_id}.dly"
    if hcn_daily_path.exists():
        return hcn_daily_path
    return None


def is_station_in_country(station_id: str, country_code: str) -> bool:
    return station_id[0: 2] == country_code


@st.cache_data
def load_ghcnd_stations(country_code: str) -> pd.DataFrame:
    """
    Loads the ghcnd-stations.txt file and converts to CSV so pandas can read it into a DataFrame.
    See https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt file for ghcnd-stations.txt file format.
    """
    data: StringIO = StringIO()
    data.write(
        f"station_id{CSV_SEPARATOR}latitude{CSV_SEPARATOR}longitude{CSV_SEPARATOR}elevation{CSV_SEPARATOR}state"
        f"{CSV_SEPARATOR}name{CSV_SEPARATOR}gsn_flag{CSV_SEPARATOR}hcn_crn_flag{CSV_SEPARATOR}wmo_id\n")
    with (DATA_PATH / "ghcnd-stations.txt").open() as infile:
        for line in infile.readlines():
            station_id: str = line[0: 11]
            if is_station_in_country(station_id, country_code) and find_daily_path(station_id):
                latitude: str = line[12: 20]
                longitude: str = line[21: 30]
                elevation: str = line[31: 37]
                state: str = line[38: 40]
                name: str = line[41: 71]
                gsn_flag: str = line[72: 75]
                hcn_crn_flag: str = line[76: 79]
                wmo_id: str = line[80: 85]
                new_row = (f"{station_id}{CSV_SEPARATOR}{latitude}{CSV_SEPARATOR}{longitude}{CSV_SEPARATOR}"
                           f"{elevation}{CSV_SEPARATOR}{state}{CSV_SEPARATOR}{name}{CSV_SEPARATOR}{gsn_flag}"
                           f"{CSV_SEPARATOR}{hcn_crn_flag}{CSV_SEPARATOR}{wmo_id}\n")
                data.write(new_row)
    data.seek(0, SEEK_SET)
    return pd.read_csv(filepath_or_buffer=data, sep=CSV_SEPARATOR)


# @st.cache
def load_ghcnd_dly_file(file_path: Path, celsius: bool) -> pd.DataFrame:
    """
    Loads a daily file (*.dly) and converts to CSV so pandas can read it into a DataFrame.
    See https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt file for dly file format.
    """
    data: StringIO = StringIO()
    with file_path.open() as infile:
        data.write(f"date{CSV_SEPARATOR}station{CSV_SEPARATOR}element{CSV_SEPARATOR}value\n")
        for line in infile.readlines():
            station_id: str = line[0: 11]
            yyyy: str = line[11: 15]
            mm: str = line[15: 17]
            element: str = line[17: 21]
            for day_of_month in range(1, 32):
                index: int = (day_of_month - 1) * 8 + 21
                value: str = convert_temperature(line[index: index + 5], celsius, element)
                new_row: str = (f"{yyyy}-{mm}-{day_of_month:02d}{CSV_SEPARATOR}{station_id}{CSV_SEPARATOR}"
                                f"{element}{CSV_SEPARATOR}{value}\n")
                data.write(new_row)
    data.seek(0, SEEK_SET)
    # noinspection PyTypeChecker
    return pd.read_csv(filepath_or_buffer=data, na_values=[-9999], thousands=",", sep=CSV_SEPARATOR)


def convert_temperature(value: str, celsius: bool, element: str) -> str | None:
    """
    Temperature is stored as tenths of a degree C
    Scale the temperature to degrees C or F (depending on if the celsius parameter is asserted)
    """
    if element not in ("TMIN", "TAVG", "TMAX"):
        return value
    if value is None or value == "-9999":
        return value
    # convert from tenths of a degree of celsius to degree celsius
    temperature: float = float(value) / 10.0
    if celsius:
        return f"{temperature:3.1f}"
    # convert to fahrenheit
    return f"{(temperature * 1.8) + 32:3.1f}"


def main() -> None:
    """The command line applications main function."""
    st.title("Weather Data Explorer")

    # get a country_code by selecting a country

    countries_df = load_ghcnd_countries()
    countries_unique_values: list[str] = countries_df["country"].unique()
    countries_selected_value: str = st.selectbox("Select country", countries_unique_values)
    countries_filtered_df: DataFrame = countries_df[countries_df["country"] == countries_selected_value]
    country_code: str = countries_filtered_df["code"].iloc[0]

    # from all the stations in the country_code, find station_states_df that contains all the states
    # that are in the country_code.

    stations_df: DataFrame = load_ghcnd_stations(country_code)
    stations_country_df: DataFrame = stations_df[stations_df["station_id"].str.startswith(country_code)]

    # select a state_code from the stations_country_df

    stations_states_unique_values: list[str] = stations_country_df["state"].unique()
    stations_states_selected_value: str = st.selectbox("Select state", stations_states_unique_values)
    stations_states_filtered_df: DataFrame = stations_country_df[
        stations_country_df["state"] == stations_states_selected_value]

    # make the station table selectable by row by using a st.dataframe(pd.dataframe)
    event = st.dataframe(stations_states_filtered_df, selection_mode="single-row", on_select="rerun")
    if len(event.selection.rows) > 0:
        # a station is selected
        station_id = stations_states_filtered_df.iloc[event.selection.rows]["station_id"].iloc[0]
        daily_path = find_daily_path(station_id)
        if daily_path is not None:
            # we have a gsn or hcn data file for the selected station
            st.subheader("Filter Data")
            celsius: bool = st.selectbox("Temperature Unit", ["F", "C"]) == "C"

            # noinspection PyTypeChecker
            daily_df: DataFrame = load_ghcnd_dly_file(daily_path, celsius=celsius)

            daily_columns: list[str] = daily_df.columns.tolist()
            daily_columns.insert(0, daily_columns.pop(daily_columns.index("element")))
            daily_selected_column: str = st.selectbox("Select column to filter by", daily_columns)

            daily_unique_values: list[str] = sorted(daily_df[daily_selected_column].unique())
            daily_selected_value: str = st.selectbox("Select value to filter by", daily_unique_values,
                                                     index=daily_unique_values.index("TMAX"))

            daily_filtered_df: DataFrame = daily_df[daily_df[daily_selected_column] == daily_selected_value]

            x_column: str = "date"
            y_column: str = "value"
            st.line_chart(daily_filtered_df.set_index(x_column)[y_column])


# intentionally not using a __main__ fence as this file is ran from "streamlit run ..."
main()
