

import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.metrics.pairwise import haversine_distances
from math import radians
import networkx as nx

from simulator.population_networks.abstract.population_network import PopulationNetwork
import simulator.constants as con
import simulator.utils.geometric as geo_fun

from shapely.geometry import Point


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
            a DsasterDistribution.
        """
        return NotImplemented



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

        # Nodes
        # ----------

        # Checks for Cache
        self.__nodes = self.get_nodes_from_cache()
        
        # If not existent, builds it
        if self.__nodes is None:

            print("No nodes found in Cache. Building from scratch")

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
            populated_places[con.ID] = populated_places.apply(lambda row : f"{row['name']} - {row.name}", axis = 1)
            populated_places[con.POPULATION] = population.round()

            # Fills with min population
            populated_places[con.POPULATION].fillna(con.MIN_POPULATION, inplace= True)


            # Sets the minimum geometry of each populated location
            populated_places[con.GEOMETRY] = populated_places[con.GEOMETRY].to_crs(con.MANIPULATION_PROJECTION)
            populated_places[con.GEOMETRY] = populated_places[con.GEOMETRY].buffer(con.MIN_CITY_RADIUS_KM*1000)
            populated_places[con.GEOMETRY] = populated_places[con.GEOMETRY].to_crs(con.USUAL_PROJECTION)

            # Adds buildings where they exist
            buildings = gpd.read_file(self.building_polygons_folder) 

            buildings[con.GEOMETRY] = buildings[con.GEOMETRY].to_crs(con.MANIPULATION_PROJECTION).buffer(con.MIN_BUILDING_RADIUS_KM).simplify(con.MIN_BUILDING_RADIUS_KM)

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

            # Saves
            print("Saving")
            self.save_nodes_to_cache(self.__nodes)

        # Checks for Cache
        self.__edges = self.get_edges_from_cache()
        
        if self.__edges is None:

            print("No edges found in Cache. Building from scratch")


            # Reads the file
            roads = gpd.read_file(self.road_lines_folder)
            roads = roads[["highway", con.GEOMETRY]].copy()


            # Simplifies the geometry
            roads[con.GEOMETRY] = roads[con.GEOMETRY].to_crs(con.MANIPULATION_PROJECTION)
            roads[con.GEOMETRY] = roads[con.GEOMETRY].simplify(con.SIMPLIFICATION_CONSTANTS_METERS)
            roads[con.GEOMETRY] = roads[con.GEOMETRY].to_crs(con.USUAL_PROJECTION)

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

            # Extracts the city centers
            city_centers = gpd.GeoDataFrame( self.__nodes[con.ID], geometry = self.__nodes.apply(lambda row: Point(row[con.LON],row[con.LAT]), axis = 1), crs = con.USUAL_PROJECTION)

            # Converts to manipulation
            city_centers[con.GEOMETRY] = city_centers[con.GEOMETRY].to_crs(con.MANIPULATION_PROJECTION)
            roads[con.GEOMETRY] = roads[con.GEOMETRY].to_crs(con.MANIPULATION_PROJECTION)

            # Extracts Nearest
            node_to_road_mapping = city_centers.sjoin_nearest(roads)[[con.ID,"index_right"]].rename(columns = {"index_right" : "road_index"})
            
            # Converts to usual
            roads[con.GEOMETRY] = roads[con.GEOMETRY].to_crs(con.USUAL_PROJECTION)

            # Constructs edges
            dfs = []
            for r in node_to_road_mapping.road_index.unique():

                # Extracts the group
                node_group = node_to_road_mapping[node_to_road_mapping.road_index == r][[con.ID]]
                df = node_group.merge(node_group, how='cross')
                df = df[df.id_x > df.id_y].copy()
                df = df.rename(columns = {"id_x": con.NODE_ID1, "id_y": con.NODE_ID2})

                # Assigns value and geometry
                df[con.VALUE] = 1
                df[con.GEOMETRY] = roads.geometry.loc[r]

                dfs.append(df)

            self.__edges = gpd.GeoDataFrame(pd.concat(dfs, ignore_index = True), geometry = con.GEOMETRY, crs = con.USUAL_PROJECTION)

            # Trims
            new_geo = []

            percentage_print = 0.1
            print_every = int(np.floor(percentage_print*self.__edges.shape[0]))

            print("Trimming Roads") # Apply generates out of memory
            for i, edge_row in self.__edges.iterrows():

                # Selected Nodes
                sel_nodes = self.__nodes[self.__nodes.id.isin([edge_row.node_id1,edge_row.node_id2])]
                # Extracts
                node_1 = sel_nodes.iloc[0]
                node_2 = sel_nodes.iloc[1]

                # Trims
                new_geo.append(geo_fun.trim_road(edge_row.geometry, node_1.lon, node_1.lat, node_2.lon, node_2.lat))

                if i % print_every == 0:
                    print(f"   Progress: {np.round(100*i/self.__edges.shape[0])}%")

            print("Done trimming")

            self.__edges[con.GEOMETRY] = new_geo

            print("Saving")
            # Saves
            self.save_edges_to_cache(self.__edges)
 



