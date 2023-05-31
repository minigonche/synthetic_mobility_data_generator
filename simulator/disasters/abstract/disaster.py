import abc
import warnings
import datetime


# Local imports
from simulator.disasters.abstract.disaster_function import DisasterFunction

class Disaster(abc.ABC):
    """
    A class used to represent an disaster. In its most basic it 
    is defined by a series of 2D distributions. Each distribution represents a
    disaster ocurring in space at a particular time. The joint density will represent 
    the severity of the disaster at a particular point in space.

    ...

    Attributes
    ----------
    id : str
            id of the disaster. Useful in case there is more than one disaster at once.
    epicenter : tuple   
        lat, lon of the epicenter
    start_date : datetime
        start datetime of the disaster
    disaster_functions : list
        a list of DisasterFunction, where each element represents a moment in time.
    disaster_timeline : list
        a list of dates corresponding to the "snapshots" of the disaster. This must 
        have the same length as the disaster_functions list.

    Methods
    -------
    is_valid()
        ensures disaster definition follows correct structure

    generate_disaster()
        given two distirbutions (a source and a target), a number of steps and a time unit,
        creates a list of distributions that start with the source distribution
        and ends with the target distribution in a given number of steps. 

    get_snapshot()
        get disaster distribution for a specific date.
    
    """

    # Attributes
    # ----------
    @abc.abstractproperty
    def id(self) -> str:
        '''
        Id of the disaster
        '''
        return NotImplemented
    
    @abc.abstractproperty
    def epicenter(self) -> tuple:
        '''
        latitude and longited of the epicenter 
         of the disaster
        '''
        return NotImplemented
    
    @abc.abstractproperty
    def start_date(self) -> datetime:
        '''
        Start date of the disaster
        '''
        return NotImplemented
    
    @abc.abstractproperty
    def disaster_functions(self) -> list:
        '''
        A list of DisasterFunction, where each element represents a moment in time
        '''
        return NotImplemented
    
    @abc.abstractproperty
    def disaster_timeline(self) -> list:
        '''
        A list of dates corresponding to the "snapshots" of the disaster. This must 
        have the same length as the disaster_functions list.
        '''
        return NotImplemented
    
    # Methods
    # -------
    def is_valid(self):
        """
        Checks the following assumptions:
        1. len(disaster_functions) == len(disaster_timeline) # no missing data
        2. len(set(disaster_timeline)) == len(disaster_timeline) # no repeted dates

        Returns
        -------
        tuple
            if fails check, returns (False, message), else (True, 'OK')

        """
        message = 'OK'
        if len(self.disaster_functions()) != len(self.disaster_timeline()):
            return (False, f"disaster_functions length {len(self.disaster_functions())} \
            does not match disaster_timeline lenght {len(self.disaster_timeline())}.")
        if len(set(self.disaster_timeline())) != len(self.disaster_timeline()):
            return (False, f"disaster_timeline has repeated dates.")
        if len(self.disaster_functions()) == 0:
            message = warnings.warn("Disaster is empty. Run generate_disaster() or initialize manually", warnings.UserWarning)
     
        return (True, message)
    
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

    def generate_disaster(self, **kwargs):
        """
        Method to automatically create a disaster. Should set the values of
        disaster_functions and disaster_timeline accordinly.

        """

        return NotImplemented
    