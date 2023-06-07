import abc
import warnings
import datetime
import pandas as pd
import geopandas as gpd

class PopulationDensity(abc.ABC):
    """
    A class used to represent simulated data as population density data.

    ...

    Attributes
    ----------
    data_dir : str
        directory where data is stored.
    crisis_datetime : datetime
        datetime of crisis. Everythin before this will be considered
        baseline
    baseline : pd.DataFrame   
        baseline dataset to calculare z-scores from
            Structure:
                Index:
                    RangeIndex
                Columns:
                    Name: id, dtype: str
                    Name: day_of_week, dtype: datetime
                    Name: hour, dtype: int
                    Name: n_baseline, dtype: float64

    agg_geometry : str
        type of geometry for aggregation. One of ['tiles', 'admin']

    Methods
    -------
    build_baseline()
        build baseline from ping data.

    build_dataset()
        builds the population dataset for given geometry 
    
    """

    # Attributes
    # ----------
    @abc.abstractproperty
    def data_dir(self) -> str:
        '''
        directory where data is stored.
        '''
        return NotImplemented
    
    @abc.abstractproperty
    def baseline(self) -> pd.DataFrame:
        '''
        baseline dataset to calculare z-scores from
        '''
        return NotImplemented
    
    @abc.abstractproperty
    def agg_geometry(self) -> str:
        '''
        type of geometry for aggregation. One of ['tiles', 'admin']
        '''
        return NotImplemented
    
    # Methods
    # -------
    
    def build_dataset(self):
        """
        Builds population density dataset

        Returns
        -------
        pd.DataFrame 
            DataFrame with the calculated population density data
        """
        return NotImplemented
    
        
    def load_data(self):
        """
        Loads data
        """
        return NotImplemented


    