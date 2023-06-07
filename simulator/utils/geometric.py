# Geometric Functions
import sys
import datetime
import numpy as np
from shapely.geometry import Polygon, Point
import simulator.constants as con
import geopandas as gpd
from math import radians, sin, cos, asin, sqrt

# local imports
import simulator.utils.errors as errors


def trim_road(geometry, lon_1, lat_1, lon_2, lat_2):
    '''
    Method that trims the given geometry to the endpoints given.
    This method is design to adjust road line strings so that they don't exceed the given endpoints. 
    '''
    # Width of square in kilometer
    kms_width = 1000

    # Extract Normal Vector
    if lon_1 == lon_2:
        N1 = 1
        N2 = 0
    else:
        N2 = -1
        N1 = (lat_2 - lat_1) / (lon_2 - lon_1)

    # Normalizes
    length = np.sqrt(N1**2+N2**2)
    N1 /= length
    N2 /= length

    # Multiplies by size
    N1 *= kms_width/111.32 # 111.32 km is one longitude/latitude near the equator
    N2 *= kms_width/111.32 # 111.32 km is one longitude/latitude near the equator

    # Location 1 point in perpendicular line
    l1_1 = (lon_1 + N1, lat_1 + N2)
    l1_2 = (lon_1 - N1, lat_1 - N2)

    # Location 2 point in perpendicular line
    l2_1 = (lon_2 + N1, lat_2 + N2)
    l2_2 = (lon_2 - N1, lat_2 - N2)

    points = [l1_1, l1_2, l2_2, l2_1]

    # Create a polygon
    polygon = Polygon(points)

    # Create a GeoDataFrame with the polygon
    return geometry.intersection(polygon)


def extract_city_centers_from_nodes(nodes):
    '''
    Method that returns the city center of the nodes in a GeoPandasDataFrame
    '''
    return gpd.GeoDataFrame( nodes[con.ID], geometry = nodes.apply(lambda row: Point(row[con.LON],row[con.LAT]), axis = 1), crs = con.USUAL_PROJECTION)


def haversine(lon1, lat1, lon2, lat2, radians = False):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    Taken from: https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    """
    # convert decimal degrees to radians 
    if not radians:
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371*1000 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

def centroid(geo_data_file : str, ids : int) -> tuple:
    try:
        gdf = gpd.read_file(geo_data_file)
    except Exception as e:
        errors.write_error(sys.argv[0], e, 
                                "error", datetime.now())
        raise e

    gdf = gdf.loc[gdf[con.ID].isin(ids)]
    gdf["cenotroids"] = gdf[con.GEOMETRY].centroid

    return gdf["cenotroids"].tolist()