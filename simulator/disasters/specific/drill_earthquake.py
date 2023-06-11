import numpy as np

# Drill Earthquake
from simulator.disasters.generic.earthquake import Earthquake
from simulator.disasters.generic.uniform_disaster_dist import UniformDisasterFun

from datetime import datetime

class DrillEarthQuake(Earthquake):
    '''
    Class for the drill earthquake
    epicenter:  
        8º24´18.71 N – 82º50´31.28 -> (8.405197, -82.842022) (PANAMA)
        8º31´56.04 N – 89º40´20.79 -> (8.532233, -89.672442) (COSTA RICA)
        Magnitude: 7,6 Mw  
        Depth: 5,6 km  
        Time: '2017-08-25 08:34:00'

    '''
    def __init__(self):
        super().__init__(
            id="Drill Earthquake",
            epicenter=(8.405197, -82.842022),
            start_date=datetime.strptime('2017-08-25 08:34:00', '%Y-%m-%d %H:%M:%S'),
            end_date=datetime.strptime('2017-08-26 09:00:00', '%Y-%m-%d %H:%M:%S'),
            continuity=datetime.strptime('2027-08-30 00:00:00', '%Y-%m-%d %H:%M:%S'),
            A0 = 7.6, 
            vxy = (0.5, 0.5), 
            method='exponential', 
            step_unit='hr',
            continuity_fun= UniformDisasterFun(mean=np.asarray((8.405197, -82.842022)), 
                                                radius_km = 100,
                                                amplitude=1.5)
        )
     
    