import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app
import paramiko
from datetime import datetime as dt
import uuid
import dash_core_components as dcc
from linebot import (
    LineBotApi, WebhookHandler
)
import json
from linebot.models import (
    TextSendMessage
)
secretFileContentJson=json.load(open("D:/YY_DASH/line/secret_key",'r'))  # 載入line_secret_key資訊
server_url=secretFileContentJson.get("server_url")  # 讀取webhooks網址

line_bot_api = LineBotApi(secretFileContentJson.get("channel_access_token"))  # 讀取line channel_access_token
handler = WebhookHandler(secretFileContentJson.get("secret_key"))  # 讀取line secret_key

series = dbc.RadioItems(
    options=[
        {"label": "12GK", "value": 1},
        {"label": "13G1", "value": 2},
        {"label": "12GD", "value": 3},
        {"label": "13G2", "value": 4},
        {"label": "32GD", "value": 5},
        {"label": "11G4", "value": 6},
    ],
    value=1,
    id="series",
    inline=True,
)

piece = dbc.RadioItems(
    options=[
        {"label": "一片", "value": 1},
        {"label": "二片", "value": 2},
        {"label": "三片", "value": 3},
        {"label": "四片", "value": 4},
    ],
    value=4,
    id="piece",
    inline=True,
)

button = html.Div(
    [
        dbc.Button("確認拍照", id="example-button", className="mr-2"),
        html.Hr(), 
        html.Br(),
        dcc.Loading(type='dot', children=html.H2(id="output", style={"vertical-align": "middle"})),
    ]
)

layout = html.Div(
    [
        series, 
        html.Br(),
        piece, 
        html.Br(),
        button
    ]
)
   



data = {"1":"12GK","2":"13G1","3":"12GD","4":"13G2","5":"32GD","6":"11G4"}

@app.callback(
    Output("output", "children"),
    [
        Input("example-button", "n_clicks")
    ], 
    [
        State("series", "value"),
        State("piece", "value")
    ]
)
def on_button_click(n_clicks, value, piece):
    print((n_clicks, value))
    if n_clicks is None:
        return "Not clicked."
    else:
        pid = data[str(value)] + "_" + str(piece) + "_" + str(uuid.uuid1().hex)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('192.168.50.87', 22, 'pi', 'Jimmy8193026')  # 網路連線設定
        stdin, stdout, stderr = ssh.exec_command("python3 /home/pi/Desktop/test2.py %s" % pid)  # 呼叫執行檔並傳送參數
        paramiko_result = stdout.readlines()  # 回傳產出結果
        print(paramiko_result)
        ssh.close()
        line_bot_api.push_message('Ua88d33cc15e1f629a54b415df99c2d62', TextSendMessage(text=pid+' done'))
        return f"拍照完成  {data[str(value)]}  {piece}片"