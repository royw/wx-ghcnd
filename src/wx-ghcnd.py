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
* create a .venv/ virtual directory if one does not exist
* install streamlit and pandas into to virtual environment
* emit the run command you will need to use.

Pandas is not as flexible as I had hoped and I didn't see a direct technique for
loading the NCEI files, so added a translation layer (load_* methods) that converts
the NCEI formats to CSV, albeit using a pipe ('|') character instead of a comma as
some of the NCEI values contain commas.
"""

from __future__ import annotations

import streamlit as st
from pandas import DataFrame

from ghcnd.load import find_daily_path, load_countries, load_dly_file, load_stations


def main() -> None:
    """The command line applications main function."""
    st.title("Weather Data Explorer")

    # get a country_code by selecting a country

    countries_df = load_countries()
    countries_unique_values: list[str] = countries_df["country"].unique()
    countries_selected_value: str = st.selectbox("Select country", countries_unique_values)
    countries_filtered_df: DataFrame = countries_df[countries_df["country"] == countries_selected_value]
    country_code: str = countries_filtered_df["code"].iloc[0]

    # from all the stations in the country_code, find station_states_df that contains all the states
    # that are in the country_code.

    stations_df: DataFrame = load_stations(country_code)
    stations_country_df: DataFrame = stations_df[stations_df["station_id"].str.startswith(country_code)]

    # select a state_code from the stations_country_df

    stations_states_unique_values: list[str] = stations_country_df["state"].unique()
    stations_states_selected_value: str = st.selectbox("Select state", stations_states_unique_values)
    stations_states_filtered_df: DataFrame = stations_country_df[
        stations_country_df["state"] == stations_states_selected_value
    ]

    # make the station table selectable by row by using a st.dataframe(pd.dataframe)
    event = st.dataframe(stations_states_filtered_df, selection_mode="single-row", on_select="rerun")
    rows = event["selection"]["rows"]
    if len(rows) > 0:
        # a station is selected
        station_id = stations_states_filtered_df.iloc[rows]["station_id"].iloc[0]
        daily_path = find_daily_path(station_id)
        if daily_path is not None:
            # we have a gsn or hcn data file for the selected station
            st.subheader("Filter Data")
            celsius: bool = st.selectbox("Temperature Unit", ["F", "C"]) == "C"

            # noinspection PyTypeChecker
            daily_df: DataFrame = load_dly_file(daily_path, celsius=celsius)

            daily_columns: list[str] = daily_df.columns.tolist()
            daily_columns.insert(0, daily_columns.pop(daily_columns.index("element")))
            daily_selected_column: str = st.selectbox("Select column to filter by", daily_columns)

            daily_unique_values: list[str] = sorted(daily_df[daily_selected_column].unique())
            daily_selected_value: str = st.selectbox(
                "Select value to filter by", daily_unique_values, index=daily_unique_values.index("TMAX")
            )

            daily_filtered_df: DataFrame = daily_df[daily_df[daily_selected_column] == daily_selected_value]

            x_column: str = "date"
            y_column: str = "value"
            st.line_chart(daily_filtered_df.set_index(x_column)[y_column])


# intentionally not using a __main__ fence as this file is ran from "streamlit run ..."
main()
