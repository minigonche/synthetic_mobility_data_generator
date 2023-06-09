import datetime
import numpy as np
import pandas as pd
import geopandas as gpd

# Local imports
import simulator.constants as con
from . import datetime_functions as dt_fun


def extract_quad_keys(pois : tuple) -> list:
    '''
    Method calculate the bing tile quad key of a specific point or list of
    points at a specific detail level.
    
    Parameters
    ----------
    poi : tuple or array of tuples
       point of interest with latitude and longitude (lat, lon)

    Returns
    -------
    np.array
        tile identifiers
    '''

    # First calculate pixelX and pixelY
    pois = np.transpose(pois)
    latitude_raw = pois[0]

    # Clip latitude to avoids a singularity at the poles, and force projected map to be square
    latitude = np.where(latitude_raw > 85.05112878, 85.05112878, np.where(latitude_raw < -85.05112878, -85.05112878, latitude_raw))

    longitude = pois[1]
    sinLatitude = np.sin(latitude * np.pi/180)

    # map size
    mapsize = np.power(2, con.LEVEL_DETAIL)

    # Caculate coordinates of point with respect to tile coord system.
    pixelX = ((longitude + 180) / 360) *  256 * np.power(2, con.LEVEL_DETAIL)
    pixelY = (0.5 - np.log((1 + sinLatitude) / (1 - sinLatitude)) / (4 * np.pi)) *  256 * np.power(2, con.LEVEL_DETAIL)

    # Calculate the tile XY coordinates
    tileX = np.floor(pixelX / 256).astype('int')
    tileY = np.floor(pixelY / 256).astype('int')
    
    quadkey = np.asarray([tileXY_to_quadkey(pX, pY, con.LEVEL_DETAIL) for pX, pY in zip(tileX, tileY)])

    # Calculate coordinates
    tilePixelX = tileX * 256
    tilePixelY = tileY * 256
    mapsize = 256 * np.power(2, con.LEVEL_DETAIL)
    x = np.where(tilePixelX < 0, 0, np.where(tilePixelX > (mapsize - 1), (mapsize - 1), tilePixelX)) / mapsize
    x = x - 0.5
    y = np.where(tilePixelY < 0, 0, np.where(tilePixelY > (mapsize - 1), (mapsize - 1), tilePixelY)) / mapsize
    y = 0.5 - y

    latitude = 90 - 360 * np.arctan(np.exp(-y * 2 * np.pi)) / np.pi 
    longitude = 360 * x


    return latitude, longitude, quadkey
    

def tileXY_to_quadkey(tileX : int, tileY : int, 
                      level : int = con.LEVEL_DETAIL) -> str:
    
    """
    Method to transform Bing Map Tile coordinates into its quadkey. Tile 
    coordinates are taken to binary and interleaved by applying interleave(Y, X).

    The convention is that bits from first argument go into even indices and bits from
    second argument go into odd indices. 

    Parameters
    ----------
    tileX : int
        tile X coordinate.
    tileY : int
        tile Y coordinate.
    level: int
        level of detail. Defaults to constant value. 

    Returns
    -------
    str
        quadkey identifier. The length of a quadkey equals the level of detail of 
        the corresponding tile. The quadkey of any tile starts with the quadkey of its parent tile.

    """

    quadkey_b = ''
    tileX_b = format(tileX, 'b')
    tileY_b = format(tileY, 'b')
    # add leading zeroes to match lenght for interleaving
    def trailing_zeroes(string, length):
        final_string = string
        for i in range(length - len(string)):
            final_string = "0" + final_string
        return final_string
    
    tileX_b = tileX_b if len(tileX_b) == level else trailing_zeroes(tileX_b, level)
    tileY_b = tileY_b if len(tileY_b) == level else trailing_zeroes(tileY_b, level)

    for i in range(level):   
        quadkey_b += tileY_b[i]
        quadkey_b += tileX_b[i]

    # bring quadkey to base 4  
    quadkey = ''
    while quadkey_b != '':
        quadkey += str(int(quadkey_b[:2]) % 4)
        quadkey_b = quadkey_b[2:]   

    return quadkey


def to_fb_date(t : datetime) -> datetime:
    """
    Method to bring datetime to fb reporting format (i.e. 8hr intervals, 
    at 00:00, 08:00 and 16:00)

    Parameters
    ----------
    t : datetime
        date to be transformed

    Returns
    -------
    datetime
        datetime in fb interval
    """
    fb_date = t.replace(second=0, microsecond=0, minute=0, hour=0)
    if t.hour >= 16 and t.hour < 24:
        fb_date = t.replace(second=0, microsecond=0, minute=0, hour=16)
    elif t.hour >= 0 and t.hour < 8:
        fb_date = t.replace(second=0, microsecond=0, minute=0, hour=0)
    elif t.hour >= 8 and t.hour < 16:
        fb_date = t.replace(second=0, microsecond=0, minute=0, hour=8)

    return fb_date
