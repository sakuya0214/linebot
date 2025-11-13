from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
DEEPL_API_KEY = os.environ["DEEPL_API_KEY"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def translate(text, target_lang):
    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    }
    resp = requests.post(url, data=data).json()
    return resp["translations"][0]["text"]

def detect_lang(text):
    # 簡單判斷中印
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return "ZH", "ID"
    else:
        return "ID", "ZH"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    src_lang, tgt_lang = detect_lang(event.message.text)
    translated = translate(event.message.text, target_lang=tgt_lang)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=translated)
    )

if __name__ == "__main__":
    app.run()
