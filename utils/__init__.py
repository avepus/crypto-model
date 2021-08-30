timeframe_map = { 'S' : 1 }
timeframe_map['M'] = timeframe_map['S'] * 60
timeframe_map['H'] = timeframe_map['M'] * 60
timeframe_map['D'] = timeframe_map['H'] * 24

def convert_timeframe_to_sec(timeframe_string):
    """Converts timeframe string to seconds
    
    Parameters:
        timeframe_string (str) -- timeframe string, e.g. 'm' for one minute or '4h' for 4 hours

    Returns:
        The timeframe value in seconds
    """
    timeframe_string = timeframe_string.upper()
    timeframe = None
    factor = None
    if timeframe_string[0].isnumeric(): #if first value is number, assume it is the factor and the next value is the timeframe
        factor = timeframe_string[0]
        timeframe = timeframe_string[1]
    else: #if first value is not numeric, it is the timeframe
        timeframe = timeframe_string[0]
        if timeframe_string[1]:
            factor = timeframe_string[1]
    return timeframe_map[timeframe] * factor

def convert_timeframe_to_ms(timeframe_string):
    """Converts timeframe string to milliseconds"""
    return convert_timeframe_to_sec(timeframe_string) * 1000
    
    
