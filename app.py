from flask import Flask, request, jsonify
import os
from googletrans import Translator
import requests

app = Flask(__name__)

# ======== 環境變數 ========
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

translator = Translator()

# ======== 自訂字典（只套中文） ========
custom_dict = {
    "伊達": "Indah",
    "依達": "Indah"
}

def apply_custom_dict(text, target_lang):
    if target_lang == "zh-tw":
        for k, v in custom_dict.items():
            text = text.replace(k, v)
    return text

# ======== 翻譯函數 ========
def translate_text(text, target_lang):
    text_with_dict = apply_custom_dict(text, target_lang)
    try:
        translated = translator.translate(text_with_dict, dest=target_lang).text
        if not translated.strip() or translated == text_with_dict:
            return "無法翻譯 😢"
        return translated
    except Exception as e:
        print("Translate error:", e)
        return "無法翻譯 😢"

# ======== LINE 回覆函數 ========
def line_reply(reply_token, original_text, translated_text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    formatted_text = f"原文：{original_text}\n翻譯：{translated_text}"
    payload = {"replyToken": reply_token, "messages": [{"type": "text", "text": formatted_text}]}
    try:
        requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=payload)
    except Exception as e:
        print("LINE reply error:", e)

# ======== Webhook ========
@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_json()
    events = body.get("events", [])
    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            text = event["message"]["text"].strip()
            if not text:
                continue
            if event["source"]["type"] == "group":
                # 判斷翻譯方向
                if any("\u4e00" <= c <= "\u9fff" for c in text):
                    target_lang = "id"   # 中文 → 印尼文
                else:
                    target_lang = "zh-tw"  # 印尼文 → 繁體中文
                translated = translate_text(text, target_lang)
                reply_token = event["replyToken"]
                line_reply(reply_token, text, translated)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
