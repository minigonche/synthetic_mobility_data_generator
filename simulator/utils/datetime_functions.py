import datetime 

def round_nearest_hour(t : datetime.datetime) -> datetime.datetime:
    """
    Round datetime to the nearest hour.
    """
    rounded = t.replace(second=0, microsecond=0, minute=0, hour=t.hour) \
               + datetime.timedelta(hours=t.minute//30)
    
    return rounded