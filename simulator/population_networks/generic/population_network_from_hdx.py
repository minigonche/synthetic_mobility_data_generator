

import datetime
import numpy as np
import abc
import geopandas as gpd
from simulator.population_networks.abstract.population_network import PopulationNetwork

class PopulationNetworkFromHDX(PopulationNetwork):
    """
    # Class for constructing a population network from the HDX data.
    """


    def __init__(self, 
                date : datetime,
                id : str,
                name : str,
                world_pop_density : str,
                populated_places : str,
                road_lines : str,
                building_polygons : str):
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
        world_pop_density : str
            Location of the World Population .csv file downloaded from HDX.
            Example: https://data.humdata.org/dataset/worldpop-population-density-for-costa-rica 
        populated_places : str
            Location of the folder containing the OSM populated places shapefile. 
            Example: https://data.humdata.org/dataset/hotosm_cri_populated_places
        road_lines : str
            Location of the folder containing the OSM road line strings shapefile. 
            Example: https://data.humdata.org/dataset/hotosm_cri_roads
        building_polygons : str
            Location of the folder containing the OSM building polygons shapefile. 
            Example: https://data.humdata.org/dataset/hotosm_cri_buildings
         
        
        
        '''
        self.__date = date
        self.__id = id
        self.__name = name
        self.world_pop_density = world_pop_density
        self.populated_places = populated_places
        self.road_lines = road_lines
        self.building_polygons = building_polygons


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
        '''
        Nodes of the network represented as a gpd.GeoPandas
        Structure:
            Index:
                RangeIndex
            Columns:
                Name: id, dtype: str
                Name: geometry, dtype: geometry
                Name: lat, dtype: float64
                Name: lon, dtype: float64
                Name: population, dtype: int64
        '''
        return NotImplemented

    @abc.abstractproperty
    def edges(self) -> np.array:
        '''
        2D array of conectivity between PopulationNodes. This is equivalent to the 
        weighted adjacency matrix of the network.    
        '''
        return NotImplemented     


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