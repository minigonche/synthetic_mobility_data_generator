# Population network for Panama and Costa Rica
from simulator.population_networks.generic.population_network_from_hdx import PopulationNetworkFromHDX
from os.path import join
import simulator.constants as con

world_pop_density_file = join(con.DATA_FOLDER,"costa_rica-panama/pd_2020_1km_ASCII_XYZ.csv")
populated_places_folder = join(con.DATA_FOLDER,"costa_rica-panama/hotosm_populated_places_points_shp")
road_lines_folder = join(con.DATA_FOLDER,"costa_rica-panama/hotosm_roads_lines_shp")
building_polygons_folder = join(con.DATA_FOLDER,"costa_rica-panama/hotosm_buildings_polygons_shp")


class PanamaCostaRica(PopulationNetworkFromHDX):
    '''
    Class for Panama and Costa Rica Population Network
    '''

    def __init__(self):
        super().__init__(id = "panama-costarica",
                        name = "Panama y Costa Rica",
                        world_pop_density_file = world_pop_density_file,
                        populated_places_folder = populated_places_folder,
                        road_lines_folder = road_lines_folder,
                        building_polygons_folder  = building_polygons_folder)
        