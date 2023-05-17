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
        specified as (lat, lon). Will help visulize the "path" of the disaster.

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

    def point_force(self, pois : np.array) -> np.array:
        """
        Parameters
        ----------
        pois : np.array
            list of points (pois of interes) to calculate forces exerted.

        Returns
        -------
        np.array
            array of 2D vectors describing the "push" of the event at that specific coordinate. 
            This will be used to simulate the movement away from this geometry (vector represents
            both direction on "push" and intensity). 

            Each element is essentially the gradient of the disaster function, evaluated at a
            specific point. If the original geometry is an area as opposed to a point, the calculated 
            force vector will some aggregation of the gradient of the disaster function, evaluated 
            for the points inside that area.

        """

        return NotImplemented
    