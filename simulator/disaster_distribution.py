import numpy as np


class DisasterDistribution:
    """
    A class used to represent an disaster snapshot. It 
    is defined by a 2D distribution representing a disaster ocurring in space at a particular time. 
    The joint density will represent the severity of the disaster at a particular point in space.

    The first moment will correspond to the "epicenter" of the disaster at a particular time. 
    Note that this might not necessarily corresponds to the true epicenter of a disaster, becuase a disaster is
    concieved to be a series of disaster distributions. 

    ...

    Attributes
    ----------

    E_x : tuple (float, float)
        first moment of the distribution. Must correspond to a location in space 
        specified as (lat, lon).

    Methods
    -------
    point_force(lat, lon)
        returns the force excerted by the disaster on a given coordinate (lat, lon)
    area_force(x0, x1, y0, y1)
        returns the force excerted by the disaster on a given area (assumed to be a square tile)
    
    """

    def __init__(self, E_x : tuple):
        """
        Parameters
        ----------
        E_x : tuple (float, float)
            first moment of the distribution. Must correspond to a location in space 
            specified as (lat, lon).
        """

        self.E_x = E_x

    def point_force(self, lat : float, lon : float) -> np.array:
        """
        Parameters
        ----------
        lat : float
            latitude of desired poi 
        lon : float 
            longitude of desired poi 

        Returns
        -------
        np.array
            2D vector describing the "push" of the event at that specific coordinate. 
            This will be used to simulate the movement away from this point (vector represents
            both direction on "push" and intensity). 

            This is essentially the gradient of the disaster function, evaluated at a
            specific point. 

        """

        return NotImplemented
    
    def area_force(self, lat_0 : float, lat_1 : float, 
                   lon_0 : float, lon_1 : float) -> np.array:
        """
        Parameters
        ----------
        lat_0 : float
            latitude of the lower left corner of the desired aoi 
        lat_1 : float
            latitude of the upper right corner of the desired aoi 
        lon_0 : float
            longitude of the lower left corner of the desired aoi 
        lon_1 : float
            longitude of the upper right corner of the desired aoi 

        Returns
        -------
        np.array
            2D vector describing the "push" of the event at that specific coordinate. 
            This will be used to simulate the movement away from this point (vector represents
            both direction on "push" and intensity). 

            This is essentially some aggregation of the gradient of the disaster function, evaluated for t.he
            points inside this area.

        """

        return NotImplemented