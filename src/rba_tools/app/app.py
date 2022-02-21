# -*- coding: utf-8 -*-
"""Web app for analyzing data

Created on Sunday 1/22/22

@author: Avery

"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from rba_tools.backtest.rba_backtrader_set import BacktraderSet
import rba_tools.retriever.get_crypto_data as gcd
import rba_tools.backtest.backtrader_extensions.strategies as strategies

from rba_tools.backtest.rba_backtrader_set import BacktraderSet

class RBASetPlotter:

    def __init__(self, set: BacktraderSet, plots: list, start_index: int = 0):
        """creates app

        Args:
            set (BacktraderSet): BacktraderSet which will be analyzed in the App
            plots (list): list of callable functions taking cerebro run data as parameter and returning plotly graph
            start_index (int, optional): Symbol index to start with. Defaults to 0.
        """
        self.set = set
        self.plots = plots
        self.index = start_index




kraken_puller = gcd.DataPuller.kraken_puller()
rba_set = BacktraderSet(['ETH/USD'], strategies.MaCrossStrategy, '1/1/18', '1/1/20', '1d', kraken_puller)

#set_plotter = RBASetPlotter(rba_set, [])



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

dash_app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF',
    'entry': '#00FF00',
    'exit': '#FFA07A'}


dash_app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    dcc.Graph(
        id='example-graph',
        figure=rba_set.current_symbol_figure
    ),
        dcc.Input(
        id='directory',
        type='text',
        placeholder=rba_set.symbol_list[rba_set.current_symbol_index],
        value=rba_set.symbol_list[rba_set.current_symbol_index],
        debounce=True,
        size='70'
        ),
    html.Button('Reload Graph', id='reload-button'),
    dcc.Dropdown(
        id='symbol-dropdown',
        value=rba_set.symbol_list[rba_set.current_symbol_index]
        ),
    html.Div(id='output-container-button',
             children='Enter a value and press submit',
             style={'color': colors['text']}),
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
    

# @dash_app.callback(
#     dash.dependencies.Output('example-graph', 'figure'),
#     [dash.dependencies.Input('example-graph', 'relayoutData'),
#      dash.dependencies.Input('reload-button', 'n_clicks')]
#     )
# def update_graph(relayoutData, n_clicks):
#     (start_range, end_range) = getStartAndEndRange(relayoutData)
    
#     if start_range is None:
#         start_range = myset.data.index[0]
#         end_range = myset.data.index[len(myset.data.index) - 1]
    
#     rangeMin = myset.data.loc[start_range:end_range, 'Low'].values.min()
#     rangeMax = myset.data.loc[start_range:end_range, 'High'].values.max()
    
#     return {
#             'data': [
#                 {'type': 'candlestick',
#                   'open' : myset.data['Open'],
#                   'high' : myset.data['High'],
#                   'low' : myset.data['Low'],
#                   'close' : myset.data['Close'],
#                   'x' : myset.data.index,
#                   'name' : myset.name},
#                 {'type': 'scatter',
#                  'name': 'Entries',
#                  'x' : df.index,
#                  'y' : df['High'],
#                  'mode': 'markers',
#                  'marker' : {'size' : 5, 'color' : colors['entry']},
#                  'text' : df['Win/Loss %']},
#                 {'type': 'scatter',
#                  'name': 'Exits',
#                  'x' : df['ExitTime'],
#                  'y' : df['exitPrice'],
#                  'mode': 'markers',
#                  'marker' : {'size' : 5, 'color' : colors['exit']},
#                  'text' : df['Win/Loss %']},
#                 ],
#             'layout': {
#                 'title': myset.name,
#                 'plot_bgcolor': colors['background'],
#                 'paper_bgcolor': colors['background'],
#                 'yaxis' : {'range' : [rangeMin, rangeMax]},
#                 'xaxis' : {'range' : [start_range, end_range],
#                            'rangeslider': {'visible': False}},
#                 'font': {
#                     'color': colors['text']
#                     }
#             }
#         }

@dash_app.callback(
    dash.dependencies.Output('symbol-dropdown', 'options'),
    [dash.dependencies.Input("directory", "value")],
)
def fileList(directory):
    try:
        return [{'label': symbol, 'value': rba_set.symbol_list.index(symbol)} for symbol in rba_set.symbol_list]
    except:
        return [{'label': "<No Symbols Found>", 'value': 0}]

@dash_app.callback(
    dash.dependencies.Output('output-container-button', 'children'),
    [dash.dependencies.Input('symbol-dropdown', 'value')])
def change_data_source(value):
    rba_set.current_symbol_index = value #need to make sure this calls other updates
    #myset.load_csv() #need to make sure this reloads updates
    return ''

if __name__ == '__main__':
    dash_app.run_server(debug=True)