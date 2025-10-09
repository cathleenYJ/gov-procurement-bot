"""
政府採購機器人主程式
負責處理Line Bot與政府採購資料的互動
"""

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import os
import logging
from procurement_processors import ProcurementProcessor
from typing import Dict, Any

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 常量定義
DEFAULT_KEYWORDS = ["資訊", "系統", "軟體", "硬體", "網路", "AI", "智慧"]

def _parse_advanced_search(message: str) -> Dict[str, Any]:
    """解析進階搜尋參數"""
    # 移除指令前綴
    content = message.replace("進階搜尋 ", "").replace("進階 ", "").strip()
    
    # 分割關鍵字和參數
    parts = content.split()
    keywords = []
    params = {}
    
    for part in parts:
        if '=' in part:
            # 這是參數
            key, value = part.split('=', 1)
            params[key] = value
        else:
            # 這是關鍵字
            keywords.append(part)
    
    # 設定預設值
    search_params = {
        'keywords': keywords if keywords else None,
        'tender_type': params.get('type'),
        'tender_way': params.get('way'),
        'date_type': params.get('date', 'isDate'),
        'start_date': params.get('start'),
        'end_date': params.get('end'),
        'procurement_nature': params.get('nature', ''),
        'limit': 10
    }
    
    return search_params

