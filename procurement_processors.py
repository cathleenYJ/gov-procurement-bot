"""
政府採購資料處理器
負責處理和分析政府採購標案資料
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from clients.procurement_client import ProcurementClient

logger = logging.getLogger(__name__)

class ProcurementProcessor:
    """政府採購資料處理器"""
    
    def __init__(self):
        self.client = ProcurementClient()
        
        # 預設關鍵字
        self.default_keywords = [
            "資訊", "系統", "軟體", "硬體", "電腦", "網路", 
            "伺服器", "資料庫", "雲端", "AI", "人工智慧",
            "智慧", "數位", "科技", "創新"
        ]
        
        # 高關注的機關
        self.priority_orgs = [
            "行政院", "經濟部", "教育部", "內政部", "財政部",
            "交通部", "國防部", "科技部", "衛生福利部"
        ]

    def get_latest_procurements(self, limit: int = 10, days: int = 3) -> List[Dict[str, Any]]:
        """獲取最新的政府採購資訊"""
        try:
            tenders = self.client.get_latest_tenders(days=days, limit=limit*2)
            
            # 篩選和排序
            filtered_tenders = self._filter_and_rank_tenders(tenders)
            
            return filtered_tenders[:limit]
            
        except Exception as e:
            logger.error(f"Error getting latest procurements: {e}")
            return []

    def search_procurements_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """根據關鍵字搜尋政府採購"""
        try:
            result = self.client.search_by_keywords(keywords, page_size=min(limit*2, 100))
            
            if result.get('success'):
                tenders = result.get('data', [])
                filtered_tenders = self._filter_and_rank_tenders(tenders, keywords)
                return filtered_tenders[:limit]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error searching procurements: {e}")
            return []

    def advanced_search_procurements(self, 
                                   keywords: List[str] = None,
                                   tender_type: Optional[str] = None,
                                   tender_way: Optional[str] = None, 
                                   date_type: str = "isDate",
                                   start_date: str = None,
                                   end_date: str = None,
                                   procurement_nature: str = "",
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """進階搜尋政府採購 - 允許指定所有搜尋參數"""
        try:
            # 如果沒有指定日期範圍，使用最近一個月
            if not start_date and not end_date:
                from datetime import datetime, timedelta
                end_date_obj = datetime.now()
                start_date_obj = end_date_obj - timedelta(days=30)
                start_date = start_date_obj.strftime("%Y/%m/%d")
                end_date = end_date_obj.strftime("%Y/%m/%d")
            
            result = self.client.search_tenders(
                tender_name=" ".join(keywords) if keywords else "",
                tender_type=tender_type,
                tender_way=tender_way,
                date_type=date_type,
                start_date=start_date,
                end_date=end_date,
                procurement_nature=procurement_nature,
                page_size=min(limit*2, 100)
            )
            
            if result.get('success'):
                tenders = result.get('data', [])
                filtered_tenders = self._filter_and_rank_tenders(tenders, keywords)
                return filtered_tenders[:limit]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return []

    def get_high_value_procurements(self, min_amount: int = 50000000, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取高金額政府採購"""
        try:
            tenders = self.client.get_high_value_tenders(min_amount=min_amount)
            
            # 按金額排序
            sorted_tenders = sorted(
                tenders, 
                key=lambda x: x.get('budget_amount', 0), 
                reverse=True
            )
            
            return sorted_tenders[:limit]
            
        except Exception as e:
            logger.error(f"Error getting high value procurements: {e}")
            return []

    def get_procurements_by_category(self, category: str = "工程類", limit: int = 10, 
                                    max_days_back: int = 30, exclude_ids: List[str] = None,
                                    page: int = 1) -> List[Dict[str, Any]]:
        """根據採購性質獲取標案，如果當日沒有資料則往前查詢
        
        當 limit > 10 時，會跨多天查詢以取得更多標案
        
        Args:
            category: 採購類別（工程類/財物類/勞務類）
            limit: 要取得的標案數量
            max_days_back: 最多往前查詢幾天
            exclude_ids: 要排除的標案ID列表（用於「更多標案」功能）
        """
        try:
            # 映射採購性質
            nature_map = {
                "工程類": "RAD_PROCTRG_CATE_1",
                "財物類": "RAD_PROCTRG_CATE_2", 
                "勞務類": "RAD_PROCTRG_CATE_3",
                "不限": ""  # 不限等於空字串
            }
            
            procurement_nature = nature_map.get(category, "RAD_PROCTRG_CATE_1")
            exclude_ids = exclude_ids or []
            logger.debug(f"get_procurements_by_category called: category={category}, limit={limit}, exclude_count={len(exclude_ids)}, page={page}")
            
            # 如果需要大量資料（limit > 10），跨多天查詢
            if limit > 10 or exclude_ids or page > 1:
                return self._get_procurements_multi_day(procurement_nature, category, limit, max_days_back, exclude_ids, page)
            
            # 一般查詢：從今天開始往前查詢，直到找到資料為止
            today = datetime.now()
            days_searched = 0
            
            while days_searched < max_days_back:
                target_date = today - timedelta(days=days_searched)
                date_str = target_date.strftime("%Y/%m/%d")
                
                logger.info(f"Searching {category} for date: {date_str}")
                
                result = self.client.search_tenders(
                    procurement_nature=procurement_nature,
                    date_type="isDate",
                    start_date=date_str,
                    end_date=date_str,
                    page_size=min(limit*2, 100),
                    page=page
                )
                
                if result.get('success'):
                    tenders = result.get('data', [])
                    if tenders:  # 如果找到資料
                        filtered_tenders = self._filter_and_rank_tenders(tenders)
                        if filtered_tenders:
                            logger.info(f"Found {len(filtered_tenders)} tenders for {category} on {date_str}")
                            # 在返回的標案中加入 category 欄位
                            result_tenders = filtered_tenders[:limit]
                            for tender in result_tenders:
                                tender['category'] = category
                            if result_tenders and days_searched > 0:
                                result_tenders[0]['_search_date'] = date_str
                            return result_tenders
                
                # 沒找到資料，往前一天
                days_searched += 1
            
            # 超過最大搜尋天數仍未找到
            logger.warning(f"No {category} tenders found in the last {max_days_back} days")
            return []
                
        except Exception as e:
            logger.error(f"Error getting procurements by category: {e}")
            return []
    
    def _get_procurements_multi_day(self, procurement_nature: str, category: str, 
                                   limit: int, max_days_back: int, exclude_ids: List[str] = None, page: int = 1) -> List[Dict[str, Any]]:
        """跨多天查詢標案（用於「更多標案」功能）
        
        策略：優先把當天的資料抓完，再往前查詢其他天
        
        Args:
            procurement_nature: 採購性質代碼
            category: 採購類別名稱
            limit: 需要的標案數量
            max_days_back: 最多往前查詢幾天
            exclude_ids: 要排除的標案ID列表
        """
        all_tenders = []
        today = datetime.now()
        days_searched = 0
        # 用於排除的ID集合（包含大小寫歸一化）
        exclude_ids = set(x for x in (exclude_ids or []))
        
        logger.info(f"Multi-day search for {category}, need {limit} tenders, excluding {len(exclude_ids)} IDs")
        
    # 持續往前查詢直到收集足夠的標案
        while len(all_tenders) < limit and days_searched < max_days_back:
            target_date = today - timedelta(days=days_searched)
            date_str = target_date.strftime("%Y/%m/%d")
            
            logger.info(f"Searching {category} for date: {date_str} (currently have {len(all_tenders)} tenders)")
            
            try:
                # 第一天（當天）抓取更多資料，確保能涵蓋所有當天標案
                # 從快取或參數傳入的 page 參數，如果是跨天則回到第一頁
                page_size = 200 if days_searched == 0 else 100
                query_page = page if days_searched == 0 and page > 1 else 1

                result = self.client.search_tenders(
                    procurement_nature=procurement_nature,
                    date_type="isDate",
                    start_date=date_str,
                    end_date=date_str,
                    page_size=page_size
                    , page=query_page
                )
                
                if result.get('success'):
                    tenders = result.get('data', [])
                    if tenders:
                        # 過濾和評分
                        filtered_tenders = self._filter_and_rank_tenders(tenders)
                        if filtered_tenders:
                            # 過濾掉要排除的ID
                            for tender in filtered_tenders:
                                tender_id = (tender.get('tender_id', '') or tender.get('tender_name', ''))
                                tender_name = tender.get('tender_name', '') or ''
                                org_name = tender.get('org_name', '') or ''
                                composite_key = f"{tender_name}|{org_name}"

                                # 如果 ID 或者名稱+機關組合在排除清單中，跳過
                                if tender_id in exclude_ids or composite_key in exclude_ids:
                                    continue

                                # 否則加入候選清單
                                all_tenders.append(tender)
                            
                            logger.info(f"Found {len(filtered_tenders)} tenders on {date_str}, {len(all_tenders)} after excluding seen IDs")
                            
                            # 如果已經收集到足夠的標案，就停止
                            if len(all_tenders) >= limit:
                                break
            except Exception as e:
                logger.error(f"Error searching date {date_str}: {e}")
            
            days_searched += 1
        
        # 去重（根據標案名稱+機關名稱）
        seen = set()
        unique_tenders = []
        for tender in all_tenders:
            key = (tender.get('tender_name', ''), tender.get('org_name', ''))
            if key not in seen:
                seen.add(key)
                unique_tenders.append(tender)
        
        logger.info(f"Multi-day search complete: {len(unique_tenders)} unique tenders from {days_searched} days")
        
        # 在返回的標案中加入 category 欄位
        for tender in unique_tenders:
            tender['category'] = category
        
        # 返回指定數量
        return unique_tenders[:limit]

    def _filter_and_rank_tenders(self, tenders: List[Dict[str, Any]], keywords: List[str] = None) -> List[Dict[str, Any]]:
        """篩選和排序標案"""
        if not tenders:
            return []
        
        scored_tenders = []
        
        for tender in tenders:
            score = self._calculate_tender_score(tender, keywords)
            if score > 0:
                tender['_score'] = score
                scored_tenders.append(tender)
        
        # 按分數排序
        return sorted(scored_tenders, key=lambda x: x['_score'], reverse=True)

    def _calculate_tender_score(self, tender: Dict[str, Any], keywords: List[str] = None) -> float:
        """計算標案的相關性分數"""
        score = 0.0
        
        tender_name = tender.get('tender_name', '').lower()
        org_name = tender.get('org_name', '').lower()
        tender_method = tender.get('tender_method', '')
        budget_amount = tender.get('budget_amount', 0)
        
        # 基礎分數
        score += 1.0
        
        # 關鍵字匹配加分
        if keywords:
            for keyword in keywords:
                if keyword.lower() in tender_name:
                    score += 3.0
                elif keyword.lower() in org_name:
                    score += 1.0
        
        # 預設關鍵字匹配
        for keyword in self.default_keywords:
            if keyword in tender_name:
                score += 2.0
        
        # 重要機關加分
        for priority_org in self.priority_orgs:
            if priority_org in org_name:
                score += 2.0
                break
        
        # 金額加分（高金額標案更重要）
        if budget_amount > 100000000:  # 1億以上
            score += 3.0
        elif budget_amount > 50000000:  # 5千萬以上
            score += 2.0
        elif budget_amount > 10000000:  # 1千萬以上
            score += 1.0
        
        # 招標方式加分（公開招標優先）
        if '公開招標' in tender_method:
            score += 1.0
        
        # 更正公告減分
        if tender.get('is_correction', False):
            score -= 0.5
        
        return score

    def format_tender_summary(self, tender: Dict[str, Any]) -> str:
        """格式化標案摘要"""
        try:
            # 格式化預算金額
            budget_amount = tender.get('budget_amount', 0)
            if budget_amount > 0:
                if budget_amount >= 100000000:
                    budget_str = f"{budget_amount / 100000000:.1f}億"
                elif budget_amount >= 10000:
                    budget_str = f"{budget_amount / 10000:.0f}萬"
                else:
                    budget_str = f"{budget_amount:,}"
            else:
                budget_str = tender.get('budget_text', '未公告')
            
            # 標案狀態
            status = ""
            if tender.get('is_correction'):
                status = " (更正公告)"
            
            summary = f"""
🏛️ {tender.get('org_name', 'N/A')}
📋 {tender.get('tender_name', 'N/A')}{status}
🏷️ 案號：{tender.get('tender_id', 'N/A')}
💰 預算：{budget_str}
📅 公告：{tender.get('announcement_date', 'N/A')}
⏰ 截止：{tender.get('deadline_date', 'N/A')}
🔧 性質：{tender.get('procurement_nature', 'N/A')}
📝 方式：{tender.get('tender_method', 'N/A')}
            """.strip()
            
            # 添加連結
            if tender.get('tender_url'):
                summary += f"\n🔗 詳細內容：{tender['tender_url']}"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error formatting tender summary: {e}")
            return f"標案：{tender.get('tender_name', 'N/A')}"

    def format_multiple_tenders(self, tenders: List[Dict[str, Any]], title: str = "政府採購資訊") -> str:
        """格式化多個標案資訊"""
        if not tenders:
            return "目前沒有找到相關的政府採購資訊。"
        
        # 檢查是否有搜尋日期資訊（非當日資料）
        search_date_info = ""
        if tenders and tenders[0].get('_search_date'):
            search_date_info = f"\n📅 查詢日期：{tenders[0]['_search_date']} (當日無資料，已自動往前查詢)"
        
        result = [f"📊 {title} (共{len(tenders)}筆){search_date_info}\n"]
        
        for i, tender in enumerate(tenders, 1):
            # 格式化金額
            budget_amount = tender.get('budget_amount', 0)
            if budget_amount > 0:
                if budget_amount >= 100000000:
                    budget_str = f"{budget_amount / 100000000:.1f}億"
                elif budget_amount >= 10000:
                    budget_str = f"{budget_amount / 10000:.0f}萬"
                else:
                    budget_str = f"{budget_amount:,}"
            else:
                budget_str = tender.get('budget_text', '未公告')
            
            # 機關名稱
            org_name = tender.get('org_name', 'N/A')
            
            # 第一行：【機關名稱，金額】
            tender_info = f"{i}. 【 {org_name}， {budget_str} 】"
            
            # 第二行：標案名稱
            tender_name = tender.get('tender_name', 'N/A')
            tender_info += f"\n{tender_name}"
            
            # 第三行：連結
            if tender.get('tender_url'):
                tender_info += f"\n🔗 {tender['tender_url']}"
            
            # 在每個標案後面加一個空行
            tender_info += "\n"
            
            result.append(tender_info)
        
        return "\n".join(result)

    def get_procurement_statistics(self) -> Dict[str, Any]:
        """獲取採購統計資訊"""
        try:
            # 獲取今日標案
            today_result = self.client.search_tenders(date_type="isNow", page_size=100)
            today_count = len(today_result.get('data', [])) if today_result.get('success') else 0
            
            # 獲取本週標案
            week_tenders = self.client.get_latest_tenders(days=7, limit=500)
            week_count = len(week_tenders)
            
            # 計算各類採購數量
            engineering_count = sum(1 for t in week_tenders if t.get('procurement_nature') == '工程類')
            goods_count = sum(1 for t in week_tenders if t.get('procurement_nature') == '財物類')
            service_count = sum(1 for t in week_tenders if t.get('procurement_nature') == '勞務類')
            
            # 計算平均金額
            valid_amounts = [t.get('budget_amount', 0) for t in week_tenders if t.get('budget_amount', 0) > 0]
            avg_amount = sum(valid_amounts) / len(valid_amounts) if valid_amounts else 0
            
            return {
                'today_count': today_count,
                'week_count': week_count,
                'engineering_count': engineering_count,
                'goods_count': goods_count,
                'service_count': service_count,
                'average_amount': avg_amount,
                'total_amount': sum(valid_amounts)
            }
            
        except Exception as e:
            logger.error(f"Error getting procurement statistics: {e}")
            return {}

    def format_statistics(self, stats: Dict[str, Any]) -> str:
        """格式化統計資訊"""
        if not stats:
            return "無法獲取統計資訊。"
        
        total_amount = stats.get('total_amount', 0)
        avg_amount = stats.get('average_amount', 0)
        
        # 格式化金額
        total_str = f"{total_amount / 100000000:.1f}億" if total_amount >= 100000000 else f"{total_amount / 10000:.0f}萬"
        avg_str = f"{avg_amount / 10000:.0f}萬" if avg_amount >= 10000 else f"{avg_amount:,.0f}"
        
        return f"""
📊 政府採購統計資訊

📅 今日新增：{stats.get('today_count', 0)} 筆
📈 本週總計：{stats.get('week_count', 0)} 筆

🏗️ 工程類：{stats.get('engineering_count', 0)} 筆
📦 財物類：{stats.get('goods_count', 0)} 筆  
🔧 勞務類：{stats.get('service_count', 0)} 筆

💰 本週總金額：{total_str}
📊 平均金額：{avg_str}
        """.strip()