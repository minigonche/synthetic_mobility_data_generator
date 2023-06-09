# Population network for Panama and Costa Rica
from simulator.population_networks.generic.population_network_from_hdx_no_geometry import PopulationNetworkFromHDXNoGeometry
from os.path import join
import simulator.constants as con


world_pop_density_file = join(con.DATA_FOLDER,"costa_rica-panama/pd_2020_1km_ASCII_XYZ.csv")
populated_places_folder = join(con.DATA_FOLDER,"costa_rica-panama/hotosm_populated_places_points_shp")


class PanamaCostaRicaZoom(PopulationNetworkFromHDXNoGeometry):
    '''
    Class for Panama and Costa Rica Population Network Zoomed at the earthquake for the simulaton
    '''

    def __init__(self):
        super().__init__(id = "panama-costarica-zoom",
                        name = "Panama y Costa Rica (Zoomed)",
                        world_pop_density_file = world_pop_density_file,
                        populated_places_folder = populated_places_folder,
                        min_lon = -83.518,
                        max_lon = -82.3717,
                        min_lat = 8.0006,
                        max_lat  = 8.9862)
        