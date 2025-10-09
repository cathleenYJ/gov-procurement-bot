"""
政府電子採購網資料客戶端
負責從政府電子採購網抓取招標資料
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class ProcurementClient:
    """政府電子採購網客戶端"""
    
    def __init__(self):
        self.base_url = "https://web.pcc.gov.tw"
        self.api_url = f"{self.base_url}/prkms/tender/common/basic/readTenderBasic"
        self.session = requests.Session()
        
        # 設置請求頭，模擬瀏覽器
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        })
        
        # 設置 cookies（可能需要從實際請求中獲取）
        self.session.cookies.update({
            'JSESSIONID': 'gggw5Kcqx87WNi4wogrcv9DT5tnWOGhDKXZUkFrN.aplapp2:instA',
            'XSRF-TOKEN': '66031a99-f757-4780-bc86-473930b10a1e',
            'cookiesession1': '678ADA5C58D1C83791ACA013619BCA78',
            'webpcc': '4bb3a3d8ab2edb41738dd541bfdf20a95d2399dd3a852e6c96fa3768646686b388649b39'
        })
        
        # 忽略 SSL 憑證驗證（處理政府網站憑證問題）
        self.session.verify = False
        
        # 抑制 SSL 警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def search_tenders(self, 
                      page_size: int = 50,
                      tender_type: Optional[str] = None,
                      tender_way: Optional[str] = None,
                      date_type: str = "isNow",
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      org_name: str = "",
                      tender_name: str = "",
                      tender_id: str = "",
                      procurement_nature: str = "",
                      page: int = 1) -> Dict[str, Any]:
        """
        搜尋政府採購標案
        
        Args:
            page_size: 每頁顯示筆數 (10, 20, 50, 100)
            tender_type: 招標類型 (TENDER_DECLARATION: 招標公告, SEARCH_APPEAL: 公開徵求, PUBLIC_READ: 公開閱覽, PREDICT: 政府採購預告)，預設不指定
            tender_way: 招標方式 (TENDER_WAY_ALL_DECLARATION: 各式招標公告, TENDER_WAY_1: 公開招標, TENDER_WAY_12: 公開取得電子報價單, TENDER_WAY_2: 公開取得報價單或企劃書, TENDER_WAY_4: 經公開評選或公開徵求之限制性招標, TENDER_WAY_5: 選擇性招標(建立合格廠商名單), TENDER_WAY_7: 選擇性招標(建立合格廠商名單後續邀標), TENDER_WAY_3: 選擇性招標(個案), TENDER_WAY_10: 電子競價, TENDER_WAY_6: 限制性招標(未經公開評選或公開徵求))，預設不指定
            date_type: 日期類型 (isNow: 當日, isSpdt: 等標期內, isDate: 日期區間)
            start_date: 開始日期 (格式: YYYY/MM/DD)
            end_date: 結束日期 (格式: YYYY/MM/DD)
            org_name: 機關名稱
            tender_name: 標案名稱
            tender_id: 標案案號
            procurement_nature: 採購性質 (RAD_PROCTRG_CATE_1: 工程類, RAD_PROCTRG_CATE_2: 財物類, RAD_PROCTRG_CATE_3: 勞務類, "": 不限)，預設不限
            page: 頁數
        """
        
        # 如果沒有指定日期且使用當日，自動設定今天的日期
        if date_type == "isNow" and not start_date:
            today = datetime.now()
            start_date = today.strftime("%Y/%m/%d")
            end_date = today.strftime("%Y/%m/%d")
        elif date_type == "isSpdt" and not start_date:
            # 等標期內：查詢未來7天
            today = datetime.now()
            start_date = today.strftime("%Y/%m/%d")
            end_date = (today + timedelta(days=7)).strftime("%Y/%m/%d")
        
        params = {
            'pageSize': page_size,
            'firstSearch': 'true' if page == 1 else 'false',
            'searchType': 'basic',
            'isBinding': 'N',
            'isLogIn': 'N',
            'level_1': 'on',
            'orgName': org_name,
            'orgId': '',
            'tenderName': tender_name,
            'tenderId': tender_id,
            'dateType': date_type,
            'radProctrgCate': procurement_nature,
            'policyAdvocacy': '',
            'd-49738-p': page
        }
        
        # 只有在指定時才加入 tenderType 和 tenderWay 參數
        if tender_type is not None:
            params['tenderType'] = tender_type
        if tender_way is not None:
            params['tenderWay'] = tender_way
        
        # 添加日期參數
        if start_date:
            params['tenderStartDate'] = start_date
        if end_date:
            params['tenderEndDate'] = end_date
            
        try:
            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            # 解析HTML回應
            return self._parse_tender_response(response.text)
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {'success': False, 'error': str(e)}

    def _parse_tender_response(self, html_content: str) -> Dict[str, Any]:
        """解析招標資料HTML回應"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找資料表格
            table = soup.find('table', {'id': 'tpam'})
            if not table:
                return {'success': False, 'error': 'No data table found'}
            
            # 解析標案資料
            tenders = []
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    tender = self._parse_tender_row(row)
                    if tender:
                        tenders.append(tender)
            
            # 解析總筆數和分頁資訊
            page_info = self._parse_page_info(soup)
            
            return {
                'success': True,
                'data': tenders,
                'total_count': page_info.get('total_count', len(tenders)),
                'current_page': page_info.get('current_page', 1),
                'total_pages': page_info.get('total_pages', 1)
            }
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {'success': False, 'error': str(e)}

    def _parse_tender_row(self, row) -> Optional[Dict[str, Any]]:
        """解析單一標案資料列"""
        try:
            cells = row.find_all('td')
            if len(cells) < 10:
                return None
            
            # 提取標案基本資訊
            item_no = cells[0].get_text(strip=True)
            org_name = cells[1].get_text(strip=True)
            
            # 解析標案案號和名稱
            tender_cell = cells[2]
            tender_id_match = re.search(r'([A-Z0-9\-]+)', tender_cell.get_text())
            tender_id = tender_id_match.group(1) if tender_id_match else ""
            
            # 查找標案名稱連結
            tender_link = tender_cell.find('a')
            tender_name = ""
            tender_url = ""
            if tender_link:
                tender_name = tender_link.get_text(strip=True)
                href = tender_link.get('href', '')
                if href.startswith('/'):
                    tender_url = f"{self.base_url}{href}"
                else:
                    tender_url = href
            
            # 檢查是否為更正公告
            is_correction = '更正公告' in tender_cell.get_text()
            
            # 提取其他資訊
            transmission_count = cells[3].get_text(strip=True)
            tender_method = cells[4].get_text(strip=True)
            procurement_nature = cells[5].get_text(strip=True)
            announcement_date = cells[6].get_text(strip=True)
            deadline_date = cells[7].get_text(strip=True)
            
            # 解析預算金額
            budget_text = cells[8].get_text(strip=True).replace(',', '')
            budget_amount = 0
            try:
                budget_amount = int(budget_text) if budget_text.isdigit() else 0
            except ValueError:
                pass
            
            return {
                'item_no': item_no,
                'org_name': org_name,
                'tender_id': tender_id,
                'tender_name': tender_name,
                'tender_url': tender_url,
                'is_correction': is_correction,
                'transmission_count': transmission_count,
                'tender_method': tender_method,
                'procurement_nature': procurement_nature,
                'announcement_date': announcement_date,
                'deadline_date': deadline_date,
                'budget_amount': budget_amount,
                'budget_text': budget_text
            }
            
        except Exception as e:
            logger.error(f"Error parsing tender row: {e}")
            return None

    def _parse_page_info(self, soup) -> Dict[str, Any]:
        """解析分頁資訊"""
        try:
            # 查找總筆數
            pagebanner = soup.find('span', {'id': 'pagebanner'})
            total_count = 0
            if pagebanner:
                text = pagebanner.get_text()
                match = re.search(r'共有.*?(\d+).*?筆資料', text)
                if match:
                    total_count = int(match.group(1))
            
            # 查找當前頁數
            current_page = 1
            active_page = soup.find('a', {'class': 'pageact'})
            if active_page:
                try:
                    current_page = int(active_page.get_text(strip=True))
                except ValueError:
                    pass
            
            # 估算總頁數（假設每頁50筆）
            total_pages = (total_count + 49) // 50 if total_count > 0 else 1
            
            return {
                'total_count': total_count,
                'current_page': current_page,
                'total_pages': total_pages
            }
            
        except Exception as e:
            logger.error(f"Error parsing page info: {e}")
            return {}

    def get_tender_detail(self, tender_url: str) -> Dict[str, Any]:
        """獲取標案詳細資訊"""
        try:
            response = self.session.get(tender_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 這裡可以進一步解析標案詳細頁面
            # 包括詳細說明、規格、聯絡方式等
            
            return {
                'success': True,
                'content': soup.get_text()[:1000]  # 暫時返回前1000個字符
            }
            
        except Exception as e:
            logger.error(f"Error getting tender detail: {e}")
            return {'success': False, 'error': str(e)}

    def search_by_keywords(self, keywords: List[str], **kwargs) -> Dict[str, Any]:
        """根據關鍵字搜尋標案"""
        # 將關鍵字組合成搜尋字串
        search_term = " ".join(keywords)
        
        # 在標案名稱中搜尋關鍵字
        return self.search_tenders(tender_name=search_term, **kwargs)

    def get_latest_tenders(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取最近幾天的最新標案"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            result = self.search_tenders(
                date_type="isDate",
                start_date=start_date.strftime("%Y/%m/%d"),
                end_date=end_date.strftime("%Y/%m/%d"),
                page_size=min(limit, 100)
            )
            
            if result.get('success'):
                return result.get('data', [])[:limit]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting latest tenders: {e}")
            return []

    def get_high_value_tenders(self, min_amount: int = 10000000) -> List[Dict[str, Any]]:
        """獲取高金額標案"""
        try:
            result = self.search_tenders(page_size=100)
            
            if result.get('success'):
                tenders = result.get('data', [])
                # 篩選高金額標案
                high_value_tenders = [
                    tender for tender in tenders 
                    if tender.get('budget_amount', 0) >= min_amount
                ]
                return high_value_tenders
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting high value tenders: {e}")
            return []