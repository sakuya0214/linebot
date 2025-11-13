from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ======== 環境變數 ========
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
DEEPL_AUTH_KEY = os.environ.get("DEEPL_AUTH_KEY")
DEEPL_URL = "https://api-free.deepl.com/v2/translate"

# ======== 自訂字典（只套中文） ========
custom_dict = {
    "伊達": "Indah",
    "依達": "Indah"
}

def apply_custom_dict(text, target_lang):
    if target_lang == "ZH-TW":  # 只在翻中文時套用
        for k, v in custom_dict.items():
            text = text.replace(k, v)
    return text

# ======== Fallback 表情訊息 ========
def fallback_message():
    return "無法翻譯 😢"

# ======== 翻譯函數 ========
def translate_text(text, target_lang):
    if not text.strip():
        return text
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
            return fallback_message()

        return translated
    except Exception as e:
        print("Translate error:", e)
        return fallback_message()

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
    print("Webhook received:", body)  # Debug log
    events = body.get("events", [])

    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            text = event["message"]["text"].strip()
            if not text:
                continue

            if event["source"]["type"] == "group":
                # 判斷翻譯方向：中文 → 印尼文，非中文 → 中文繁體
                if any("\u4e00" <= c <= "\u9fff" for c in text):
                    target_lang = "ID"
                else:
                    target_lang = "ZH-TW"

                translated = translate_text(text, target_lang)
                reply_token = event["replyToken"]
                line_reply(reply_token, text, translated)
                print("Replied:", translated)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
