import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from app import app
from apps import dashboard, control, manage, human, information
import dash
from germination.yy_class import callDB
import datetime
import pandas as pd
import json

secretFileContentJson=json.load(open("D:/YY_DASH/line/secret_key",'r'))  # 載入line_secret_key資訊
dbconnect = callDB(
    secretFileContentJson.get("DB_IP"), 
    secretFileContentJson.get("DB_PORT"), 
    secretFileContentJson.get("DB_ACCOUNT"), 
    secretFileContentJson.get("DB_PASSWD"), 
    secretFileContentJson.get("DB_NAME")
)
excel_path = '//Nas001/發芽率e化/'

sidebar = html.Div(
    [
        dcc.Link(dbc.CardImg(src=app.get_asset_url('yy-logo-ch-outline2.png')), href='/'),
        html.Br(),
        html.Hr(),
        html.H4("發芽成效總覽", className='titile'),
        dbc.Nav(
            [
                dbc.NavLink("監控儀錶板", href="/dashboard", id="apps_dashboard-link", className='nav-content',),
                dbc.NavLink("新增品種", href="/information", id="apps_information-link", className='nav-content',),
            ],
            vertical=True,
            pills=True,
            className='nav-content',
        ),
        html.Br(),
        html.H4("智能辨識", className='titile'),
        dbc.Nav(
            [
                dbc.NavLink("操作控制區", href="/control", id="apps_control-link", className='nav-content',),
                dbc.NavLink("人工區", href="/human", id="apps_human-link", className='nav-content',),
                dbc.NavLink("管理資料區", href="/manage", id="apps_manage-link", className='nav-content',),
                html.Br(),
                html.Hr(),
                dbc.Button('同步資料', id='update_from_excel', color="warning"),
            ],
            vertical=True,
            pills=True,
            className='nav-content',
        ),
        
    ],
    id='side_bar', 
    className='side_bar',
)

content = html.Div(id="page_content")

app.layout = html.Div(
    [
        dcc.Location(id="url"), 
        sidebar, 
        content,
    ]
)



# corresponding nav link to true, allowing users to tell see page they are on
@app.callback(
    [
        Output(f"apps_{i}-link", "active") for i in [
            'dashboard', 
            'control', 
            'manage', 
            'human',
            'information',
        ]
    ],
    [Input("url", "pathname")]
)
def toggle_active_links(pathname):
    if pathname == "/":
        # set home page as '/'
        return True, False, False, False, False
    return [pathname == f"/{i}" for i in ['dashboard', 'control', 'manage', 'human', 'information']]


@app.callback(
    Output("page_content", "children"), 
    [
        Input("url", "pathname"),
    ]
)
def render_page_content(pathname):
    if pathname == "/":  # 首頁(預設儀表板)
        return dashboard.layout
    
    elif pathname == "/dashboard":  # 儀表板
        return dashboard.layout
    elif pathname == "/control":  # 操作控制區
        return control.layout
    elif pathname == "/manage":  # 管理介面
        return manage.layout
    elif pathname == "/human":  # 人工操作
        return human.layout
    elif pathname == "/information":  # 人工操作
        return information.layout
    
    
    # If the user tries to reach a different page, return a 404 message  非指定的網址
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.H1("不要亂看啦~", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )

@app.callback(
    Output('update_from_excel', 'color'),
    [
        Input('update_from_excel', 'n_clicks')
    ]
)
def update_data(n_clicks):
    ctx = dash.callback_context.triggered
    print(ctx)
    if 'update_from_excel' in ctx[0]['prop_id']:
        last_record = dbconnect.get_last_schedule()
        filename = '生產排程{} 1-12月'.format(str(datetime.datetime.now().year))
        year = str(datetime.datetime.now().year - 1911)
        month = "{:02d}".format(datetime.datetime.now().month)
        last_month = "{:02d}".format(datetime.datetime.now().month-1)
        sheetname = year+month+'排程'
        sheetname_last = year+last_month+'排程'
        print('last', last_record)
        xls = pd.ExcelFile(excel_path + '{}.xlsx'.format(filename))
        sheet_list = xls.sheet_names # see all sheet names
        for i in sheet_list:
            if sheetname[0:5] in i:
                sheetname = i
                print(sheetname)
                break
        for i in sheet_list:
            if sheetname_last in i:
                sheetname_last = i
                print(sheetname_last)
                break    
#         for sheet in [sheetname_last, sheetname]:
        df = pd.read_excel(
            excel_path + '{}.xlsx'.format(filename), 
            sheet_name = sheetname, 
            usecols=[1, 3, 5, 9], 
            converters={'生產序號':str,'播種日期':pd.to_datetime,'交貨日':pd.to_datetime,'編號':str}
        )
        if last_record[0][2:4] != month:
            print('update all')
            df_use = df
            df_use.loc[:,'交貨日'] = df_use.loc[:,'交貨日'].fillna(df_use['播種日期'])
            df_use = df_use[df_use['生產序號'].notna()]
            dbconnect.update_schedule(df_use)
            df = pd.read_excel(
                excel_path + '{}.xlsx'.format(filename), 
                sheet_name = sheetname_last, 
                usecols=[1, 3, 5, 9], 
                converters={'生產序號':str,'播種日期':pd.to_datetime,'交貨日':pd.to_datetime,'編號':str}
            )
            start_data = (df[df['生產序號'] == last_record[0]].index)[0]
            print(start_data)
            df_use = df.iloc[start_data:len(df)]
            df_use.loc[:,'交貨日'] = df_use.loc[:,'交貨日'].fillna(df_use['播種日期'])
            df_use = df_use[df_use['生產序號'].notna()]
            dbconnect.update_schedule(df_use)
        else:
            print('update what i dont have')
            start_data = (df[df['生產序號'] == last_record[0]].index)[0]
            print(start_data)
            df_use = df.iloc[start_data:len(df)]
            df_use.loc[:,'交貨日'] = df_use.loc[:,'交貨日'].fillna(df_use['播種日期'])
            df_use = df_use[df_use['生產序號'].notna()]
            dbconnect.update_schedule(df_use)
        return 'success'
    else:
        return dash.no_update

if __name__ == '__main__':
    app.run_server(
        debug=True,
        port=8051,
        host='0.0.0.0',
    )

