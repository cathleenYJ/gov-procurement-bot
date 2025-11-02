"""
政府採購機器人主程式
負責處理Line Bot與政府採購資料的互動
"""

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FollowEvent
)
from dotenv import load_dotenv
import os
import logging
import sqlite3
from procurement_processors import ProcurementProcessor

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === 使用者狀態管理 ===
user_states = {}  # user_id -> {"state": "ask_company", "data": {...}}

# === 資料庫初始化 ===
def init_db():
    """初始化使用者資料庫"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (line_user_id TEXT PRIMARY KEY,
                  company TEXT,
                  contact_name TEXT,
                  email TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def save_user(user_id, company, contact_name, email):
    """儲存或更新使用者資料"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO users 
                     (line_user_id, company, contact_name, email, updated_at) 
                     VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                  (user_id, company, contact_name, email))
        conn.commit()
        conn.close()
        logger.info(f"User data saved: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving user data: {e}")
        return False

def get_user(user_id):
    """取得使用者資料"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT company, contact_name, email FROM users WHERE line_user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        if result:
            return {
                'company': result[0],
                'contact_name': result[1],
                'email': result[2]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user data: {e}")
        return None

# 初始化資料庫
init_db()

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

    @handler.add(FollowEvent)
    def handle_follow(event):
        """處理使用者加入好友事件"""
        user_id = event.source.user_id
        
        try:
            # 檢查使用者是否已登錄
            user_data = get_user(user_id)
            
            if user_data:
                # 已登錄過的使用者（重新加入）
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="📋 招標查詢", text="招標查詢")),
                    QuickReplyButton(action=MessageAction(label="👤 我的資料", text="我的資料")),
                    QuickReplyButton(action=MessageAction(label="❓ 使用說明", text="help"))
                ])
                
                welcome_message = f"""歡迎回來，{user_data['contact_name']}！

🏢 {user_data['company']}

很高興再次為您服務！
您可以直接開始查詢政府採購標案。

點擊下方按鈕快速開始 👇"""
            else:
                # 新使用者 - 只顯示開始登錄按鈕
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="✍️ 開始登錄", text="開始登錄"))
                ])
                
                welcome_message = """👋 歡迎使用政府採購機器人！

🤖 我可以幫您：
• 即時查詢政府採購標案
• 按類別篩選（工程/財物/勞務）
• 快速瀏覽標案資訊

📝 開始使用前，請先登錄您的公司資料：
• 公司名稱
• 聯絡人姓名
• Email

✨ 點擊下方「開始登錄」即可開始！"""
            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=welcome_message, quick_reply=quick_reply)
            )
            
            logger.info(f"New user followed: {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling follow event: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="歡迎使用政府採購機器人！輸入任何訊息開始使用。")
            )

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_message = event.message.text.strip()
        user_message_lower = user_message.lower()
        user_id = event.source.user_id
        
        try:
            # === 處理使用者資料登錄流程 ===
            if user_id in user_states:
                state = user_states[user_id]["state"]
                
                if state == "ask_company":
                    user_states[user_id]["data"]["company"] = user_message
                    user_states[user_id]["state"] = "ask_contact"
                    response_text = "請輸入聯絡人姓名："
                    
                elif state == "ask_contact":
                    user_states[user_id]["data"]["contact_name"] = user_message
                    user_states[user_id]["state"] = "ask_email"
                    response_text = "請輸入聯絡人 Email："
                    
                elif state == "ask_email":
                    data = user_states[user_id]["data"]
                    data["email"] = user_message
                    
                    # 儲存到資料庫
                    if save_user(user_id, data["company"], data["contact_name"], data["email"]):
                        response_text = f"""✅ 登錄完成！

🏢 公司：{data['company']}
👤 聯絡人：{data['contact_name']}
📧 Email：{data['email']}

