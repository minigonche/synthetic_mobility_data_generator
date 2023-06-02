
import datetime
import numpy as np


from simulator.disasters.abstract.disaster import Disaster
from simulator.disasters.generic.normal_disaster_dist import NormalDisasterFun

class Earthquake(Disaster):
    """
    Class for constructing an earthquake.
    """

    def __init__(self, id : str, 
                 epicenter : tuple, start_date : datetime, 
                 disaster_functions : list = [],
                 disaster_timeline : list = []):
        '''
        Constructor method

        Parameters
        ----------
        id : str
            id of the disaster. Useful in case there is more than one disaster at once.
        epicenter : tuple
            lat, lon of the epicenter
        start_date : datetime
            start datetime of the disaster
        disaster_functions : list
            a list of DisasterDistribution, where each element represents a moment in time.
        disaster_timeline : list
            a list of dates corresponding to the "snapshots" of the disaster. This must 
            have the same length as the disaster_functions list.
        
        '''

        self.__id = id
        self.__start_date = start_date
        self.__epicenter = np.asarray(epicenter)
        self.__disaster_functions = disaster_functions
        self.__disaster_timeline = disaster_timeline
        

    def id(self) -> str:
        return self.__id
    
    def start_date(self) -> datetime:

        return self.__start_date
    
    def disaster_functions(self) -> list:
        return self.__disaster_functions
    
    def disaster_timeline(self) -> list:
        return self.__disaster_timeline
    
    def epicenter(self) -> tuple:
        return self.__epicenter

    # Methods
    # -------
    def adjust_resolution(self, resolution : tuple):
        """
        Adjust the resolution of the disaster up or down by expanding or shrinking both
        the disaster_functions and disaster_timeline.

        Parameters
        ----------
        resolution : tuple (int, str)
            desired resolution. e.g (1, 'hr')

        """
        return NotImplemented

    def generate_disaster(self, A0 : int, vxy : tuple, 
                          steps : int, method : str, step_unit : str = 'hr'):
        """
        Method to automatically create a disaster. Should set the values of
        disaster_functions and disaster_timeline accordinly.

        The earhwuake is concieved as a progression of normal disaster distributions.
        This function needs to vary the amplitude accross time. 

        In this case we will model a decrease of amplitude and no change of variance.

        Parameters
        ----------
        A0 : int
            Initial amplitude. The multiplier to the intensity when at the epicenter (i.e 
            x = mean_x and y = mean_y)
        vxy : tuple
            values for variance (var_x, var_y)
        steps : int
            number of steps till the "end" of the disaster. This will dictate len(disaster_timeline)
        method : str
            method of decrease of amplitude. one of 'linear', 'exponential', 'parabolic'
        step_unit : str
            time unit for the step. One of 'hr' or 'day'

        """
        assert method in ['linear', 'exponential', 'parabolic']
        assert step_unit in ['hr', 'day']


        time_step = datetime.timedelta(days = 1) if step_unit == 'day' else datetime.timedelta(hours = 1)
        vxy = np.asarray(vxy)

        # init
        A = A0  
        disaster_function = NormalDisasterFun(mean=self.__epicenter, 
                variance=vxy, amplitude=A)
        disaster_timeline = [self.__start_date]
        disaster_functions = [disaster_function]

        for idx, step in enumerate(range(steps)):
            disaster_timeline.append(disaster_timeline[idx] + time_step)
            
            if method == 'linear':
                A = (-A0 / steps) * step + A0
            elif method == 'exponetial':
                A = A0 * np.exp(-step)
            elif method == 'parabolic':
                A = (A0 / steps**2) * (-step**2) + A0
            
            # Define disaster function for this instant
            disaster_function = NormalDisasterFun(mean=self.__epicenter, 
                 variance=vxy, amplitude=A)
            
            disaster_functions.append(disaster_function)

            # set values
            self.__disaster_functions = disaster_functions
            self.__disaster_timeline = disaster_timeline
    
