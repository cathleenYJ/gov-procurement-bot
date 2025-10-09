# 📱 Line Bot 設定與使用指南

## 🚀 快速開始

### 1. 設定 Line Bot 憑證

首先，你需要在 [Line Developers Console](https://developers.line.biz/console/) 建立一個 Line Bot：

#### 建立 Provider
1. 登入 Line Developers Console
2. 點擊 "Create a new provider"
3. 輸入 Provider 名稱（例如：政府採購機器人）

#### 建立 Channel
1. 在 Provider 下點擊 "Create a Messaging API channel"
2. 填寫基本資訊：
   - **Channel name**: 政府採購查詢機器人
   - **Channel description**: 查詢台灣政府電子採購網資料
   - **Category**: 工具
3. 同意條款並建立

#### 獲取憑證
建立完成後，在 Channel 設定頁面找到：
- **Channel access token**: 點擊 "Issue" 按鈕生成
- **Channel secret**: 複製這個值

### 2. 設定環境變數

編輯 `.env` 檔案：

```bash
# 將以下值替換為你的實際憑證
CHANNEL_ACCESS_TOKEN=你的_CHANNEL_ACCESS_TOKEN
CHANNEL_SECRET=你的_CHANNEL_SECRET
```

### 3. 設定 Webhook

在 Line Developers Console 的 Channel 設定中：

1. **Webhook URL**: 設定為你的伺服器 URL + `/callback`
   - 本地開發: `https://你的-ngrok-url.ngrok.io/callback`
   - 生產環境: `https://你的域名/callback`

2. **Webhook 設定**:
   - 啟用 "Use webhook"
   - 停用 "Auto-reply messages"（因為我們要自訂回應）

### 4. 啟動 Line Bot

```bash
# 啟動政府採購 Line Bot
./dev.sh bot
```

## 🤖 Line Bot 指令說明

### 📝 基本指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `採購` / `標案` | 查看最新採購資訊 | 輸入：採購 |
| `高額` / `大案` | 查看高金額採購案（>5000萬） | 輸入：高額 |
| `統計` / `數據` | 查看採購統計資料 | 輸入：統計 |
| `幫助` / `help` | 顯示完整使用指南 | 輸入：幫助 |

### 🔍 搜尋指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `search 關鍵字` | 英文搜尋 | search 資訊系統 |
| `搜尋 關鍵字` | 中文搜尋 | 搜尋 AI人工智慧 |

### 📂 分類查詢

| 指令 | 說明 | 回傳內容 |
|------|------|----------|
| `工程` | 工程類採購案 | 建築、土木、機電工程等 |
| `財物` | 財物類採購案 | 設備、材料、用品等 |
| `勞務` | 勞務類採購案 | 服務、顧問、維護等 |

### 💡 智慧搜尋

**直接輸入關鍵字**，Bot 會自動搜尋相關採購案：
- 輸入：`資訊系統` → 自動搜尋包含「資訊系統」的採購案
- 輸入：`AI` → 自動搜尋包含「AI」的採購案

## 📊 回應格式說明

### 採購資訊格式
```
📊 [標題] ([金額]) - [機關名稱]
• 採購類型：[工程/財物/勞務]
• 公告日期：[日期]
• 截止日期：[日期]
• 詳細連結：[網址]
```

### 統計資訊格式
```
📈 政府採購統計資訊

📅 今日標案：[數量] 筆
📅 本週標案：[數量] 筆

🏗️ 工程類：[數量] 筆
🛒 財物類：[數量] 筆
👥 勞務類：[數量] 筆

💰 總金額：[金額]
```

## 🛠️ 本地開發設定

### 使用 ngrok 進行本地測試

1. **安裝 ngrok**:
   ```bash
   # macOS
   brew install ngrok/ngrok/ngrok

   # 或下載二進制檔案
   # https://ngrok.com/download
   ```

2. **啟動 ngrok**:
   ```bash
   # 將本地 5000 端口暴露到公網
   ngrok http 5000
   ```

3. **設定 Webhook URL**:
   - 複製 ngrok 提供的 URL（例如：`https://abc123.ngrok.io`）
   - 在 Line Developers Console 設定 Webhook URL 為：`https://abc123.ngrok.io/callback`

4. **啟動 Bot**:
   ```bash
   ./dev.sh bot
   ```

## 🌐 生產環境部署

### 部署到 Heroku

1. **建立 Heroku 應用**:
   ```bash
   heroku create your-gov-procurement-bot
   ```

2. **設定環境變數**:
   ```bash
   heroku config:set CHANNEL_ACCESS_TOKEN=你的token
   heroku config:set CHANNEL_SECRET=你的secret
   ```

3. **部署程式碼**:
   ```bash
   git push heroku main
   ```

4. **設定 Webhook URL**:
   - Heroku URL: `https://your-gov-procurement-bot.herokuapp.com/callback`

### 部署到 Vercel

1. **安裝 Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **部署**:
   ```bash
   vercel --prod
   ```

3. **設定環境變數**:
   ```bash
   vercel env add CHANNEL_ACCESS_TOKEN
   vercel env add CHANNEL_SECRET
   ```

## 🧪 測試你的 Line Bot

### 基本測試
1. **加好友**: 掃描 Line Bot 的 QR Code
2. **發送訊息**: 輸入 `幫助` 查看指令
3. **測試功能**: 嘗試不同的指令

### 功能測試清單
- [ ] `幫助` - 顯示使用指南
- [ ] `採購` - 獲取最新採購資訊
- [ ] `統計` - 查看統計資料
- [ ] `search 資訊` - 關鍵字搜尋
- [ ] `工程` - 分類查詢
- [ ] 直接輸入關鍵字 - 智慧搜尋

## 🔧 故障排除

### 常見問題

**Q: Bot 沒有回應訊息**
- 檢查 Webhook URL 是否正確設定
- 確認環境變數已正確設定
- 查看伺服器日誌：`tail -f server.log`

**Q: 收到 "Invalid signature" 錯誤**
- 檢查 `CHANNEL_SECRET` 是否正確
- 確認 Webhook 請求來自 Line 官方

**Q: 無法獲取採購資料**
- 檢查網路連線
- 確認政府採購網 API 正常運作
- 查看 `test_procurement.py` 測試結果

**Q: 本地開發無法接收訊息**
- 確保 ngrok 正在運行
- 檢查防火牆設定
- 確認端口 5000 未被佔用

### 除錯指令

```bash
# 測試政府採購 API 連線
./dev.sh procurement

# 測試完整功能
./dev.sh test

# 測試 API 端點
./dev.sh api

# 查看伺服器日誌
tail -f server.log
```

## 📞 支援

如果遇到問題：
1. 檢查 `SUCCESS_SUMMARY.md` 了解專案狀態
2. 查看 `CLEANUP_SUMMARY.md` 了解清理記錄
3. 執行 `./dev.sh test` 驗證功能
4. 檢查 Line Developers Console 的錯誤日誌

---

**🎉 現在開始享受你的政府採購查詢機器人吧！**