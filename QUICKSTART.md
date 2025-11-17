# 🚀 Supabase 快速開始指南

這份指南幫助你快速設定 Supabase 並開始使用。

## 步驟 1: 安裝依賴套件

```bash
pip install -r requirements.txt
```

這會安裝所有必要的套件，包括新增的 `supabase`。

## 步驟 2: 建立 Supabase 專案

### 2.1 註冊/登入 Supabase
訪問 https://supabase.com/ 並登入（可使用 GitHub 帳號）

### 2.2 建立新專案
1. 點擊 **New Project**
2. 填入資訊：
   - Name: `gov-procurement-bot`
   - Database Password: 設定一個強密碼（記下來）
   - Region: 選擇 `Northeast Asia (Tokyo)`
3. 點擊 **Create new project**
4. 等待 1-2 分鐘讓專案初始化

## 步驟 3: 建立資料表

### 3.1 開啟 SQL Editor
1. 在左側選單點擊 **SQL Editor**
2. 點擊 **New query**

### 3.2 執行建表 SQL
複製並貼上以下 SQL，然後點擊 **Run**：

```sql
-- 建立使用者資料表
CREATE TABLE users (
  line_user_id TEXT PRIMARY KEY,
  company TEXT NOT NULL,
  contact_name TEXT NOT NULL,
  email TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 建立索引
CREATE INDEX idx_users_company ON users(company);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- 建立自動更新時間戳的觸發器
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

看到 **Success. No rows returned** 就表示成功！

## 步驟 4: 取得 API 金鑰

1. 點擊左側的 **Settings** (齒輪圖示)
2. 選擇 **API**
3. 找到並複製：
   - **URL**: `https://xxxxx.supabase.co`
   - **anon public** key: `eyJhbGci...` (很長的一串)

## 步驟 5: 設定環境變數

### 5.1 複製範例檔案
```bash
cp .env.example .env
```

### 5.2 編輯 .env 檔案
用文字編輯器開啟 `.env`，填入以下資訊：

```bash
# Line Bot 設定
CHANNEL_ACCESS_TOKEN=你的_line_bot_token
CHANNEL_SECRET=你的_line_bot_secret

# Supabase 資料庫設定
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGci...你的_anon_key

# 管理員設定
ADMIN_PASSWORD=設定一個強密碼

# 伺服器設定
PORT=5000
DEBUG=true
```

## 步驟 6: 測試連接

執行以下命令測試 Supabase 連接：

```bash
python -c "from clients.supabase_client import SupabaseClient; client = SupabaseClient(); print('✅ Supabase 連接成功！')"
```

如果看到 **✅ Supabase 連接成功！** 就表示設定正確！

## 步驟 7: 啟動應用

```bash
python procurement_bot.py
```

你應該會看到：
```
INFO:__main__:Supabase client initialized successfully
 * Running on http://127.0.0.1:5000
```

## 🎯 驗證功能

### 方法 1: 透過 Line Bot
1. 將 Line Bot 設定完成（設定 Webhook URL）
2. 加入機器人好友
3. 點擊「開始登錄」
4. 依序填入資料
5. 確認收到「✅ 登錄完成！」

### 方法 2: 透過管理介面
訪問：`http://localhost:5000/admin/users?password=你的管理員密碼`

應該會看到：
```json
{
  "status": "success",
  "total_users": 0,
  "users": []
}
```

### 方法 3: 在 Supabase Dashboard
1. 回到 Supabase Dashboard
2. 點擊 **Table Editor**
3. 選擇 `users` 表
4. 可以看到資料表結構（目前無資料）

## ✅ 完成檢查清單

- [ ] Supabase 專案已建立
- [ ] users 資料表已建立
- [ ] 已取得 URL 和 API Key
- [ ] .env 檔案已設定
- [ ] pip install 已完成
- [ ] 連接測試成功
- [ ] Flask 應用可啟動
- [ ] 可以透過管理介面查看資料

## ❓ 常見問題

### Q: 執行 SQL 時出錯？
A: 確認：
- 是否有清空之前的 SQL
- 是否完整複製了所有 SQL
- 點擊 **Run** 按鈕執行

### Q: 找不到 API Key？
A: 路徑是：Settings > API > Project API keys > anon public

### Q: 連接測試失敗？
A: 檢查：
1. `.env` 檔案在專案根目錄
2. SUPABASE_URL 和 SUPABASE_KEY 格式正確
3. 沒有多餘的引號或空格
4. 已執行 `pip install supabase`

### Q: 想要看詳細設定？
A: 查看 `SUPABASE_SETUP.md` 有完整的說明

## 📚 下一步

- 閱讀 `SUPABASE_SETUP.md` 了解進階功能
- 設定 Line Bot Webhook
- 部署到 Vercel 或 Heroku
- 設定自動備份

## 🆘 需要協助？

如果遇到問題：
1. 檢查 `SUPABASE_SETUP.md` 的疑難排解章節
2. 查看 Supabase Dashboard 的 Logs
3. 確認所有環境變數設定正確

---

**🎉 恭喜！你已完成 Supabase 設定！**
