# 政府採購爬蟲 Line Bot

此專案從新聞爬蟲改造而來，專門用於抓取台灣政府電子採購網的招標資料，並透過 Line Bot 提供即時政府採購資訊查詢服務。

## 功能特色

- **政府採購資料整合**：從政府電子採購網抓取最新招標公告
- **智能關鍵字搜尋**：支援關鍵字搜尋相關採購案件
- **分類查詢**：支援工程類、財物類、勞務類採購分類查詢
- **Line Bot 整合**：支援即時聊天獲取採購資訊
- **統計分析**：提供採購資料統計和趨勢分析

## 技術架構

- **後端框架**：Flask + Line Bot SDK
- **資料擷取**：requests + BeautifulSoup (解析HTML)
- **資料庫**：Supabase (PostgreSQL)
- **資料來源**：政府電子採購網 (https://web.pcc.gov.tw)
- **部署方式**：支援本地開發和雲端部署（Vercel/Heroku）

## 需求環境

- Python 3.8+
- 支援的作業系統：macOS, Linux, Windows

## 安裝步驟

1. **克隆專案**
   ```bash
   git clone <repository-url>
   cd gov-procurement-crawler
   ```

2. **創建虛擬環境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # 或在 Windows 上：venv\Scripts\activate
   ```

3. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

4. **環境配置**
   ```bash
   cp .env.example .env
   # 編輯 .env 文件，填入以下資訊：
   # - Line Bot 的 Token 和 Secret
   # - Supabase URL 和 API Key
   # - 管理員密碼
   ```

5. **設定 Supabase 資料庫**
   
   a. 前往 [Supabase](https://supabase.com/) 建立免費帳號
   
   b. 建立新專案（New Project）
   
   c. 在 SQL Editor 中執行以下 SQL 建立資料表：
   ```sql
   CREATE TABLE users (
     line_user_id TEXT PRIMARY KEY,
     company TEXT NOT NULL,
     contact_name TEXT NOT NULL,
     email TEXT NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- 建立更新時間自動更新的觸發器
   CREATE OR REPLACE FUNCTION update_updated_at_column()
   RETURNS TRIGGER AS $$
   BEGIN
     NEW.updated_at = NOW();
     RETURN NEW;
   END;
   $$ language 'plpgsql';

   CREATE TRIGGER update_users_updated_at 
     BEFORE UPDATE ON users 
     FOR EACH ROW 
     EXECUTE FUNCTION update_updated_at_column();
   ```
   
   d. 從專案設定頁面複製以下資訊到 `.env` 檔案：
   - `SUPABASE_URL`: Project URL (Settings > API)
   - `SUPABASE_KEY`: anon public key (Settings > API)

## 使用方法

### 本地開發

```bash
# 運行本地開發版本
python linebot_app.py
```

專案將在 http://localhost:5000 運行

### 測試API

```bash
# 測試政府採購資料獲取
curl http://localhost:5000/test
```

### 生產部署

專案支援多種部署方式：

#### Vercel 部署
- 將 `api/index.py` 部署為 serverless function
- Webhook URL 格式：`https://your-domain.vercel.app/api/index`

#### Heroku 部署
```bash
# 設定環境變數
heroku config:set CHANNEL_ACCESS_TOKEN=your_token
heroku config:set CHANNEL_SECRET=your_secret
heroku config:set PORT=5000
```

### Line Bot 設定

1. 前往 [Line Developers Console](https://developers.line.biz/)
2. 創建 Messaging API channel
3. 複製 Channel Access Token 和 Channel Secret 到 `.env` 文件
4. 設定 Webhook URL 指向您的部署域名 + `/callback`
5. 在 Line 中添加 Bot 為好友

### 聊天指令

#### 基本指令：
- **採購/標案**：獲取最新政府採購資訊
- **高額/大案**：獲取高金額採購案件
- **統計/數據**：查看採購統計資料

#### 搜尋指令：
- **search 關鍵字**：搜尋相關採購案件
- **搜尋 關鍵字**：搜尋相關採購案件

#### 分類查詢：
- **工程**：工程類採購案件
- **財物**：財物類採購案件  
- **勞務**：勞務類採購案件

### 更多（分頁）與不重複結果

「更多」按鈕現在會嘗試使用分頁（page）取得下一頁結果，以避免回傳與使用者已看過的標案重複。

- 每次點擊「更多」，系統會向後翻一頁（若當日資料太少，會自動往前天數抓取）；
- 每次點擊「更多」，系統會向後翻一頁（若當日資料太少，會自動往前天數抓取）；分頁號碼會被儲存到 Supabase（user_browsing_state.page），使用者重新回到對話或在其他裝置繼續查詢時可以保持翻頁進度；
- 系統在查詢時會排除已查看的標案 ID；若分頁沒有新資料，會自動使用多日跨查詢以取得更多不重複資料；
- 如果仍看到重複，可以確認是否使用了「更多」按鈕（訊息文字為「更多財物類」而非「財物類」），或嘗試晚一點再查詢（官方資料更新後會有新結果）。

#### 幫助指令：
- **help/幫助**：顯示使用指南

#### 範例：
```
search 資訊系統
搜尋 AI人工智慧
高額
工程
統計
```

## 專案結構

```
gov-procurement-crawler/
├── procurement_bot.py               # 核心邏輯模塊
├── linebot_app.py                  # 本地開發入口
├── procurement_processors.py       # 採購資料處理器
├── container.py                    # 依賴注入容器
├── clients/
│   └── procurement_client.py       # 政府採購網客戶端
├── api/
│   └── index.py                    # 生產部署入口
├── requirements.txt                # Python 依賴
├── .env.example                    # 環境變數範例
├── README.md                      # 專案說明
└── .gitignore                     # Git 忽略規則
```

## 開發說明

### 核心模塊

- **`procurement_bot.py`**：包含所有業務邏輯
  - Line Bot 訊息處理
  - Flask 應用工廠函數

- **`procurement_processors.py`**：採購資料處理器
  - 政府採購資料抓取
  - 關鍵字搜尋和篩選
  - 資料格式化和排序

- **`clients/procurement_client.py`**：政府採購網客戶端
  - HTTP 請求處理
  - HTML 解析
  - 分頁處理

### 資料來源

- **政府電子採購網**：https://web.pcc.gov.tw
  - 招標公告
  - 公開徵求
  - 公開閱覽
  - 政府採購預告

### 搜尋和篩選邏輯

1. **關鍵字匹配**：在標案名稱和機關名稱中搜尋
2. **分類篩選**：按採購性質（工程類、財物類、勞務類）
3. **金額篩選**：支援高金額標案篩選
4. **評分排序**：根據相關性和重要性排序

### 支援的查詢參數

- **日期範圍**：當日、等標期內、自訂日期區間
- **招標類型**：招標公告、公開徵求、公開閱覽、採購預告
- **招標方式**：公開招標、選擇性招標、限制性招標等
- **採購性質**：工程類、財物類、勞務類

## API 說明

### 測試端點

```bash
GET /test
```

返回範例：
```json
{
  "status": "success",
  "message": "成功獲取政府採購資料",
  "data_count": 3,
  "sample_data": {
    "tender_name": "智慧福利雞舍電力改善工程",
    "org_name": "國立屏東科技大學",
    "budget_amount": 5557810
  }
}
```

### 健康檢查

```bash
GET /
```

返回系統狀態資訊。

## 注意事項

- 政府採購網可能有存取限制，建議適度使用
- Line Bot 有訊息長度限制，長內容會被截斷
- 建議定期檢查政府採購網頁面結構變化
- 生產環境建議使用環境變數管理敏感信息
- 大量查詢可能觸發網站防護機制

## 法律聲明

此專案僅供學習和研究使用，請遵守以下規範：
- 遵守政府電子採購網使用條款
- 適度使用，避免對政府網站造成負擔
- 不得用於商業用途
- 資料僅供參考，正式資訊請以官方網站為準

## 授權

此專案僅供學習和個人使用，請遵守相關法律法規。
