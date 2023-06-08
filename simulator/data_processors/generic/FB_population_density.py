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

    def __init__(self, dataset_id : str, data_dir : str, crisis_datetime : datetime,
                  agg_geometry : str):
        '''
        Constructor method

        Parameters
        ----------
        data_dir : str
            directory where data is stored.
        '''

        self.__data_dir = data_dir
        self.__dataset_id = f"fb_population_density_{dataset_id}"
        self.__crisis_datetime = crisis_datetime
        self.__baseline = pd.DataFrame()
        self.__crisis = pd.DataFrame()
        self.__data = pd.DataFrame()

        assert agg_geometry in ['tile', 'admin']
        self.__agg_geometry = agg_geometry
        if self.agg_geometry() == 'admin':
            self.__geo_col_name = 'admin'
            return NotImplemented
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
    
    def dataset_id(self) -> str:
        return self.__dataset_id
    
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
        df[con.PERCENT_CHANGE] = df[con.N_DIFFERENCE] * 100 / (df[con.N_BASELINE] + con.EPSILON)
        df[con.Z_SCORE] = df[con.N_DIFFERENCE] / df['n_baseline_std']
        df[con.DS] = df[con.DATETIME].dt.date

        # Calclate the lat and lon of the geometry centroid
        if self.agg_geometry() == 'admin':
            return NotImplemented
        elif self.agg_geometry() == 'tile':
            df[con.LATITUDE], df[con.LONGITUDE] = utils.facebook.tile_centroid(df[self.__geo_col_name])

        self.__data = df

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
                df_tmp.rename(columns={con.DATETIME: con.DATE_TIME,
                                       con.LAT: con.LATITUDE, 
                                       con.LON: con.LONGITUDE}, inplace=True)

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
        df_raw[con.DATE_TIME] = df_raw[con.DATE_TIME].apply(utils.facebook.to_fb_date())

        # extract date of week for comparison
        df_raw[con.DAY_OF_WEEK] = df_raw[con.DATE_TIME].weekday()
        df_raw[con.HOUR] = df_raw[con.DATE_TIME].hour

        # builds ids
        if self.agg_geometry() == 'admin':
            return NotImplemented
        
        if self.agg_geometry() == 'tile':
            tile_ids = utils.facebook.extract_quad_keys(df_raw[[con.LAT, con.LON]].to_numpy())
            df_raw[self.__geo_col_name] = tile_ids.tolist()

        # If the same person appeared at multiple locations in a time interval we only count their most frequent location.
        df_raw.sort_values(con.DATE_TIME, inplace=True)
        df_raw.drop_duplicates(subset=[self.__geo_col_name, con.DATE_TIME], 
                                keep="last", inplace=True)
                
        # build baseline
        df_baseline_raw = df_raw[df_raw[con.DATE_TIME] < self.crisis_datetime()]
        cols_to_drop = set(df_baseline_raw.columns) - set([self.__geo_col_name, 
                                                           con.DAY_OF_WEEK, con.HOUR])

        df_baseline_raw.drop(columns=cols_to_drop, inplace=True)
        df_baseline_raw[con.N_BASELINE] = 1

        df_baseline = df_baseline_raw.groupby([self.__geo_col_name, 
                                               con.DAY_OF_WEEK, con.HOUR], as_index=False) \
                                                .agg({con.N_BASELINE:['mean','std']})
        
        df_baseline.columns = [self.__geo_col_name, con.DAY_OF_WEEK, 
                               con.HOUR, con.N_BASELINE, 'n_baseline_std']
        
        # make sure std is at least 0.1
        df_baseline.loc[df_baseline['n_baseline_std'] < con.MIN_STD,'n_baseline_std' ] =  con.MIN_STD

        self.__baseline = df_baseline

        # build crisis
        df_crisis_raw = df_raw[df_raw[con.DATE_TIME] >= self.crisis_datetime()]
        cols_to_drop = set(df_crisis_raw.columns) - set([self.__geo_col_name, 
                                                         con.DAY_OF_WEEK, con.HOUR, con.DATE_TIME])

        df_crisis_raw.drop(columns=cols_to_drop, inplace=True)
        df_crisis_raw[con.CRISIS] = 1
        df_crisis = df_crisis_raw.groupby([self.__geo_col_name, con.DAY_OF_WEEK, 
                                           con.HOUR, con.DATE_TIME])[con.CRISIS] \
                                            .mean().reset_index()
        self.__crisis = df_crisis

    def write_dataset_to_file(self):
        out_folder = os.path.join(con.DATA_FOLDER, f"{self.dataset_id()}", 
                            f"dataset=population-density", f"scale={self.__agg_geometry}")
        
        if not os.path.exists(out_folder):
            os.mkdir(out_folder)

        for date in self.__data[con.DS].unique():
            for hour in [0, 8, 16]:
                # file naming conventions
                date_str = datetime.datetime.strftime(date, "%Y-%m-%d")
                hour_str = f"0{hour}00" if hour // 10 == 0 else f"{hour}00"
                file_name = f"{self.dataset_id()}_{date_str}_{hour_str}.csv"
                out_file = os.path.join(out_folder, file_name)

                df_tmp = self.__data.loc[self.__data[con.DS == date] & self.__data[con.HOUR == hour]]
                df_tmp[con.DS] = date_str
                df_tmp[con.FB_POP_DENSITY_COLS].to_csv(out_file, index=False)
