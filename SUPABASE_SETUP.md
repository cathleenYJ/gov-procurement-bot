# Supabase 資料庫設定指南

本文件說明如何設定 Supabase 作為政府採購機器人的資料庫。

## 📋 前置準備

- Supabase 帳號（免費方案即可）
- 專案的 `.env` 檔案

## 🚀 快速設定步驟

### 1. 建立 Supabase 專案

1. 前往 [Supabase](https://supabase.com/) 並登入
2. 點擊 **New Project**
3. 填入專案資訊：
   - **Project Name**: `gov-procurement-bot`（或你喜歡的名稱）
   - **Database Password**: 設定一個安全的密碼（請記住此密碼）
   - **Region**: 選擇 `Northeast Asia (Tokyo)` 以獲得最佳效能
4. 點擊 **Create new project** 並等待專案建立完成（約 1-2 分鐘）

### 2. 建立資料表

專案建立完成後：

1. 在左側選單點擊 **SQL Editor**
2. 點擊 **New query**
3. 貼上以下 SQL 並執行（點擊右下角的 **Run** 按鈕）：

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

-- 建立索引以加速查詢
CREATE INDEX idx_users_company ON users(company);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

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

-- 加入註解說明
COMMENT ON TABLE users IS '政府採購機器人使用者資料表';
COMMENT ON COLUMN users.line_user_id IS 'Line 使用者唯一識別碼';
COMMENT ON COLUMN users.company IS '公司名稱';
COMMENT ON COLUMN users.contact_name IS '聯絡人姓名';
COMMENT ON COLUMN users.email IS '聯絡人電子郵件';
COMMENT ON COLUMN users.created_at IS '資料建立時間';
COMMENT ON COLUMN users.updated_at IS '資料最後更新時間';
```

4. 執行成功後，你應該會看到「Success. No rows returned」訊息

### 3. 取得 API 金鑰

1. 在左側選單點擊 **Settings** (齒輪圖示)
2. 選擇 **API**
3. 複製以下兩個值：
   - **Project URL**: 形如 `https://xxxxx.supabase.co`
   - **anon public key**: 一個很長的 JWT token

### 4. 設定環境變數

編輯專案根目錄的 `.env` 檔案，加入以下設定：

```bash
# Supabase 資料庫設定
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc...
```

將上面的值替換為你剛才複製的實際值。

### 5. 驗證設定

執行以下命令測試連接：

```bash
python -c "from clients.supabase_client import SupabaseClient; client = SupabaseClient(); print('✅ Supabase 連接成功！')"
```

如果看到「✅ Supabase 連接成功！」訊息，表示設定完成！

## 📊 資料表結構說明

### users 資料表

| 欄位名稱 | 資料型別 | 說明 | 限制 |
|---------|---------|------|------|
| line_user_id | TEXT | Line 使用者 ID | PRIMARY KEY |
| company | TEXT | 公司名稱 | NOT NULL |
| contact_name | TEXT | 聯絡人姓名 | NOT NULL |
| email | TEXT | 電子郵件 | NOT NULL |
| created_at | TIMESTAMP | 建立時間 | 自動設定 |
| updated_at | TIMESTAMP | 更新時間 | 自動更新 |

### 觸發器說明

- **update_users_updated_at**: 當資料更新時，自動將 `updated_at` 欄位設為當前時間

## 🔒 安全性設定（選用）

如果你想要加強安全性，可以設定 Row Level Security (RLS)：

1. 在 **SQL Editor** 執行：

```sql
-- 啟用 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 允許所有人讀取（因為我們使用 anon key）
CREATE POLICY "允許讀取所有使用者" ON users
  FOR SELECT
  USING (true);

-- 允許所有人新增/更新（你也可以根據需求調整）
CREATE POLICY "允許新增使用者" ON users
  FOR INSERT
  WITH CHECK (true);

CREATE POLICY "允許更新使用者" ON users
  FOR UPDATE
  USING (true);
```

## 🎯 測試資料

你可以手動新增測試資料：

```sql
INSERT INTO users (line_user_id, company, contact_name, email)
VALUES ('test_user_001', '測試公司', '測試人員', 'test@example.com');
```

然後在 **Table Editor** 查看資料是否正確插入。

## 📈 查看資料

### 方法 1: Table Editor

1. 點擊左側選單的 **Table Editor**
2. 選擇 `users` 表
3. 可以直接查看、編輯、刪除資料

### 方法 2: SQL Editor

執行查詢：

```sql
-- 查看所有使用者
SELECT * FROM users ORDER BY created_at DESC;

-- 統計使用者數量
SELECT COUNT(*) as total_users FROM users;

-- 查看最近註冊的使用者
SELECT company, contact_name, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 10;
```

### 方法 3: API 端點

啟動你的 Flask 應用後，訪問：

```
http://localhost:5000/admin/users?password=YOUR_ADMIN_PASSWORD
```

## 🔧 常見問題

### Q1: 無法連接到 Supabase？

**檢查清單**：
- ✅ 確認 `.env` 檔案中的 `SUPABASE_URL` 和 `SUPABASE_KEY` 正確
- ✅ 確認已安裝 `supabase` 套件：`pip install supabase`
- ✅ 檢查網路連接
- ✅ 確認 Supabase 專案狀態正常（在 Dashboard 查看）

### Q2: 插入資料失敗？

**可能原因**：
- 缺少必填欄位（company, contact_name, email）
- line_user_id 重複（主鍵衝突）
- RLS 政策設定過於嚴格

**解決方法**：
- 檢查錯誤訊息
- 在 Supabase Dashboard 的 Logs 查看詳細錯誤
- 暫時停用 RLS 測試：`ALTER TABLE users DISABLE ROW LEVEL SECURITY;`

### Q3: 如何備份資料？

在 SQL Editor 執行：

```sql
-- 匯出所有資料（複製結果）
SELECT * FROM users;
```

或使用 Supabase Dashboard 的備份功能（付費方案）。

### Q4: 如何重設資料表？

⚠️ **警告：這會刪除所有資料！**

```sql
-- 刪除所有資料但保留資料表結構
TRUNCATE TABLE users;

-- 完全刪除資料表（包括結構）
DROP TABLE IF EXISTS users CASCADE;
-- 然後重新執行建立資料表的 SQL
```

## 📚 進階設定

### 自動備份

考慮設定定期備份腳本：

```python
# backup_users.py
from clients.supabase_client import SupabaseClient
import json
from datetime import datetime

client = SupabaseClient()
users = client.get_all_users()

filename = f"backup_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(users, f, ensure_ascii=False, indent=2)

print(f"✅ 備份完成：{filename}")
```

### 效能優化

如果使用者數量增長，考慮：
- 增加索引
- 使用分頁查詢
- 啟用 Connection Pooling

## 🆘 需要協助？

- [Supabase 官方文件](https://supabase.com/docs)
- [Supabase Discord 社群](https://discord.supabase.com/)
- [Python Client 文件](https://supabase.com/docs/reference/python/introduction)

---

**🎉 設定完成後，你的機器人就可以使用 Supabase 儲存使用者資料了！**
