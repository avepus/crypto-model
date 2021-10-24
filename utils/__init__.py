from re import split
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
    #set timeframe to the alpha character in the string
    timeframe = ''.join(char for char in timeframe_string if not char.isdigit())
    #set factor to the digits
    digits = ''.join(char for char in timeframe_string if char.isdigit())
    factor = int(digits) if digits else 1
    return timeframe_map[timeframe] * factor

def timeframe_name(timeframe_string):
    """Converts a timeframe string to a the highest time increment"""
    secs = convert_timeframe_to_sec(timeframe_string)
    increment_symbol = get_highest_time_increment(secs)
    increments = int(secs / timeframe_map[increment_symbol])
    return str(increments) + increment_symbol
    
def get_highest_time_increment(seconds):
    if seconds % timeframe_map['D'] == 0: return 'D'
    if seconds % timeframe_map['H'] == 0: return 'H'
    if seconds % timeframe_map['M'] == 0: return 'M'
    else: raise ValueError(f"timeframe value of {seconds} seconds is invalid")


def convert_timeframe_to_ms(timeframe_string):
    """Converts timeframe string to milliseconds"""
    return convert_timeframe_to_sec(timeframe_string) * 1000
    

if __name__ == "__main__":
    print(convert_timeframe_to_sec('m') % timeframe_map['M'])
