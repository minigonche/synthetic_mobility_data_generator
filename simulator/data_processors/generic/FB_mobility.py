import os
import sys
import warnings
import datetime
import pandas as pd
import geopandas as gpd

import simulator.utils.general as fun
import simulator.utils.errors as error_fun
import simulator.utils.facebook as fb_fun
import simulator.constants as con
import simulator.utils.geometric as geo_fun
from simulator.data_processors.abstract.data_processor import DataProcessor

TAB = "  "

class FBMobility(DataProcessor):
    """
    Class for constructing a mobility dataset with the same
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
            self.__geo_col_name = con.ADMIN_KEY
            assert self.__geo_file
        elif self.agg_geometry() == 'tile':
            self.__geo_col_name = con.QUAD_KEY
        else:
            self.__geo_col_name = "not_defined"

        baseline_cols = baseline_cols + [f"start_{self.__geo_col_name}"] \
              + [f"end_{self.__geo_col_name}"]

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
        Builds mobility dataset

        df structure:
            Index:
                RangeIndex
            Columns:
                Name: start_latitude, dtype: float
                Name: start_longitude, dtype: float
                Name: end_latitude, dtype: float
                Name: end_longitude, dtype: float
                Name: length_km, dtype: float
                Name: start_quadkey, dtype: str  *or start_id if agg by administrative geometry
                Name: end_quadkey, dtype: str  *or end_id if agg by administrative geometry
                Name: date_time, dtype: datetime
                Name: n_baseline, dtype: float64
                Name: n_crisis, dtype: float64
                Name: n_difference, dtype: float64
                Name: percent_change, dtype: float64
                Name: z_score, dtype: float64
                Name: ds, dtype: date

        """

        print("Calulates fb mobility statistics.")
        if not self.__crisis_loaded or not self.__baseline_loaded:
            self.load_data()
           
        if self.__crisis.empty :
            error_fun.write_error(sys.argv[0], 
                                    f"Can't calculate statistics without data after crisis date.", 
                            "warning", datetime.datetime.now())
            return 
            
        if self.__baseline.empty:
            error_fun.write_error(sys.argv[0], 
                                    f"Can't calculate statistics without baseline data.", 
                            "warning", datetime.datetime.now())
            return 
        

        # Merge left will remove entries that dont' have a baseline. This is NOT IDEAL
        # but it is currenlty how Data for Good handles it.
        merge_cols = [con.FB_START_LATITUDE, con.FB_START_LONGITUDE, con.FB_END_LATITUDE, con.FB_END_LONGITUDE] + self.__baseline_cols
        df = self.baseline().merge(self.crisis(), 
                    on=merge_cols, how="inner")
        
        #  Add length
        df[con.LENGTH_KM] = df.apply(lambda x: geo_fun.haversine(x[con.FB_START_LONGITUDE], 
                                                                    x[con.FB_START_LATITUDE], x[con.FB_END_LONGITUDE],
                                                                        x[con.FB_END_LATITUDE]), axis=1)

        df[con.N_DIFFERENCE] = df[con.N_CRISIS] - df[con.N_BASELINE]
        df[con.PERCENT_CHANGE] = df[con.N_DIFFERENCE] * 100 / (df[con.N_BASELINE] + con.EPSILON)
        df[con.Z_SCORE] = df[con.N_DIFFERENCE] / df['n_baseline_std']
        df[con.DS] = df[con.DATE_TIME].dt.date

        self.__data = df

        print("All Done.")

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
        print(f"{TAB}{TAB}Loads files from disk.")
        df_raw = fun.load_ping_data(self.data_dir())
        print(f"{TAB}{TAB}Done.")

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
            gdf = gdf[[con.GEOMETRY, con.ADMIN_KEY]]


            gdf_raw = gpd.GeoDataFrame(
                df_raw, geometry=gpd.points_from_xy(df_raw[con.FB_LONGITUDE], df_raw[con.FB_LATITUDE]), crs="EPSG:4326"
            )
            gdf_raw = gdf.sjoin(gdf_raw, how="left", predicate='contains')
            
            gdf_raw["centroid"] = gdf_raw[con.GEOMETRY].centroid
            gdf_raw[con.FB_LONGITUDE] = gdf_raw["centroid"].x
            gdf_raw[con.FB_LATITUDE] = gdf_raw["centroid"].y

            df_raw = pd.DataFrame(gdf_raw.drop(columns=[con.GEOMETRY]))
        
        if self.agg_geometry() == 'tile':
            tile_lat, tile_lon, tile_ids = fb_fun.extract_quad_keys(df_raw[[con.FB_LATITUDE, con.FB_LONGITUDE]].to_numpy())
            df_raw[self.__geo_col_name] = tile_ids.tolist()
            df_raw[con.FB_LATITUDE] = tile_lat.tolist()
            df_raw[con.FB_LONGITUDE] = tile_lon.tolist()

        # If the same person appeared at multiple locations in a time interval we only count their most frequent location.
        df_raw.sort_values(con.DATE_TIME, inplace=True)
        df_raw.drop_duplicates(subset=[con.ID, con.DATE_TIME], 
                                keep="last", inplace=True)
        
        # loop over date intervals
        dates = df_raw[con.DATE_TIME].unique() 
        start = dates[0]
        df_mov = pd.DataFrame()
        for idx, i in enumerate(dates):
            
            if idx == len(dates) - 1:
                break
            start = dates[idx]
            end = dates[idx + 1]
            # creates start and end dataframes
            df_start = df_raw[df_raw[con.DATE_TIME] == start].copy()
            df_start.rename(columns={con.FB_LATITUDE : con.FB_START_LATITUDE, 
                                        con.FB_LONGITUDE : con.FB_START_LONGITUDE,
                                        self.__geo_col_name : f"start_{self.__geo_col_name}"}, inplace=True)
            print(df_start.head())
            df_end = df_raw[df_raw[con.DATE_TIME] == end].copy()
            df_end.rename(columns={con.FB_LATITUDE : con.FB_END_LATITUDE, 
                            con.FB_LONGITUDE : con.FB_END_LONGITUDE, 
                            self.__geo_col_name : f"end_{self.__geo_col_name}"}, inplace=True)

            cols_drop = list(set(df_end.columns) - set([con.ID, con.FB_END_LATITUDE, 
                                                con.FB_END_LONGITUDE, f"end_{self.__geo_col_name}"]))
            df_end.drop(columns=cols_drop, inplace=True)
            print(df_end.head())

            # joins by device id
            merge_cols = [con.ID]
            df_tmp = df_start.merge(df_end, on=merge_cols, how='inner')
            df_tmp["count"] = 1
            groupby_cols = self.__baseline_cols + [con.DATE_TIME, con.FB_START_LATITUDE, 
                            con.FB_START_LONGITUDE, con.FB_END_LATITUDE, 
                            con.FB_END_LONGITUDE, con.DAY_OF_WEEK, con.HOUR]
            print(df_tmp.head())
            df_mov_tmp = df_tmp.groupby(groupby_cols)["count"].sum().reset_index()
            
            df_mov = pd.concat([df_mov, df_mov_tmp])

        # build baseline
        print(f"{TAB}{TAB}Builds baseline.")
        df_baseline_raw = df_mov[df_mov[con.DATE_TIME] < self.crisis_datetime()]
        if df_baseline_raw.empty:
            error_fun.write_error(sys.argv[0], f"No data found before disaster date. Can't build baseline.", 
                                "warning", datetime.datetime.now())
        else:
            group_by_cols = [con.FB_START_LATITUDE, con.FB_START_LONGITUDE, 
                 con.FB_END_LATITUDE, con.FB_END_LONGITUDE] + self.__baseline_cols 
            df_baseline = df_baseline_raw.groupby(group_by_cols, as_index=False) \
                                                    .agg({"count": ['mean','std']})
                        
            baseline_cols = group_by_cols + [con.N_BASELINE, 'n_baseline_std']
            df_baseline.columns = baseline_cols
            
            # make sure std is at least 0.1
            df_baseline['n_baseline_std'] = df_baseline['n_baseline_std'].fillna(con.MIN_STD)
            df_baseline.loc[df_baseline['n_baseline_std'] < con.MIN_STD,'n_baseline_std' ] =  con.MIN_STD

            self.__baseline = df_baseline

        self.__baseline_loaded = True

        # build crisis
        print(f"{TAB}{TAB}Builds crisis.")
        df_crisis = df_mov[df_mov[con.DATE_TIME] >= self.crisis_datetime()]
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
                            f"dataset=mobility", f"scale={self.__agg_geometry}")
        
        if not os.path.exists(out_folder):
            os.mkdir(out_folder)

        for date in self.__data[con.DS].unique():
            for hour in [0, 8, 16]:
                # file naming conventions
                date_str = datetime.datetime.strftime(date, "%Y-%m-%d")
                hour_str = f"0{hour}00" if hour // 10 == 0 else f"{hour}00"
                file_name = f"{self.dataset_id()}_{date_str}_{hour_str}.csv"
                out_file = os.path.join(out_folder, file_name)

                df_tmp = self.__data.loc[(self.__data[con.DS] == date) & (self.__data[con.HOUR] == hour)]
                df_tmp[con.DS] = date_str
                if self.__agg_geometry == "tile":
                    df_tmp[con.FB_TILE_MOBILITY_COLS].to_csv(out_file, index=False)
                elif self.__agg_geometry == "admin":
                    df_tmp[con.FB_ADMIN_MOBILITY_COLS].to_csv(out_file, index=False)

    def write_as_readymapper_output(self, out_folder):
        
        if not os.path.exists(out_folder):
            print(f"{TAB}Folder {out_folder} doesn't exist. Creating it.")
            os.mkdir(out_folder)

        if self.data().empty:
            print("No data to write.")
            return

        df = self.data()[[con.DS, con.DATE_TIME, con.FB_START_LATITUDE, 
                          con.FB_START_LONGITUDE, con.FB_END_LATITUDE, 
                          con.FB_END_LONGITUDE, con.PERCENT_CHANGE, con.N_CRISIS,
                          con.N_BASELINE, con.LENGTH_KM]]
        df[con.DATE_TIME] = df[con.DATE_TIME].dt.strftime(con.READYMAPPER_MOV_DT_FORMAT)

        df.rename(columns={con.DS : con.READYMAPPER_DT, 
                           con.FB_START_LATITUDE: con.READYMAPPER_START_LAT,
                            con.FB_START_LONGITUDE: con.READYMAPPER_START_LON,
                           con.FB_END_LATITUDE: con.READYMAPPER_END_LAT,
                           con.FB_END_LONGITUDE: con.READYMAPPER_END_LON}, inplace=True)

        df.to_csv(os.path.join(out_folder, "data.csv"), index=False)