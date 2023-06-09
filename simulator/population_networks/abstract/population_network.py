
import datetime
import numpy as np
import abc
import geopandas as gpd
import pandas as pd
import os

import simulator.constants as con
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
        Given an array of forces exerted on the nodes of the network, the network updates
        itself to account for the given force.

        Parameters
        ----------
        force : np.array
            an array of float intensities as returned by the DisasterDistribution.
        """
        
        return NotImplemented

    def sample_from_node(self, node_id : str, num_points : int = 1):
        '''
        Method that returns a sample point from the corresponding node

        Parameters
        ----------
        node_id : str
            The node id

        Returns
        -------
        pd.DataFrame
            DataFrame  with random lon and lat tuples from the node 
        '''

        arr = self.nodes.loc[[node_id]].sample_points(num_points).values
        return pd.DataFrame({con.LON : np.apply_along_axis(lambda p: p.x, 0, arr),
                             con.LAT : np.apply_along_axis(lambda p: p.y, 0, arr)})
  

    def sample_from_edge(self, edge_id : str, num_points : int = 1):
        '''
        Method that returns a sample point from the corresponding edge

        Parameters
        ----------
        edge_id : str
            The edge id

        Returns
        -------
        pd.DataFrame
            DataFrame  with random lon and lat tuples from the edge 
        '''

        arr = self.edges.loc[[edge_id]].sample_points(num_points).values
        return pd.DataFrame({con.LON : np.apply_along_axis(lambda p: p.x, 0, arr),
                        con.LAT : np.apply_along_axis(lambda p: p.y, 0, arr)})   


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
                Name: date, dtype: datetime64[ns]. Date of the sample
                Name: node_id, dtype: str. Nearest Node in the population to the device
                Name: lon, dtype: float. Longitude of the device.
                Name: lat, dtype: float. Latitude of the device 
                Name: accuracy, dtype: float64 (optional). Accuracy of the sample

        """

        return NotImplemented


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

        nodes = gpd.read_file(filepath)
        # Sets Index
        nodes.index = nodes[con.ID]

        return nodes 

    def save_nodes_to_cache(self, nodes : gpd.GeoDataFrame):
        # Gets the complete path
        filepath = cf.get_cache_file(self.build_nodes_id())
        
        # Drops the index columns (which is the same as the id column). Will be restores when loaded
        nodes.reset_index(drop=True).to_file(filepath)


    def get_edges_from_cache(self, include_message = True):
        # Gets the complete path
        filepath = cf.get_cache_file(self.build_edges_id())

        if not os.path.exists(filepath):
            return None

        if include_message:
            print("   Reading edges from Cache")

        edges = gpd.read_file(filepath)
        # Sets the index 
        edges.index = pd.MultiIndex.from_tuples(edges.apply(lambda row: (row[con.NODE_ID1], row[con.NODE_ID2]), axis = 1), names=[con.NODE_ID1, con.NODE_ID2])

        return edges

    def save_edges_to_cache(self, edges : gpd.GeoDataFrame):
        # Gets the complete path
        filepath = cf.get_cache_file(self.build_edges_id())

        # Drops the index columns (which is the same as the node_id1 and node_id2 column). Will be restores when loaded
        edges.reset_index(drop=True).to_file(filepath)
