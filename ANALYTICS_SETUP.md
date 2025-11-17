# 使用者行為分析系統設定指南

## 📋 概述

這個使用者行為分析系統可以讓你追蹤和分析使用者的查詢行為，包括：
- 查詢頻率和類別偏好
- 標案瀏覽記錄
- 使用者活躍度
- 熱門標案排行

## 🚀 快速設定

### 步驟 1: 建立資料表

1. 前往 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇你的專案
3. 點擊左側的 **SQL Editor**
4. 點擊 **New query**
5. 複製 `database_schema_analytics.sql` 的全部內容
6. 貼上並點擊 **Run** 執行

執行成功後，你會看到：
- ✅ 4個新資料表
- ✅ 多個索引
- ✅ 3個分析視圖
- ✅ 自動統計函數

### 步驟 2: 驗證資料表

執行以下SQL確認資料表已建立：

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
  'user_query_logs',
  'tender_views', 
  'user_browsing_state',
  'user_activity_stats'
);
```

應該會看到4個資料表。

### 步驟 3: 重啟應用

```bash
# 停止現有應用（Ctrl+C）

# 重新啟動
/Users/yangyijie/Desktop/gov-procurement-crawler/.venv/bin/python procurement_bot.py
```

## 📊 資料表說明

### 1. user_query_logs（查詢記錄）
記錄每次使用者的查詢行為。

| 欄位 | 說明 |
|------|------|
| line_user_id | Line 使用者 ID |
| query_type | 查詢類型（工程類/財物類/勞務類等） |
| query_text | 使用者輸入的文字 |
| category | 標案類別 |
| result_count | 返回結果數量 |
| created_at | 查詢時間 |

### 2. tender_views（標案瀏覽記錄）
記錄使用者查看過的標案。

| 欄位 | 說明 |
|------|------|
| line_user_id | Line 使用者 ID |
| tender_id | 標案 ID |
| tender_name | 標案名稱 |
| org_name | 機關名稱 |
| category | 標案類別 |
| budget_amount | 預算金額 |
| viewed_at | 瀏覽時間 |

### 3. user_browsing_state（瀏覽狀態）
儲存使用者「更多標案」功能的狀態。

| 欄位 | 說明 |
|------|------|
| line_user_id | Line 使用者 ID |
| category | 目前查詢類別 |
| seen_tender_ids | 已看過的標案ID陣列 |
| last_updated | 最後更新時間 |

### 4. user_activity_stats（活動統計）
彙總每個使用者的活動數據。

| 欄位 | 說明 |
|------|------|
| line_user_id | Line 使用者 ID |
| total_queries | 總查詢次數 |
| total_tender_views | 總瀏覽標案數 |
| favorite_category | 最常查詢的類別 |
| last_active_at | 最後活動時間 |
| first_query_at | 首次查詢時間 |

## 🔍 使用分析 API

所有分析 API 都需要管理員密碼。

### 1. 每日查詢統計

```bash
curl "http://localhost:5000/admin/analytics/daily?password=YOUR_PASSWORD&days=7"
```

返回最近7天的查詢統計。

**範例回應**：
```json
{
  "status": "success",
  "days": 7,
  "data": [
    {
      "query_date": "2025-11-17",
      "query_type": "工程類查詢",
      "category": "工程類",
      "query_count": 25,
      "unique_users": 8
    }
  ]
}
```

### 2. 熱門標案排行

```bash
curl "http://localhost:5000/admin/analytics/popular?password=YOUR_PASSWORD&limit=10"
```

返回最熱門的標案（按瀏覽次數）。

**範例回應**：
```json
{
  "status": "success",
  "total": 10,
  "data": [
    {
      "tender_name": "資訊系統升級案",
      "org_name": "交通部",
      "category": "財物類",
      "view_count": 45,
      "unique_viewers": 15,
      "last_viewed": "2025-11-17T10:30:00"
    }
  ]
}
```

### 3. 活躍使用者排行

```bash
curl "http://localhost:5000/admin/analytics/active-users?password=YOUR_PASSWORD&limit=10"
```

返回最活躍的使用者。

**範例回應**：
```json
{
  "status": "success",
  "total": 10,
  "data": [
    {
      "line_user_id": "U1234567890",
      "company": "某某工程公司",
      "contact_name": "王小明",
      "total_queries": 150,
      "total_tender_views": 500,
      "favorite_category": "工程類",
      "last_active_at": "2025-11-17T14:20:00"
    }
  ]
}
```

### 4. 特定使用者統計

```bash
curl "http://localhost:5000/admin/analytics/user/U1234567890?password=YOUR_PASSWORD"
```

返回特定使用者的詳細統計。

## 📈 直接查詢資料庫

你也可以在 Supabase SQL Editor 直接查詢：

### 查看今日查詢統計
```sql
SELECT 
  query_type,
  category,
  COUNT(*) as count,
  COUNT(DISTINCT line_user_id) as unique_users
