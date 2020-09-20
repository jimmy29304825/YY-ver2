import dash
import dash_auth
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(
    __name__, 
    suppress_callback_exceptions=True,
#     external_stylesheets=external_stylesheets
)
server = app.server
# 忽略callback無指定id之警告
# app.config.prevent_initial_callbacks=True
app.title = '研耘科技-發芽率E化平台'

# Keep this out of source code repository - save in a file or a database
VALID_USERNAME_PASSWORD_PAIRS = {
    'yyostech': '0911',
    'yyostech': 'yyostech',
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)