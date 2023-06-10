import numpy as np
from abc import ABC
import geopandas as gpd
import pandas as pd

from simulator.population_networks.abstract.population_network import PopulationNetwork
from simulator.disasters.abstract.disaster import Disaster
import simulator.constants as con

from simulator.disasters.specific.drill_earthquake import DrillEarthQuake
from simulator.population_networks.specific.panama_costarica_zoom import PanamaCostaRicaZoom

from simulator.simulations.abstract.simulation import Simulation


from datetime import datetime, timedelta
from scipy.special import expit
from shapely.geometry import Point


# Specific Variables
start_date_str = '2017-08-20 00:00:00'
end_date_str = '2017-08-30 00:00:00'
population_with_coverage = 0.3 # Percentage of Population with coverage
frequency_hours = 4

class PanamaDrill(Simulation):
    """
    The CEPREDENAC Panama Drill on June 12 2023
    ...
    
    """

    def __init__(self):
        
        super().__init__(
            id = "panama_costa_rica_drill",
            start_date =  datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S'),
            end_date =  datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S'),
            frequency = frequency_hours,
            disaster = DrillEarthQuake(),
            population_network = PanamaCostaRicaZoom()
        )

    
    def simulate(self):
        """
        This is the main method for this package. Each iteration has 4 steps
            1. interact: 
                gets DisasterDistribution and calculates force array
            2. update_flow: 
                calculates PopulationNetwork (population_network_1) using calculated force array
            3. sample:
                samples data from PopulationNetwork (population_network_1), accounting for
                previous state (population_network_0.sample())
            4. step : population_network_0 = population_network_1

        The first two steps create a new population network with adjusted weights to 
        account for a possible disaster and adjusted node attributes to account
        for possible fatalities. The third step is then called on the new population
        network to create a mobility dataset at that moment. The last step sets up the next
        iteration. 

        The simulated data is then written to file.
        """

        # Extracts Population Network and 
        population_network = self.population_network
        disaster = self.disaster

        # Extracts Neighbors
        adjacent_nodes = {}

        for node_id in population_network.nodes[con.ID]:
            
            # Creates the slice
            neighbors = set([node_id])

            # Node 1
            try:
                neighbors = neighbors.union(population_network.edges.loc[pd.IndexSlice[node_id, :], con.NODE_ID2].values)
            except KeyError:
                pass

            # Node 2
            try:
                neighbors = neighbors.union(population_network.edges.loc[pd.IndexSlice[:,node_id], con.NODE_ID1].values)
            except KeyError:
                pass

            adjacent_nodes[node_id] = list(neighbors)

        self.adjacent_nodes = adjacent_nodes
        
        # Starts Simulation
        self.disaster_on = False

        # Tracking set
        population_network.nodes["dist"] = population_network.nodes.apply(lambda row: (row[con.LON] - disaster.epicenter[1])**2 + (row[con.LAT] - disaster.epicenter[0])**2, axis = 1) 
        tracking_set = set(population_network.nodes.sort_values("dist").head(40)[con.ID].values)

        total_elements = int(np.round(population_with_coverage*population_network.nodes[con.POPULATION].sum()))

        # Creates IDs
        ids = np.array([i for i in range(total_elements)])
        device_positions = population_network.initial_sample(ids)

        # Creates device trajectories
        device_trajectories = device_positions.rename(columns = {con.NODE_ID : con.START_NODE})
        device_trajectories[con.END_NODE] = device_trajectories[con.START_NODE]

        # Sets Up

        # Updates flow and nodes
        population_network.update_flow()
        nodes = population_network.nodes


        # Initializes movement (all devices are in nodes) 
        device_trajectories = device_trajectories[[con.START_NODE]].groupby(con.START_NODE).apply(self.extract_destination_node)
        if device_trajectories.index.nlevels > 1:
            device_trajectories = device_trajectories.droplevel(0)

        # Assigns position of lat and Lon of Start Node
        device_trajectories[con.LON] = nodes.loc[device_trajectories[con.START_NODE], con.LON].values
        device_trajectories[con.LAT] = nodes.loc[device_trajectories[con.START_NODE], con.LAT].values

        # Sets up device positions
        device_positions[con.LON] = device_trajectories[con.LON] 
        device_positions[con.LAT] = device_trajectories[con.LAT] 


        # Starts Simulation

        # For plotting
        center = pd.DataFrame({con.LON : [disaster.epicenter[1]], con.LAT :[disaster.epicenter[0]]})
        center = gpd.GeoDataFrame(center, geometry = center.apply(lambda row : Point(row.lon, row.lat) , axis = 1), crs = con.USUAL_PROJECTION)


        current_date = self.start_date

        while current_date <= self.end_date:

            print(f"{current_date}")
            
            print(f"   Population in area of interest: { device_positions[device_positions[con.NODE_ID].isin(tracking_set)].shape[0]}")

            # Updates nodes
            fun = disaster.get_function_by_date(current_date)

            if fun is None:
                population_network.update_flow()
                print("   Disaster has not started")
            else:
                self.disaster_on = True
                # Extracts Forces
                force = fun.intensity(population_network.nodes.apply(lambda row : (row[con.LON], row[con.LAT]), axis=1))
                print(f"   Min Force: {np.round(np.min(force),4)}   Max Force: {np.round(np.max(force),4)}")
                population_network.update_flow(force = force)

            # Divides in two
            node_trajectories = device_trajectories[device_trajectories[con.START_NODE] == device_trajectories[con.END_NODE]]
            edge_trajectories = device_trajectories[device_trajectories[con.START_NODE] != device_trajectories[con.END_NODE]].copy()


            # Process node trajectories
            # --------------------------
            new_edge_trajectories = node_trajectories[[con.START_NODE]].groupby(con.START_NODE).apply(self.extract_destination_node)
            if new_edge_trajectories.index.nlevels > 1:
                new_edge_trajectories = device_trajectories.droplevel(0)
            # Process edge trajectories
            # --------------------------
            # Two modes
            if self.disaster_on:
                edge_trajectories[con.REACH_PROBABILITY] = nodes.loc[edge_trajectories[con.END_NODE], con.FINAL_FORCE].apply(expit).values
                edge_trajectories[con.REACH_PROBABILITY] /= ( edge_trajectories[con.REACH_PROBABILITY].values + nodes.loc[edge_trajectories[con.START_NODE], con.FINAL_FORCE].apply(expit)).values
            else:
                edge_trajectories[con.REACH_PROBABILITY] = nodes.loc[edge_trajectories[con.END_NODE], con.FINAL_FORCE].values
                edge_trajectories[con.REACH_PROBABILITY] /= edge_trajectories[con.REACH_PROBABILITY].values + nodes.loc[edge_trajectories[con.START_NODE], con.FINAL_FORCE].values

            random_vector = np.random.random(edge_trajectories.shape[0])

            # Devices that reach
            edge_trajectories.loc[random_vector <= edge_trajectories[con.REACH_PROBABILITY], con.START_NODE] = edge_trajectories[con.END_NODE]

            # Devices that don't
            edge_trajectories.loc[random_vector > edge_trajectories[con.REACH_PROBABILITY], con.END_NODE] = edge_trajectories[con.START_NODE]


            # Consolidates
            new_node_trajectories = edge_trajectories[[con.ID, con.START_NODE, con.END_NODE]]

            # Creates new frame
            new_device_trajectories = pd.concat((new_edge_trajectories, new_node_trajectories))

            new_device_positions = population_network.sample(device_positions, new_device_trajectories.loc[device_positions[con.ID], con.END_NODE].values)
            
            # Sets Date
            date_string = current_date.strftime("%m-%d-%Y_%H:%M:%S")
            new_device_positions[con.DATE] = date_string

            self.export_iteration(date_string, new_device_positions)

            # Advances
            device_positions = new_device_positions
            device_trajectories = new_device_trajectories

            current_date += timedelta(hours = self.frequency)

            ax = gpd.GeoDataFrame(device_positions, geometry = device_positions.apply(lambda row : Point(row.lon, row.lat) , axis = 1), crs = con.USUAL_PROJECTION).plot(markersize = 0.1)
            center.plot(color = "red", ax = ax)








    # Support Methods
    def extract_destination_node(self, df):
        '''
        Extracts the next nodes for the current node
        '''

        node_id = df[con.START_NODE].iloc[0]

        forces = self.population_network.nodes.loc[self.adjacent_nodes[node_id],[con.FINAL_FORCE]]

        if self.disaster_on:
            forces[con.FINAL_FORCE] = forces[con.FINAL_FORCE].apply(expit)

        # Top 3
        forces = forces.sort_values( by = con.FINAL_FORCE, ascending = False).head(min(5, forces.shape[0]))

        #if node_id in tracking_set or len(tracking_set.intersection(forces.index.values)) > 0:
        #    print(node_id)
        #    display(forces)

        forces[con.FINAL_FORCE] /= forces[con.FINAL_FORCE].sum()


        new_positions = np.random.choice(forces.index.values, df.shape[0],
                p= forces[con.FINAL_FORCE].values)

        return pd.DataFrame({con.ID : df.index, con.START_NODE : node_id, con.END_NODE : new_positions}, index = df.index)


    