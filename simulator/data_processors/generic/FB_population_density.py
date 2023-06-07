import os
import sys
import warnings
import datetime
import pandas as pd
import geopandas as gpd

import simulator.utils as utils
import simulator.constants as con
from simulator.data_processors.abstract.population_density import PopulationDensity



class FBPopulationDensity(PopulationDensity):
    """
    Class for constructing a population density dataset with the same
    structure as the ones porduced by fb.
    """

    def __init__(self, data_dir : str, crisis_datetime : datetime,
                  agg_geometry : str):
        '''
        Constructor method

        Parameters
        ----------
        data_dir : str
            directory where data is stored.
        '''

        self.__data_dir = data_dir
        self.__crisis_datetime = crisis_datetime
        self.__baseline = pd.DataFrame()
        self.__crisis = pd.DataFrame()
        self.__data = pd.DataFrame()

        assert agg_geometry in ['tile', 'admin']
        self.__agg_geometry = agg_geometry
        if self.agg_geometry() == 'admin':
            self.__geo_col_name = 'admin'
        elif self.agg_geometry() == 'tile':
            self.__geo_col_name = con.QUAD_KEY
        else:
            self.__geo_col_name = "not_defined"


    # Attributes
    # ----------
    def data_dir(self) -> str:
        return self.__data_dir
    
    def crisis_datetime(self) -> str:
        return self.__crisis_datetime
    
    def agg_geometry(self) -> str:
        return self.__agg_geometry
    
    def baseline(self) -> pd.DataFrame:
        if self.__baseline.empty:
            self.load_data()

        return self.__baseline
    
    # Methods
    # -------
    
    def build_dataset(self):
        """
        Builds population density dataset

        df structure:
            Index:
                RangeIndex
            Columns:
                Name: id, dtype: str
                Name: day_of_week, dtype: datetime
                Name: hour, dtype: int
                Name: n_baseline, dtype: float64
        """

        if self.__crisis.empty or self.__baseline.empty:
            self.load_data()

        # Merge left will remove entries that dont' have a baseline. This is NOT IDEAL
        # but it is currenlty how Data for Good handles it.
        df = pd.merge([self.__crisis, self.__baseline], 
                      on=[self.__geo_col_name, con.DAY_OF_WEEK, con.HOUR], how="left")

        df[con.N_DIFFERENCE] = df[con.N_CRISIS] - df[con.N_BASELINE]
        df[con.DENSITY_BASELINE] = df[con.N_BASELINE] / df[con.N_BASELINE].sum()
        df[con.DENSITY_CRISIS] = df[con.N_CRISIS] / df[con.N_CRISIS].sum()
        df[con.PERCENT_CHANGE] = "percent_change"
        df[con.Z_SCORE] = "z_score"
        df[con.DS] = "ds"




    def load_from_file(self):
        """
        Loads data and returns it as a DataFrame 

        Returns
        -------
        pd.DataFrame
            DataFrame with loaded ping data
        """

        df = pd.DataFrame()
        for file in os.listdir(self.data_dir()):
            try:
                df_tmp = pd.read_csv(file, parse_dates=[con.DATETIME])

                # Check minimun required columns
                if not set(df_tmp.columns).issubset(con.DATASET_MIN_COLS):
                    utils.errors.write_error(sys.argv[0], f"incorrect data structure for file {file}", 
                                "error", datetime.now())
                    continue

                df = pd.concat([df, df_tmp])

            except Exception as e:
                utils.errors.write_error(sys.argv[0], e, 
                                "error", datetime.now())

    
        if df.empty:
            raise Exception("Not possible to load data. Check error log.")
        
        return df

    def load_data(self):
        """
        Builds baseline and crisis from ping data. 

        df_crisis structure:
            Index:
                RangeIndex
            Columns:
                Name: id, dtype: str
                Name: day_of_week, dtype: int
                Name: hour, dtype: int
                Name: datetime, dtype: datetime
                Name: n_crisis, dtype: float64
        df_baseline structure:
            Index:
                RangeIndex
            Columns:
                Name: id, dtype: str
                Name: day_of_week, dtype: int
                Name: hour, dtype: int
                Name: n_baseline, dtype: float64
                
        """
        df_raw = self.load_from_file()

        # brings data to fb datetime intervals
        df_raw[con.DATETIME] = df_raw[con.DATETIME].apply(utils.facebook.to_fb_date())

        # extract date of week for comparison
        df_raw[con.DAY_OF_WEEK] = df_raw[con.DATETIME].weekday()
        df_raw[con.HOUR] = df_raw[con.DATETIME].hour

        # builds ids
        if self.agg_geometry() == 'admin':
            return NotImplemented
        
        if self.agg_geometry() == 'tile':
            tile_ids = utils.facebook.extract_quad_keys(df_raw[[con.LAT, con.LON]].to_numpy())
            df_raw[self.__geo_col_name] = tile_ids.tolist()

        # If the same person appeared at multiple locations in a time interval we only count their most frequent location.
        df_raw.sort_values(con.DATETIME, inplace=True)
        df_raw.drop_duplicates(subset=[self.__geo_col_name, con.DATETIME], 
                                keep="last", inplace=True)
                
        # build baseline
        df_baseline_raw = df_raw[df_raw[con.DATETIME] < self.crisis_datetime()]
        cols_to_drop = set(df_baseline_raw.columns) - set([self.__geo_col_name, con.DAY_OF_WEEK, con.HOUR])

        df_baseline_raw.drop(columns=cols_to_drop, inplace=True)
        df_baseline_raw[con.N_BASELINE] = 1

        df_baseline = df_baseline_raw.groupby([self.__geo_col_name, con.DAY_OF_WEEK, con.HOUR])[con.N_BASELINE].mean().reset_index()
        self.__baseline = df_baseline

        # build crisis
        df_crisis_raw = df_raw[df_raw[con.DATETIME] >= self.crisis_datetime()]
        cols_to_drop = set(df_crisis_raw.columns) - set([self.__geo_col_name, con.DAY_OF_WEEK, con.HOUR, con.DATETIME])

        df_crisis_raw.drop(columns=cols_to_drop, inplace=True)
        df_crisis_raw[con.CRISIS] = 1
        df_crisis = df_crisis_raw.groupby([self.__geo_col_name, con.DAY_OF_WEEK, con.HOUR, con.DATETIME])[con.CRISIS].mean().reset_index()
        self.__crisis = df_crisis