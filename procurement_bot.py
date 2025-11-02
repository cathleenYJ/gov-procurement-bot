"""
政府採購機器人主程式
負責處理Line Bot與政府採購資料的互動
"""

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from dotenv import load_dotenv
import os
import logging
from procurement_processors import ProcurementProcessor

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        user_message = event.message.text.strip()
        user_message_lower = user_message.lower()
        
        try:
            # 處理圖文選單按鈕「招標查詢」（使用 Quick Reply）
            if user_message == "招標查詢":
                # 建立 Quick Reply 按鈕
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="工程類", text="工程類")),
                    QuickReplyButton(action=MessageAction(label="財物類", text="財物類")),
                    QuickReplyButton(action=MessageAction(label="勞務類", text="勞務類"))
                ])
                
                # 發送帶有 Quick Reply 的訊息
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="好的！請問您想查詢的是哪一類標案？\n請點選下方按鈕：",
                        quick_reply=quick_reply
                    )
                )
                return
                
            elif "工程類" in user_message or user_message_lower in ["工程", "1", "1."]:
                # 工程類採購
                tenders = procurement_processor.get_procurements_by_category(
                    "工程類", limit=5
                )
                response_text = procurement_processor.format_multiple_tenders(
                    tenders, "工程類採購"
                )
                
            elif "財物類" in user_message or user_message_lower in ["財物", "2", "2."]:
                # 財物類採購
                tenders = procurement_processor.get_procurements_by_category(
                    "財物類", limit=5
                )
                response_text = procurement_processor.format_multiple_tenders(
                    tenders, "財物類採購"
                )
                
            elif "勞務類" in user_message or user_message_lower in ["勞務", "3", "3."]:
                # 勞務類採購
                tenders = procurement_processor.get_procurements_by_category(
                    "勞務類", limit=5
                )
                response_text = procurement_processor.format_multiple_tenders(
                    tenders, "勞務類採購"
                )
                
            elif user_message_lower in ["help", "幫助", "指令", "?"]:
                # 幫助訊息
                response_text = """
🤖 政府採購機器人使用指南

 分類查詢：
• 工程類 - 查看當日「工程類」標案（5筆）
• 財物類 - 查看當日「財物類」標案（5筆）
• 勞務類 - 查看當日「勞務類」標案（5筆）

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

💡 使用方式：
• 點擊圖文選單按鈕，選擇標案類別即可查詢
                """.strip()
                
            else:
                # 預設回應
                response_text = """請選擇標案類別：
1. 工程類
2. 財物類
3. 勞務類

或輸入 'help' 查看使用指南。"""

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