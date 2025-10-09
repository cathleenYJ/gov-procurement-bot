# 🏛️ 政府採購 Line Bot 部署指南

## 🚀 Render 部署

### 1. 準備工作
- ✅ 確保所有代碼已推送到 GitHub
- ✅ 確保 `requirements.txt` 包含所有依賴
- ✅ 設置環境變數：`CHANNEL_ACCESS_TOKEN` 和 `CHANNEL_SECRET`
- ✅ 測試本地功能：`./dev.sh test`

### 2. 在 Render 上創建 Web Service

1. **登入 Render**
   - 前往 [Render Dashboard](https://dashboard.render.com)
   - 登入您的 Render 帳號

2. **創建新服務**
   - 點擊 "New" → "Web Service"
   - 選擇 "Connect GitHub" 或 "Connect GitLab"
   - 授權 Render 訪問您的倉庫

3. **選擇倉庫**
   - 找到您的 `gov-procurement-crawler` 專案
   - 點擊 "Connect"

4. **配置服務**
   ```
   Name: gov-procurement-bot
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python api/index.py
   ```

5. **進階設定**
   - **Instance Type**: 選擇適合的方案（Free 方案即可開始）
   - **Region**: 選擇最近的地區（建議 Asia Pacific）

### 3. 環境變數設置

在 Render 的 "Environment" 設定中添加以下變數：

| 變數名稱 | 值 | 說明 |
|----------|-----|------|
| `CHANNEL_ACCESS_TOKEN` | `你的_Line_Bot_Channel_Access_Token` | Line Bot 存取權杖 |
| `CHANNEL_SECRET` | `你的_Line_Bot_Channel_Secret` | Line Bot 秘密金鑰 |
| `PORT` | `10000` | Render 自動設置的端口 |
| `DEBUG` | `false` | 生產環境關閉除錯模式 |

### 4. 部署服務

點擊 "Create Web Service" 開始部署。Render 會：
- 自動 clone 您的程式碼
- 執行 `pip install -r requirements.txt`
- 啟動 `python api/index.py`

### 5. 獲取 Webhook URL

部署成功後，在 Render 服務頁面找到：
- **Service URL**: `https://your-service-name.onrender.com`

這個 URL 就是您的 Webhook URL！

## 🔗 設定 Line Bot Webhook

### 在 Line Developers Console 設定

1. **前往 Line Developers Console**
   - 登入 [Line Developers Console](https://developers.line.biz/console/)

2. **選擇您的 Channel**
   - 找到您的政府採購機器人 Channel

3. **設定 Webhook**
   - **Webhook URL**: `https://your-service-name.onrender.com/callback`
   - 啟用 "Use webhook"
   - 停用 "Auto-reply messages"

4. **驗證設定**
   - 點擊 "Verify" 按鈕確認 Webhook URL 正確

## 🧪 測試部署

### 測試 Webhook
```bash
# 測試健康檢查
curl https://your-service-name.onrender.com/

# 測試採購資料 API
curl https://your-service-name.onrender.com/test
```

### 測試 Line Bot
1. **加 Line Bot 為好友**
   - 掃描 QR Code 或搜尋 Bot ID

2. **發送測試訊息**
   ```
   幫助    # 查看指令說明
   採購    # 測試最新採購資料
   統計    # 測試統計功能
   ```

## 📊 監控與維護

### 查看日誌
- 在 Render Dashboard 點擊您的服務
- 前往 "Logs" 標籤查看即時日誌
- 檢查是否有錯誤訊息

### 重新部署
- 推送程式碼到 GitHub 會自動觸發重新部署
- 或在 Render Dashboard 手動觸發重新部署

### 資源使用量
- 監控 CPU 和記憶體使用量
- Free 方案有使用限制，注意不要超過

## 🛠️ 故障排除

### 常見問題

**Q: 部署失敗**
- 檢查 `requirements.txt` 是否正確
- 確認所有依賴都已列出
- 查看 Render 的 build logs

**Q: Webhook 驗證失敗**
- 確認 URL 正確：`https://your-service-name.onrender.com/callback`
- 檢查服務是否正在運行
- 查看應用日誌確認 `/callback` 路由正常

**Q: Line Bot 沒有回應**
- 確認環境變數已正確設定
- 檢查 `CHANNEL_ACCESS_TOKEN` 和 `CHANNEL_SECRET`
- 測試本地功能：`./dev.sh test`

**Q: 記憶體不足**
- Free 方案記憶體有限
- 考慮升級到付費方案
- 優化程式碼減少記憶體使用

### 除錯步驟

1. **檢查服務狀態**
   ```bash
   curl -I https://your-service-name.onrender.com/
   ```

2. **查看應用日誌**
   - 在 Render Dashboard 查看 logs
   - 檢查是否有 Python 錯誤

3. **測試本地環境**
   ```bash
   ./dev.sh test      # 測試功能
   ./dev.sh api       # 測試 API
   ./dev.sh linebot   # 測試模組
   ```

## 💰 費用說明

### Free 方案
- **免費額度**: 每月 750 小時
- **靜態 IP**: 不支援
- **自訂域名**: 不支援
- **SSL 憑證**: 自動提供

### 付費方案
- **Starter**: $7/月 - 每月 750 小時 + 額外功能
- **Standard**: $25/月 - 更多資源和功能

## 🔄 更新部署

### 自動部署
推送程式碼到 GitHub 會自動觸發重新部署。

### 手動部署
1. 在 Render Dashboard 點擊您的服務
2. 點擊 "Manual Deploy" → "Deploy latest commit"

## 📞 支援

如果遇到部署問題：
1. 檢查 `LINEBOT_GUIDE.md` 的設定說明
2. 查看 Render 的 [官方文檔](https://docs.render.com/)
3. 檢查專案的 `SUCCESS_SUMMARY.md` 確認功能正常
4. 聯繫 Render 支援或查看 [Render 狀態頁面](https://status.render.com/)

---

**🎉 成功部署後，您的政府採購 Line Bot 就可以 24/7 運作了！**

### 監控內存使用
應用會在日誌中輸出內存使用情況：
```
開始獲取新聞，當前內存使用: 45.2 MB
RSS 文章數: 8，總文章數: 8
AMD 文章數: 5
NVIDIA 文章數: 5
最終處理文章數: 10，內存使用: 67.8 MB
處理完成，生成 8 條新聞，內存使用: 52.1 MB
```

### 如果仍然遇到內存問題
1. **檢查 Render 日誌** 查看具體的內存使用模式
2. **減少採購資料數量** 修改 `procurement_processors.py` 中的 `max_tenders`
3. **降低並發數** 修改 `max_workers` 設置
4. **升級實例類型** 在 Render 中選擇更大的內存配置

## 故障排除

### ModuleNotFoundError
如果遇到模塊導入錯誤，確保：
1. `__init__.py` 文件存在於項目根目錄
2. `api/index.py` 中的路徑設置正確
3. 所有依賴都在 `requirements.txt` 中

### 內存不足錯誤
如果仍然遇到內存問題：
1. 檢查應用日誌中的內存使用情況
2. 考慮減少 `max_articles` 和 `max_workers`
3. 在 Render 中升級到更大的實例類型

### Line Bot SDK 警告
目前使用的 Line Bot SDK 版本較舊，建議升級到 v3：
```bash
pip install line-bot-sdk==3.0.0
```

然後更新導入：
```python
from linebot.v3 import LineBotApi
from linebot.v3.webhook import WebhookHandler
```