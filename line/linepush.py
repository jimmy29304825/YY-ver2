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



line_bot_api.push_message("USER ID or GROUP ID",TextSendMessage(text=""))