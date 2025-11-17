"""
Supabase 資料庫設定腳本
用於驗證連接並提供建表 SQL
"""

from clients.supabase_client import SupabaseClient
import sys

def main():
    print("=" * 60)
    print("🔧 Supabase 資料庫設定")
    print("=" * 60)
    
    # 測試連接
    print("\n1️⃣ 測試連接...")
    try:
        client = SupabaseClient()
        print("✅ Supabase 連接成功！")
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        sys.exit(1)
    
    # 檢查資料表
    print("\n2️⃣ 檢查資料表...")
    try:
        # 嘗試查詢 users 表
        response = client.client.table("users").select("*").limit(1).execute()
        print(f"✅ users 資料表已存在（目前有 {len(response.data)} 筆測試資料）")
        
        # 統計使用者數量
        count = client.get_user_count()
        print(f"📊 資料庫中共有 {count} 位使用者")
        
    except Exception as e:
        error_msg = str(e)
        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            print("⚠️  users 資料表尚未建立")
            print("\n" + "=" * 60)
            print("📋 請在 Supabase Dashboard 執行以下 SQL：")
            print("=" * 60)
            print("""
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
""")
            print("=" * 60)
            print("\n📍 步驟：")
            print("1. 前往 https://supabase.com/dashboard")
            print("2. 選擇你的專案")
            print("3. 點擊左側的 'SQL Editor'")
            print("4. 點擊 'New query'")
            print("5. 複製上面的 SQL 並貼上")
            print("6. 點擊 'Run' 執行")
            print("7. 再次執行此腳本驗證")
            print("=" * 60)
        else:
            print(f"❌ 檢查資料表時發生錯誤: {e}")
            
    print("\n" + "=" * 60)
    print("✨ 設定完成！你現在可以：")
    print("   • 執行 procurement_bot.py 啟動應用")
    print("   • 查看 QUICKSTART.md 了解更多")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
