# -*- coding: utf-8 -*-
"""Web app for analyzing data

Created on Sunday 1/22/22

@author: Avery

"""

from dash import dcc, html, Dash, dependencies
import plotly.graph_objects as go
from dataclasses import dataclass,field
from rba_tools.backtest.backtrader_extensions.plotting.plotinfo import unpickle_last_dpic,DataAndPlotInfoContainer
import rba_tools.backtest.backtrader_extensions.plotting.plot as rbsplot
import rba_tools.constants as constants

@dataclass
class AppInfo:
    dpic: DataAndPlotInfoContainer = field(default=unpickle_last_dpic())

app_info = AppInfo()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(style={'backgroundColor': constants.COLORS['background']}, children=[
    dcc.Graph(id='ohlcv-graph'),
    html.Button('Reload Graph', id='reload-button'),
    # ,
    #     dcc.Input(
    #     id='directory',
    #     type='text',
    #     placeholder=rba_set.symbol_list[rba_set.current_symbol_index],
    #     value=rba_set.symbol_list[rba_set.current_symbol_index],
    #     debounce=True,
    #     size='70'
    #     ),
    # html.Button('Reload Graph', id='reload-button'),
    # dcc.Dropdown(
    #     id='symbol-dropdown',
    #     value=rba_set.symbol_list[rba_set.current_symbol_index]
    #     ),
    # html.Div(id='output-container-button',
    #          children='Enter a value and press submit',
    #          style={'color': colors['text']}),
        ])
        


def trimDatetime(d): #not sure if needed
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
    dependencies.Output('ohlcv-graph', 'figure'),
    [dependencies.Input('ohlcv-graph', 'relayoutData'),
     dependencies.Input('reload-button', 'n_clicks')]
    )
def update_graph(relayoutData, n_clicks):
    (start_range, end_range) = getStartAndEndRange(relayoutData)
    
    return rbsplot.get_candlestick_plot_from_dpi(app_info.dpic.data_and_plots_list[0], start_range, end_range)
    return {
            'data': [
                {'type': 'candlestick',
                  'open' : df['Open'],
                  'high' : df['High'],
                  'low' : df['Low'],
                  'close' : df['Close'],
                  'x' : df.index,
                  'name' : app_info.dpic.strategy}
                ],
            'layout': {
                'title': app_info.dpic.strategy,
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'yaxis' : {'range' : [rangeMin, rangeMax]},
                'xaxis' : {'range' : [start_range, end_range],
                           'rangeslider': {'visible': False}},
                'font': {
                    'color': colors['text']
                    }
            }
        }

# @app.callback(
#     dash.dependencies.Output('symbol-dropdown', 'options'),
#     [dash.dependencies.Input("directory", "value")],
# )
# def fileList(directory):
#     try:
#         return [{'label': symbol, 'value': rba_set.symbol_list.index(symbol)} for symbol in rba_set.symbol_list]
#     except:
#         return [{'label': "<No Symbols Found>", 'value': 0}]

# @app.callback(
#     dash.dependencies.Output('output-container-button', 'children'),
#     [dash.dependencies.Input('symbol-dropdown', 'value')])
# def change_data_source(value):
#     rba_set.current_symbol_index = value #need to make sure this calls other updates
#     #myset.load_csv() #need to make sure this reloads updates
#     return ''

if __name__ == '__main__':
    app.run_server(debug=True)