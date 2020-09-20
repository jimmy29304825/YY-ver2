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
from datetime import datetime as dt
from datetime import timedelta
from germination.yy_class import callDB, par, germination
import cv2
import uuid
import math
from linebot.models import TextSendMessage
from linebot import LineBotApi
import json

secretFileContentJson=json.load(open("D:/YY_DASH/line/secret_key",'r'))  # 載入line_secret_key資訊

line_bot_api = LineBotApi(secretFileContentJson.get("channel_access_token"))  # 讀取line channel_access_token

dbcnt = callDB(
    secretFileContentJson.get("DB_IP"), 
    secretFileContentJson.get("DB_PORT"), 
    secretFileContentJson.get("DB_ACCOUNT"), 
    secretFileContentJson.get("DB_PASSWD"), 
    secretFileContentJson.get("DB_NAME")
)
par = par(
    secretFileContentJson.get("PI_IP"), 
    22, 
    secretFileContentJson.get("PI_ACCOUNT"), 
    secretFileContentJson.get("PI_PASSWD")
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
                dbc.Col(dbc.Row(html.H2('發芽率辨識操作', id='apps_dashboard-title'), justify='center'),),

            ], 
            justify='end',
            align='center',
        )
    ], 
    className='nav_title'
)

# offset：前面控幾格
# size：寬幾格
# order： 從哪一格開始
# 1-12整數

image_banner = dbc.Card(
    [
        dbc.CardHeader("辨識結果顯示區"),
        dbc.CardBody(
            [
                
#                 dbc.CardImg(id='photo'),
                dcc.Loading(children=dcc.Graph(id='photo'),type="circle"),
            ]
        ),
        dbc.CardFooter([
            dbc.Row(
                [
                    dbc.Col(dbc.Button("重拍", color="warning", id="retake")),
                    dbc.Col(dbc.Button("確認，拍下一張", color="success", id="take_next"), xl={'offset':3}),
                    dbc.Col(dbc.Button("確認，結束拍攝", color="info", id="finish_process"), xl={'offset':3}),
                ])
        ]),
    ],
)

def datepicker(date):
    
    return dcc.DatePickerSingle(
        id='saw_date_picker',
        min_date_allowed=dt(2020, 1, 1),
        max_date_allowed=dt.now().date(),
        initial_visible_month=dt.now().date(),
        date=str(dt.now().date()- timedelta(days=6)),
    )


inline_radioitems = dbc.FormGroup(
    [
#         dbc.Label("辨識片數"),
        dbc.RadioItems(
            options=[
                {"label": "一片", "value": 1},
                {"label": "二片", "value": 2},
                {"label": "三片", "value": 3},
                {"label": "四片", "value": 4},
            ],
            value=4,
            id="saw_pieces",
            inline=True,
        ),
    ]
)

production_number = dbc.Select(
    id="production_number_dropdown",
    options=[{'label':'無播種紀錄' , 'value': 'no data'}],
    value = 'no data'
)
control_banner = dbc.Card(
    [
        dbc.CardHeader("輸入區"),
        dbc.CardBody(
            [
                dbc.InputGroup(
                    id='saw_date',
                ), 
                dbc.Row(dbc.Col(dbc.InputGroup(
                    [dbc.InputGroupAddon('生產序號', addon_type="prepend"), production_number],
                    id='production_number',))),
                html.Br(),
                inline_radioitems,
                html.Hr(),
                html.Div(id='germination_target'),
            ]
        ),
        dbc.CardFooter([
            dbc.Row(
                [
                    dbc.Col(dbc.Button("開始拍攝", color="success", id="start_picture")),
                ],
                justify='center'
            )
        ]),
    ],
)



result_banner = dbc.Card(
    [
        dbc.CardHeader("結果呈現區"),
        dbc.CardBody(
            id='germination_result'
        ),
    ],
)

layout = html.Div(
    [
        title,
#         dcc.Graph(figure=fig),
        dbc.Row(
            [
                dbc.Col([control_banner, html.Br(), result_banner], width=5),
                dbc.Col(image_banner, width=7),
                dcc.Interval(
                    id='interval',
                    interval=60*60*24*1000, # in milliseconds
                    n_intervals=0
                )
            ]
        )
        
    ]
)

@app.callback(Output('saw_date', 'children'),
              [Input('interval', 'n_intervals')])
def update_metrics(n_intervals):
    if n_intervals == 0:
        return [dbc.InputGroupAddon('播種日期', addon_type="prepend"), datepicker('date')]
    else:
        return dash.no_update


