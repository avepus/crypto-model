# -*- coding: utf-8 -*-
"""Web app for analyzing data

Created on Sunday 1/22/22

@author: Avery

"""

from dash import dcc, html, Dash
import plotly.graph_objects as go
from rba_tools.backtest.backtrader_extensions.plotting.plotinfo import unpickle_last_dpic

app_dict = {'dpic': unpickle_last_dpic()}
colors = {
    'background': '#111111',
    'text': '#7FDBFF',
    'entry': '#00FF00',
    'exit': '#FFA07A'}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

dash_app = Dash(__name__, external_stylesheets=external_stylesheets)


dash_app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    dcc.Graph(
        id='ohlcv-graph',
        figure=app_dict['dpic']
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
#     dash.dependencies.Output('ohlcv-graph', 'figure'),
#     [dash.dependencies.Input('ohlcv-graph', 'relayoutData'),
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