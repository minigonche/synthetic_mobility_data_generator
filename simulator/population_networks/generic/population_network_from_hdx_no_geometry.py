

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


class PopulationNetworkFromHDXNoGeometry(PopulationNetwork):
    """
    Class for constructing a population network from the HDX data. This class does not include infrastructure 
    geometry for the nodes and for the roads, only circle polygons and straight lines respectively.
    """


    def __init__(self, 
                id : str,
                name : str,
                world_pop_density_file : str,
                populated_places_folder : str,
                min_lon : float = -np.inf,
                max_lon : float = np.inf,
                min_lat : float = -np.inf,
                max_lat  : float = np.inf):
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
        min_lon : float
            Minimum longitude for the simulation. Will discard any populated points outside the barrier. Default is -infinity
        max_lon : float
            Maximum longitude for the simulation. Will discard any populated points outside the barrier. Default is infinity
        min_lat : float
            Minimum latitude for the simulation. Will discard any populated points outside the barrier. Default is -infinity
        max_lat : float
            Maximum latitude for the simulation. Will discard any populated points outside the barrier. Default is infinity 
    
        
        '''
        super().__init__()

        self.__id = id
        self.__name = name
        self.world_pop_density_file = world_pop_density_file
        self.populated_places_folder = populated_places_folder
        self.min_lon = min_lon
        self.max_lon = max_lon
        self.min_lat = min_lat
        self.max_lat = max_lat

        # Edges and Nodes
        self.__nodes = None
        self.__edges = None


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
    def update_flow(self, force : np.array = None):
        nodes = self.nodes

        # Updates the repelling force
        nodes[con.REPELLING_FORCE] = force

        # Attractive force is population percentage
        nodes[con.ATTRACTIVE_FORCE] = nodes[con.POPULATION] / nodes[con.POPULATION].sum()
        nodes[con.ATTRACTIVE_FORCE] = nodes[con.ATTRACTIVE_FORCE]  / nodes[con.ATTRACTIVE_FORCE].max()

        if force is not None:
            # Final Force
            nodes[con.FINAL_FORCE] = nodes[con.ATTRACTIVE_FORCE] - nodes[con.REPELLING_FORCE]
        else:
            nodes[con.FINAL_FORCE] = nodes[con.ATTRACTIVE_FORCE]


    def sample(self, 
              current_state : pd.DataFrame,
              target_nodes : np.array,
              accuracy : bool = False) -> pd.DataFrame:
        """
        The main method for the mobility simulation. Returns the next position of the given devices in the current
        state, according to the target_nodes

        Parameters
        ----------
        current_state : pd.DataFrame
            Previous sample to ensure continuity. 
        target_nodes : np.array
            Array with the ids of the nodes that the devices are headed
        accuracy : bool
            indicates if accuracy must be simulated.

        Returns
        ----------
        pd.DataFrame             
            Columns:
                Name: id, dtype: int64. Device Id
                Name: node_id, dtype: str. Nearest Node in the population to the device
                Name: lon, dtype: float. Longitude of the device.
                Name: lat, dtype: float. Latitude of the device 
                Name: accuracy, dtype: float64 (optional). Accuracy of the sample

        """

        nodes = self.nodes
        
        # Creates the noise
        vals = np.random.uniform(-1,1, size = current_state.shape[0])

        noise = np.array([con.CITY_NOISE]*current_state.shape[0])
        noise[(current_state[con.NODE_ID] != target_nodes).values] = con.ROAD_NOISE
        noise *= vals

        # Updates Values
        vals = np.random.rand(current_state.shape[0])


        new_positions = current_state.copy()

        new_positions[con.NODE_ID] = target_nodes

        new_positions[con.LON] = vals*new_positions[con.LON].values + (1-vals)*nodes.loc[target_nodes, con.LON].values + noise
        new_positions[con.LAT] = vals*new_positions[con.LAT].values + (1-vals)*nodes.loc[target_nodes, con.LAT].values + noise

        return(new_positions)



    def initial_sample(self, 
                        ids : np.array) -> pd.DataFrame:
        """
        Generates the position for the given device ids

        Parameters
        ----------
        ids : np.array
            ids of the devices to be sampled
        accuracy : bool
            indicates if accuracy must be simulated.

        Returns
        ----------
        pd.DataFrame             
            Columns:
                Name: id, dtype: int64. Device Id
                Name: node_id, dtype: str. Nearest Node in the population to the device
                Name: lon, dtype: float. Longitude of the device.
                Name: lat, dtype: float. Latitude of the device 
                Name: accuracy, dtype: float64 (optional). Accuracy of the sample

        """
        nodes = self.nodes

        # Creates ID
        device_positions = pd.DataFrame({con.ID : ids})

        # All devices start at node
        device_positions[con.NODE_ID] = np.random.choice(nodes[con.ID].values, len(ids),
                    p=nodes[con.POPULATION].values / nodes[con.POPULATION].sum())

        # Samples node Lat and lon
        noise = np.random.uniform(-1,1, size=len(ids))


        device_positions[con.LON] = nodes.loc[device_positions[con.NODE_ID], con.LON].values + noise*con.CITY_NOISE
        device_positions[con.LAT] = nodes.loc[device_positions[con.NODE_ID], con.LAT].values + noise*con.CITY_NOISE

        return(device_positions)


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

            # Filters out
            original_size = world_pop_density.shape[0]
            world_pop_density = world_pop_density[(world_pop_density.X <= self.max_lon) & (world_pop_density.X >= self.min_lon)].copy()
            world_pop_density = world_pop_density[(world_pop_density.Y <= self.max_lat) & (world_pop_density.Y >= self.min_lat)].copy()

            print(f"Retained: {world_pop_density.shape[0]} ({np.round(100*world_pop_density.shape[0]/original_size,2)} %) rows of World Pop Density")

            world_pop_density = gpd.GeoDataFrame(world_pop_density, geometry=gpd.points_from_xy(world_pop_density.X, world_pop_density.Y), crs=con.USUAL_PROJECTION)


            # Populated Places
            populated_places = gpd.read_file(self.populated_places_folder)
            
            # Drops places without name
            populated_places = populated_places.dropna(subset = "name").reset_index(drop = True)

            # Filters out
            original_size = populated_places.shape[0]

            populated_places = populated_places[(populated_places.geometry.x <= self.max_lon) & (populated_places.geometry.x >= self.min_lon)].copy()
            populated_places = populated_places[(populated_places.geometry.y <= self.max_lat) & (populated_places.geometry.y >= self.min_lat)].copy()

            print(f"Retained: {populated_places.shape[0]} ({np.round(100*populated_places.shape[0]/original_size,2)} %) rows of OSM Populated Places")


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


            # Assigns
            self.__nodes = populated_places[[con.ID, con.GEOMETRY, con.LAT, con.LON, con.POPULATION]].copy()
            self.__nodes.index = self.__nodes[con.ID]

            # Saves
            print("   Saving")
            self.save_nodes_to_cache(self.__nodes)


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




