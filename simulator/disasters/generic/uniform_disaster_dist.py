import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
import matplotlib.pyplot as plt


from simulator.disasters.abstract.disaster_function import DisasterFunction
import simulator.utils.geometric as geo_fun

class UniformDisasterFun(DisasterFunction):
    """
    Class for constructing a uniform disaster distribution.
    """


    def __init__(self, mean : np.array, 
                 radius_km : int, amplitude : float):
        '''
        Constructor method

        Parameters
        ----------
        mean : np.array
            1D np.array with [lat, lon] values of the epicenter of the disaster
        variance : np.array
            1D np.array with the variance of the disaster
        
        '''
        # Check shapes of parameters
        assert mean.shape == (2,) 

        # Check ranges of "epicenter" 
        assert (mean[0] >= -90 and mean[0] <= 90)
        assert (mean[1] >= -180 and mean[0] <= 180)


        self.__mean = mean
        self.__radius_km = radius_km
        self.__amplitude = amplitude
        self.__variance = None
        
    @property
    def mean(self) -> np.array:
        return self.__mean

    @property  
    def radius_km(self) -> np.array:
        return self.__radius_km
    
    @property  
    def variance(self) -> np.array:
        return self.__variance
    
    @property    
    def amplitude(self) -> float:
        return self.__amplitude

    
    def __bearing(self, poi) -> float:
        lat_1 = np.radians(self.__mean[0])
        lon_1 = np.radians(self.__mean[1])
        lat_2 = np.radians(poi[0])
        lon_2 = np.radians(poi[1])

        delta_lon = lon_2 - lon_1

        x = np.sin(delta_lon) * np.cos(lat_2)
        y = np.cos(lat_1)*np.sin(lat_2) \
           - np.sin(lat_1)*np.cos(lat_2)*np.cos(delta_lon)
        theta = np.arctan2(x, y)

        # (theta*180/np.pi + 360) % 360  # in degrees 
        return (theta*180/np.pi + 360) % 360 # in degrees 

    def __density(self, poi) -> float:
        """
        Uniform distribution
        """
        lat_1 = np.radians(self.__mean[0])
        lon_1 = np.radians(self.__mean[1])
        lat_2 = np.radians(poi[0])
        lon_2 = np.radians(poi[1])

        if geo_fun.haversine(lon_1, lat_1, lon_2, lat_2) < self.__radius_km:
            return self.__amplitude 
        else:
            return 0              

    def direction(self, pois : list) -> np.array:
        """
        Method to model direction flows in mobility. This will be calculated as the 
        forward azimuth (or bearing) which if followed in a straight line along a great-circle 
        arc will take you from the epicenter of the disaster to the point of impact.

        θ = atan2( sin Δλ ⋅ cos φ2 , cos φ1 ⋅ sin φ2 - sin φ1 ⋅ cos φ2 ⋅ cos Δλ )
        where	φ1,λ1 is the start point, φ2,λ2 the end point (Δλ is the difference in longitude)
        
        Parameters
        ----------
        pois : np.array
            list of points in the format (lon, lat) to calculate forces exerted.

        Returns
        -------
        np.array
            array of angles describing the bearing at a given point in degrees

        """
        pois_coord = [(p[1], p[0]) for p in pois] # invert to match (lat, lon)
        pois_coord = np.asarray(pois_coord)

        bearings = self.__bearing(np.transpose(pois_coord))

        return bearings.tolist()
    
    def intensity(self, pois : np.array) -> np.array:
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
        pois_coord = [(p[1], p[0]) for p in pois] # invert to match (lat, lon)
        pois_coord = np.asarray(pois_coord)

        intensity = self.__density(np.transpose(pois_coord))

        return intensity.tolist()
    
    def generate_geopandas(self) -> gpd.GeoDataFrame:

        lower_left = [self.__mean[0] - 5, self.__mean[1] - 5] # ~500 km radius
        upper_right = [self.__mean[0] + 5, self.__mean[1] + 5] # ~500 km radius

        x = np.linspace(lower_left[0], upper_right[0], 50)
        y = np.linspace(lower_left[1], upper_right[1], 50)

        grid = np.meshgrid(x, y)
        Z = self.__density(grid)

        contours = plt.contour(grid[1], grid[0], Z)

        geometries = []
        intensity = []
        for idx, contour in enumerate(contours.collections):
            mpoly = []
            paths = contour.get_paths()
            if len(paths) != 1:
                continue
            path = paths[0]
            path.should_simplify = False
            poly = path.to_polygons()
            # Each polygon should contain only an exterior ring
            exterior = []
            if len(poly) != 1:
                continue
            exterior = poly[0]
            mpoly.append(Polygon(exterior))
            geometries.append(mpoly[0])
            intensity.append(Z[idx][idx])

        gdf = gpd.GeoDataFrame(geometry=geometries, data={"intensity": intensity})
        gdf = gdf.set_crs('epsg:4326')

        return gdf


