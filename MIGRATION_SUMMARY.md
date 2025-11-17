# Supabase 整合總結

## ✅ 已完成的變更

### 1. 新增依賴套件
- 在 `requirements.txt` 中新增 `supabase` 套件

### 2. 建立 Supabase 客戶端模組
- **檔案**: `clients/supabase_client.py`
- **功能**:
  - `save_user()`: 儲存/更新使用者資料
  - `get_user()`: 取得單一使用者資料
  - `get_all_users()`: 取得所有使用者（管理用）
  - `delete_user()`: 刪除使用者
  - `get_user_count()`: 統計使用者數量

### 3. 更新主程式
- **檔案**: `procurement_bot.py`
- **變更**:
  - 移除 SQLite 相關程式碼
  - 新增 Supabase 客戶端初始化
  - 更新所有 `get_user()` 和 `save_user()` 呼叫以使用 Supabase
  - 更新管理端點 `/admin/users` 和 `/admin/user/<user_id>`

### 4. 更新環境變數設定
- **檔案**: `.env.example`
- **新增**:
  - `SUPABASE_URL`: Supabase 專案 URL
  - `SUPABASE_KEY`: Supabase anon public key
  - `ADMIN_PASSWORD`: 管理員密碼

### 5. 更新文件
- **README.md**: 新增 Supabase 設定步驟
- **SUPABASE_SETUP.md**: 詳細的 Supabase 設定指南

## 🚀 下一步操作

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設定 Supabase
按照 `SUPABASE_SETUP.md` 的指示：
1. 建立 Supabase 帳號和專案
2. 執行 SQL 建立資料表
3. 複製 URL 和 API Key 到 `.env`

### 3. 設定環境變數
```bash
# 複製範例檔案
cp .env.example .env

# 編輯 .env 填入以下資訊：
# - SUPABASE_URL
# - SUPABASE_KEY
# - CHANNEL_ACCESS_TOKEN
# - CHANNEL_SECRET
# - ADMIN_PASSWORD
```

### 4. 測試連接
```bash
python -c "from clients.supabase_client import SupabaseClient; client = SupabaseClient(); print('✅ 連接成功！')"
```

### 5. 啟動應用
```bash
python procurement_bot.py
```

## 📊 資料表結構

```sql
CREATE TABLE users (
  line_user_id TEXT PRIMARY KEY,
  company TEXT NOT NULL,
  contact_name TEXT NOT NULL,
  email TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔄 從 SQLite 遷移資料（如有需要）

如果你已有 SQLite 資料需要遷移：

```python
import sqlite3
from clients.supabase_client import SupabaseClient

# 讀取 SQLite 資料
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('SELECT line_user_id, company, contact_name, email FROM users')
rows = cursor.fetchall()
conn.close()

# 寫入 Supabase
client = SupabaseClient()
for row in rows:
    line_user_id, company, contact_name, email = row
    client.save_user(line_user_id, company, contact_name, email)
    print(f"✅ 已遷移: {company} - {contact_name}")

print(f"\n🎉 完成！共遷移 {len(rows)} 筆資料")
```

## 🎯 功能驗證

### 測試使用者註冊流程
1. 在 Line 加入機器人好友
2. 點擊「開始登錄」
3. 依序輸入公司名稱、聯絡人、Email
4. 確認收到「✅ 登錄完成！」訊息

### 測試資料查詢
訪問管理端點（需要密碼）：
```
http://localhost:5000/admin/users?password=YOUR_ADMIN_PASSWORD
```

### 測試資料更新
1. 在 Line 輸入「我的資料」
2. 確認顯示正確資料
3. 點擊「修改資料」
4. 重新輸入新資料

## ⚠️ 注意事項

1. **安全性**: 
   - 不要將 `.env` 檔案提交到 Git
   - 使用強密碼作為 `ADMIN_PASSWORD`
   - 定期更換 API Key

2. **效能**:
   - Supabase 免費方案有使用限制
   - 考慮實作快取機制減少資料庫查詢

3. **備份**:
   - 定期備份資料
   - 使用 Supabase Dashboard 的備份功能

## 📚 相關文件

- [Supabase 官方文件](https://supabase.com/docs)
- [Python Client 文件](https://supabase.com/docs/reference/python/introduction)
- [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) - 詳細設定指南

## 🆘 疑難排解

### 錯誤: "缺少 Supabase 配置"
- 確認 `.env` 檔案存在並包含 `SUPABASE_URL` 和 `SUPABASE_KEY`
- 確認環境變數值正確（無多餘空格）

### 錯誤: "Import 'supabase' could not be resolved"
- 執行 `pip install supabase`
- 確認虛擬環境已啟動

### 資料無法儲存
- 檢查 Supabase 專案狀態
- 查看 Supabase Dashboard 的 Logs
- 確認資料表已正確建立

---

**🎊 恭喜！你已成功將專案從 SQLite 遷移到 Supabase！**
