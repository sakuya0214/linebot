from flask import Flask, request, jsonify
import requests
import os
from googletrans import Translator

app = Flask(__name__)

# ======== 環境變數 ========
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
DEEPL_AUTH_KEY = os.environ.get("DEEPL_AUTH_KEY")

DEEPL_URL = "https://api-free.deepl.com/v2/translate"

translator = Translator()

# ======== 自訂字典（只套中文） ========
def apply_custom_dict(text, target_lang):
    if target_lang == "ZH-TW":  # 只在翻中文時套用
        custom_dict = {
            "伊達": "Indah",
            "依達": "Indah"
        }
        for k, v in custom_dict.items():
            text = text.replace(k, v)
    return text

# ======== DeepL 翻中文 ========
def translate_with_deepl(text, target_lang="ZH-TW"):
    text_with_dict = apply_custom_dict(text, target_lang)
    try:
        data = {
            "auth_key": DEEPL_AUTH_KEY,
            "text": text_with_dict,
            "target_lang": target_lang
        }
        response = requests.post(DEEPL_URL, data=data)
        response.raise_for_status()
        result = response.json()
        translated = result["translations"][0]["text"]

        if not translated.strip() or translated == text_with_dict:
            return "無法翻譯"

        return translated
    except Exception as e:
        print("DeepL translate error:", e)
        return "無法翻譯"

# ======== Google 翻印尼文 ========
def translate_with_google(text, src_lang="id", dest_lang="zh-tw"):
    try:
        translated = translator.translate(text, src=src_lang, dest=dest_lang).text
        if not translated.strip() or translated == text:
            return "無法翻譯"
        return translated
    except Exception as e:
        print("Google translate error:", e)
        return "無法翻譯"

# ======== LINE 回覆 ========
def line_reply(reply_token, original_text, translated_text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    formatted_text = f"原文：{original_text}\n翻譯：{translated_text}"
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": formatted_text}]
    }
    try:
        res = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=payload)
        print("LINE reply status:", res.status_code, res.text)
    except Exception as e:
        print("LINE reply error:", e)

# ======== Webhook ========
@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_json()
    print("Webhook received:", body)
    events = body.get("events", [])

    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"].strip()
            if not user_text:
                continue

            if event["source"]["type"] == "group":
                # 判斷翻譯方向
                if user_text.isascii():
                    # ASCII → DeepL 翻繁體中文
                    translated = translate_with_deepl(user_text, "ZH-TW")
                else:
                    # 非 ASCII → Google 翻繁體中文（假設來源是印尼文）
                    translated = translate_with_google(user_text, src_lang="id", dest_lang="zh-tw")

                reply_token = event["replyToken"]
                line_reply(reply_token, user_text, translated)
                print("Replied:", translated)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
