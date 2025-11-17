"""
使用者行為分析模組
記錄和分析使用者的查詢行為
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class UserAnalytics:
    """使用者行為分析類"""
    
    def __init__(self, supabase_client):
        """
        初始化分析模組
        
        Args:
            supabase_client: Supabase 客戶端實例
        """
        self.client = supabase_client.client
    
    # ===================================================================
    # 記錄使用者行為
    # ===================================================================
    
    def log_query(self, line_user_id: str, query_type: str, 
                  query_text: str = None, category: str = None, 
                  result_count: int = 0) -> bool:
        """
        記錄使用者查詢行為
        
        Args:
            line_user_id: Line 使用者 ID
            query_type: 查詢類型（工程類/財物類/勞務類/更多標案/help等）
            query_text: 使用者輸入的原始文字
            category: 查詢的標案類別
            result_count: 返回的結果數量
            
        Returns:
            bool: 是否記錄成功
        """
        try:
            data = {
                "line_user_id": line_user_id,
                "query_type": query_type,
                "query_text": query_text,
                "category": category,
                "result_count": result_count
            }
            
            self.client.table("user_query_logs").insert(data).execute()
            
            # 更新統計資料
            self._update_user_stats(line_user_id)
            
            logger.info(f"Query logged: {line_user_id} - {query_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging query: {e}")
            return False
    
    def log_tender_view(self, line_user_id: str, tender: Dict[str, Any]) -> bool:
        """
        記錄使用者查看標案
        
        Args:
            line_user_id: Line 使用者 ID
            tender: 標案資料字典
            
        Returns:
            bool: 是否記錄成功
        """
        try:
            data = {
                "line_user_id": line_user_id,
                "tender_id": tender.get('tender_id'),
                "tender_name": tender.get('tender_name', ''),
                "org_name": tender.get('org_name'),
                "category": tender.get('category'),
                "budget_amount": tender.get('budget_amount')
            }
            
            self.client.table("tender_views").insert(data).execute()
            
            # 更新統計資料
            self._update_user_stats(line_user_id)
            
            logger.info(f"Tender view logged: {line_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging tender view: {e}")
            return False
    
    def log_tender_views_batch(self, line_user_id: str, tenders: List[Dict[str, Any]]) -> bool:
        """
        批次記錄使用者查看的多個標案
        
        Args:
            line_user_id: Line 使用者 ID
            tenders: 標案列表
            
        Returns:
            bool: 是否記錄成功
        """
        try:
            data_list = []
            for tender in tenders:
                data_list.append({
                    "line_user_id": line_user_id,
                    "tender_id": tender.get('tender_id'),
                    "tender_name": tender.get('tender_name', '')[:100],  # 限制長度
                    "org_name": tender.get('org_name'),
                    "category": tender.get('category'),
                    "budget_amount": tender.get('budget_amount')
                })
            
            if data_list:
                self.client.table("tender_views").insert(data_list).execute()
                self._update_user_stats(line_user_id)
                logger.info(f"Batch tender views logged: {line_user_id} - {len(data_list)} tenders")
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging batch tender views: {e}")
            return False
    
    # ===================================================================
    # 瀏覽狀態管理（用於「更多標案」功能）
    # ===================================================================
    
    def get_browsing_state(self, line_user_id: str) -> Optional[Dict[str, Any]]:
        """
        取得使用者的瀏覽狀態
        
        Args:
            line_user_id: Line 使用者 ID
            
        Returns:
            dict: 瀏覽狀態（category, seen_tender_ids）
        """
        try:
            response = self.client.table("user_browsing_state").select(
                "category, seen_tender_ids, last_updated, page"
            ).eq("line_user_id", line_user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting browsing state: {e}")
            return None
    
    def update_browsing_state(self, line_user_id: str, category: str, 
                            seen_tender_ids: List[str], page: int = 1) -> bool:
        """
        更新使用者的瀏覽狀態
        
        Args:
            line_user_id: Line 使用者 ID
            category: 目前查詢的類別
            seen_tender_ids: 已看過的標案ID列表
            
        Returns:
            bool: 是否更新成功
        """
        try:
            data = {
                "line_user_id": line_user_id,
                "category": category,
                "seen_tender_ids": seen_tender_ids
                ,"page": page
            }
            
            self.client.table("user_browsing_state").upsert(data).execute()
            
            logger.info(f"Browsing state updated: {line_user_id} - {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating browsing state: {e}")
            return False
    
    # ===================================================================
    # 統計資料查詢
    # ===================================================================
    
    def get_user_stats(self, line_user_id: str) -> Optional[Dict[str, Any]]:
        """
        取得使用者的統計資料
        
        Args:
            line_user_id: Line 使用者 ID
            
        Returns:
            dict: 統計資料
        """
        try:
            response = self.client.table("user_activity_stats").select("*").eq(
                "line_user_id", line_user_id
            ).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return None
    
    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        取得最近幾天的查詢統計
        
        Args:
            days: 查詢天數
            
        Returns:
            list: 每日統計資料
        """
        try:
            response = self.client.table("daily_query_stats").select("*").limit(
                days
            ).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return []
    
    def get_popular_tenders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        取得熱門標案排行
        
        Args:
            limit: 返回數量
            
        Returns:
            list: 熱門標案列表
        """
        try:
            response = self.client.table("popular_tenders").select("*").limit(
                limit
            ).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting popular tenders: {e}")
            return []
    
    def get_active_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        取得活躍使用者排行
        
        Args:
            limit: 返回數量
            
        Returns:
            list: 活躍使用者列表
        """
        try:
            response = self.client.table("user_activity_ranking").select("*").limit(
                limit
            ).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    # ===================================================================
    # 內部輔助方法
    # ===================================================================
    
    def _update_user_stats(self, line_user_id: str) -> bool:
        """
        更新使用者統計資料（內部方法）
        
        Args:
            line_user_id: Line 使用者 ID
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 呼叫 Supabase 的 RPC 函數來更新統計
            self.client.rpc('update_user_activity_stats', {
                'p_user_id': line_user_id
            }).execute()
            
            return True
            
        except Exception as e:
            logger.debug(f"Stats update (non-critical): {e}")
            return False
