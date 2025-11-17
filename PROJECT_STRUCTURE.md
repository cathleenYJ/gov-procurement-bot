# 專案檔案結構說明

## 📁 核心檔案

### Python 程式碼
- **procurement_bot.py** - 主程式（Line Bot 和 Flask 應用）
- **procurement_processors.py** - 政府採購資料處理器

### 客戶端模組 (clients/)
- **supabase_client.py** - Supabase 資料庫客戶端
- **analytics_client.py** - 使用者行為分析模組
- **procurement_client.py** - 政府採購網爬蟲客戶端
- **base_client.py** - 基礎 HTTP 客戶端
- **__init__.py** - 模組初始化檔案

### API 部署 (api/)
- **index.py** - Vercel serverless 部署入口

## 📋 配置檔案

- **.env** - 環境變數（本地使用，不提交到 Git）
- **.env.example** - 環境變數範例檔案
- **requirements.txt** - Python 依賴套件清單
- **.gitignore** - Git 忽略規則
- **.editorconfig** - 編輯器配置

## 📖 文件檔案

- **README.md** - 專案主要說明文件
- **QUICKSTART.md** - Supabase 快速設定指南
- **SUPABASE_SETUP.md** - Supabase 詳細設定說明
- **ANALYTICS_SETUP.md** - 使用者行為分析設定指南

## 🗄️ 資料庫

- **database_schema_analytics.sql** - 行為分析資料表結構（在 Supabase 執行）

## 🛠️ 開發工具

- **dev.sh** - 本地開發啟動腳本

## 📂 目錄結構

```
gov-procurement-crawler/
├── clients/                    # 客戶端模組
│   ├── __init__.py
│   ├── analytics_client.py     # 行為分析
│   ├── base_client.py          # HTTP 基礎
│   ├── procurement_client.py   # 採購網爬蟲
│   └── supabase_client.py      # 資料庫
│
├── api/                        # Vercel 部署
│   └── index.py
│
├── procurement_bot.py          # 主程式
├── procurement_processors.py   # 資料處理
├── requirements.txt            # 依賴套件
├── .env                        # 環境變數（本地）
├── .env.example                # 環境變數範例
│
└── docs/                       # 文件（概念上）
    ├── README.md
    ├── QUICKSTART.md
    ├── SUPABASE_SETUP.md
    └── ANALYTICS_SETUP.md
```

## 🚫 不會被提交的檔案（.gitignore）

- `.venv/` - Python 虛擬環境
- `__pycache__/` - Python 快取
- `*.pyc` - Python 編譯檔案
- `.env` - 環境變數（包含敏感資訊）
- `*.log` - 日誌檔案
- `.DS_Store` - macOS 系統檔案
- `.vscode/`, `.idea/` - IDE 設定檔

## 📝 建議的開發流程

1. **本地開發**
   ```bash
   source .venv/bin/activate
   python procurement_bot.py
   ```

2. **部署前檢查**
   - 確認 `.env.example` 已更新
   - 測試所有功能
   - 檢查 requirements.txt

3. **部署到 Vercel**
   - 推送到 GitHub
   - Vercel 自動部署
   - 設定環境變數

## 🔧 維護建議

- **定期更新依賴**：`pip install --upgrade -r requirements.txt`
- **備份資料庫**：定期從 Supabase 匯出資料
- **監控日誌**：檢查錯誤和異常行為
- **清理舊資料**：執行 `cleanup_old_logs()` 函數
