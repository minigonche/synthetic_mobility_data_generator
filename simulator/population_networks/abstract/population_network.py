
import datetime
import numpy as np
import abc
import geopandas as gpd
import pandas as pd
import os

import simulator.utils.cache as cf

class PopulationNetwork(abc.ABC):
    """
    A class used to represent the population network.
    """


    # Attributes
    # ---------
    @property
    @abc.abstractmethod
    def id(self) -> str:
        '''
        Unique identifier for the Population Network
        '''
        return NotImplemented

    @property
    @abc.abstractmethod
    def name(self) -> str:
        '''
        Human readable name for the Population Network
        '''
        return NotImplemented

    @property
    @abc.abstractmethod
    def nodes(self) -> gpd.GeoDataFrame:
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

    @property
    @abc.abstractmethod
    def edges(self) -> pd.DataFrame:
        '''
        Pandas DataFrame with the edges. All edges are symmetric. Missing edges will have a value of 0
        Columns:
            node_id1 : id of the first node, dtype: str
            node_id2 : id of the second node, dtype: str
            value : connectivity value, dtype : float
        '''
        return NotImplemented     


    @property
    @abc.abstractmethod
    def connective_infrastructure(self) -> gpd.GeoDataFrame:
        '''
        Description of road or fluvial infrastructure that connects different nodes.
        This will be used to simulate people on the connective infrastructure.
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


    # Cache Methods
    # ----------------------
    def build_nodes_id(self):
        '''Builds the unique ID for the nodes of the given population network in Cache'''
        return(f"{self.id}-nodes")

    def build_edges_id(self):
        '''Builds the unique ID for the edges of the given population network in Cache'''
        return(f"{self.id}-edges")

    def get_nodes_from_cache(self, include_message = True):
        # Gets the complete path
        filepath = cf.get_cache_file(self.build_nodes_id())

        if not os.path.exists(filepath):
            return None

        if include_message:
            print("   Reading nodes from Cache")

        return gpd.read_file(filepath)

    def save_nodes_to_cache(self, nodes : gpd.GeoDataFrame):
        # Gets the complete path
        filepath = cf.get_cache_file(self.build_nodes_id())

        nodes.to_file(filepath)


    def get_edges_from_cache(self, include_message = True):
        # Gets the complete path
        filepath = cf.get_cache_file(self.build_edges_id())

        if not os.path.exists(filepath):
            return None

        if include_message:
            print("   Reading edges from Cache")

        return gpd.read_file(filepath)

    def save_edges_to_cache(self, edges : gpd.GeoDataFrame):
        # Gets the complete path
        filepath = cf.get_cache_file(self.build_edges_id())

        edges.to_file(filepath)