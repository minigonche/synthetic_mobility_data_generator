import numpy as np
import geopandas as gpd

from population_network import PopulationNetwork

class Simulation:
    """
    A class used to run the simulation.
    ...

    Attributes
    ----------
    state : int
        number of iterations
    start_date : datetime
        start date of the simulation
    end_date : datetime
        end date of the simulation
    event_timeline : np.array
        array of disaster distributions. It is directly extracted from the Disaster object, but it must start
        at the given start_date and end at the given end_date. Missing values represent that at that given step
        of the simulation there is no disaster. 
    population_network : PopulationNetwork
        innitial population network for the simmulation.
    simulated_data : geopandas.GeoDataFrame
        GeoDataFrame with the simulated data.
        Index:
            RangeIndex
        Columns:
            Name: date, dtype: datetime64[ns]
            Name: Geometry, dtype: geometry
            Name: count, dtype: int64
            Name: accuracy, dtype: float64 (optional)

    Methods
    -------
    __interact()
        mediates the interaction between a disaster_distribution and a population network by adjusting
        the population network with the effect of the disaster.
    simulate()
        run simulation.
    
    """

    def __init__(self, id : str, event_timeline : np.array,
                  population_network : PopulationNetwork, simulated_data : gpd.GeoDataFrame):
        
        self.id = id
        self.event_timeline = event_timeline
        self.population_network = population_network
        self.simulated_data = gpd.GeoDataFrame()

    
    def __interact(self, iter):
        """
        Interaction between event and population network. This interacion should will
        affect edge values, increasing or decreasing them according to the interaction of the 
        network with the distribution of the disaster. It may also affect node attributes (e.g. 
        population to account for fatalities)
        
        Returns
        -------
        PopulationNetwork

        """

        return NotImplemented
    
    def simulate(self):
        """
        This is the main method for this package. Each iteration has two steps
            1. interact
            2. sample

        The interact method creates a new population network with adjusted weights to 
        account for a possible disaster and adjusted node attributes to account
        for possible fatalities. The sample method is then called on the new population
        network to create a mobility dataset at that moment. 

        The simulated data is then written to file.
        """

        return NotImplemented
    