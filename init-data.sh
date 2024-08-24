#!/usr/bin/env bash

BASE_URL="https://www.ncei.noaa.gov/pub/data/ghcn/daily"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DATA_PATH="${SCRIPT_DIR}/data"
mkdir -p "${DATA_PATH}"

declare -a FILES=("ghcnd-countries.txt" "ghcnd-states.txt" "ghcnd-stations.txt" "readme.txt" \
                  "ghcnd_gsn.tar.gz" "ghcnd_hcn.tar.gz")

for filename in "${FILES[@]}"
  do
    if [ -f "${DATA_PATH}/${filename}" ]; then
      echo "skipping "${DATA_PATH}/${filename}""
    else
      url="${BASE_URL}/${filename}"
      echo "getting "${DATA_PATH}/${filename}""
      $(curl --remote-name --output-dir "${DATA_PATH}" "${url}")
    fi
  done

if [ ! -d "${DATA_PATH}/ghcnd_gsn" ]; then
  echo "extracting ${DATA_PATH}/ghcnd_gsn.tar.gz"
  tar xf "${DATA_PATH}/ghcnd_gsn.tar.gz" --overwrite --directory "${DATA_PATH}"
fi

if [ ! -d "${DATA_PATH}/ghcnd_hcn" ]; then
  echo "extracting ${DATA_PATH}/ghcnd_hcn.tar.gz"
  tar xf "${DATA_PATH}/ghcnd_hcn.tar.gz" --overwrite --directory "${DATA_PATH}"
fi

if [ ! -d .venv ]; then
  echo "creating virtual environment in .venv/"
  python3 -m venv .venv
fi

if [ ! -f .venv/bin/streamlit ]; then
  echo "installing dependencies into virtual environment"
  .venv/bin/pip3 install streamlit pandas
fi

echo "to start server, run: .venv/bin/streamlit run wx-ghcnd.py"
