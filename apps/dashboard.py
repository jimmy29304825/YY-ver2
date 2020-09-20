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
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta, date
from plotly.subplots import make_subplots
from dash_extensions import Download
from dash_extensions.snippets import send_bytes
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
columns=[{"name": i, "id": i} for i in ['生產序號', '作物編號', '品種名稱', '需求客戶',  '播種數量', '發芽率']]
table = dash_table.DataTable(
    id='schedule_table',
    columns=columns,
    editable=False,
    style_table={'height': '1000px'},
    page_size=30,
    style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)',
        }
    ],
    style_header={
        'backgroundColor': 'rgb(230, 230, 230)',
        'fontWeight': 'bold',
        'fontSize': 17
    },
    style_data={
        'fontSize': 17
    },
)


# 設定繪圖功能紐
config={
    'displaylogo':False, 
    'modeBarButtonsToRemove':
        [
            'toImage',
            'toggleSpikelines',
            'lasso2d',
            'autoScale2d',
        ]
}
loading_type='dot'
# 'graph', 'cube', 'circle', 'dot'


dropDown_year = dcc.Dropdown(
        id='time_range',
        options=[
            {'label': '本週', 'value': 'week'},
            {'label': '本月', 'value': 'month'},
            {'label': '本季', 'value': 'season'},
            {'label': '本年', 'value': 'year'},
        ],
        value='month',
        searchable=False,
        clearable=False
    ),

title = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(dbc.Row(html.H2('發芽率監控儀表板', id='apps_dashboard-title'), justify='center'), xl={'order':1, 'size':4}),
                dbc.Col(dropDown_year, xl={'order':7, 'size':1},),
                dbc.Col(html.Div(id='date_picker_db'), xl={'order':8, 'size':3},),
                dbc.Col(html.Div([dbc.Button("資料匯出", id="btn", color="success", className="mr-1"), Download(id="download")]), xl={'order':11, 'size':2})
            ], 
            justify='end',
            align='center',
        )
    ], 
    className='nav_title'
)





ger_graph = dcc.Graph(id='germination_graph')
saw_graph = dcc.Graph(id='saw_count_graph')
series_rank = html.Div(
    [
        html.H2('各品種播種數量與發芽率資訊'),
        dbc.ListGroup(
            [

            ],
            id='series_list'
        ),
    ]
)
schedule_table = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.H2('生產序號表格'), width=6),
                dbc.Col(
                    dbc.ButtonGroup(
                        [
                            dbc.Button("所有資料"),
                            dbc.Button("達標資料", color="success"),
                            dbc.Button("異常資料", color="danger")
                        ]
                    ),
                    width=4
                )
            ],
            justify="between"
        ),
        table
    ]
)

layout = html.Div(
    [
        title,
        html.H2('整體播種情況'),
        dbc.Row(
            [
                dbc.Col(ger_graph),
            ]
        ),
        html.Br(),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(series_rank, width=6),
                dbc.Col(schedule_table, width=6),
            ]
        ),
        dcc.Interval(
            id='interval_db',
            interval=60*60*24*1000,  # in milliseconds
            n_intervals=0
        ),
        html.A("Générer !", href="/download_excel/", hidden=True, id='download_link')
    ]
)

# 更新日期，預設當月資料


@app.callback(
    Output('date_picker_db', 'children'),
    [
        Input('interval_db', 'n_intervals')
    ]
)
def update_metrics(n_intervals):
    end = datetime.now().date()
    month = datetime.now().date().month
    year = datetime.now().date().year
    start = f'{year}-{month:02d}-01'
    datepicker = dcc.DatePickerRange(
        minimum_nights=5,
        clearable=True,
        with_portal=True,
        end_date=end,
        start_date=start,
        id='date_r'
    )
    if n_intervals == 0:
        return [datepicker]
    else:
        return dash.no_update


def time_range(range_picker, end, y):
    start = None
    if range_picker == 'month':
        month = datetime.now().date().month
        year = datetime.now().date().year
        start = f'{year}-{month:02d}-01'
    elif range_picker == 'week':
        week = datetime.now().date().weekday()
        start = datetime.now().date() - timedelta(days=week + 1)
    elif range_picker == 'season':
        if date(y, 1, 1) <= end <= date(y, 3, 31):
            start = date(y, 1, 1)
        elif date(y, 4, 1) <= end <= date(y, 6, 30):
            start = date(y, 4, 1)
        elif date(y, 7, 1) <= end <= date(y, 9, 30):
            start = date(y, 7, 1)
        elif date(y, 10, 1) <= end <= date(y, 12, 31):
            start = date(y, 110, 1)
    elif range_picker == 'year':
        start = date(y, 1, 1)
    return start

def series_data(serie_name, serie_id, x, ycnt, yper, y_total_per, max_y):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=x, y=yper, name='每日發芽率'))
    fig.add_trace(go.Bar(x=x, y=ycnt, name='每日播種數量'), secondary_y=True)
    fig.update_yaxes(range=[0, 120], secondary_y=False)
    fig.update_yaxes(range=[0, max_y], secondary_y=True)
    fig.update_layout(
        margin={'t': 10, 'b': 5, 'r': 5, 'l': 0},
#         legend=dict(orientation='h'),
        showlegend=False,
#         title=f'{serie_name}播種數量統計趨勢圖',
        height=150,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.5)',
    )
    text = html.Div(
        [
            html.H4(f'{serie_name} ({serie_id})'),
            html.H5(children=f'{int(sum(ycnt[:-1])):,d}株'),
            html.H5(children=f'{(y_total_per*100):.2f}%'),
        ]
    )
    res = dbc.Row(
        [
            dbc.Col(text, width=3),
            dbc.Col(dcc.Graph(figure=fig), width=9)
        ],
        justify="between"
    )
    return res


