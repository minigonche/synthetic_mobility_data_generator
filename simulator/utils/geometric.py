# Geometric Functions
import numpy as np
from shapely.geometry import Polygon, Point
import simulator.constants as con
import geopandas as gpd
import pandas as pd
from math import radians, sin, cos, asin, sqrt

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


def extract_samples_from_geo_frame(geo_frame : gpd.GeoDataFrame, 
                                   sample_amount : np.array,
                                   search_unit,
                                   initial_sample_size = 100,
                                   sample_step = 0.2,
                                   print_iteration_progress = False,
                                   percentage_print = 0.25):
    '''
    Method that extracts samples form a geo DataFrame.
    This method was created to precompute samples for the simulation, since
    sampling from geometry is extremely inefficient. 
    '''

    # internal columns
    COUNT = "count"
    SAMPLE_AMOUNT = "__sample_amount__"
    PER = "__per__"

    # Adds Sample Amount
    geo_frame[SAMPLE_AMOUNT] = sample_amount

    # Explodes geometry to search the border
    exploded_geometries = geo_frame.explode(index_parts=False)
    exploded_geometries = exploded_geometries[[con.GEOMETRY]].copy()

    # Construct Border
    dfs = []
    for ind, row in exploded_geometries.iterrows():
        boundary = list(row.geometry.exterior.coords)
        dfs.append(pd.DataFrame({con.LON : [t[0] for t in boundary], con.LAT : [t[1] for t in boundary]}, index = [ind for _ in boundary]))

    boundary_points = pd.concat(dfs)

    # Sample point DataFrame structure
    sample_points = pd.DataFrame(columns=[con.ID, con.LON, con.LAT])


    # Progress
    progress = pd.DataFrame(columns=[con.ID, COUNT])
    progress = progress.merge(geo_frame[[con.ID, SAMPLE_AMOUNT]].reset_index(drop = True), how = "right").fillna(0)
    progress[PER] = progress[COUNT] / progress[SAMPLE_AMOUNT]

    # Filters
    progress = progress[progress[PER] < 1]

    sample_size = initial_sample_size

    print("Started Sampling")
    while progress.shape[0] > 0:

        current_progress = np.round(100*(geo_frame.shape[0] - progress.shape[0])/geo_frame.shape[0],2)
        print(f"      Min Coverage: {np.round(100*progress[PER].min(), 2)}%")
        print(f"      Constructing Samples for {progress.shape[0]} elements of {geo_frame.shape[0]} ({current_progress}%)")

        dfs = []
        batch = int(np.ceil(progress.shape[0]*percentage_print))

        sample_size = int(np.round(sample_size*(1 + sample_step)))

        print(f"      Sample Size: {sample_size}")
            
        for id, row in progress.iterrows():

            if print_iteration_progress and len(dfs) % batch == 0:
                print(f"         Progress: {np.round(100*len(dfs)/progress.shape[0])}%")

            
            # Extracts valid points
            local_sample_points = boundary_points.loc[row[con.ID]]
            if row[con.ID] in sample_points.index:
                local_sample_points = pd.concat((local_sample_points, sample_points.loc[row[con.ID],[con.LON, con.LAT]]))

            
            local_sample_points = local_sample_points.sample(sample_size, replace = True)

            # Adds Noise
            local_sample_points[con.LON] += np.random.uniform(-1*search_unit, search_unit, local_sample_points.shape[0])
            local_sample_points[con.LON] = np.round(local_sample_points[con.LON],5)

            local_sample_points[con.LAT] += np.random.uniform(-1*search_unit, search_unit, local_sample_points.shape[0])
            local_sample_points[con.LAT] = np.round(local_sample_points[con.LAT],5)
            
            local_sample_points[con.GEOMETRY] = local_sample_points.apply(lambda row: Point(row[con.LON], row[con.LAT]), axis = 1)



            dfs.append(local_sample_points)


        print("         Done")

        possible_sample_points = pd.concat(dfs, ignore_index=True)
        possible_sample_points = gpd.GeoDataFrame(possible_sample_points, geometry= con.GEOMETRY, crs = con.USUAL_PROJECTION)


        print("      Filtering")
        inter = geo_frame[[con.ID, con.GEOMETRY]].sjoin(possible_sample_points[[con.GEOMETRY]])

        final_sample_points = inter[[con.ID, "index_right"]].merge(possible_sample_points, left_on = "index_right", right_index = True)
        final_sample_points = final_sample_points[[con.ID, con.LON, con.LAT]]

        # Joins
        sample_points = pd.concat((sample_points, final_sample_points))

        # Checks threshold
        progress = pd.DataFrame(sample_points[con.ID].value_counts()).reset_index()
        progress = progress.merge(geo_frame[[con.ID, SAMPLE_AMOUNT]].reset_index(drop = True), how = "right").fillna(0)
        progress[PER] = progress[COUNT] / progress[SAMPLE_AMOUNT]

        # Cleans
        sample_points = sample_points.reset_index(drop = True)
        under = sample_points.merge(progress.loc[progress[PER] <= 1,[con.ID]])

        over = sample_points.merge(progress.loc[progress[PER] > 1,[con.ID]])
        over = over.groupby(con.ID).apply(lambda df : df.sample(int(np.round(geo_frame.loc[df[con.ID].iloc[0], SAMPLE_AMOUNT])),replace=True))
        
        sample_points = pd.concat((under, over), ignore_index = True)
        sample_points.index = sample_points[con.ID]
        

        # Sets Progress
        progress = progress[progress[PER] < 1]


    # Deletes temporal columns
    geo_frame = geo_frame.drop(SAMPLE_AMOUNT, axis = 1)
    print("   Finished Sampling")
    print(f"   Current Samples: {sample_points.shape[0]}")
        
    return sample_points


