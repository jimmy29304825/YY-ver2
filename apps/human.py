from dash.dependencies import Input, Output, State
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
from app import app
import datetime
import plotly.graph_objects as go
import cv2
import dash_table
import numpy as np
from germination.yy_class import callDB, par, germination
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


dropdown_week = dcc.Dropdown(
    options=[
        {'label':'', 'value':'empty'}
    ],
    id='crop_name',
    clearable=False,
    placeholder='請選擇物種',
)


title = html.Div(
    [
        dbc.Row([
                dbc.Col(
                    dbc.Row(html.H2('人工區', id='apps_dashboard-title'), justify='center'), 
                ),
            ], 
            justify='end',
            align='center',
        )
    ], 
    className='nav_title'
)
def make_fig(num, img):
    sp_image = go.Figure()
    sp_image = sp_image.add_trace(go.Image(z=img))
    sp_image = sp_image.update_layout(margin=dict(l=5, r=5, t=5, b=5))
    sp_image = sp_image.update_xaxes(showticklabels=False)
    sp_image = sp_image.update_yaxes(showticklabels=False)
    image_banner = html.Div(
        [
            dbc.Row(dbc.Col(dcc.Graph(figure=sp_image, id='image-%s' % str(num), style={'height':'300px'})), justify='center'),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button("未發芽", id='no_ger-%s' % str(num), color="danger", className="mt-auto"), 
                        width=dict(order='first')
                    ),
                    dbc.Col(
                        dbc.Button("發芽", id='is_ger-%s' % str(num), color="success", className="mt-auto"), 
                        width=dict(order='last')
                    ),
                ],
                justify='around'
            ),
            dbc.Row(dbc.Col(html.P(children=str(num), id='sponge_%s' % str(num), hidden=True))),
        ]
    )
    return image_banner
table = dash_table.DataTable(
    id='human_table',
    style_data_conditional=[{
        'if': {'row_index': 'odd'},
        'backgroundColor': 'rgb(248, 248, 248)'
    }],
    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
    page_size=15,
    style_table={'height': '500px'},
)

control_banner = dbc.Card(
    [
        dbc.CardHeader("輸入區"),
        dbc.CardBody(
            [
                dropdown_week, 
                html.Br(),
                dbc.Button("查詢", color="info", block=True, id='search_button'),
                html.Hr(),
                dcc.Loading(type=loading_type, children=table),
            ]
        ),
    ],
)

layout = html.Div(
    [
        title,
        dbc.Row(
            [
                dbc.Col(control_banner, width=3),
                dbc.Col(dcc.Loading(type=loading_type, children=html.Div(id='image_show')), width=9),
            ]
        ),
        dcc.Interval(
            id='human_interval',
            interval=60*60*24*1000, # in milliseconds
            n_intervals=0
        ),
        html.P(id='sp_list', hidden=True),
    ]
)

# 進入(刷新)網站時取得crop name
@app.callback(
    Output('crop_name', 'options'),
    [
        Input('human_interval', 'n_intervals')
    ]
)
def get_crop(n_intervals):
    if n_intervals == 0:
        print('get crop name from db')
        options = [
            {'label':"13G1", 'value':'13G1'},
            {'label':"13G2", 'value':'13G2'},
            {'label':"12GK", 'value':'12GK'}
        ]
        return options
    else:
        return dash.no_update
        


