-- ===================================================================
-- 使用者行為分析資料庫架構
-- 在 Supabase SQL Editor 中執行此檔案
-- ===================================================================

-- 1. 使用者查詢記錄表
CREATE TABLE IF NOT EXISTS user_query_logs (
  id BIGSERIAL PRIMARY KEY,
  line_user_id TEXT NOT NULL,
  query_type TEXT NOT NULL,  -- '工程類', '財物類', '勞務類', '更多標案', '我的資料', 'help'
  query_text TEXT,            -- 使用者輸入的原始文字
  category TEXT,              -- 查詢的標案類別
  result_count INTEGER,       -- 返回的標案數量
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- 外鍵關聯（可選，如果使用者還沒註冊就不會有關聯）
  CONSTRAINT fk_user FOREIGN KEY (line_user_id) 
    REFERENCES users(line_user_id) ON DELETE CASCADE
);

-- 2. 標案瀏覽記錄表
CREATE TABLE IF NOT EXISTS tender_views (
  id BIGSERIAL PRIMARY KEY,
  line_user_id TEXT NOT NULL,
  tender_id TEXT,             -- 標案ID（如果有的話）
  tender_name TEXT NOT NULL,  -- 標案名稱
  org_name TEXT,              -- 機關名稱
  category TEXT,              -- 標案類別
  budget_amount BIGINT,       -- 預算金額
  viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT fk_user_tender FOREIGN KEY (line_user_id) 
    REFERENCES users(line_user_id) ON DELETE CASCADE
);

-- 3. 使用者瀏覽狀態表（用於「更多標案」功能）
CREATE TABLE IF NOT EXISTS user_browsing_state (
  line_user_id TEXT PRIMARY KEY,
  category TEXT NOT NULL,               -- 目前瀏覽的類別
  seen_tender_ids TEXT[] DEFAULT '{}',  -- 已看過的標案ID陣列
  page INTEGER DEFAULT 1,               -- 使用者目前的分頁（從 1 開始），用於更多按鈕翻頁
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT fk_user_browsing FOREIGN KEY (line_user_id) 
    REFERENCES users(line_user_id) ON DELETE CASCADE
);

-- 4. 使用者活動統計表（彙總資料，加快查詢速度）
CREATE TABLE IF NOT EXISTS user_activity_stats (
  line_user_id TEXT PRIMARY KEY,
  total_queries INTEGER DEFAULT 0,           -- 總查詢次數
  total_tender_views INTEGER DEFAULT 0,      -- 總瀏覽標案數
  favorite_category TEXT,                    -- 最常查詢的類別
  last_active_at TIMESTAMP WITH TIME ZONE,   -- 最後活動時間
  first_query_at TIMESTAMP WITH TIME ZONE,   -- 首次查詢時間
  
  CONSTRAINT fk_user_stats FOREIGN KEY (line_user_id) 
    REFERENCES users(line_user_id) ON DELETE CASCADE
);

-- ===================================================================
-- 建立索引以提升查詢效能
-- ===================================================================

