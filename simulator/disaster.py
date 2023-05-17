import datetime

# Local imports
from disaster_distribution import DisasterDistribution

class Disaster:
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
    disaster_distributions : list
        a list of DisasterDistribution, where each element represents a moment in time.
    disaster_timeline : list
        a list of dates corresponding to the "snapshots" of the disaster. This must 
        have the same length as the disaster_distributions list.

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

    def __init__(self, id,  disaster_distributions : list = [], 
                 disaster_timeline : list = []):
        """
        Parameters
        ----------
        id : str
            id of the disaster
        disaster_distributions : list
            a list of DisasterDistribution, where each element represents a moment in time.
        disaster_timeline : list
            a list of dates corresponding to the "snapshots" of the disaster. This must 
            have the same length as the disaster_distributions list.
        """

        self.id = id
        self.disaster_distributions = disaster_distributions
        self.disaster_timeline = disaster_timeline

    def is_valid(self):
        """
        Checks the following assumptions:
        1. len(disaster_distributions) == len(disaster_timeline) # no missing data
        2. len(set(disaster_timeline)) == len(disaster_timeline) # no repeted dates

        Raises
        ----------
        InvalidDisaster 
            if fails check, raises exception

        """
        return NotImplemented
    
    def adjust_resolution(self, resolution : tuple):
        """
        Adjust the resolution of the disaster up or down by expanding or shrinking both
        the disaster_distributions and disaster_timeline.

        Parameters
        ----------
        resolution : tuple (int, str)
            desired resolution. e.g (1, 'hr')

        """
        return NotImplemented

    def generate_disaster(self, dist_0 : DisasterDistribution, dist_n : DisasterDistribution, 
                          steps : int, time_unit : tuple):
        """
        Given two distirbutions (a source and a target), a number of steps and a time unit,
        creates a list of distributions that start with the source distribution
        and ends with the target distribution in a given number of steps. 

        Parameters
        ----------
        dist_0 : DisasterDistribution
            source disaster distribution
        dist_n : DisasterDistribution
            target disaster distribution
        steps : int
            number of steps to take between dist_0 and dist_n. This will essentially be
            len(disaster_distributions)
        time_unit : tuple (int, 'str')
            time unit for the steps. This will be used to compute disaster_timeline. 
        """

        return NotImplemented
    
    def get_snapshot(self, date : datetime, exact : bool = True) -> DisasterDistribution:

        """
        Checks that datetime exists and returns the corresponding DisasterDistribution. If 
        exact == False, returns the DisasterDistribution for the closest date. 

        Parameters
        ----------
        date : datetime
            date to get corresponding DisasterDistribution

        exact : bool
            return DisasterDistribution corresponding to exact date match (default is True)

        Returns
        -------
        DisasterDistribution
            an instance of DisasterDistribution, corresponding to the specified date.
        """


        return NotImplemented