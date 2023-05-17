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
    population_network_0 : PopulationNetwork
        PopulationNetwork for the simmulation at moment iter - 1. For the first iteration, it is the initial 
        PopulationNetwork.
    population_network_1 : PopulationNetwork
        PopulationNetwork for the simmulation for current iteration.
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
                  population_network_0 : PopulationNetwork, simulated_data : gpd.GeoDataFrame):
        
        self.id = id
        self.event_timeline = event_timeline
        self.population_network_0 = population_network_0
        self.population_network_1 = None
        self.simulated_data = gpd.GeoDataFrame()

    
    def __interact(self) -> np.array:
        """
        Interaction between event and population network. This interacion can be understood
        in terms of forces. Each disaster distribution has a force profile that interacts with the 
        nodes of the network. The weights of the edges of the network are thus updated to account for 
        this.

        Returns
        ----------
        force_array : np.array
            returns the force array on PopulationNetwork (population_network_0) for
            DisasterDistribution at current iter.
        """

        return NotImplemented
    
    def simulate(self):
        """
        This is the main method for this package. Each iteration has two steps
            1. interact: 
                gets DisasterDistribution and calculates force array
            2. flow: 
                calculates PopulationNetwork (population_network_1) using calculated force array
            3. sample:
                samples data from PopulationNetwork (population_network_1), accounting for
                previous state (population_network_0.sample())
            4. step : population_network_0 = population_network_1

        The interact method creates a new population network with adjusted weights to 
        account for a possible disaster and adjusted node attributes to account
        for possible fatalities. The sample method is then called on the new population
        network to create a mobility dataset at that moment. 

        The simulated data is then written to file.
        """

        return NotImplemented
    