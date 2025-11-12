import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from langdetect import detect

app = Flask(__name__)

# ---- 環境變數 (可直接部署 Railway) ----
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN") or "QlyDbhy8kPfh15MUZlJyIXu43OQIBT5rSDzWCxAMelTgCmHlCM7HlHpuPD4zhmbS5Ga+W0cmW7SGPZEo7PrCNvrCmHE3dK6IkuVhUbI8zRjUwAf3+ZW7xXsCX25nj8IQ74icKofMdEzzNDc9QIZs8gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET") or "3e557ae4660d67a1768eb76640cec0d1"
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY") or "648881f3-2f5e-4a29-8d64-8d566de02bd1:fx"

DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


def deepl_translate(text, target_lang):
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    }
    response = requests.post(DEEPL_API_URL, data=data)
    result = response.json()
    return result["translations"][0]["text"]


def translate_auto(text):
    lang = detect(text)
    if lang.startswith("zh"):
        translated = deepl_translate(text, "ID")  # 中文→印尼文
    else:
        translated = deepl_translate(text, "ZH")  # 印尼文→中文
    return f"🌐 原文：{text}\n💬 翻譯：{translated}"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    translated = translate_auto(user_text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=translated)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
