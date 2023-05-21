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