FROM user_query_logs
WHERE created_at >= CURRENT_DATE
GROUP BY query_type, category
ORDER BY count DESC;
```

### 查看最熱門的標案
```sql
SELECT * FROM popular_tenders LIMIT 10;
```

### 查看活躍使用者
```sql
SELECT * FROM user_activity_ranking LIMIT 10;
```

### 查看特定使用者的瀏覽歷史
```sql
SELECT 
  tender_name,
  org_name,
  category,
  viewed_at
FROM tender_views
WHERE line_user_id = 'U1234567890'
ORDER BY viewed_at DESC
LIMIT 20;
```

## 🎯 實用分析查詢

### 1. 每小時查詢分布
```sql
SELECT 
  EXTRACT(HOUR FROM created_at) as hour,
  COUNT(*) as query_count
FROM user_query_logs
WHERE created_at >= CURRENT_DATE
GROUP BY hour
ORDER BY hour;
```

### 2. 類別偏好分析
```sql
SELECT 
  category,
  COUNT(*) as total_queries,
  COUNT(DISTINCT line_user_id) as unique_users,
  ROUND(AVG(result_count), 2) as avg_results
FROM user_query_logs
WHERE category IS NOT NULL
GROUP BY category
ORDER BY total_queries DESC;
```

### 3. 使用者留存率
```sql
SELECT 
  DATE(first_query_at) as signup_date,
  COUNT(*) as new_users,
  SUM(CASE WHEN last_active_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 ELSE 0 END) as active_in_7_days
FROM user_activity_stats
GROUP BY DATE(first_query_at)
ORDER BY signup_date DESC;
```

## 🧹 資料維護

### 清理90天前的舊記錄

```sql
SELECT cleanup_old_logs(90);
```

### 手動更新使用者統計

```sql
SELECT update_user_activity_stats('U1234567890');
```

### 重建所有使用者統計

```sql
-- 清空統計表
TRUNCATE user_activity_stats;

-- 重新計算所有使用者
INSERT INTO user_activity_stats (line_user_id)
SELECT DISTINCT line_user_id FROM user_query_logs;

-- 更新每個使用者的統計
DO $$
DECLARE
  user_record RECORD;
BEGIN
  FOR user_record IN SELECT line_user_id FROM user_activity_stats LOOP
    PERFORM update_user_activity_stats(user_record.line_user_id);
  END LOOP;
END $$;
```

## 📊 建立自訂報表

你可以建立自己的視圖來產生特定報表：

```sql
-- 每週活躍度報表
CREATE VIEW weekly_activity AS
SELECT 
  DATE_TRUNC('week', created_at) as week,
  COUNT(DISTINCT line_user_id) as active_users,
  COUNT(*) as total_queries
FROM user_query_logs
GROUP BY week
ORDER BY week DESC;

-- 使用
SELECT * FROM weekly_activity LIMIT 10;
```

## ⚡ 效能優化建議

1. **定期清理舊資料**：保留最近3-6個月的資料即可
2. **使用分析視圖**：預先計算好的視圖查詢更快
3. **建立額外索引**：如果有特定查詢模式，可以建立對應索引

## 🔒 隱私考量

- 只儲存必要的資料
- 定期清理舊資料
- 不要將個人資料直接暴露在公開 API
- 使用強密碼保護管理端點

## 💡 進階應用

### 1. 推薦系統
根據使用者的瀏覽歷史推薦相關標案。

### 2. 異常檢測
發現異常的查詢模式（如爬蟲）。

### 3. 使用者分群
根據行為將使用者分類（活躍/偶爾使用/沉睡）。

### 4. A/B 測試
測試不同功能對使用者行為的影響。

---

**🎉 現在你的系統已經具備完整的行為分析能力了！**