def create_app():
    """創建並配置 Flask 應用"""
    # 載入環境變數
    load_dotenv()

    app = Flask(__name__)

    # Line Bot 配置
    CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
    CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

    if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
        logger.error("Missing Line Bot credentials. Please set CHANNEL_ACCESS_TOKEN and CHANNEL_SECRET in .env file")
        return app

    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)

    # 創建政府採購處理器實例
    procurement_processor = ProcurementProcessor()

    @app.route("/callback", methods=['POST'])
    def callback():
        signature = request.headers['X-Line-Signature']
        body = request.get_data(as_text=True)
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
        return 'OK'

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_message = event.message.text.lower().strip()
        
        try:
            # 處理不同的指令
            if user_message in ["procurement", "採購", "標案"]:
                # 獲取最新採購資訊
                tenders = procurement_processor.get_latest_procurements(limit=5)
                response_text = procurement_processor.format_multiple_tenders(
                    tenders, "最新政府採購資訊"
                )
                
            elif user_message in ["high", "高額", "大案", "高金額"]:
                # 獲取高金額採購
                tenders = procurement_processor.get_high_value_procurements(
                    min_amount=50000000, limit=5
                )
                response_text = procurement_processor.format_multiple_tenders(
                    tenders, "高金額政府採購"
                )
                
            elif user_message in ["stats", "統計", "數據"]:
                # 獲取統計資訊
                stats = procurement_processor.get_procurement_statistics()
                response_text = procurement_processor.format_statistics(stats)
                
            elif user_message.startswith("search ") or user_message.startswith("搜尋 "):
                # 關鍵字搜尋
                keyword = user_message.replace("search ", "").replace("搜尋 ", "").strip()
                if keyword:
                    tenders = procurement_processor.search_procurements_by_keywords(
                        [keyword], limit=5
                    )
                    response_text = procurement_processor.format_multiple_tenders(
                        tenders, f"'{keyword}' 相關採購"
                    )
                else:
                    response_text = "請提供搜尋關鍵字，例如：search 資訊系統"
                    
            elif user_message.startswith("進階搜尋 ") or user_message.startswith("進階 "):
                # 進階搜尋 - 解析參數
                try:
                    # 解析進階搜尋參數
                    search_params = _parse_advanced_search(user_message)
                    
                    tenders = procurement_processor.advanced_search_procurements(**search_params)
                    
                    if tenders:
                        # 建立搜尋條件描述
                        conditions = []
                        if search_params.get('keywords'):
                            conditions.append(f"關鍵字: {' '.join(search_params['keywords'])}")
                        if search_params.get('tender_type'):
                            conditions.append(f"類型: {search_params['tender_type']}")
                        if search_params.get('tender_way'):
                            conditions.append(f"方式: {search_params['tender_way']}")
                        if search_params.get('procurement_nature'):
                            conditions.append(f"性質: {search_params['procurement_nature']}")
                        
                        title = "進階搜尋結果"
                        if conditions:
                            title += f" ({', '.join(conditions)})"
                        
                        response_text = procurement_processor.format_multiple_tenders(tenders, title)
                    else:
                        response_text = "沒有找到符合條件的採購資訊。"
                        
                except Exception as e:
                    logger.error(f"Error in advanced search: {e}")
                    response_text = "進階搜尋格式錯誤，請參考說明：\n進階搜尋 關鍵字 type=TENDER_DECLARATION way=TENDER_WAY_1 date=isDate start=2025/01/01 end=2025/12/31 nature=RAD_PROCTRG_CATE_1"
                    
            elif user_message in ["工程", "工程類"]:
                # 工程類採購
                tenders = procurement_processor.get_procurements_by_category(
                    "工程類", limit=5
                )
                response_text = procurement_processor.format_multiple_tenders(
                    tenders, "工程類採購"
                )
                
            elif user_message in ["財物", "財物類"]:
                # 財物類採購
                tenders = procurement_processor.get_procurements_by_category(
                    "財物類", limit=5
                )
                response_text = procurement_processor.format_multiple_tenders(
                    tenders, "財物類採購"
                )
                
            elif user_message in ["勞務", "勞務類"]:
                # 勞務類採購
                tenders = procurement_processor.get_procurements_by_category(
                    "勞務類", limit=5
                )
                response_text = procurement_processor.format_multiple_tenders(
                    tenders, "勞務類採購"
                )
                
            elif user_message in ["不限", "全部", "所有"]:
                # 不限分類（所有類型）
                tenders = procurement_processor.get_procurements_by_category(
                    "不限", limit=5
                )
                response_text = procurement_processor.format_multiple_tenders(
                    tenders, "所有類型採購"
                )
                
            elif user_message in ["help", "幫助", "指令", "?"]:
                # 幫助訊息
                response_text = """
🤖 政府採購機器人使用指南

📝 基本指令：
• 採購/標案 - 查看最新採購資訊
• 高額/大案 - 查看高金額採購案
• 統計/數據 - 查看採購統計資料

🔍 搜尋指令：
• search 關鍵字 - 搜尋相關採購案
• 搜尋 關鍵字 - 搜尋相關採購案
• 進階搜尋 關鍵字 [type=招標類型] [way=招標方式] [date=日期類型] [start=開始日期] [end=結束日期] [nature=採購性質]

參數說明：
• type: 招標類型 (TENDER_DECLARATION, SEARCH_APPEAL, PUBLIC_READ, PREDICT) - 預設不指定
• way: 招標方式 (TENDER_WAY_1, TENDER_WAY_2, TENDER_WAY_3, ...) - 預設不指定  
• date: 日期類型 (isNow, isSpdt, isDate) - 預設 isDate
• start/end: 日期範圍 (YYYY/MM/DD格式)
• nature: 採購性質 (RAD_PROCTRG_CATE_1, RAD_PROCTRG_CATE_2, RAD_PROCTRG_CATE_3 或空白) - 預設不限

📂 分類查詢：
• 工程 - 工程類採購案
• 財物 - 財物類採購案  
• 勞務 - 勞務類採購案
• 不限 - 所有類型採購案

💡 範例：
• search 資訊系統
• 搜尋 AI人工智慧
• 進階搜尋 口罩 date=isDate start=2025/10/01 end=2025/10/31
• 進階搜尋 工程 type=TENDER_DECLARATION way=TENDER_WAY_1 nature=RAD_PROCTRG_CATE_1
                """.strip()
                
            else:
                # 預設回應 - 嘗試以用戶輸入作為關鍵字搜尋
                if len(user_message) > 1:
                    tenders = procurement_processor.search_procurements_by_keywords(
                        [user_message], limit=3
                    )
                    if tenders:
                        response_text = procurement_processor.format_multiple_tenders(
                            tenders, f"'{user_message}' 相關採購"
                        )
                    else:
                        response_text = f"沒有找到與 '{user_message}' 相關的採購資訊。\n\n輸入 'help' 查看使用指南。"
                else:
                    response_text = "請輸入指令查詢政府採購資訊，輸入 'help' 查看使用指南。"

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            response_text = "系統忙碌中，請稍後再試。如果問題持續，請聯繫管理員。"

        # 發送回應
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

    @app.route("/")
    def health_check():
        return "政府採購機器人正常運行中！"

    @app.route("/test")
    def test_procurement():
        """測試端點，用於驗證採購資料獲取功能"""
        try:
            processor = ProcurementProcessor()
            tenders = processor.get_latest_procurements(limit=3)
            
            if tenders:
                result = {
                    "status": "success",
                    "message": "成功獲取政府採購資料",
                    "data_count": len(tenders),
                    "sample_data": tenders[0] if tenders else None
                }
            else:
                result = {
                    "status": "warning", 
                    "message": "沒有獲取到採購資料",
                    "data_count": 0
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Test endpoint error: {e}")
            return {
                "status": "error",
                "message": f"測試失敗: {str(e)}"
            }

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)