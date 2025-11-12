from flask import Flask, request, jsonify
import requests
from langdetect import detect

app = Flask(__name__)

# ======== 配置 ========
LINE_CHANNEL_ACCESS_TOKEN = "QlyDbhy8kPfh15MUZlJyIXu43OQIBT5rSDzWCxAMelTgCmHlCM7HlHpuPD4zhmbS5Ga+W0cmW7SGPZEo7PrCNvrCmHE3dK6IkuVhUbI8zRjUwAf3+ZW7xXsCX25nj8IQ74icKofMdEzzNDc9QIZs8gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "3e557ae4660d67a1768eb76640cec0d1"
DEEPL_AUTH_KEY = "648881f3-2f5e-4a29-8d64-8d566de02bd1:fx"

DEEPL_URL = "https://api-free.deepl.com/v2/translate"

# ======== 翻譯函數 ========
def translate_text(text):
    try:
        lang_detected = detect(text)
    except:
        lang_detected = "zh"

    if lang_detected.startswith("zh"):
        target_lang = "ID"  # 中文 → 印尼文
    else:
        target_lang = "ZH"  # 印尼文 → 中文

    data = {
        "auth_key": DEEPL_AUTH_KEY,
        "text": text,
        "target_lang": target_lang
    }
    response = requests.post(DEEPL_URL, data=data)
    result = response.json()
    return result["translations"][0]["text"]

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
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=payload)

# ======== Webhook ========
@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_json()
    events = body.get("events", [])

    for event in events:
        # 僅處理文字訊息
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"]

            # 群組內訊息全部自動翻譯
            if event["source"]["type"] == "group":
                translated = translate_text(user_text)
                reply_token = event["replyToken"]
                line_reply(reply_token, user_text, translated)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
