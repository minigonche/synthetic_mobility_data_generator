
import datetime
import numpy as np
import geopandas as gpd

class PopulationNetwork:
    """
    A class used to represent the population network.

    ...

    Attributes
    ----------

    nodes : np.array
        1D array of PopulationNodes
    edges : np.array
        2D array of conectivity between PopulationNodes. This is equivalent to the 
        weighted adjacency matrix of the network.
    date : datetime
        date corresponding to this network.

    Methods
    -------
    
    """

    def __init__(self, date : datetime, nodes : np.array = np.empty, 
                 edges : np.array = np.empty):
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

    def flow(self, force : np.array):
        """
        Given a an array of forces excerted on the nodes of the network, the network updates
        its edge weights to account for the given force.

        Parameters
        ----------
        force : np.array
            an array of 2D force vectors as returned by the point_force method of 
            a DsasterDistribution.
        """

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