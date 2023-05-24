import os
import json

# Constants

# Config Variables
# Loads config
CONFIG = {}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.json')) as f:
    CONFIG = json.load(f)

# Global constants from config
DATA_FOLDER = CONFIG['data_folder']
CACHE_FOLDER = CONFIG["cache_folder"] 

# Creates Cache folder if it does not exist
if not os.path.exists(CACHE_FOLDER):
    os.mkdir(CACHE_FOLDER)

# Projection
USUAL_PROJECTION = "EPSG:4326"
MANIPULATION_PROJECTION = 'EPSG:3857'
BUFFER_PROJECTION = "EPSG:3395"


# Column Names
POPULATION = "population"
ID = "id"
GEOMETRY = "geometry"
LAT = "lat"
LON = "lon"
