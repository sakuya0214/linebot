const express = require('express');
const { Client, middleware } = require('@line/bot-sdk');
const axios = require('axios');

const app = express();

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

// ===== Fallback 表情訊息 =====
function fallbackMessage() {
    return "無法翻譯 😢";
}

// ===== Google Translate API =====
async function translate(text, targetLang) {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
    const res = await axios.get(url);
    return res.data[0][0][0];
}

// ===== 翻譯 + 校對 =====
async function translateWithProof(text) {
    if (!text.trim()) return text;

    // 套用自訂字典
    let modifiedText = text.replace(/伊達|依達/g, match => customDict[match] || match);

    try {
        // 檢測語言：含中文 → 印尼文，否則反過來
        const toIndo = /[\u4e00-\u9fff]/.test(text);
        const targetLang = toIndo ? 'id' : 'zh-TW';
        const backLang = toIndo ? 'zh-TW' : 'id';

        // 一次翻譯
        const translated = await translate(modifiedText, targetLang);

        // 二次翻譯（校對）
        const proofread = await translate(translated, backLang);

        // 判斷是否有效
        if (!translated || translated === modifiedText) return { translated: fallbackMessage(), proof: fallbackMessage() };

        return {
            translated,
            proof: proofread || fallbackMessage()
        };
    } catch (e) {
        console.log("Translate error:", e.message);
        return { translated: fallbackMessage(), proof: fallbackMessage() };
    }
}

// ===== Webhook =====
app.post('/callback', middleware(config), async (req, res) => {
    try {
        const events = req.body.events;

        for (let event of events) {
            if (event.type === 'message' && event.message.type === 'text' && event.source.type === 'group') {
                const userText = event.message.text;
                const { translated, proof } = await translateWithProof(userText);

                await client.replyMessage(event.replyToken, {
                    type: 'text',
                    text: `原文：${userText}\n翻譯：${translated}\n校對：${proof}`
                });
            }
        }
        res.sendStatus(200);
    } catch (err) {
        console.log("Webhook error:", err);
        res.sendStatus(500);
    }
});

// ===== 啟動 server =====
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
