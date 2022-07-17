# -*- coding: utf-8 -*-
"""Web app for analyzing data

Created on Sunday 1/22/22

@author: Avery

"""

from dash import dcc, html, Dash, dependencies
from dataclasses import dataclass,field
import plotly.graph_objects as go
from rba_tools.backtest.backtrader_extensions.plotting.data_plot_info_container import DataPlotInfoContainer,unpickle_last_dpic,get_last_dpic_file_name,get_pickle_file_list,unpickle_dpic
import rba_tools.backtest.backtrader_extensions.plotting.plot as rbsplot
import rba_tools.constants as constants

@dataclass
class AppInfo:
    dpic: DataPlotInfoContainer = field(default=unpickle_last_dpic())
    file: str = field(default=get_last_dpic_file_name())

app_info = AppInfo()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(style={'backgroundColor': constants.COLORS['background']}, children=[
    # dcc.Input(
    #     id='directory',
    #     type='text',
    #     placeholder=app_info.file,
    #     value=app_info.file,
    #     debounce=True,
    #     size='70'
    #     ),
    dcc.Dropdown(get_pickle_file_list(), app_info.file, id='file-dropdown'),
    dcc.Graph(id='ohlcv-graph'),
    html.Button('Reload Graph', id='reload-button'),
    html.Div(id='div_variable')
    ,
    # html.Div(id='output-container-button',
    #          children='Enter a value and press submit',
    #          style={'color': colors['text']}),
        ])
        


def trimDatetime(d): #not sure if neede
    loc = d.find('.')
    if loc == -1:
        return d
    return d[0:loc]

def getStartAndEndRange(relayoutData): #not sure if needed. probably merge into rba_set
    if relayoutData is None:
        return (None, None)
    if 'xaxis.range[0]' in relayoutData.keys():
        start_range = relayoutData['xaxis.range[0]']
        start_range = trimDatetime(start_range)
        end_range = relayoutData['xaxis.range[1]']
        end_range = trimDatetime(end_range)
        return (start_range, end_range)
    if 'xaxis.range' in relayoutData.keys():
        start_range = relayoutData['xaxis.range'][0]
        start_range = trimDatetime(start_range)
        end_range = relayoutData['xaxis.range'][1]
        end_range = trimDatetime(end_range)
        return (start_range, end_range)
    return (None, None)
    

@app.callback(
    [dependencies.Output('ohlcv-graph', 'figure'),
    dependencies.Output('div_variable', 'children')],
    [dependencies.Input('ohlcv-graph', 'relayoutData'),
     dependencies.Input('reload-button', 'n_clicks'),
     dependencies.Input('file-dropdown', 'value')]
    )
def update_graph(relayoutData, n_clicks, value):
    (start_range, end_range) = getStartAndEndRange(relayoutData)

    if not value == app_info.file:
        app_info.file = value
        app_info.dpic = unpickle_dpic(value)

    dpic_fig_list = rbsplot.get_data_plot_info_container_plot_list(app_info.dpic, start_range, end_range)

    candlestick_fig = dpic_fig_list.pop(0)

    ind_plot_list = [dcc.Graph(id='graph' + str(i), figure=dpic_fig_list[i]) for i in range(len(dpic_fig_list))]

    return [candlestick_fig,
            ind_plot_list]

# @app.callback(
#     dash.dependencies.Output('output-container-button', 'children'),
#     [dash.dependencies.Input('symbol-dropdown', 'value')])
# def change_data_source(value):
#     rba_set.current_symbol_index = value #need to make sure this calls other updates
#     #myset.load_csv() #need to make sure this reloads updates
#     return ''

if __name__ == '__main__':
    app.run_server(debug=True)