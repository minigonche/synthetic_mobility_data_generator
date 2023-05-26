

import datetime
import numpy as np
import abc
import pandas as pd
import geopandas as gpd
from sklearn.metrics.pairwise import haversine_distances
from math import radians

from simulator.population_networks.abstract.population_network import PopulationNetwork
import simulator.constants as con


class PopulationNetworkFromHDX(PopulationNetwork):
    """
    Class for constructing a population network from the HDX data.
    """


    def __init__(self, 
                date : datetime,
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
        self.__date = date
        self.__id = id
        self.__name = name
        self.world_pop_density_file = world_pop_density_file
        self.populated_places_folder = populated_places_folder
        self.road_lines_folder = road_lines_folder
        self.building_polygons_folder = building_polygons_folder

        


    # Attributes
    # ----------
    def date(self) -> datetime:
        return self.__date
        
    def id(self) -> str:
        return self.__id

    @abc.abstractproperty
    def name(self) -> str:
        return self.__name

    @abc.abstractproperty
    def nodes(self) -> gpd.GeoPandas:
        # Checks if None
        if self.nodes is None:
            self.build()

        return self.nodes

    @abc.abstractproperty
    def edges(self) -> pd.DataFrame:
        if self.edges is None:
            self.build()

        return self.edges  


    @abc.abstractproperty
    def connective_infrastructure(self) -> gpd.GeoPandas:
        '''
        Description of road or fluvial infrastructure that connects different nodes.
        This will be used to simulate people on the connective infrastructue.
            Index:
                RangeIndex
            Columns:
                Name: node_id1, dtype: str
                Name: node_id2, dtype: str
                Name: geometry, dtype: LineString      
        '''
        return None   



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
            previous sample to ensure continuity. If empty, generates a randome one. 
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
        self.nodes = self.__get_nodes_from_cache()
        
        # If not existent, builds it
        if self.nodes is None:


            # Density
            world_pop_density = pd.read_csv(self.world_pop_density_file)
            world_pop_density = gpd.GeoDataFrame(world_pop_density, geometry=gpd.points_from_xy(world_pop_density.X, world_pop_density.Y), crs=con.USUAL_PROJECTION)

            # Populated Places
            populated_places = gpd.read_file(self.populated_places_folder)

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


            # Forms the final Frame
            populated_places[con.ID] = populated_places.apply(lambda row : f"{row['name']} - {row.name}", axis = 1)
            populated_places[con.POPULATION] = population
            populated_places[con.LAT] = populated_places.geometry.y
            populated_places[con.LON] = populated_places.geometry.x

            # Assigns
            self.nodes = populated_places[[con.ID, con.GEOMETRY, con.LAT, con.LON, con.POPULATION]].copy()

            # Saves
            self.__save_nodes_to_cache(self.nodes)