@app.callback(
    [
        Output(a, 'disabled') for a in [f'no_ger-{i}' for i in range(1, 9)]
    ]+[
        Output(a, 'color') for a in [f'no_ger-{i}' for i in range(1, 9)]
    ],
    [
        Input(a, 'n_clicks') for a in [f'is_ger-{i}' for i in range(1, 9)]
    ],
    [
        State(a, 'children') for a in [f'sponge_{i}' for i in range(1, 9)]
    ]+[
        State('sp_list', 'children')
    ]
)
def close_butto_yes(n1, n2, n3, n4, n5, n6, n7, n8, sp1, sp2, sp3, sp4, sp5, sp6, sp7, sp8, sp_list):
    callback = [sp1, sp2, sp3, sp4, sp5, sp6, sp7, sp8]
    n_clicks = [n1, n2, n3, n4, n5, n6, n7, n8]
    ctx = dash.callback_context.triggered
    
    res = [dash.no_update, ]*16    
    if 'ger' in ctx[0]['prop_id'] and n_clicks[int(ctx[0]['prop_id'].split('-')[1].split('.')[0])-1] == 1:
        print('save')
        sponge_id = eval(sp_list)[ctx[0]['prop_id'].split('.')[0].split('_')[1]]
        dbcnt.save_artificial_judgment(sponge_id, 1)
        res[int(ctx[0]['prop_id'].split('-')[1].split('.')[0])-1] = True
        res[int(ctx[0]['prop_id'].split('-')[1].split('.')[0])+7] = 'secondary'
        # 儲存辨識結果
        return res
    else:
        return res
    
@app.callback(
    [
        Output(a, 'disabled') for a in [f'is_ger-{i}' for i in range(1, 9)]
    ]+[
        Output(a, 'color') for a in [f'is_ger-{i}' for i in range(1, 9)]
    ],
    [
        Input(a, 'n_clicks') for a in [f'no_ger-{i}' for i in range(1, 9)]
    ],
    [
        State(a, 'children') for a in [f'sponge_{i}' for i in range(1, 9)]
    ]+[
        State('sp_list', 'children')
    ]
)
def close_butt_no(n1, n2, n3, n4, n5, n6, n7, n8, sp1, sp2, sp3, sp4, sp5, sp6, sp7, sp8, sp_list):
    callback = [sp1, sp2, sp3, sp4, sp5, sp6, sp7, sp8]
    n_clicks = [n1, n2, n3, n4, n5, n6, n7, n8]
    ctx = dash.callback_context.triggered    
    
    res = [dash.no_update, ]*16    
    if 'ger' in ctx[0]['prop_id'] and n_clicks[int(ctx[0]['prop_id'].split('-')[1].split('.')[0])-1] == 1:
        print('save')
        sponge_id = eval(sp_list)[ctx[0]['prop_id'].split('.')[0].split('_')[1]]
        dbcnt.save_artificial_judgment(sponge_id, 0)
        res[int(ctx[0]['prop_id'].split('-')[1].split('.')[0])-1] = True
        res[int(ctx[0]['prop_id'].split('-')[1].split('.')[0])+7] = 'secondary'
        # 儲存辨識結果
        return res
    else:
        return res
    
    
@app.callback(
    [
        Output('image_show', 'children'),
        Output('human_table', 'data'),
        Output('human_table', 'columns'),
        Output('sp_list', 'children'),
    ],
    [
        Input('search_button', 'n_clicks'),
    ],
    [
        State('crop_name', 'value'),
    ]
)
def get_data(n_clicks, value):
    if value != None:
        # 取得該編號八筆資料
        # 統計辨識資料
        result_list, result_table = dbcnt.get_single_sponge(value)
        df = pd.DataFrame(
            result_table, 
            columns=['品種編號', '總播種量', '人工判斷數量']
        )
        data = df.to_dict('records')
        columns=[{"name": i, "id": i} for i in ['品種編號', '總播種量', '人工判斷數量']]
        
        print(len(result_list))
        sp_list = {}
        for x, i in enumerate(result_list):
            sp_list.update({f"ger-{x+1}":str(i[0])})
        
        image_group = html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(make_fig(1, result_list[0][1]), width=3),
                        dbc.Col(make_fig(2, result_list[1][1]), width=3),
                        dbc.Col(make_fig(3, result_list[2][1]), width=3),
                        dbc.Col(make_fig(4, result_list[3][1]), width=3),
                    ]),
                    html.Hr(),
                    dbc.Row(
                    [
                        dbc.Col(make_fig(5, result_list[4][1]), width=3),
                        dbc.Col(make_fig(6, result_list[5][1]), width=3),
                        dbc.Col(make_fig(7, result_list[6][1]), width=3),
                        dbc.Col(make_fig(8, result_list[7][1]), width=3),
                    ])
            ],
            id='image_show'
        )
        return image_group, data, columns, str(sp_list)
    else:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update