現在您可以開始查詢政府採購資訊了！
輸入「招標查詢」或點擊圖文選單按鈕開始。"""
                    else:
                        response_text = "❌ 登錄失敗，請稍後再試。"
                    
                    # 清除狀態
                    del user_states[user_id]
                    
                else:
                    response_text = "請輸入「開始登錄」以重新開始。"
                    del user_states[user_id]
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return
            
            # === 使用者資料管理指令 ===
            if user_message_lower in ["開始登錄", "註冊", "登錄"]:
                user_states[user_id] = {"state": "ask_company", "data": {}}
                response_text = "歡迎使用政府採購機器人！\n\n請輸入您的公司名稱："
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return
                
            elif user_message_lower in ["修改資料", "更新資料"]:
                user_data = get_user(user_id)
                if user_data:
                    response_text = f"""目前登錄資料：

🏢 公司：{user_data['company']}
👤 聯絡人：{user_data['contact_name']}
📧 Email：{user_data['email']}

請輸入新的公司名稱（開始重新登錄）："""
                    user_states[user_id] = {"state": "ask_company", "data": {}}
                else:
                    response_text = "您尚未登錄資料，請輸入「開始登錄」進行登錄。"
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return
                
            elif user_message_lower in ["我的資料", "查看資料", "個人資料"] or user_message == "個人資料":
                user_data = get_user(user_id)
                if user_data:
                    # 已有資料，顯示並詢問是否修改
                    quick_reply = QuickReply(items=[
                        QuickReplyButton(action=MessageAction(label="✏️ 修改資料", text="修改資料")),
                        QuickReplyButton(action=MessageAction(label="✅ 不修改", text="招標查詢"))
                    ])
                    
                    response_text = f"""您的登錄資料：

🏢 公司：{user_data['company']}
👤 聯絡人：{user_data['contact_name']}
📧 Email：{user_data['email']}

是否需要修改資料？"""
                    
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=response_text, quick_reply=quick_reply)
                    )
                else:
                    # 沒有資料，直接開始登錄流程
                    user_states[user_id] = {"state": "ask_company", "data": {}}
                    response_text = "歡迎使用政府採購機器人！\n您尚未登錄資料。\n\n請輸入您的公司名稱："
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=response_text)
                    )
                return
            
            # === 處理標案查詢 ===
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

👤 使用者資料管理：
• 開始登錄 - 登錄公司資料（首次使用）
• 我的資料 - 查看已登錄的資料
• 修改資料 - 更新公司資訊

📂 分類查詢：
• 工程類 - 查看「工程類」標案（5筆）
• 財物類 - 查看「財物類」標案（5筆）
• 勞務類 - 查看「勞務類」標案（5筆）

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
                # 預設回應 - 檢查使用者是否已登錄
                user_data = get_user(user_id)
                
                if user_data:
                    # 已登錄使用者的歡迎訊息
                    quick_reply = QuickReply(items=[
                        QuickReplyButton(action=MessageAction(label="📋 招標查詢", text="招標查詢")),
                        QuickReplyButton(action=MessageAction(label="👤 我的資料", text="我的資料")),
                        QuickReplyButton(action=MessageAction(label="❓ 使用說明", text="help"))
                    ])
                    
                    response_text = f"""歡迎回來，{user_data['contact_name']}！

🏢 {user_data['company']}

📋 快速開始：
點擊下方按鈕開始查詢標案

輸入 'help' 查看完整使用指南"""
                    
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=response_text, quick_reply=quick_reply)
                    )
                    return
                else:
                    # 新使用者的歡迎訊息
                    quick_reply = QuickReply(items=[
                        QuickReplyButton(action=MessageAction(label="✍️ 開始登錄", text="開始登錄")),
                        QuickReplyButton(action=MessageAction(label="❓ 使用說明", text="help"))
                    ])
                    
                    response_text = """👋 歡迎使用政府採購機器人！

為了提供更好的服務，請先登錄您的公司資料：

✍️ 點擊「開始登錄」填寫資料
• 公司名稱
• 聯絡人姓名
• Email

📌 登錄後即可開始查詢政府採購標案！"""
                    
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=response_text, quick_reply=quick_reply)
                    )
                    return
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