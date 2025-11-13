const express = require('express');
const { Client, middleware } = require('@line/bot-sdk');
const axios = require('axios');

const app = express();
app.use(express.json());

// ===== LINE 設定 =====
const config = {
    channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN,
    channelSecret: process.env.LINE_CHANNEL_SECRET
};
const client = new Client(config);

// ===== 自訂字典 =====
const customDict = {
    "伊達": "Indah",
    "依達": "Indah"
};

// ===== DeepL 或 Google 翻譯函數 =====
async function translateText(text) {
    // 自訂字典套用（只中文）
    let modifiedText = text.replace(/伊達|依達/g, match => customDict[match] || match);

    try {
        let targetLang = /[\u4e00-\u9fff]/.test(text) ? 'id' : 'zh';
        // 這裡用 Google Translate 網頁 API 範例
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${targetLang}&dt=t&q=${encodeURIComponent(modifiedText)}`;
        const res = await axios.get(url);
        const translated = res.data[0][0][0];
        return translated || "無法翻譯 😢";
    } catch (e) {
        console.log("Translate error:", e.message);
        return "無法翻譯 😢";
    }
}

// ===== LINE Webhook =====
app.post('/callback', middleware(config), async (req, res) => {
    try {
        const events = req.body.events;
        for (let event of events) {
            if (event.type === 'message' && event.message.type === 'text' && event.source.type === 'group') {
                const userText = event.message.text;
                const translated = await translateText(userText);

                await client.replyMessage(event.replyToken, {
                    type: 'text',
                    text: `原文：${userText}\n翻譯：${translated}`
                });
            }
        }
        res.sendStatus(200);
    } catch (err) {
        console.log("Webhook error:", err.message);
        res.sendStatus(500);
    }
});

// ===== 啟動 server =====
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
