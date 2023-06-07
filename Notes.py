from os.path import join
import simulator.constants as con
import simulator.utils.geometric as geo_fun
import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np

world_pop_density_file = join(con.DATA_FOLDER,"costa_rica-panama/pd_2020_1km_ASCII_XYZ.csv")
populated_places_folder = join(con.DATA_FOLDER,"costa_rica-panama/hotosm_populated_places_points_shp")
road_lines_folder = join(con.DATA_FOLDER,"costa_rica-panama/hotosm_roads_lines_shp")
building_polygons_folder = join(con.DATA_FOLDER,"costa_rica-panama/hotosm_buildings_polygons_shp")


search_unit = 0.0018 # 200m in the equator

# Reads the file
roads = gpd.read_file(road_lines_folder)
roads = roads[["highway", con.GEOMETRY]].copy()


# Creates Intersection
intersection = roads.sjoin(roads)
# Renames
intersection = intersection.reset_index().rename(columns = {"index" : "index_left"})

# Filters out self intersections
intersection = intersection[intersection.index_left != intersection.index_right]
# Filters out roads without same type
intersection = intersection[intersection.highway_left == intersection.highway_right]


# Create an undirected graph and finds connected components to merge
graph = nx.Graph()
graph.add_nodes_from(roads.index.values)
graph.add_edges_from(intersection.apply(lambda row: (row.index_left, row.index_right), axis = 1).values)
components = list(nx.connected_components(graph))

# Assigns the groups / components
i = 0
dfs = []
for comp in components:
    dfs.append(pd.DataFrame({"group" : i},index = list(comp)))
    i += 1

groups = pd.concat(dfs)
roads["group"] = groups['group']

# Dissolves
roads = roads.dissolve(by="group").reset_index(drop = True)

# Adds population
roads[con.ROAD_LENGTH] = roads[con.GEOMETRY].to_crs(con.MANIPULATION_PROJECTION).length/1000
roads[con.POPULATION] = roads[con.ROAD_LENGTH].apply(lambda l : min(10,int(np.round(l*con.ROAD_SAMPLE_DENSITY_BY_KM))))


# Explodes geometry to search the border
exploded_geometries = roads.explode(index_parts=False)
exploded_geometries = exploded_geometries[[con.GEOMETRY]].copy()

# Construct Segments
print("Constructs Segment")

dfs = []
for ind, row in exploded_geometries.iterrows():
    coords = np.array(exploded_geometries.iloc[0].geometry.coords)

    dfs.append(pd.DataFrame({"lon_x" : [t[0] for t in coords[:-1]], 
                            "lat_x" : [t[1] for t in coords[:-1]],
                            "lon_y" : [t[0] for t in coords[1:]], 
                            "lat_y" : [t[1] for t in coords[1:]]}, 
                index = [ind]*(len(coords)-1)))

segment_points = pd.concat(dfs)

print_iteration_progress = True
percentage_print = 0.1

dfs = []

batch = int(np.ceil(roads.shape[0]*percentage_print))


for ind in np.unique(segment_points.index.values):

    if print_iteration_progress and len(dfs) % batch == 0:
        print(f"         Progress: {np.round(100*len(dfs)/roads.shape[0])}%")

    df = segment_points.loc[ind]

    # Extracts Sample size
    sample_size = roads.loc[df.index.values[0], con.POPULATION]

    selected = df.sample(sample_size, replace = True)

    vals = np.random.rand(selected.shape[0])

    selected[con.LON] = selected["lon_x"]*vals + selected["lon_y"]*(1-vals) + np.random.uniform(-1*search_unit, search_unit, size = selected.shape[0])
    selected[con.LAT] = selected["lat_x"]*vals + selected["lat_y"]*(1-vals) + np.random.uniform(-1*search_unit, search_unit, size = selected.shape[0])

    dfs.append(selected[[con.LON, con.LAT]])

    
sample_points_by_road = pd.concat(dfs)
