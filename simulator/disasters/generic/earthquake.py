
import datetime
import numpy as np


from simulator.disasters.abstract.disaster import Disaster
from simulator.disasters.generic.normal_disaster_dist import NormalDisasterFun
from simulator.disasters.generic.uniform_disaster_dist import UniformDisasterFun
from simulator.disasters.abstract.disaster_function import DisasterFunction

class Earthquake(Disaster):
    """
    Class for constructing an earthquake.
    """

    def __init__(self, id : str, 
                 epicenter : tuple, 
                 start_date : datetime,
                 end_date : datetime,
                 A0 : int = None, 
                 vxy : tuple = None, 
                 method : str = None, 
                 step_unit : str = 'hr',
                 disaster_functions : list = None,
                 disaster_timeline : list = None,
                 continuity : datetime = None,
                 continuity_fun : DisasterFunction = None):
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
        end_date : datetime
            end datetime of the disaster
        A0 : int
            Initial amplitude. The multiplier to the intensity when at the epicenter (i.e 
            x = mean_x and y = mean_y)
        vxy : tuple
            values for variance (var_x, var_y)
        method : str
            method of decrease of amplitude. one of 'linear', 'exponential', 'parabolic'
        step_unit : str
            time unit for the step. One of 'hr' or 'day'        
        disaster_functions : list
            a list of DisasterDistribution, where each element represents a moment in time.
        disaster_timeline : list
            a list of dates corresponding to the "snapshots" of the disaster. This must 
            have the same length as the disaster_functions list.
        
        '''

        self.__id = id
        self.__start_date = start_date
        self.__end_date = end_date
        self.__epicenter = np.asarray(epicenter)
        self.__disaster_functions = disaster_functions
        self.__disaster_timeline = disaster_timeline
        self.__continuity = continuity
        self.__continuity_fun = continuity_fun

        # Diaster construction Variables
        self.__A0 = A0 
        self.__vxy = vxy
        self.__method = method
        self.__step_unit = step_unit
        
    @property
    def id(self) -> str:
        return self.__id
    
    @property
    def start_date(self) -> datetime:
        return self.__start_date
    
    @property
    def end_date(self) -> datetime:
        return self.__end_date        
    
    @property
    def disaster_functions(self) -> list:
        if self.__disaster_functions is None:
            self.generate_disaster()

        return self.__disaster_functions
    
    @property
    def disaster_timeline(self) -> list:
        if self.__disaster_timeline is None:
            self.generate_disaster()

        return self.__disaster_timeline
    
    @property
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

    def generate_disaster(self):
        """
        Method to automatically create a disaster. Should set the values of
        disaster_functions and disaster_timeline accordingly.

        The earthquake is conceived as a progression of normal disaster distributions.
        This function needs to vary the amplitude across time. 

        In this case we will model a decrease of amplitude and no change of variance.

        """

        print("   Generating Disaster")

        # Extracts Variables
        method = self.__method
        step_unit = self.__step_unit
        A0 = self.__A0
        vxy = self.__vxy

        
        # Checks
        assert method in ['linear', 'exponential', 'parabolic']
        assert step_unit in ['hr', 'day']

        vxy = np.asarray(vxy)

        # Computes steps
        if self.__continuity:
            time_step = datetime.timedelta(days = 1) if step_unit == 'day' else datetime.timedelta(hours = 1)
            steps = (self.__continuity - self.__start_date).total_seconds()
            steps = int(np.round(steps/time_step.total_seconds())) # Divides by unit   
        else: 
            time_step = datetime.timedelta(days = 1) if step_unit == 'day' else datetime.timedelta(hours = 1)
            steps = (self.__end_date - self.__start_date).total_seconds()
            steps = int(np.round(steps/time_step.total_seconds())) # Divides by unit 

        print(f"      Number of steps to compute: {steps} {step_unit}")    

        if self.__disaster_functions or self.__disaster_timeline:
            assert len(self.__disaster_functions) == len(self.__disaster_timeline)
            
            # TODO develop resolution adjustments.
            return


        # init
        A = A0  
        disaster_function = NormalDisasterFun(mean=self.__epicenter, 
                variance=vxy, amplitude=A)
        disaster_timeline = [self.__start_date]
        disaster_functions = [disaster_function]
        
        for idx, step in enumerate(range(steps)):
            disaster_timeline.append(disaster_timeline[idx] + time_step)
            if self.__continuity and ((disaster_timeline[idx] + time_step) > self.__end_date):
                disaster_functions.append(self.__continuity_fun)
            else:
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
    
