# 引用Web Server套件
from flask import Flask, request, abort

# 從linebot 套件包裡引用 LineBotApi 與 WebhookHandler 類別
from linebot import (
    LineBotApi, WebhookHandler
)

# 引用無效簽章錯誤
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, JoinEvent
)

# 載入json處理套件
import json

# 載入基礎設定檔
secretFileContentJson=json.load(open("./line_secret_key",'r'))  # 載入line_secret_key資訊
server_url=secretFileContentJson.get("server_url")  # 讀取webhooks網址

# 設定Server啟用細節
app = Flask(__name__,static_url_path = "/python/factory/test/YY_new/line/YY",   # url連結名稱(https://ngrok/static_url_path/)
            static_folder = "/python/factory/test/YY_new/line/YY")  #  https://ngrok/static_url_path/對應到的local資料夾位置
# 生成實體物件
line_bot_api = LineBotApi(secretFileContentJson.get("channel_access_token"))  # 讀取line channel_access_token
handler = WebhookHandler(secretFileContentJson.get("secret_key"))  # 讀取line secret_key

# 啟動server對外接口，使Line能丟消息進來
@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == 'ID?' or event.message.text == 'id?':
        User_ID = TextMessage(text=event.source.user_id)
        line_bot_api.reply_message(event.reply_token, User_ID)
        print ('Reply User ID =>' + event.source.user_id)
    elif event.message.text == 'GroupID?':
        Group_ID = TextMessage(text=event.source.group_id)
        line_bot_api.reply_message(event.reply_token, Group_ID)
        print ('Reply Group ID =>' + event.source.group_id)
    else:
        None


@handler.add(JoinEvent)
def handle_join(event):
    newcoming_text = "謝謝邀請我這個機器來至此群組！！我會盡力為大家服務的～"
    print(event)
    print()
    line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=newcoming_text)
        )
    print("JoinEvent =", JoinEvent)






if __name__ == "__main__":
    app.run(host='0.0.0.0')