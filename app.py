# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import *
import pandas as pd
import plotly.graph_objects as go

from utils import *
from utils_tensorflow import *
from forecast import fit_arma

from tensorflow import keras
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# data = pd.read_pickle('data/bpi_data.pkl')
# data = update_bpi_file(data)

ticker = '^GSPC'
df = load_ticker_data(ticker, start_history='2012-01-01')
data = df['adjclose']

model = keras.models.load_model('models/keras_tuned_model.h5')
past_history = 30
target_size = 7

dataset, _, col_scaler = prepare_dataset(df, 'adjclose')

LAST_SEQUENCE = dataset.shape[0] - 1 - past_history
test_batch = prepare_test_batch(dataset, LAST_SEQUENCE, None,  past_history).take(1)
prediction = model.predict(test_batch)[0]
prediction_rescaled = return_original_scale(prediction, col_scaler['adjclose'])

business_days = CustomBusinessDay(calendar=USFederalHolidayCalendar())
try:
    start_date = datetime.strptime(df.index[-1], '%Y-%m-%d') + timedelta(days=1)
except TypeError:
    start_date = df.index[-1] + timedelta(days=1)

prediction_index = pd.date_range(start=start_date, periods=target_size, freq=business_days)


p = 12
q = 0
data.index = pd.DatetimeIndex(data.index)
# pred_start = data.index.max()
# pred_end = pred_start + pd.Timedelta(days=30)
# pred = fit_arma(data, p, q, pred_start, pred_end)

fig = go.Figure()
fig.add_trace(go.Scatter(x=data.index,
                         y=data.values,
                         name=ticker,
                         mode='lines',
                         line_color='deepskyblue'))

fig.add_trace(go.Scatter(x=prediction_index,
                         y=prediction_rescaled.flatten(),
                         name="Tensorflow forecast",
                         mode='lines',
                         line_color='green',
                         line_dash='dash'))

# fig.add_trace(go.Scatter(x=pred.index,
#                          y=pred.values,
#                          name="ARMA forecast",
#                          mode='lines',
#                          line_color='green',
#                          line_dash='dash'))

fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=3,
                     label="3m",
                     step="month",
                     stepmode="backward"),
                dict(count=6,
                     label="6m",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(count=1,
                     label="YTD",
                     step="year",
                     stepmode="todate"),
                dict(step="all")
            ])
        ),
        # autorange=True,
        # rangeslider=dict(
        #     visible=True
        # ),
        type="date"
    ),
    yaxis=dict(
        autorange=True
    ),
    height=400,
    width=800
)


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H2(children='S&P 500 Index Dashboard'),

    html.H4(show_current_date()),

    html.H5(children='This dashboard is my learning effort during Machine Learning bootcamp. '
                     'The ultimate purpose of creating it is learning prediction of time series data.'),

    # html.H5(f'Presented data range is: {data.index.min()} - {data.index.max()}'),

    html.Div(
        id='div1'
    ),

    dcc.Graph(
        id='bpi-graph',
        figure=fig
    )

])


# TODO: get this callback working. See https://dash.plot.ly/getting-started-part-2
@app.callback(
    Output('div1', 'children'),
    [Input('bpi-graph', 'figure')])
def get_ranges(figure):
    # Make data available in the scope of this function.
    global data

    # slider_range = figure.layout.xaxis.Rangeslider.range
    slider_range = figure['layout']['xaxis']['range']
    # print(slider_range)
    output = f'''
            Author: Kuba Kozłowski
            range {slider_range}
        '''
    # new_y_low = data[slider_range[0]]
    # new_y_high = data[slider_range[1]]

    # fig.update_layout(
    #     yaxis=dict(
    #         autorange=False,
    #         range=[new_y_low, new_y_high]
    #     )
    # )

    return output


if __name__ == '__main__':
    app.run_server(debug=True)