# 選擇日期篩選生產序號
@app.callback(
    Output('production_number', 'children'),
    [
        Input('saw_date_picker', 'date'),
    ]
)
def get_production_number(date):
    print('查詢%s的生產序號' % date)
    print('生產序號、六碼編號')
    production_data = dbcnt.get_productionID(date)
    if production_data == []:
        return dash.no_update

    else:  
        option = production_data
        production_number = dbc.Select(
            id="production_number_dropdown",
            options=option,
            value=option[0]['value']
        )
        children = [dbc.InputGroupAddon('生產序號', addon_type="prepend"), production_number]
        return children

# 選擇生產序號後顯示詳細資訊
@app.callback(
    Output('germination_target', 'children'),
    [
        Input('production_number_dropdown', 'value'),
    ]
)
def get_production_info(production_number_dropdown):
    if production_number_dropdown != 'no data':
        print('查詢指定生產序號的詳細資料：%s' % production_number_dropdown)
        print('六碼編號、作物名稱(第五碼)、播種日期、目標客戶、預計交貨日期、辨識參數(隱)、補料參數(隱)')
        data = dbcnt.get_productionID_info(production_number_dropdown)
        info = [
            html.P('種植品種：%s' % data[0]),
            html.P('種法：%s' % data[1]),
            html.P('播種日：%s' % data[2]),
            html.P('目標客戶：%s' % data[3]),
            html.P('預計出貨日：%s' % data[4]),
        ]
        return info
    else:
        return dash.no_update


