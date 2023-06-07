

import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.metrics.pairwise import haversine_distances
from math import radians
import networkx as nx

from simulator.population_networks.abstract.population_network import PopulationNetwork
import simulator.constants as con
import simulator.utils.geometric as geo_fun
import simulator.utils.cache as cf
import os

from shapely.geometry import Point, LineString

import pickle
import random


class PopulationNetworkFromHDX(PopulationNetwork):
    """
    Class for constructing a population network from the HDX data.
    """


    def __init__(self, 
                id : str,
                name : str,
                world_pop_density_file : str,
                populated_places_folder : str,
                road_lines_folder : str,
                building_polygons_folder : str):
        '''
        Constructor method

        Parameters
        ----------
        date : datetime
            Date corresponding to the Population Network.
        id : str
            Id of the Population Network
        name : str
            Name of the Population Network
        world_pop_density_file : str
            Location of the World Population .csv file downloaded from HDX.
            Example: https://data.humdata.org/dataset/worldpop-population-density-for-costa-rica 
        populated_places_folder : str
            Location of the folder containing the OSM populated places shapefile. 
            Example: https://data.humdata.org/dataset/hotosm_cri_populated_places
        road_lines_folder : str
            Location of the folder containing the OSM road line strings shapefile. 
            Example: https://data.humdata.org/dataset/hotosm_cri_roads
        building_polygons_folder : str
            Location of the folder containing the OSM building polygons shapefile. 
            Example: https://data.humdata.org/dataset/hotosm_cri_buildings
         
        
        
        '''
        super().__init__()

        self.__id = id
        self.__name = name
        self.world_pop_density_file = world_pop_density_file
        self.populated_places_folder = populated_places_folder
        self.road_lines_folder = road_lines_folder
        self.building_polygons_folder = building_polygons_folder

        # Edges and Nodes
        self.__nodes = None
        self.__edges = None

        # Sampling
        self.__node_samples = None
        self.__edges_samples = None


        


    # Attributes
    # ----------
    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def nodes(self) -> gpd.GeoDataFrame:
        # Checks if None
        if self.__nodes is None:
            # Tries loading from cache
            self.__nodes = self.get_nodes_from_cache()

            if self.__nodes is None:
                self.build() # Builds if no cache is found

        return self.__nodes

    @property
    def edges(self) -> pd.DataFrame:
        if self.__edges is None:
            # Tries loading from cache
            self.__edges = self.get_edges_from_cache()

            if self.__edges is None:
                self.build()            

        return self.__edges  

    @property   
    def connective_infrastructure(self) -> gpd.GeoDataFrame:
        return self.__edges    



    # Methods
    # ------- 
    def update_flow(self, force : np.array):
        """
        Given an array of forces excerted on the nodes of the network, the network updates
        itself to account for the given force.

        Parameters
        ----------
        force : np.array
            an array of 2D force vectors as returned by the point_force method of 
            a DisasterDistribution.
        """
        return NotImplemented


    def sample_from_node(self, node_id : str, num_points : int = 1):
        
        if self.__node_samples is None:
            self.__node_samples = self.get_node_samples_from_cache()

            if self.__node_samples is None:
                self.build() # Builds if no cache is found

        return self.__node_samples.loc[node_id,[con.LON, con.LAT]].sample(num_points, replace = True)


    def sample_from_edge(self, edge_id : str, num_points : int = 1):
        if self.__edges_samples is None:
            self.__edges_samples = self.get_edge_samples_from_cache()

            if self.__edges_samples is None:
                self.build() # Builds if no cache is found

        
        t = self.__edges_samples.loc[[edge_id]*num_points]
        vals = np.random.rand(num_points)
        t[con.LON] = t[con.LON_X]*vals + t[con.LON_Y]*(1-vals)
        t[con.LAT] = t[con.LAT_X]*vals + t[con.LAT_Y]*(1-vals)

        return(t[[con.LON, con.LAT]])



    def sample(self, state_0 : gpd.GeoDataFrame = gpd.GeoDataFrame(), 
               accuracy : bool = False) -> gpd.GeoDataFrame:
        """
        The main method for the mobility simulation. Returns a mobility dataset for the 
        given network. It must contain at least a geometry (i.e. Point, Polygon), a 
        device count, and a datetime. Optionally returns accuracy.

        The sampling should be mediated by 
            1. Node locations
            2. Population per node
            3. Distribution of population
            4. Connectivity

        Parameters
        ----------
        state_0 : gpd.GeoDataFrame
            previous sample to ensure continuity. If empty, generates a random one. 
        accuracy : bool
            indicates if accuracy must be simulated.

        Returns
        ----------
        geopandas.GeoDataFrame 
            Index:
                RangeIndex
            Columns:
                Name: date, dtype: datetime64[ns]
                Name: Geometry, dtype: geometry
                Name: count, dtype: int64
                Name: accuracy, dtype: float64 (optional)

        """

        return NotImplemented


    def build(self):
        '''
        Method that constructs the population network and builds its necessary attributes.
        Also this method saves the components to avoid recomputing
        '''

        print("Builds")
        print("-------")
        print("")
        # Nodes
        # ----------

        print("Loads Nodes")
        # Checks for Cache
        if self.__nodes is None:
            self.__nodes = self.get_nodes_from_cache()
        
        # If not existent, builds it
        if self.__nodes is None:

            print("   No nodes found in Cache. Building from scratch")

            # Density
            world_pop_density = pd.read_csv(self.world_pop_density_file)
            world_pop_density = gpd.GeoDataFrame(world_pop_density, geometry=gpd.points_from_xy(world_pop_density.X, world_pop_density.Y), crs=con.USUAL_PROJECTION)

            # Populated Places
            populated_places = gpd.read_file(self.populated_places_folder)

            # Drops places without name
            populated_places = populated_places.dropna(subset = "name").reset_index(drop = True)

            # Uses Haversine Distance
            # (A lot faster than geopandas.distance)
            world_pop_density["lon_rad"] = world_pop_density.geometry.x.apply(lambda v : radians(v))
            world_pop_density["lat_rad"] = world_pop_density.geometry.y.apply(lambda v : radians(v))

            populated_places["lon_rad"] = populated_places.geometry.x.apply(lambda v : radians(v))
            populated_places["lat_rad"] = populated_places.geometry.y.apply(lambda v : radians(v))

            # Extracts closest city
            closest_city = world_pop_density.apply(lambda row : np.argmin(haversine_distances(populated_places[["lat_rad", "lon_rad"]], [[row["lat_rad"], row["lon_rad"]]])[:,0]), axis = 1)

            # Groups, sums and assigns
            world_pop_density["city"] = closest_city
            population = world_pop_density[["Z","city"]].groupby("city").sum()


            # Sets Columns
            populated_places[con.LAT] = populated_places.geometry.y
            populated_places[con.LON] = populated_places.geometry.x                       
            populated_places[con.ID] = populated_places.apply(lambda row : f"{row['name']}_{row.name}", axis = 1)
            populated_places[con.POPULATION] = population.round()

            # Fills with min population
            populated_places[con.POPULATION].fillna(con.MIN_POPULATION, inplace= True)


            # Sets the minimum geometry of each populated location
            populated_places[con.GEOMETRY] = populated_places[con.GEOMETRY].to_crs(con.MANIPULATION_PROJECTION)
            populated_places[con.GEOMETRY] = populated_places[con.GEOMETRY].buffer(con.MIN_CITY_RADIUS_KM*1000).simplify(con.MIN_CITY_RADIUS_KM*1000)
            populated_places[con.GEOMETRY] = populated_places[con.GEOMETRY].to_crs(con.USUAL_PROJECTION)

            # Adds buildings where they exist
            buildings = gpd.read_file(self.building_polygons_folder) 

            buildings[con.GEOMETRY] = buildings[con.GEOMETRY].to_crs(con.MANIPULATION_PROJECTION).buffer(con.MIN_BUILDING_RADIUS_KM*1000).simplify(con.MIN_BUILDING_RADIUS_KM*1000)

            # Uses Haversine Distance
            # (A lot faster than geopandas.distance)
            buildings["lon_rad"] = buildings.geometry.centroid.to_crs(con.USUAL_PROJECTION).x.apply(lambda v : radians(v))
            buildings["lat_rad"] = buildings.geometry.centroid.to_crs(con.USUAL_PROJECTION).y.apply(lambda v : radians(v))

            buildings[con.GEOMETRY] = buildings[con.GEOMETRY].to_crs(con.USUAL_PROJECTION)

            # Extracts closest city
            closest_city = buildings.apply(lambda row : np.argmin(haversine_distances(populated_places[["lat_rad", "lon_rad"]], [[row["lat_rad"], row["lon_rad"]]])[:,0]), axis = 1)

            # Groups,dissolves and drops NAs
            buildings["city"] = closest_city
            buildings = buildings[["city", con.GEOMETRY]].dissolve(by = "city").dropna()

            # Sets the geometry
            populated_places.loc[populated_places.index.isin(buildings.index), con.GEOMETRY] = buildings[con.GEOMETRY]


            # Assigns
            self.__nodes = populated_places[[con.ID, con.GEOMETRY, con.LAT, con.LON, con.POPULATION]].copy()
            self.__nodes.index = self.__nodes[con.ID]

            # Saves
            print("   Saving")
            self.save_nodes_to_cache(self.__nodes)


        print("")

        # Node Samples
        # -----------------

        print("Load Node Samples")
        if self.__node_samples is None:
            self.__node_samples = self.get_node_samples_from_cache()

        if self.__node_samples is None:

            print("   No node samples found in Cache. Building from scratch")

            # Nodes            
            nodes = self.__nodes

            sample_points = geo_fun.extract_samples_from_geo_frame(geo_frame = nodes, 
                                                                    sample_amount = nodes[con.POPULATION].values,
                                                                    search_unit = 0.0018, # 200m in the equator
                                                                    initial_sample_size = 100,
                                                                    sample_step = 0.1,
                                                                    print_iteration_progress = False,
                                                                    percentage_print = 0.25)


            print("   Finished Sampling")
            print(f"   Total Samples: {sample_points.shape[0]}")

            self.__node_samples = sample_points

            # Saves
            print("   Saving")
            self.save_node_samples(self.__node_samples)


        print("")

        # Edges
        # -----------------

        print("Loads Edges")

        # Checks for Cache
        if self.__edges is None:
            self.__edges = self.get_edges_from_cache()
        
        if self.__edges is None:

            print("   No edges found in Cache. Building from scratch")

            # Nodes            
            nodes = self.__nodes
                        
            # Modified Local Sensitive Hashing
            # Extracts City Centers
            city_centers = geo_fun.extract_city_centers_from_nodes(nodes)

            # Projects to manipulation
            city_centers[con.GEOMETRY] = city_centers[con.GEOMETRY].to_crs(con.MANIPULATION_PROJECTION) 
            city_centers["x"] = city_centers[con.GEOMETRY].x
            city_centers["y"] = city_centers[con.GEOMETRY].y


            # Extracts possible neighbors
            dist_meters = con.MAX_DISTANCE_BETWEEN_ADJACENT_CITIES_KM*1000

            dfs = []
            for _, row in city_centers.iterrows():
                filtered = city_centers[(np.abs(city_centers.x - row.x) < dist_meters) & (np.abs(city_centers.y - row.y) < dist_meters)]

                dfs.append(pd.DataFrame({con.NODE_ID1 : row[con.ID], con.NODE_ID2 : filtered[con.ID]}))


            edges = pd.concat(dfs, ignore_index=True)
            edges = edges[edges[con.NODE_ID1] > edges[con.NODE_ID2]]


            # Corrects distance
            nodes.index = nodes[con.ID]

            edges = edges.merge(nodes[[con.ID, con.LON, con.LAT]].rename(columns={con.ID : con.NODE_ID1})).rename(columns = {con.LAT : "lat_x", con.LON : "lon_x"})
            edges = edges.merge(nodes[[con.ID, con.LON, con.LAT]].rename(columns={con.ID : con.NODE_ID2})).rename(columns = {con.LAT : "lat_y", con.LON : "lon_y"})

            edges["lat_x"] = edges["lat_x"].apply(radians)
            edges["lon_x"] = edges["lon_x"].apply(radians)
            edges["lat_y"] = edges["lat_y"].apply(radians)
            edges["lon_y"] = edges["lon_y"].apply(radians)

            edges[con.DISTANCE] = edges.apply(lambda row: geo_fun.haversine(row.lon_x, row.lat_x, row.lon_y, row.lat_y, True), axis = 1)

            # Filters by actual distance
            edges = edges[edges[con.DISTANCE] < con.MAX_DISTANCE_BETWEEN_ADJACENT_CITIES_KM*1000]

            # Checks if graph is connected
            graph = nx.Graph()
            graph.add_nodes_from(nodes[con.ID].values)
            graph.add_edges_from(edges.apply(lambda row: (row[con.NODE_ID1], row[con.NODE_ID2]), axis = 1).values)
            components = list(nx.connected_components(graph))

            print(f"      Total Edges: {edges.shape[0]}")
            print(f"      Connected Components: {len(components)}")


            # Recovers the lat and lot
            edges = edges[[con.NODE_ID1, con.NODE_ID2, con.DISTANCE]].copy()
            edges = edges.merge(nodes[[con.ID, con.LON, con.LAT]].rename(columns={con.ID : con.NODE_ID1})).rename(columns = {con.LAT : "lat_x", con.LON : "lon_x"})
            edges = edges.merge(nodes[[con.ID, con.LON, con.LAT]].rename(columns={con.ID : con.NODE_ID2})).rename(columns = {con.LAT : "lat_y", con.LON : "lon_y"})


            # Creates the line string geometry
            edges = gpd.GeoDataFrame( edges, geometry = edges.apply(lambda row : LineString([Point(row.lon_x, row.lat_x), Point(row.lon_y, row.lat_y)]) , axis = 1), crs = con.USUAL_PROJECTION)

            # Constant Value
            edges[con.VALUE] = 1

            # Converts to GeoDataFrame
            edges = edges[[con.NODE_ID1, con.NODE_ID2, con.VALUE, con.GEOMETRY]].copy()

            # Assigns
            self.__edges = edges

            print("   Saving")
            # Saves
            self.save_edges_to_cache(self.__edges)

        print("")

        print("Load Edge Samples")
        if self.__edges_samples is None:
            self.__edges_samples = self.get_edge_samples_from_cache()

        if self.__edges_samples is None:

            print("   No edge samples found in Cache. Building from scratch")

            # Nodes            
            edges = self.__edges

            # Gets the coordinates
            edge_sample_constructor = edges[[con.NODE_ID1,con.NODE_ID2,con.GEOMETRY]].copy()
            coords = edge_sample_constructor[con.GEOMETRY].apply(lambda geo : geo.coords).values


            edge_sample_constructor[con.LON_X] = [coor[0][0] for coor in coords]
            edge_sample_constructor[con.LAT_X] = [coor[0][1] for coor in coords]
            edge_sample_constructor[con.LON_Y] = [coor[1][0] for coor in coords]
            edge_sample_constructor[con.LAT_Y] = [coor[1][1] for coor in coords]

            edge_sample_constructor = edge_sample_constructor[[con.NODE_ID1,con.NODE_ID2,con.LON_X, con.LAT_X, con.LON_Y, con.LAT_Y]].copy()

            # Switches
            edge_sample_constructor = pd.concat((edge_sample_constructor, edge_sample_constructor.rename(columns = {con.NODE_ID1:con.NODE_ID2, con.NODE_ID2 : con.NODE_ID1})), ignore_index = True)

            edge_sample_constructor.index = pd.MultiIndex.from_tuples(edge_sample_constructor.apply(lambda row: (row[con.NODE_ID1], row[con.NODE_ID2]), axis = 1), names=[con.NODE_ID1, con.NODE_ID2])

            self.__edges_samples = edge_sample_constructor

            # Saves
            print("   Saving")
            self.save_edge_samples(self.__edges_samples)

 


    # Extra Cache Methods
    # -------------------
    def build_node_samples_id(self):
        '''Builds the unique ID for the nodes samples in Cache'''
        return(f"{self.id}-nodes-samples.csv")


    def build_edge_samples_id(self):
        '''Builds the unique ID for the edges samples in Cache'''
        return(f"{self.id}-edges-samples.csv")        

    def save_node_samples(self, node_samples):
        
        filepath = cf.get_cache_file(self.build_node_samples_id())

        # Drops the index columns (which is the same as the id column). Will be restores when loaded
        node_samples.to_csv(filepath, index = False)

    def get_node_samples_from_cache(self, include_message= True):
        # Gets the complete path
        filepath = cf.get_cache_file(self.build_node_samples_id())

        if not os.path.exists(filepath):
            return None

        if include_message:
            print("   Reading node samples from Cache")

        node_samples = pd.read_csv(filepath)

        # Sets Index
        node_samples.index = node_samples[con.ID]

        return node_samples 


    def get_edge_samples_from_cache(self, include_message= True):
        # Gets the complete path
        filepath = cf.get_cache_file(self.build_edge_samples_id())

        if not os.path.exists(filepath):
            return None
        
        if include_message:
            print("   Reading edge samples from Cache")

        edge_samples = pd.read_csv(filepath)

        # Sets the index 
        edge_samples.index = pd.MultiIndex.from_tuples(edge_samples.apply(lambda row: (row[con.NODE_ID1], row[con.NODE_ID2]), axis = 1), names=[con.NODE_ID1, con.NODE_ID2])

        return edge_samples

    def save_edge_samples(self, edge_samples):
        
        filepath = cf.get_cache_file(self.build_edge_samples_id())

        # Drops the index columns (which is the same as the node_id1 and node_id2 columns). Will be restores when loaded
        edge_samples.to_csv(filepath, index = False)




