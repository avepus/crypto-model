from collections import OrderedDict
from dataclasses import field, dataclass


MATPLOTLIB_TO_PLOTLY_MARKER_MAP = {
    '^' : 'triangle-up',
    'v' : 'triangle-down',
    'o' : 'circle-dot'
}

MATPLOTLIB_TO_PLOTLY_COLOR_MAP = {
    'g' : 'green',
    'lime' : 'green'
}


@dataclass
class LinePlotInfo():
    """holds line level plot info which consists of the
    name of the line and the plotinfo dictionary variables
    used to determine how to plot the line.
    
    This is the individual line level of the plotting"""
    line_name: str
    plotinfo: dict
    overlay: bool = field(default=False)
    mode: str = field(default=None)
    markers: dict = field(init=False)

    def __post_init__(self):
        if isinstance(self.plotinfo, OrderedDict):
            self.plotinfo = dict(self.plotinfo)
        self.markers = get_marker_dict(self.plotinfo)


def get_marker_dict(plotinfo):
    """obtains the dictionary to passed into go.Scatter(... , marker=thisReturnValue)"""
    ret_dict = {}
    if plotinfo.get('color'):
        ret_dict['color'] = plotinfo.get('color')
        if MATPLOTLIB_TO_PLOTLY_COLOR_MAP.get(ret_dict['color']):
            ret_dict['color'] = MATPLOTLIB_TO_PLOTLY_COLOR_MAP.get(ret_dict['color'])
    
    if plotinfo.get('markersize'):
        ret_dict['size'] = plotinfo.get('markersize')

    if MATPLOTLIB_TO_PLOTLY_MARKER_MAP.get(plotinfo.get('marker')):
        ret_dict['symbol'] = MATPLOTLIB_TO_PLOTLY_MARKER_MAP.get(plotinfo.get('marker'))

    return ret_dict

