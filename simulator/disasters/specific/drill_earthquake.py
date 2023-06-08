# Drill Earthquake
from simulator.disasters.generic.earthquake import Earthquake

from datetime import datetime

class DrillEarthQuake(Earthquake):
    '''
    Class for the drill earthquake
    '''
    def __init__(self):
        super().__init__(
            id="Drill Earthquake",
            epicenter=(8.360193, -82.869058),
            start_date=datetime.strptime('2023-03-01 13:55:26', '%Y-%m-%d %H:%M:%S'),
            end_date=datetime.strptime('2023-03-04 00:00:00', '%Y-%m-%d %H:%M:%S'),
            A0 = 3, 
            vxy = (1, 1), 
            method='exponential', 
            step_unit='hr')    