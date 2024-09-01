# wx-ghcnd.py

This script is ran by "streamlit run wx-ghcnd.py" and lets the user plot
historical weather data (https://www.ncei.noaa.gov/pub/data/ghcn/daily/). Why?
To play with streamlit and pandas.

Usage, running the program launches your default browser to the apps page.
Simply choose the country, state, and weather station. The TMAX plot should
appear. Other interesting elements are: TMIN, TAVG, PRCP, SNOW

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

You may delete the data/_.tar.gz files after the _.dly files have been
extracted.

Also, the init-data.sh script will:

- create a .venv/ virtual directory if one does not exists
- install streamlit and pandas into to virtual environment
- emit the run command you will need to use.

Pandas is not as flexible as I had hoped and I didn't see a direct technique for
loading the NCEI files, so added a translation layer (load\_\* methods) that
converts the NCEI formats to CSV, albeit using a pipe ('|') character instead of
a comma as some of the NCEI values contain commas.
