from dash.dependencies import Input, Output, State
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
import dash_table
from app import app
import datetime
from germination.yy_class import callDB
import plotly.graph_objects as go
import json

secretFileContentJson=json.load(open("D:/YY_DASH/line/secret_key",'r'))  # 載入line_secret_key資訊
dbcnt = callDB(
    secretFileContentJson.get("DB_IP"), 
    secretFileContentJson.get("DB_PORT"), 
    secretFileContentJson.get("DB_ACCOUNT"), 
    secretFileContentJson.get("DB_PASSWD"), 
    secretFileContentJson.get("DB_NAME")
)
# 設定繪圖功能紐
config={
    'displaylogo':False, 
    'modeBarButtonsToRemove':[
        'toImage', 
        'toggleSpikelines', 
        'lasso2d', 
        'autoScale2d',
    ]
}
loading_type='dot'
# 'graph', 'cube', 'circle', 'dot'

title = html.Div(
    [
        dbc.Row([
                dbc.Col(dbc.Row(html.H2('資料檢視區', id='apps_dashboard-title'), justify='center'), xl={'order':1, 'size':8}),
            ], 
            justify='end',
            align='center',
        )
    ], 
    className='nav_title'
)

input_group = dbc.InputGroup(
    [
        dbc.InputGroupAddon(
            dbc.Button("查詢", id="schedule_button"),
            addon_type="prepend",
        ),
        dbc.Input(id="schedule_input", placeholder="name"),
    ]
)


layout = html.Div(
    [
        title,
        dbc.Row(
            [
                dbc.Col(input_group)
            ]
        ), 
        dbc.Row(
            [
                dbc.Col(html.Div(id='text_record'))
            ]
        ), 
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='view_photo'))
            ]
        ), 
        html.P(id='records', hidden=True)
    ]
)



@app.callback(
    [
        Output('view_photo', 'figure'),
        Output('text_record', 'children'),
        Output('records', 'children'),
    ],
    [Input('schedule_button', 'n_clicks')],
    [
        State('schedule_input', 'value'),
        State('records', 'children'),
    ]
    )
def display_output(schedule_button, schedule_input, datetimes):
    print(schedule_button, schedule_input, datetimes)
    img, data_list = dbcnt.get_views(datetimes, schedule_input)
    if data_list != None:
        text = [
            html.P(data_list[0]),
            html.P(data_list[1]),
            html.P(data_list[2]),
            html.P(data_list[3]),
            html.P(data_list[4]),
        ]
        photo = go.Figure()
        photo = photo.add_trace(go.Image(z=img))
        photo = photo.update_layout(margin=dict(l=5, r=5, t=5, b=5))
        photo = photo.update_xaxes(showticklabels=False)
        photo = photo.update_yaxes(showticklabels=False)
       
        return photo, text, data_list[4]
    else:
        text = [
            html.P('最後一張'),
        ]
        return dash.no_update, text, ''
    



