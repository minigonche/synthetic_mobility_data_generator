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
RESULTS_FOLDER = CONFIG["results_folder"] 
ERRORS_FOLDER = CONFIG["errors_folder"]
ERRORS_FILE = "errors.csv"

# Creates Cache folder if it does not exist
if not os.path.exists(CACHE_FOLDER):
    os.mkdir(CACHE_FOLDER)

# Creates errors folder if it does not exist
if not os.path.exists(ERRORS_FOLDER):
    os.mkdir(ERRORS_FOLDER)

# Projection
USUAL_PROJECTION = "EPSG:4326"
MANIPULATION_PROJECTION = 'EPSG:3857'
BUFFER_PROJECTION = "EPSG:3395"

# Degrees
DEGREE_EQUIVALENT_IN_KM = 111.32

SIMPLIFICATION_CONSTANTS_METERS = 500

# Column Names
POPULATION = "population"
ID = "id"
GEOMETRY = "geometry"
LAT = "lat"
LON = "lon"
VALUE = "value"
NODE_ID = "node_id"
NODE_ID1 = "node_id1"
NODE_ID2 = "node_id2"
DISTANCE = "distance"
DATETIME = "datetime"
GEO_ID = "geo_id"
HOUR = "hour"
POSITION = "position"
DATE = "date"
NOISE = "noise"
LON_X = "lon_x"
LAT_X = "lat_x"
LAT_Y = "lat_y"
LON_Y = "lon_y"


# fb specific column names
FB_LATITUDE = "latitude"
FB_LONGITUDE = "longitude"
DATE_TIME = "date_time"
DAY_OF_WEEK = "day_of_week"
QUAD_KEY = "quadkey"
ADMIN_KEY = "GID_2"
N_BASELINE = "n_baseline"
N_CRISIS = "n_crisis"
N_DIFFERENCE = "n_difference"
DENSITY_BASELINE = "density_baseline"
DENSITY_CRISIS = "density_crisis"
PERCENT_CHANGE = "percent_change"
Z_SCORE = "z_score"
DS = "ds"
COUNTRY = "country"
FB_START_LATITUDE = "start_latitude"
FB_START_LONGITUDE = "start_longitude"
FB_END_LATITUDE = "end_latitude"
FB_END_LONGITUDE = "end_longitude"
START_QUADKEY = "start_quadkey"
END_QUADKEY = "end_quadkey"
START_ADMIN_KEY = "start_GID_2"
END_ADMIN_KEY = "end_GID_2"
LENGTH_KM = "length_km"

# Ready mapper const
READYMAPPER_LAT = "lat"
READYMAPPER_LON = "lon"
READYMAPPER_DT = "dt"
READYMAPPER_START_LATITUDE = "start_lat"
READYMAPPER_START_LONGITUDE = "start_lon"
READYMAPPER_END_LATITUDE = "end_lat"
READYMAPPER_END_LONGITUDE = "end_lon"

# Min columns for simulated dataset
DATASET_MIN_COLS = [ID, LAT, LON, DATE]
FB_TILE_POP_DENSITY_COLS = [FB_LATITUDE, FB_LONGITUDE, QUAD_KEY,
                        DATE_TIME, N_BASELINE, N_CRISIS, N_DIFFERENCE, 
                        DENSITY_BASELINE, DENSITY_CRISIS, PERCENT_CHANGE, Z_SCORE, DS]

FB_ADMIN_POP_DENSITY_COLS = [FB_LATITUDE, FB_LONGITUDE, ADMIN_KEY,
                        DATE_TIME, N_BASELINE, N_CRISIS, N_DIFFERENCE, 
                        DENSITY_BASELINE, DENSITY_CRISIS, PERCENT_CHANGE, Z_SCORE, DS]

FB_TILE_MOBILITY_COLS = [FB_START_LATITUDE, FB_START_LONGITUDE, FB_END_LATITUDE, FB_END_LONGITUDE, LENGTH_KM, START_QUADKEY, 
                        END_QUADKEY, DATE_TIME, N_BASELINE, N_CRISIS, N_DIFFERENCE, 
                        PERCENT_CHANGE, Z_SCORE, DS]

FB_ADMIN_MOBILITY_COLS = [FB_START_LATITUDE, FB_START_LONGITUDE, FB_END_LATITUDE, FB_END_LONGITUDE, LENGTH_KM, START_ADMIN_KEY, 
                        END_ADMIN_KEY, DATE_TIME, N_BASELINE, N_CRISIS, N_DIFFERENCE, 
                        PERCENT_CHANGE, Z_SCORE, DS]

# Noise
CITY_NOISE =  0.0045 # 500m in the equator
ROAD_NOISE = 0.0018 # 200m in the equator


# City
MIN_CITY_RADIUS_KM = 1.5
MIN_BUILDING_RADIUS_KM = 0.5
MIN_POPULATION = 500
MAX_DISTANCE_BETWEEN_ADJACENT_CITIES_KM = 8

# Roads
ROADS_WIDTH_KM = 0.35
ROAD_LENGTH = "road_length"
ROAD_SAMPLE_DENSITY_BY_KM = 25


# Simulator Constants
LOCATION = "location"
LOCATION_ID = "location_id"
NODE = "node"
EDGE = "edge"


# Forces
ATTRACTIVE_FORCE = "attractive_force"
REPELLING_FORCE = "repelling_force"

# Bing Map Tiles Constants
LEVEL_DETAIL = 14

# fb data constants
FINAL_FORCE = "final_force"
REACH_PROBABILITY = "reach_probability"
EPSILON = 1
MIN_STD = 0.1

# Node Positions
START_NODE = "start_node"
END_NODE = "end_node"

# Dateitme constants
DEFAULT_DT_FORMAT = '%m-%d-%Y_%H:%M:%S'
READYMAPPER_DT_FORMAT = "%Y-%m-%d_%H:%M:%S"
READYMAPPER_MOV_DT_FORMAT = "%Y-%m-%d %H:%M:%S"