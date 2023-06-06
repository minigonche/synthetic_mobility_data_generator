
import os
import datetime

# Local imports
import simulator.constants as con

def write_error(source : str, msg : str, 
                 type : str, timestamp : datetime.datetime, errors_file : str = None):
    """
    Method to write warnings and errors to file.
    """
    if not errors_file:
        errors_file = os.path.join(con.ERRORS_FOLDER, con.ERRORS_FILE)
    datetime = timestamp.strftime("%m/%d/%Y, %H:%M:%S")
    with open(errors_file, 'a') as out:
        out.write(f"{datetime},{source},{type},{msg}\n")