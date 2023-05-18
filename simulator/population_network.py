
import datetime
import numpy as np
from abc import ABC
import geopandas as gpd

class PopulationNetwork(ABC):
    """
    A class used to represent the population network.

    ...

    Attributes
    ----------
    nodes : gpd.GeoPandas
        nodes 
            Index:
                RangeIndex
            Columns:
                Name: id, dtype: str
                Name: geometry, dtype: geometry
                Name: lat, dtype: float64
                Name: lon, dtype: float64
                Name: population, dtype: int64
    edges : np.array
        2D array of conectivity between PopulationNodes. This is equivalent to the 
        weighted adjacency matrix of the network.
    connective_infrastructure : gpd.GeoPandas
        Description of road or fluvial infrastructure that connects different nodes.
        This will be used to simulate people on the connective infrastructue.
            Index:
                RangeIndex
            Columns:
                Name: node_id1, dtype: str
                Name: node_id2, dtype: str
                Name: geometry, dtype: LineString

    date : datetime
        date corresponding to this network.

    Methods
    ------- 
    update_flow()
        update the network based on an array of forces.

    sample()
        generate points in space that simulate the a mobility dataset for the 
        given network.
    """

    def __init__(self, date : datetime, nodes : np.array = np.empty, 
                 edges : np.array = np.empty, connective_infrastructure : gpd.GeoPandas = gpd.GeoPandas()):
        """
        Parameters
        ----------
        date : datetime
            date corresponding to this network.
        nodes : np.array
            1D array of PopulationNode
        edges : np.array
            2D array of conectivity between PopulationNodes. This is equivalent to the 
            adjacency matrix of the network.
        
        """

        self.date = date
        self.nodes = nodes
        self.edges = edges
        self.connective_infrastructure = connective_infrastructure

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