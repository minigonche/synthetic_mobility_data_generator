import numpy as np
from abc import ABC
import geopandas as gpd
import os

from simulator.population_networks.abstract.population_network import PopulationNetwork
from simulator.disasters.abstract.disaster import Disaster
import simulator.constants as con

from datetime import datetime 

class Simulation(ABC):
    """
    A class used to run the simulation.
    ...

    Attributes
    ----------
    id : str
        Id of the simulation
    start_date : datetime
        start date of the simulation
    end_date : datetime
        end date of the simulation
    frequency : float
        The frequency the simulation will act in hours
    disaster : Disaster
        The disaster that will act no the simulation
    population_network : PopulationNetwork
        PopulationNetwork for the simulation.



    Methods
    -------
    __interact()
        mediates the interaction between a disaster_distribution and a population network by adjusting
        the population network with the effect of the disaster.
    simulate()
        run simulation.
    
    """

    def __init__(self, id : str,
                       start_date : datetime,
                       end_date : datetime,
                       frequency : float,
                       disaster : Disaster,
                       population_network : PopulationNetwork):
        
        self.id = id
        self.start_date = start_date
        self.end_date = end_date
        self.frequency = frequency 
        self.disaster = disaster
        self.population_network = population_network

    
    def simulate(self):
        """
        This is the main method for this package. Each iteration has 4 steps
            1. interact: 
                gets DisasterDistribution and calculates force array
            2. update_flow: 
                calculates PopulationNetwork (population_network_1) using calculated force array
            3. sample:
                samples data from PopulationNetwork (population_network_1), accounting for
                previous state (population_network_0.sample())
            4. step : population_network_0 = population_network_1

        The first two steps create a new population network with adjusted weights to 
        account for a possible disaster and adjusted node attributes to account
        for possible fatalities. The third step is then called on the new population
        network to create a mobility dataset at that moment. The last step sets up the next
        iteration. 

        The simulated data is then written to file.
        """

        return NotImplemented

    def export_iteration(self, date_string, df):
        '''
        Method that exports to disk the given iteration DataFame for the corresponding date
        '''

        export_folder = os.path.join(con.RESULTS_FOLDER, self.id)
        if not os.path.exists(export_folder):
            # Create the folder
            os.makedirs(export_folder)

        # Creates Filename   
        filename = f"{os.path.join(export_folder,date_string)}.csv"
        
        # Saves
        df[[con.ID, con.DATE, con.LON, con.LAT]].to_csv(filename, index = False)
     


    