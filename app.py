from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ======== 環境變數設定 ========
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
DEEPL_AUTH_KEY = os.environ.get("DEEPL_AUTH_KEY")

DEEPL_URL = "https://api-free.deepl.com/v2/translate"

# ======== 自訂字典 ========
custom_dict = {
    "伊達": "Indah",
    "依達": "Indah"
}

def apply_custom_dict(text):
    for k, v in custom_dict.items():
        text = text.replace(k, v)
    return text

# ======== 翻譯函數 ========
def translate_text(text, target_lang="ZH-TW"):  # 繁體中文
    if not text.strip():
        return text  # 空訊息直接回原文
    try:
        # 先套用自訂字典
        text_with_dict = apply_custom_dict(text)

        # DeepL 翻譯
        data = {
            "auth_key": DEEPL_AUTH_KEY,
            "text": text_with_dict,
            "target_lang": target_lang
        }
        response = requests.post(DEEPL_URL, data=data)
        response.raise_for_status()
        result = response.json()
        translated = result["translations"][0]["text"]
        return translated
    except Exception as e:
        print("Translate error:", e)
        return "無法翻譯"  # 出錯時回覆

# ======== LINE 回覆函數 ========
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
    print("Webhook received:", body)  # Debug log
    events = body.get("events", [])

    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"].strip()
            if not user_text:
                continue  # 空訊息跳過

            if event["source"]["type"] == "group":
                # 判斷翻譯方向
                if user_text.isascii():
                    target_lang = "ZH-TW"  # 英文或 ASCII → 繁體中文
                else:
                    target_lang = "ID"  # 非 ASCII → 印尼文

                translated = translate_text(user_text, target_lang)
                reply_token = event["replyToken"]
                line_reply(reply_token, user_text, translated)
                print("Replied:", translated)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
