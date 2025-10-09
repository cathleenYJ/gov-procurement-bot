# 🎯 開始使用

## 📝 前置作業檢查清單

- [ ] Python 3.7+ 已安裝
- [ ] Git 已安裝 
- [ ] Line Developer 帳號 (如需 Line Bot 功能)

## ⚡ 5 分鐘快速啟動

### 1️⃣ 下載並設定

```bash
# 克隆專案 (如果還沒有)
git clone https://github.com/你的用戶名/gov-procurement-crawler.git
cd gov-procurement-crawler

# 一鍵設定
./dev.sh setup
```

### 2️⃣ 測試功能

```bash
# 測試政府採購 API
./dev.sh procurement

# 預期輸出：
# 🔍 測試搜尋功能...
# ✅ 找到 X 筆資料
# 1. 某某資訊系統採購案
# 2. 某某工程專案
# 3. 某某勞務採購
```

### 3️⃣ 完整測試

```bash
# 執行完整測試套件
./dev.sh test

# 這會測試：
# - 政府採購客戶端連線
# - 資料處理器功能
# - 關鍵字搜尋
# - 分類篩選
```

### 4️⃣ 啟動 Line Bot (選用)

如果你想使用 Line Bot 功能：

1. **設定 Line Bot 憑證**
   ```bash
   # 編輯 .env 檔案
   nano .env
   
   # 填入你的 Line Bot 憑證
   CHANNEL_ACCESS_TOKEN=你的token
   CHANNEL_SECRET=你的secret
   ```

2. **啟動 Bot**
   ```bash
   ./dev.sh bot
   ```

3. **測試 Bot**
   - 將你的 Line Bot 加為好友
   - 傳送 `幫助` 查看所有指令
   - 試試 `今日採購` 或 `搜尋 資訊`

## 🔍 測試搜尋功能

即使沒有 Line Bot，你也可以直接測試搜尋：

```bash
# 進入 Python 環境
source venv/bin/activate
python

# 在 Python 中測試
>>> from clients.procurement_client import ProcurementClient
>>> client = ProcurementClient()
>>> results = client.search_tenders(keyword="資訊", days=7)
>>> print(f"找到 {len(results)} 筆採購案")
>>> print(results[0]['title'])  # 顯示第一筆標題
```

## 🆘 遇到問題？

### 檢查清單

1. **Python 版本**
   ```bash
   python --version  # 應該是 3.7+
   ```

2. **網路連線**
   ```bash
   curl -I https://web.pcc.gov.tw/  # 應該回傳 200
   ```

3. **依賴安裝**
   ```bash
   ./dev.sh deps  # 檢查依賴狀態
   ```

### 重新安裝

如果遇到任何問題，完全重新安裝：

```bash
# 清理
./dev.sh clean
rm -rf venv

# 重新設定
./dev.sh setup

# 重新測試
./dev.sh test
```

## ✅ 成功指標

當你看到以下輸出時，表示一切正常：

```
✅ 找到 XX 筆資料
✅ 政府採購客戶端測試: 通過
✅ 資料處理器測試: 通過
✅ 關鍵字搜尋測試: 通過
✅ 分類篩選測試: 通過
🎉 所有測試通過！
```

## 🎯 下一步

- 探索 `QUICKSTART.md` 了解更多功能
- 查看 `PROJECT_SUMMARY.md` 了解技術細節
- 修改搜尋參數來客製化你的需求

**開始爬取政府採購資料吧！** 🚀