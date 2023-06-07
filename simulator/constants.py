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
NODE_ID1 = "node_id1"
NODE_ID2 = "node_id2"
DISTANCE = "distance"
POSITION = "position"
DATE = "date"
NOISE = "noise"



LON_X = "lon_x"
LAT_X = "lat_x"
LAT_Y = "lat_y"
LON_Y = "lon_y"


# Noise
CITY_NOISE =  0.009 # 1000m in the equator
ROAD_NOISE = 0.0018 # 200m in the equator

# City
MIN_CITY_RADIUS_KM = 1.5
MIN_BUILDING_RADIUS_KM = 0.5
MIN_POPULATION = 500
MAX_DISTANCE_BETWEEN_ADJACENT_CITIES_KM = 45

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
FINAL_FORCE = "final_force"
REACH_PROBABILITY = "reach_probability"

# Node Positions
START_NODE = "start_node"
END_NODE = "end_node"
