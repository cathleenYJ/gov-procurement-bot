# 🏛️ 政府採購爬蟲 Line Bot - 快速開始

## 📋 專案概述

這是一個基於 Line Bot 的台灣政府電子採購網資料爬蟲系統，可以：
- 🔍 搜尋政府採購資訊
- 📊 提供統計分析
- 🏷️ 分類篩選招標案件
├── 🧪 測試相關
│   └── test_procurement.py   # 採購功能測試 透過 Line Bot 即時互動

## 🚀 快速開始

### 1. 設定開發環境

```bash
# 一鍵設定（推薦）
./dev.sh setup

# 或手動設定
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. 設定 Line Bot

編輯 `.env` 檔案：

```env
# Line Bot 設定
CHANNEL_ACCESS_TOKEN=你的_LINE_BOT_CHANNEL_ACCESS_TOKEN
CHANNEL_SECRET=你的_LINE_BOT_CHANNEL_SECRET

# 伺服器設定
DEBUG=true
PORT=5000
HOST=0.0.0.0
```

### 3. 測試功能

```bash
# 完整功能測試
./dev.sh test

# 測試政府採購 API 連線
./dev.sh procurement

# 測試 API 端點
./dev.sh api
```

### 4. 啟動 Line Bot

```bash
# 啟動政府採購 Line Bot
./dev.sh bot
```

## 🤖 Line Bot 指令

### 基本指令
- `幫助` - 顯示所有可用指令
- `狀態` - 檢查 Bot 運行狀態

### 搜尋指令
- `搜尋 關鍵字` - 搜尋包含關鍵字的採購案
- `今日採購` - 今日新發布的採購案
- `本週採購` - 本週的採購案

### 分類搜尋
- `資訊採購` - 資訊類採購案
- `工程採購` - 工程類採購案
- `勞務採購` - 勞務類採購案

### 統計資訊
- `統計` - 顯示採購案統計資訊
- `熱門關鍵字` - 最受關注的採購關鍵字

## 🛠️ 開發指令

### 系統管理
```bash
./dev.sh setup        # 設定開發環境
./dev.sh clean        # 清理臨時文件
./dev.sh deps         # 檢查依賴更新
```

### 測試功能
```bash
./dev.sh test         # 完整功能測試
./dev.sh procurement  # 測試採購 API
./dev.sh api         # 測試 API 端點
```

### 啟動服務
```bash
./dev.sh bot         # 啟動 Line Bot
./dev.sh run         # 啟動舊版服務器
```

## 📁 專案結構

```
gov-procurement-crawler/
├── 🤖 Line Bot 相關
│   ├── linebot_app.py          # Line Bot 主應用
│   ├── procurement_bot.py      # 政府採購 Bot 邏輯
│   └── api/index.py           # API 端點
├── 🕷️ 爬蟲相關
│   ├── clients/
│   │   ├── procurement_client.py  # 政府採購 API 客戶端
│   │   └── ...
│   └── procurement_processors.py # 資料處理邏輯
├── ⚙️ 系統配置
│   ├── container.py           # 依賴注入容器
│   ├── requirements.txt       # Python 依賴
│   ├── .env.example          # 環境變數範例
│   └── dev.sh               # 開發工具腳本
└── 🧪 測試相關
    ├── test_procurement.py   # 採購功能測試
    └── test_basic.py        # 基本測試
```

## 🔧 API 端點

### 基本端點
- `GET /` - 健康檢查
- `POST /callback` - Line Bot webhook

### 測試端點
- `GET /test` - 測試採購資料擷取
- `GET /search?q=關鍵字` - 搜尋採購案

## 📊 資料來源

- **政府電子採購網**: https://web.pcc.gov.tw/
- **API 端點**: `/tps/pss/tender.do?searchMode=common`
- **資料格式**: HTML (需要解析)
- **更新頻率**: 即時

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 授權

此專案使用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案

## 🆘 故障排除

### 常見問題

1. **虛擬環境問題**
   ```bash
   rm -rf venv
   ./dev.sh setup
   ```

2. **依賴衝突**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

3. **Line Bot 連線失敗**
   - 檢查 `.env` 檔案中的 `CHANNEL_ACCESS_TOKEN` 和 `CHANNEL_SECRET`
   - 確認 webhook URL 設定正確

4. **政府採購網 API 無回應**
   ```bash
   ./dev.sh procurement  # 測試 API 連線
   ```

### 日誌檢查

```bash
# 檢查 Line Bot 日誌
./dev.sh bot 2>&1 | tee bot.log

# 檢查採購 API 日誌
./dev.sh procurement 2>&1 | tee api.log
```

## 📞 支援

如有問題，請：
1. 查看 [故障排除](#故障排除) 部分
2. 檢查 [Issues](https://github.com/你的用戶名/gov-procurement-crawler/issues)
3. 創建新的 Issue 描述問題