@app.callback(
    [
        Output('germination_graph', 'figure'),
        Output('series_list', 'children'),
        Output('schedule_table', 'data'),
    ],
    [
        Input('date_r', 'end_date'),
        Input('time_range', 'value')
     ],
    [
        State('date_r', 'start_date')
    ]
)
def update_output(end_date, range_picker, start_date):
    ctx = dash.callback_context.triggered[0]
    print(ctx)
    end, start = end_date, start_date
    if ctx['prop_id'] == 'date_r.end_date':
        end = end_date
        start = start_date
    elif ctx['prop_id'] == 'time_range.value':
        end = datetime.now().date()
        y = datetime.now().date().year
        print(range_picker, end, y)
        start = time_range(range_picker, end, y)
    print(f"{start} ~ {end}")

    data = dbcnt.get_dashboard_data(start, end)
    df = pd.DataFrame(data, columns=['生產序號', '作物編號', '播種日期', '出貨日期', '品種名稱', '需求客戶', '播種數量', '發芽數量', '發芽率'])
    # df = pd.read_csv('C:/Users/jimmy/OneDrive/桌面/schedule.csv')
    df['播種日期'] = pd.to_datetime(df['播種日期'])
    df['出貨日期'] = pd.to_datetime(df['出貨日期'])
    df_use = df.query(f'播種日期 >= "{start}" and 播種日期 <= "{end}"')

    # 發芽率+播種數量

    fig1 = df_use.groupby('播種日期').sum()[['播種數量', '發芽數量']].reset_index()
    x = fig1['播種日期'].to_list()
    x = x + [max(x) + timedelta(days=5)]
    x.sort()
    ycnt = fig1['播種數量'].to_list() + [None]
    yper = ((fig1['發芽數量'] / fig1['播種數量']) * 100).to_list() + [None]
    germination_graph = make_subplots(specs=[[{"secondary_y": True}]])
    germination_graph.add_trace(go.Scatter(x=x, y=yper, name='每日發芽率'))
    germination_graph.add_trace(go.Bar(x=x, y=ycnt, name='每日播種數量'), secondary_y=True)
    germination_graph.update_layout(
#         title='整體發芽率走勢圖',
        legend=dict(orientation='h', yanchor="top", y=1.2, xanchor="left", x=0.19),
        xaxis_title='日期',
        yaxis_title='發芽率',
        margin={'t': 20, 'b': 20, 'r': 10, 'l': 10},
    )
    germination_graph.update_yaxes(range=[0, 120], secondary_y=False)
    germination_graph.update_yaxes(range=[0, int(float(max(fig1['播種數量'].to_list())) * 1.5)], secondary_y=True)

    # 品種資料
    series = df_use.groupby(['作物編號', '品種名稱']).sum().sort_values('播種數量', ascending=False).reset_index()[['作物編號', '品種名稱']].to_numpy()
    colors = ["primary", "secondary", "success", "info", "warning", "danger", "light", "dark"]
    ser_list = []
    for serie, color in zip(series, colors):
        serie_id = serie[0]
        df_serie = df_use.query(f'作物編號 == "{serie_id}"')
        serie_name = df_serie['品種名稱'].iloc[0]
        fig1 = df_serie.groupby('播種日期').sum()[['播種數量', '發芽數量']].reset_index()
        x = fig1['播種日期'].to_list()
        x = x + [max(x) + timedelta(days=5)]
        x.sort()
        ycnt = fig1['發芽數量'].to_list() + [None]
        yper = ((fig1['發芽數量'] / fig1['播種數量']) * 100).to_list() + [None]
        y_total_per = sum(ycnt[:-1]) / fig1['播種數量'].sum()
        max_y = int(float(max(fig1['播種數量'].to_list())) * 1.5)
        res = series_data(serie_name, serie_id, x, ycnt, yper, y_total_per, max_y)
        print(color)
        ser_list.append(dbc.ListGroupItem(res, color=color))

    # schedule_table
    data = df_use[['生產序號', '作物編號', '品種名稱', '需求客戶',  '播種數量', '發芽率']].to_dict('records')
    return germination_graph, ser_list, data

# 各品種彈跳視窗功能
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

for i in range(6):
    app.callback(
        Output(f"modal_{i+1}", "is_open"),
        [Input(f"open_{i+1}", "n_clicks"), Input(f"close_{i+1}", "n_clicks")],
        [State(f"modal_{i+1}", "is_open")],
    )(toggle_modal)



@app.callback(
        Output('download', 'data'),
    [
        Input('btn', 'n_clicks')
     ],
    [
        State('schedule_table', 'data')
    ]
)
def generate_xlsx(n_nlicks, data):
    df = pd.DataFrame.from_records(data)
    # data = np.column_stack((np.arange(10), np.arange(10) * 2))
    # df = pd.DataFrame(columns=["a column", "another column"], data=data)
    def to_xlsx(bytes_io):
        print(bytes_io)
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        xslx_writer.save()

    return send_bytes(to_xlsx, "schedule_data.xlsx")