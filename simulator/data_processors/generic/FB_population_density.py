import os
import sys
import warnings
import datetime
import pandas as pd
import geopandas as gpd

import simulator.utils.errors as error_fun
import simulator.utils.facebook as fb_fun
import simulator.constants as con
from simulator.data_processors.abstract.population_density import PopulationDensity

TAB = "  "

class FBPopulationDensity(PopulationDensity):
    """
    Class for constructing a population density dataset with the same
    structure as the ones porduced by fb.
    """

    def __init__(self, disaster_name : str, data_dir : str, crisis_datetime : datetime,
                  agg_geometry : str, out_dir : str, geo_file : str = None,
                  baseline_cols : list = [con.HOUR, con.DAY_OF_WEEK]):
        '''
        Constructor method

        Parameters
        ----------
        data_dir : str
            directory where data is stored.
        '''

        self.__data_dir = data_dir
        self.__out_dir = out_dir
        self.__dataset_id = f"disaster-name={disaster_name}"
        self.__crisis_datetime = crisis_datetime
        self.__baseline = pd.DataFrame()
        self.__crisis = pd.DataFrame()
        self.__data = pd.DataFrame()
        self.__baseline_loaded = False
        self.__crisis_loaded = False
        self.__geo_file = geo_file

        assert agg_geometry in ['tile', 'admin']
        self.__agg_geometry = agg_geometry
        if self.agg_geometry() == 'admin':
            self.__geo_col_name = 'admin'
            assert self.__geo_file
        elif self.agg_geometry() == 'tile':
            self.__geo_col_name = con.QUAD_KEY
        else:
            self.__geo_col_name = "not_defined"

        baseline_cols.append(self.__geo_col_name)
        self.__baseline_cols = baseline_cols


    # Attributes
    # ----------
    def data_dir(self) -> str:
        return self.__data_dir
    
    def crisis_datetime(self) -> str:
        return self.__crisis_datetime
    
    def agg_geometry(self) -> str:
        return self.__agg_geometry
    
    def baseline(self) -> pd.DataFrame:
        if not self.__baseline_loaded:
            self.load_data()

        return self.__baseline
    
    def crisis(self) -> pd.DataFrame:
        if not self.__crisis_loaded:
            self.load_data()
            
        return self.__crisis
    
    def data(self) -> pd.DataFrame:
        if not self.__baseline_loaded or not self.__crisis_loaded:
            self.load_data()
        return self.__data
    
    def dataset_id(self) -> str:
        return self.__dataset_id
    
    # Methods
    # -------

    def set_baseline(self, baseline : pd.DataFrame):
        self.__baseline = baseline
        self.__baseline_loaded = True

    def set_crisis(self, crisis : pd.DataFrame):
        self.__crisis = crisis
        self.__crisis_loaded = True
    
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

        print("Calulates fb population density statistics.")
        if not self.__crisis_loaded or not self.__baseline_loaded:
            self.load_data()
           
        if self.__crisis.empty :
            error_fun.write_error(sys.argv[0], 
                                    f"Can't calculate statistics without dataafter crisis date.", 
                            "warning", datetime.datetime.now())
            return 
            
        if self.__baseline.empty:
            error_fun.write_error(sys.argv[0], 
                                    f"Can't calculate statistics without baseline data.", 
                            "warning", datetime.datetime.now())
            return 

        # Merge left will remove entries that dont' have a baseline. This is NOT IDEAL
        # but it is currenlty how Data for Good handles it.
        merge_cols = [con.LATITUDE, con.LONGITUDE] + self.__baseline_cols
        df = self.baseline().merge(self.crisis(), 
                    on=merge_cols, how="inner")

        df[con.N_DIFFERENCE] = df[con.N_CRISIS] - df[con.N_BASELINE]
        df[con.DENSITY_BASELINE] = df[con.N_BASELINE] / df[con.N_BASELINE].sum()
        df[con.DENSITY_CRISIS] = df[con.N_CRISIS] / df[con.N_CRISIS].sum()
        df[con.PERCENT_CHANGE] = df[con.N_DIFFERENCE] * 100 / (df[con.N_BASELINE] + con.EPSILON)
        df[con.Z_SCORE] = df[con.N_DIFFERENCE] / df['n_baseline_std']
        df[con.DS] = df[con.DATE_TIME].dt.date
        
        self.__data = df
        print("All Done.")

    def load_from_file(self):
        """
        Loads data and returns it as a DataFrame 

        Returns
        -------
        pd.DataFrame
            DataFrame with loaded ping data
        """


        print(f"{TAB}Loads data from file.")

        df = pd.DataFrame()
        date_parser = lambda x: datetime.datetime.strptime(x, con.DEFAULT_DT_FORMAT)
        for file in os.listdir(self.data_dir()):
            file_path = os.path.join(self.data_dir(), file)
            try:
                df_tmp = pd.read_csv(file_path, parse_dates=[con.DATE], date_parser=date_parser)

                # Check minimun required columns
                if not set(set(con.DATASET_MIN_COLS)).issubset(df_tmp.columns):
                    error_fun.write_error(sys.argv[0], f"incorrect data structure for file {file_path}", 
                                "error", datetime.datetime.now())
                    continue

                df_tmp.rename(columns={con.DATE: con.DATE_TIME,
                                       con.LAT: con.LATITUDE, 
                                       con.LON: con.LONGITUDE}, inplace=True)

                

                df = pd.concat([df, df_tmp])

            except Exception as e:
                error_fun.write_error(sys.argv[0], e, 
                                "error", datetime.datetime.now())

    
        if df.empty:
            raise Exception("Not possible to load data. Check error log.")
        
        print(f"{TAB}{TAB}Done.")
        
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
        print(f"{TAB}Builds raw dataset.")
        df_raw = self.load_from_file()

        # brings data to fb datetime intervals
        df_raw[con.DATE_TIME] = df_raw[con.DATE_TIME].apply(fb_fun.to_fb_date)

        # extract date of week for comparison
        df_raw[con.DAY_OF_WEEK] = df_raw[con.DATE_TIME].dt.weekday
        df_raw[con.HOUR] = df_raw[con.DATE_TIME].dt.hour

        # builds latitude, longitude and geometry ids
        if self.agg_geometry() == 'admin':
            try:
                gdf = gpd.read_file(self.__geo_file)
            except Exception as e:
                error_fun.write_error(sys.argv[0], e, 
                                "error", datetime.datetime.now())
                return
            gdf_raw = gpd.GeoDataFrame(
                df_raw, geometry=gpd.points_from_xy(df_raw[con.LONGITUDE], df_raw[con.LATITUDE]), crs="EPSG:4326"
            )
            gdf_raw = gdf_raw[[con.GEOMETRY, con.LATITUDE, con.LONGITUDE, con.ID]]
            gdf_raw = gdf.sjoin(gdf_raw, how="inner", predicate='contains')
            df_raw = pd.DataFrame(gdf_raw.drop(columns=[con.GEOMETRY]))
        
        if self.agg_geometry() == 'tile':
            tile_lat, tile_lon, tile_ids = fb_fun.extract_quad_keys(df_raw[[con.LATITUDE, con.LONGITUDE]].to_numpy())
            df_raw[self.__geo_col_name] = tile_ids.tolist()
            df_raw[con.LATITUDE] = tile_lat.tolist()
            df_raw[con.LONGITUDE] = tile_lon.tolist()

        # If the same person appeared at multiple locations in a time interval we only count their most frequent location.
        df_raw.sort_values(con.DATE_TIME, inplace=True)
        df_raw.drop_duplicates(subset=[con.ID, con.DATE_TIME], 
                                keep="last", inplace=True)
        
        # agregates
        group_by_cols = [con.LATITUDE, con.LONGITUDE, con.DATE_TIME] + self.__baseline_cols
        df_raw["count"] = 1
        df = df_raw.groupby(group_by_cols)["count"].sum().reset_index()
                
        # build baseline
        print(f"{TAB}{TAB}Builds baseline.")
        df_baseline_raw = df[df[con.DATE_TIME] < self.crisis_datetime()]
        if df_baseline_raw.empty:
            error_fun.write_error(sys.argv[0], f"No data found before disaster date. Can't build baseline.", 
                                "warning", datetime.datetime.now())
        else:
            group_by_cols = [con.LATITUDE, con.LONGITUDE] + self.__baseline_cols
            df_baseline = df_baseline_raw.groupby(group_by_cols, as_index=False) \
                                                    .agg({"count": ['mean','std']})
            
            # df_baseline.rename(columns={"count" : con.N_BASELINE}, inplace=True)
            
            baseline_cols = group_by_cols + [con.N_BASELINE, 'n_baseline_std']
            df_baseline.columns = baseline_cols
            
            # make sure std is at least 0.1
            df_baseline['n_baseline_std'] = df_baseline['n_baseline_std'].fillna(con.MIN_STD)
            df_baseline.loc[df_baseline['n_baseline_std'] < con.MIN_STD,'n_baseline_std' ] =  con.MIN_STD

            self.__baseline = df_baseline

        self.__baseline_loaded = True

        # build crisis
        print(f"{TAB}{TAB}Builds crisis.")
        df_crisis = df[df[con.DATE_TIME] >= self.crisis_datetime()]
        if df_crisis.empty:
            error_fun.write_error(sys.argv[0], f"No data found after disaster date. Can't build crisis.", 
                                "warning", datetime.datetime.now())
            
            self.__crisis = df_crisis
        else:
            df_crisis.rename(columns={"count": con.N_CRISIS}, inplace=True)
            self.__crisis = df_crisis

        self.__crisis_loaded = True
        print(f"{TAB}{TAB}Done.")
 
        

    def write_dataset_to_file(self):
        out_folder = os.path.join(self.__out_dir, f"{self.dataset_id()}", 
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
                if self.__agg_geometry == "tile":
                    df_tmp[con.FB_TILE_POP_DENSITY_COLS].to_csv(out_file, index=False)
                elif self.__agg_geometry == "admin":
                    df_tmp[con.FB_ADMIN_POP_DENSITY_COLS].to_csv(out_file, index=False)
