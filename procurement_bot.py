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

� 指令規則說明：
• 所有指令不區分大小寫
• 中英文指令皆可使用
• 每個指令最多返回5筆結果
• 結果會按相關性智能排序
• 每個標案都附上詳細連結，可直接點擊查看

�📝 基本指令：
• 採購/標案/procurement - 查看「最近3天」的最新標案
• 高額/大案/high - 查看預算超過5千萬的高金額標案
• 統計/數據/stats - 查看今日標案數量和本週統計

🔍 搜尋指令：
• search 關鍵字 - 搜尋標案名稱包含關鍵字的當日標案
• 搜尋 關鍵字 - 同上，支援中文關鍵字

📂 分類查詢：
• 工程 - 查看當日「工程類」標案
• 財物 - 查看當日「財物類」標案  
• 勞務 - 查看當日「勞務類」標案
• 不限 - 查看當日所有類型標案

🎯 智慧功能：
• 當輸入不符合任何指令時，系統會自動將輸入作為關鍵字進行搜尋
• 支援多個關鍵字，用空格分隔
• 結果會優先顯示相關度高的標案

📊 回傳格式：
每筆標案包含：
• 📋 標案名稱（前30字）
• 💰 預算金額（萬為單位）
• 🏛️ 機關名稱（前15字）
• 🔗 詳細連結（可直接點擊）

⚠️ 注意事項：
• 資料來源：政府電子採購網
• 更新頻率：即時從官方網站抓取
• 如遇到系統忙碌，請稍後再試

💡 使用範例：
• 輸入「採購」→ 查看最近3天最新標案
• 輸入「高額」→ 查看大額標案機會
• 輸入「資訊系統」→ 自動搜尋相關標案
• 輸入「工程」→ 查看工程類標案
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