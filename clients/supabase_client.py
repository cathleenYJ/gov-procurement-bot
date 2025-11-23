"""
Supabase 資料庫客戶端
處理與 Supabase 的所有資料庫互動
"""

from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv
import logging
import os

# 載入環境變數
load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase 資料庫客戶端"""
    
    def __init__(self):
        """初始化 Supabase 客戶端"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "缺少 Supabase 配置。請在 .env 文件中設置 SUPABASE_URL 和 SUPABASE_KEY"
            )
        
        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    
    def save_user(self, line_user_id: str, company: str, contact_name: str, email: str, position: str, industry: str) -> bool:
        """
        儲存或更新使用者資料
        
        Args:
            line_user_id: Line 使用者 ID
            company: 公司名稱
            contact_name: 聯絡人姓名
            email: 電子郵件
            position: 職務/職位
            industry: 產業類別
            
        Returns:
            bool: 是否儲存成功
        """
        try:
            data = {
                "line_user_id": line_user_id,
                "company": company,
                "contact_name": contact_name,
                "email": email,
                "position": position,
                "industry": industry,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # 使用 upsert 來插入或更新（根據 line_user_id 作為主鍵）
            response = self.client.table("users").upsert(data).execute()
            
            logger.info(f"User data saved successfully: {line_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user data to Supabase: {e}")
            return False
    
    def get_user(self, line_user_id: str) -> dict | None:
        """
        取得使用者資料
        
        Args:
            line_user_id: Line 使用者 ID
            
        Returns:
            dict: 使用者資料，若找不到則返回 None
        """
        try:
            response = self.client.table("users").select(
                "company, contact_name, email, position, industry"
            ).eq("line_user_id", line_user_id).execute()
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                logger.info(f"User data retrieved: {line_user_id}")
                return {
                    'company': user_data['company'],
                    'contact_name': user_data['contact_name'],
                    'email': user_data['email'],
                    'position': user_data['position'],
                    'industry': user_data['industry']
                }
            
            logger.info(f"No user data found for: {line_user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user data from Supabase: {e}")
            return None
    
    def get_all_users(self) -> list:
        """
        取得所有使用者資料（管理用）
        
        Returns:
            list: 所有使用者資料列表
        """
        try:
            response = self.client.table("users").select(
                "line_user_id, company, contact_name, email, position, industry, created_at, updated_at"
            ).order("created_at", desc=True).execute()
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} users")
                return response.data
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting all users from Supabase: {e}")
            return []
    
    def delete_user(self, line_user_id: str) -> bool:
        """
        刪除使用者資料
        
        Args:
            line_user_id: Line 使用者 ID
            
        Returns:
            bool: 是否刪除成功
        """
        try:
            response = self.client.table("users").delete().eq(
                "line_user_id", line_user_id
            ).execute()
            
            logger.info(f"User data deleted: {line_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user data from Supabase: {e}")
            return False
    
    def get_user_count(self) -> int:
        """
        取得使用者總數
        
        Returns:
            int: 使用者數量
        """
        try:
            response = self.client.table("users").select(
                "line_user_id", count="exact"
            ).execute()
            
            return response.count if response.count else 0
            
        except Exception as e:
            logger.error(f"Error getting user count from Supabase: {e}")
            return 0