# 控制樹梅派拍照、呈現圖片
@app.callback(
    [
        Output('photo', 'figure'),
        Output('germination_result', 'children'),
    ],        
    [
        Input('start_picture', 'n_clicks'),
        Input('retake', 'n_clicks'),
        Input('take_next', 'n_clicks'),
        Input('finish_process', 'n_clicks'),
        Input('saw_pieces', 'value'),
        Input('production_number_dropdown', 'value'),
    ]
)
def take_photo(start_picture, retake, take_next, finish_process, saw_pieces, production_number_dropdown):
    
    if production_number_dropdown != 'no data':
        print('目標生產編號：', production_number_dropdown)
        productionid = production_number_dropdown
        ctx = dash.callback_context.triggered
        print('操作項目：', ctx[0]['prop_id'])
        if 'start_picture' in ctx[0]['prop_id'] or 'retake' in ctx[0]['prop_id']:
            print('call樹梅派(傳送pid)，拍照中...辨識%s片'% saw_pieces)
            photoid = 'photo_'+uuid.uuid1().hex
            par.connect_raspi(photoid, saw_pieces)
            print('照片檔(pid)：', photoid)
            img = dbcnt.get_view_photo(photoid)
            photo = go.Figure()
            photo = photo.add_trace(go.Image(z=img))
            photo = photo.update_layout(margin=dict(l=5, r=5, t=5, b=5))
            photo = photo.update_xaxes(showticklabels=False)
            photo = photo.update_yaxes(showticklabels=False)
            return photo, dash.no_update

        elif 'take_next' in ctx[0]['prop_id']:
            print('辨識確認的照片序號並儲存')
            # 取得照片
            image, photoid, piece = dbcnt.get_use_photo()
            # 取得參數
            data = dbcnt.get_parameter(productionid)
            # 辨識照片
            series_id = data[0]
            thresholds = data[3]
            percent = data[2]
            ger = germination(series_id, percent, piece)
            res, ger_cnt = ger.identify(image)
            non_ger_cnt = piece*96 - ger_cnt
            # 儲存結果
            processid = 'process_'+uuid.uuid1().hex
            process_record = (processid, productionid, photoid, piece, ger_cnt)
            dbcnt.save_germination_record(process_record, ger.result_list)
            print('call樹梅派(傳送pid)，拍照中...辨識%s片'% saw_pieces)
            photoid = 'photo_'+uuid.uuid1().hex
            par.connect_raspi(photoid, saw_pieces)
            print('照片檔(pid)', photoid)
            img = dbcnt.get_view_photo(photoid)
            photo = go.Figure()
            photo = photo.add_trace(go.Image(z=img))
            photo = photo.update_layout(margin=dict(l=5, r=5, t=5, b=5))
            photo = photo.update_xaxes(showticklabels=False)
            photo = photo.update_yaxes(showticklabels=False)
            result = [
                html.P('品種：%s' % series_id, className="card-text"),
                html.P('辨識片數：%s片' % str(piece), className="card-text"),
                html.P('數量：%s株' % str(ger_cnt + non_ger_cnt), className="card-text"),
                html.P('發芽率：{}%'.format(str(res)), className="card-text"),
                html.P('發芽數量：%s株' % str(ger_cnt), className="card-text"),
                html.P('未發芽數量：%s株' % str(non_ger_cnt), className="card-text"),
            ]
            return photo, result

        elif 'finish_process' in ctx[0]['prop_id']:
            print('辨識確認的照片序號並儲存')
            # 取得照片
            image, photoid, piece = dbcnt.get_use_photo()
            # 取得參數
            data = dbcnt.get_parameter(productionid)
            # 辨識照片
            series_id = data[0]
            thresholds = data[3]
            percent = data[2]
            ger = germination(series_id, percent, piece)
            res, ger_cnt = ger.identify(image)
            non_ger_cnt = piece*96 - ger_cnt
            # 儲存結果
            processid = 'process_'+uuid.uuid1().hex
            process_record = (processid, productionid, photoid, piece, ger_cnt)
            dbcnt.save_germination_record(process_record, ger.result_list)
            photo = go.Figure()
            print('統計中...')
            res_data = dbcnt.get_summary(productionid)
            total_sponge = sum(x[3] for x in res_data)*12*8
            sum_n = sum(x[4] for x in res_data)
            total_perecnt = round((sum_n/total_sponge)*100, 2)
            print(total_sponge, sum_n, total_perecnt)
            parameter = dbcnt.get_parameter(productionid)
            nursery_rate = parameter[4]
            thinning_rate = parameter[5]
            cultivation_rate = parameter[6]
            if nursery_rate >= sum_n/total_sponge:  # 沒達到：加上昨天的播種紀錄計算發芽率是否有達到 nursery_rate
                lastday = str(parameter[7] - timedelta(days=1))
                print(parameter[0], lastday)
                data = dbcnt.get_lastday(parameter[0], lastday)
                if data[0] == None:
                    data = [0, 0]
                print(data)
                print(data, total_sponge)
                new_total_sponge = (data[1]*96)+total_sponge
                new_ger_cnt = data[0]+sum_n
                if nursery_rate >= new_ger_cnt/new_total_sponge:  # 未達標：計算要播幾片 nursery_rate thinning_rate cultivation_rate
                    print('補播')
                    less_cnt = int(new_total_sponge * nursery_rate) - new_ger_cnt # 缺
                    less_piece = int((((less_cnt / thinning_rate / cultivation_rate) + 1) // 96) + 1)
                    less_per = (float(nursery_rate) - float(new_ger_cnt/new_total_sponge))
                    print(less_piece, '片', less_per)
                    text = f'''[發芽率異常通報]\n生產序號：{productionid} ({parameter[0]})\n共播種{total_sponge:,d}株，發芽{sum_n:,d}株，\n發芽率{total_perecnt:.2f}%，\n未達到育苗標準{nursery_rate*100}%，\n統計昨日{parameter[0]}播種紀錄，\n(播{int(data[0]):,d}株，發芽{int(data[1]):,d}株)，\n仍差{less_per*100:.2f}%，應補播{less_piece}片。'''
                    text_for_dash = f'應補播{less_piece}片'
                    line_bot_api.push_message('C14c1eebfb9938766f5ef01216c4cc003', TextSendMessage(text=text))
                    print(text_for_dash)
                    dash_status = html.H4('發芽情況：{}'.format(text_for_dash), className="card-text")
                else:
                    text_for_dash = '正常'
                    dash_status = html.P('發芽情況：{}'.format(text_for_dash), className="card-text")
                    print(text_for_dash)
            else:
                text_for_dash = '正常'
                print(text_for_dash)
                dash_status = html.P('發芽情況：{}'.format(text_for_dash), className="card-text")
                
            result = [
                html.P('品種：%s' % res_data[0][5], className="card-text"),
                html.P('拍攝辨識次數：%s次' % str(len(res_data)), className="card-text"),
                html.P('總計播種數量：%s株' % str(total_sponge), className="card-text"),
                html.P('發芽數量：%s株' % str(sum_n), className="card-text"),
                html.P('發芽率：{}%'.format(str(total_perecnt)), className="card-text"),
                dash_status
            ]
            return photo, result
        else:
            return dash.no_update, dash.no_update

    else:
        return dash.no_update, dash.no_update