-- user_query_logs 索引
CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON user_query_logs(line_user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON user_query_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_logs_query_type ON user_query_logs(query_type);
CREATE INDEX IF NOT EXISTS idx_query_logs_category ON user_query_logs(category);

-- tender_views 索引
CREATE INDEX IF NOT EXISTS idx_tender_views_user_id ON tender_views(line_user_id);
CREATE INDEX IF NOT EXISTS idx_tender_views_viewed_at ON tender_views(viewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_tender_views_category ON tender_views(category);
CREATE INDEX IF NOT EXISTS idx_tender_views_org_name ON tender_views(org_name);

-- user_browsing_state 索引
CREATE INDEX IF NOT EXISTS idx_browsing_state_updated ON user_browsing_state(last_updated DESC);

-- user_activity_stats 索引
CREATE INDEX IF NOT EXISTS idx_activity_stats_last_active ON user_activity_stats(last_active_at DESC);

-- ===================================================================
-- 建立自動更新觸發器
-- ===================================================================

-- 自動更新 user_browsing_state 的 last_updated
CREATE OR REPLACE FUNCTION update_browsing_state_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.last_updated = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_browsing_state_timestamp
  BEFORE UPDATE ON user_browsing_state
  FOR EACH ROW
  EXECUTE FUNCTION update_browsing_state_timestamp();

-- ===================================================================
-- 建立實用的分析視圖（View）
-- ===================================================================

-- 每日查詢統計
CREATE OR REPLACE VIEW daily_query_stats AS
SELECT 
  DATE(created_at) as query_date,
  query_type,
  category,
  COUNT(*) as query_count,
  COUNT(DISTINCT line_user_id) as unique_users
FROM user_query_logs
GROUP BY DATE(created_at), query_type, category
ORDER BY query_date DESC;

-- 使用者活動排行
CREATE OR REPLACE VIEW user_activity_ranking AS
SELECT 
  u.line_user_id,
  u.company,
  u.contact_name,
  s.total_queries,
  s.total_tender_views,
  s.favorite_category,
  s.last_active_at
FROM user_activity_stats s
JOIN users u ON s.line_user_id = u.line_user_id
ORDER BY s.total_queries DESC;

-- 熱門標案排行
CREATE OR REPLACE VIEW popular_tenders AS
SELECT 
  tender_name,
  org_name,
  category,
  COUNT(*) as view_count,
  COUNT(DISTINCT line_user_id) as unique_viewers,
  MAX(viewed_at) as last_viewed
FROM tender_views
GROUP BY tender_name, org_name, category
ORDER BY view_count DESC;

-- ===================================================================
-- 建立自動統計更新函數
-- ===================================================================

-- 更新使用者活動統計
CREATE OR REPLACE FUNCTION update_user_activity_stats(p_user_id TEXT)
RETURNS VOID AS $$
BEGIN
  INSERT INTO user_activity_stats (
    line_user_id,
    total_queries,
    total_tender_views,
    favorite_category,
    last_active_at,
    first_query_at
  )
  SELECT 
    p_user_id,
    (SELECT COUNT(*) FROM user_query_logs WHERE line_user_id = p_user_id),
    (SELECT COUNT(*) FROM tender_views WHERE line_user_id = p_user_id),
    (SELECT category 
     FROM user_query_logs 
     WHERE line_user_id = p_user_id AND category IS NOT NULL
     GROUP BY category 
     ORDER BY COUNT(*) DESC 
     LIMIT 1),
    NOW(),
    (SELECT MIN(created_at) FROM user_query_logs WHERE line_user_id = p_user_id)
  ON CONFLICT (line_user_id) DO UPDATE SET
    total_queries = (SELECT COUNT(*) FROM user_query_logs WHERE line_user_id = p_user_id),
    total_tender_views = (SELECT COUNT(*) FROM tender_views WHERE line_user_id = p_user_id),
    favorite_category = (SELECT category 
                        FROM user_query_logs 
                        WHERE line_user_id = p_user_id AND category IS NOT NULL
                        GROUP BY category 
                        ORDER BY COUNT(*) DESC 
                        LIMIT 1),
    last_active_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- 資料清理函數（可選）
-- ===================================================================

-- 清理超過指定天數的舊記錄
CREATE OR REPLACE FUNCTION cleanup_old_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM user_query_logs 
  WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- 註解說明
-- ===================================================================

COMMENT ON TABLE user_query_logs IS '使用者查詢記錄表，記錄每次查詢行為';
COMMENT ON TABLE tender_views IS '標案瀏覽記錄表，記錄使用者查看的標案詳情';
COMMENT ON TABLE user_browsing_state IS '使用者瀏覽狀態表，用於「更多標案」功能的狀態管理';
COMMENT ON TABLE user_activity_stats IS '使用者活動統計彙總表，提供快速查詢';

-- ===================================================================
-- 完成提示
-- ===================================================================

DO $$
BEGIN
  RAISE NOTICE '✅ 使用者行為分析資料庫架構建立完成！';
  RAISE NOTICE '';
  RAISE NOTICE '📊 已建立的資料表：';
  RAISE NOTICE '  - user_query_logs: 查詢記錄';
  RAISE NOTICE '  - tender_views: 標案瀏覽記錄';
  RAISE NOTICE '  - user_browsing_state: 瀏覽狀態';
  RAISE NOTICE '  - user_activity_stats: 活動統計';
  RAISE NOTICE '';
  RAISE NOTICE '📈 已建立的分析視圖：';
  RAISE NOTICE '  - daily_query_stats: 每日查詢統計';
  RAISE NOTICE '  - user_activity_ranking: 使用者活動排行';
  RAISE NOTICE '  - popular_tenders: 熱門標案排行';
END $$;
