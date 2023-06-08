import numpy as np
import abc



class DisasterFunction(abc.ABC):
    """
    A class used to represent an disaster snapshot. It 
    is understood as a set of two functions that for any point in space, will evaluate
    the direction of the force excerted by the disaster and the intensity of the disaster 
    at that point.  
    
    
    1. Intensity: 
        2D function f(lat, lon) representing the intensity of the disaster ocurring in space at a particular time. 
    2. Direction
        2D function f(lat, lon) reoresenting the direciton of push away from the disaster. 

    ...

    Methods
    -------
    direction(np.array)
        returns the direction excerted by the disaster on a given coordinate (lat, lon)
    intensity(np.array)
        returns the intensity excerted by the disaster on a given coordinate (lat, lon)
    
    """

    @property
    @abc.abstractmethod
    def mean(self) -> np.array:
        return NotImplemented
    
    @property
    @abc.abstractmethod
    def variance(self) -> np.array:
        return NotImplemented
    
    
    @property
    @abc.abstractmethod
    def amplitude(self) -> float:
        return NotImplemented
    
    # Methods
    # -------
    def direction(self, pois : list) -> list:
        """
        Method to model direction flows in mobility.
        
        Parameters
        ----------
        pois : list
            list of points in the format (lon, lat)  to calculate forces exerted.

        Returns
        -------
        list
            array of angles describing the bearing at a point  

        """

        return NotImplemented
    
    def intensity(self, pois :list) -> list:
        """
        Method to model fatalities and damage.

        Parameters
        ----------
        pois : np.array
            list of points in the format (lon, lat)  to calculate forces exerted.

        Returns
        -------
        np.array
            array of floats that describe the intensity of the disaster at a specific point.
        """

        return NotImplemented
    
    def generate_geopandas(self):
        """
        Method to generate geopandas of function

        Returns
        -------
        gpd.GeoDataFrame
            Geopandas describing the contour lines of the 2D functions associated with the disaster.
            Structure:
            Index:
                RangeIndex
            Columns:
                Name: geometry, dtype: geometry
                Name: intensity, dtype: float64
        """
        return NotImplemented