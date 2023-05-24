# Cache functions
import os
import simulator.constants as con


def get_cache_file(name : str) -> str:
    '''
    Method that returns the absolute filepath of a given filename in the cache

    Parameters
    ---------
    name : str
        Name of the file or folder in the cache
    
    Returns
    -------
    str
        Complete filepath of the given element
    ''' 

    return(os.path.join(con.CACHE_FOLDER, name))