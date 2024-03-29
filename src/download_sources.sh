#!/bin/sh
cd "$(dirname "$0")" # Set the file path as a home directory
/app/venv/bin/python -m opendatacrawler -d https://data.europa.eu -m -p ./data -f kml
/app/venv/bin/python /app/src/index_metadata.py