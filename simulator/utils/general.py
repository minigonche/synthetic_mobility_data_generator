
import os
import sys
import datetime
import pandas as pd

import simulator.constants as con
import simulator.utils.errors as error_fun



def binary_search(search_val, array):
    '''
    Method that searches in the given array in a binary fashion

    Parameters
    ----------
    search_val : object
        The value to search

    array : list
        List for searching

    Return
    ------
    int
        The position of the closest value less or equal to the given value. Returns -1 if the list is empty.
    '''

    if len(array) == 0:
        return -1

    low = 0
    high = len(array) - 1
    closest_index = -1

    while low <= high:
        mid = (low + high) // 2
        if array[mid] <= search_val:
            closest_index = mid
            low = mid + 1
        else:
            high = mid - 1

    return closest_index

def load_ping_data(data_dir):
    """
    Loads data and returns it as a DataFrame 

    Returns
    -------
    pd.DataFrame
        DataFrame with loaded ping data
    """

    df = pd.DataFrame()
    date_parser = lambda x: datetime.datetime.strptime(x, con.DEFAULT_DT_FORMAT)
    for file in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file)
        try:
            df_tmp = pd.read_csv(file_path, parse_dates=[con.DATE], date_parser=date_parser)

            # Check minimun required columns
            if not set(set(con.DATASET_MIN_COLS)).issubset(df_tmp.columns):
                error_fun.write_error(sys.argv[0], f"incorrect data structure for file {file_path}", 
                            "error", datetime.datetime.now())
                continue

            df_tmp.rename(columns={con.DATE: con.DATE_TIME,
                                    con.LAT: con.FB_LATITUDE, 
                                    con.LON: con.FB_LONGITUDE}, inplace=True)

            
            df = pd.concat([df, df_tmp])

        except Exception as e:
            error_fun.write_error(sys.argv[0], e, 
                            "error", datetime.datetime.now())


    if df.empty:
        raise Exception("Not possible to load data. Check error log.")
    
    return df