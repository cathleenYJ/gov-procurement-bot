"""
Eazy Procurement Bot 主程式
負責處理Line Bot與政府採購資料的互動
"""

from flask import Flask, request, abort, jsonify
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
from procurement_processors import ProcurementProcessor
from clients.supabase_client import SupabaseClient
from clients.analytics_client import UserAnalytics

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === 使用者狀態管理 ===
user_states = {}  # user_id -> {"state": "ask_company", "data": {...}}
user_tender_cache = {}  # user_id -> {"category": "工程類", "seen_ids": [], "search_date": "2025/11/17"}

# === Supabase 客戶端初始化 ===
def init_supabase():
    """初始化 Supabase 客戶端"""
    try:
        supabase_client = SupabaseClient()
        logger.info("Supabase client initialized successfully")
        return supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise


def parse_more_category(message: str) -> str | None:
    """
    從使用者輸入中解析更多標案的類別字串。

    Examples:
        parse_more_category('更多工程類') -> '工程類'
        parse_more_category('更多工程') -> '工程類'
        parse_more_category('更多財物類') -> '財物類'
    """
    if not message:
        return None
    if '工程' in message:
        return '工程類'
    if '財物' in message:
        return '財物類'
    if '勞務' in message:
        return '勞務類'
    return None

def save_user(supabase_client, user_id, company, contact_name, email, position):
    """儲存或更新使用者資料"""
    return supabase_client.save_user(user_id, company, contact_name, email, position)

def get_user(supabase_client, user_id):
    """取得使用者資料"""
    return supabase_client.get_user(user_id)

def create_app():
    """創建並配置 Flask 應用"""
    # 載入環境變數
    load_dotenv()

    app = Flask(__name__)

    # Line Bot 配置
    CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
    CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')  # 管理員密碼

    if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
        logger.error("Missing Line Bot credentials. Please set CHANNEL_ACCESS_TOKEN and CHANNEL_SECRET in .env file")
        return app

    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)

    # 創建政府採購處理器實例
    procurement_processor = ProcurementProcessor()
    
    # 初始化 Supabase 客戶端
    try:
        supabase_client = init_supabase()
        # 初始化行為分析模組
        analytics = UserAnalytics(supabase_client)

        def handle_category_query(user_id: str, category: str, event) -> None:
            """Helper: 查詢指定類別並回覆結果（含更新 cache 與 DB）。"""
            tenders = procurement_processor.get_procurements_by_category(category, limit=10)

            analytics.log_query(
                line_user_id=user_id,
                query_type=f"{category}查詢",
                query_text=category,
                category=category,
                result_count=len(tenders)
            )

            if tenders:
                analytics.log_tender_views_batch(user_id, tenders)
                seen_ids = [t.get('tender_id', '') or t.get('tender_name', '') for t in tenders]
                user_tender_cache[user_id] = {"category": category, "seen_ids": seen_ids, "page": 1}
                analytics.update_browsing_state(user_id, category, seen_ids, page=1)

            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label=f"📋 更多{category}標案", text=f"更多{category}")),
                QuickReplyButton(action=MessageAction(label="🔍 其他分類", text="標案查詢"))
            ])

            response_text = procurement_processor.format_multiple_tenders(tenders, f"{category}採購")

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response_text, quick_reply=quick_reply)
            )
    # NOTE: parse_more_category is defined at module level for testability (see below)
    
        # 是否禁用本地記憶體快取（方便在開發或測試時避免快取造成的結果重複）
        DISABLE_MEMORY_CACHE = os.getenv('DISABLE_MEMORY_CACHE', 'false').lower() in ('true', '1', 'yes')
        # 是否完全跳過 DB 的 browsing state（在測試時可避免數據庫的歷史 state 影響結果）
        BYPASS_DB_BROWSING = os.getenv('BYPASS_DB_BROWSING', 'false').lower() in ('true', '1', 'yes')
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
        return app

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
            user_data = get_user(supabase_client, user_id)
            
            if user_data:
                # 已登錄過的使用者（重新加入）
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="標案查詢", text="標案查詢")),
                    QuickReplyButton(action=MessageAction(label="建立公司檔案", text="建立公司檔案")),
                    QuickReplyButton(action=MessageAction(label="如何查詢標案", text="如何查詢標案")),
                    QuickReplyButton(action=MessageAction(label="我們提供的服務", text="我們提供的服務"))
                ])
                
                welcome_message = f"""歡迎回來，{user_data['contact_name']}！

🏢 {user_data['company']}
💼 {user_data['position']}

很高興再次為您服務！
您可以直接開始查詢政府採購標案。

點擊下方按鈕快速開始 👇"""
            else:
                # 新使用者 - 只顯示開始登錄按鈕
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="✍️ 開始登錄", text="開始登錄"))
                ])
                
                welcome_message = """👋 歡迎使用 Eazy Procurement Bot！

🤖 我可以幫您：
• 即時查詢政府採購標案
• 按類別篩選（工程/財物/勞務）
• 快速瀏覽標案資訊

📝 開始使用前，請先登錄您的公司資料：
• 公司
• 聯絡人
• Email
• 職務/職位

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
                TextSendMessage(text="歡迎使用 Eazy Procurement Bot！輸入任何訊息開始使用。")
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
                    user_states[user_id]["state"] = "ask_position"
                    response_text = "請輸入您的職務/職位："
                    
                elif state == "ask_position":
                    data = user_states[user_id]["data"]
                    data["position"] = user_message
                    
                    # 儲存到資料庫
                    if save_user(supabase_client, user_id, data["company"], data["contact_name"], data["email"], data["position"]):
                        response_text = f"""✅ 登錄完成！

🏢 公司：{data['company']}
👤 聯絡人：{data['contact_name']}
📧 Email：{data['email']}
💼 職務：{data['position']}

現在您可以開始查詢政府採購資訊了！
輸入「標案查詢」或點擊圖文選單按鈕開始。"""
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
                response_text = "歡迎使用 Eazy Procurement Bot！\n\n請輸入您的公司名稱："
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return
                
            elif user_message_lower in ["修改資料", "更新資料"]:
                user_data = get_user(supabase_client, user_id)
                if user_data:
                    response_text = f"""目前登錄資料：

• 公司：{user_data['company']}
• 聯絡人：{user_data['contact_name']}
• Email：{user_data['email']}
• 職務：{user_data['position']}

請輸入新的公司名稱（開始重新登錄）：
• 公司
• 聯絡人
• Email
• 職務/職位"""
                    user_states[user_id] = {"state": "ask_company", "data": {}}
                else:
                    response_text = "您尚未登錄資料，請輸入「開始登錄」進行登錄。"
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return
                
            elif user_message_lower in ["我的資料", "查看資料", "建立公司檔案"] or user_message == "建立公司檔案":
                user_data = get_user(supabase_client, user_id)
                if user_data:
                    # 已有資料，顯示並詢問是否修改
                    quick_reply = QuickReply(items=[
                        QuickReplyButton(action=MessageAction(label="✏️ 修改資料", text="修改資料")),
                        QuickReplyButton(action=MessageAction(label="✅ 不修改", text="標案查詢"))
                    ])
                    
                    response_text = f"""您的登錄資料：

🏢 公司：{user_data['company']}
👤 聯絡人：{user_data['contact_name']}
📧 Email：{user_data['email']}
💼 職務：{user_data['position']}

是否需要修改資料？"""
                    
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=response_text, quick_reply=quick_reply)
                    )
                else:
                    # 沒有資料，直接開始登錄流程
                    user_states[user_id] = {"state": "ask_company", "data": {}}
                    response_text = "歡迎使用 Eazy Procurement Bot！\n您尚未登錄資料。\n\n請輸入您的公司名稱："
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=response_text)
                    )
                return
            
            # === 處理標案查詢 ===
            # 處理圖文選單按鈕「標案查詢」（使用 Quick Reply）
            if user_message == "標案查詢":
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
                
            # === 處理「更多標案」請求 ===
            elif user_message.startswith("更多") and any(x in user_message for x in ["工程", "財物", "勞務", "工程類", "財物類", "勞務類"]):
                # 解析類別
                if "工程" in user_message:
                    category = "工程類"
                elif "財物" in user_message:
                    category = "財物類"
                elif "勞務" in user_message:
                    category = "勞務類"
                else:
                    category = None
                
                logger.info(f"=== 更多標案請求 === User: {user_id}, Category: {category}")
                
                # 為避免跨進程快取不一致，優先從資料庫取得最新的快取狀態（然後更新記憶體）
                # 這樣不同進程或多台機器能共享同一個 browsing state
                db_state = None if BYPASS_DB_BROWSING else analytics.get_browsing_state(user_id)
                cache = user_tender_cache.get(user_id, {})

                if db_state and db_state.get("category") == category:
                    cache = {
                        "category": db_state["category"],
                        "seen_ids": db_state.get("seen_tender_ids", []),
                        "page": db_state.get("page", 1)
                    }
                    user_tender_cache[user_id] = cache
                    logger.info(f"Loaded browsing state from DB for {user_id}, seen={len(cache['seen_ids'])}, page={cache['page']}")
                else:
                    # fallback to memory cache if DB not available
                    cache = user_tender_cache.get(user_id, {})
                logger.info(f"Memory cache: {cache.get('category') if cache else None}, seen_ids: {len(cache.get('seen_ids', []))}")
                
                # 如果記憶體快取不存在或類別不匹配，從資料庫讀取
                if not cache or cache.get("category") != category:
                    logger.info(f"Memory cache not found for {user_id}, loading from database...")
                    db_state = None if BYPASS_DB_BROWSING else analytics.get_browsing_state(user_id)
                    if db_state and db_state.get("category") == category:
                        cache = {
                            "category": db_state["category"],
                            "seen_ids": db_state.get("seen_tender_ids", []),
                            "page": db_state.get("page", 1)
                        }
                        user_tender_cache[user_id] = cache
                        logger.info(f"Loaded {len(cache['seen_ids'])} seen IDs from database")
                    else:
                        logger.warning(f"No cache found in database either. DB state: {db_state}")
                
                if category and cache.get("category") == category:
                    # 取得已看過的ID
                    seen_ids = cache.get("seen_ids", [])
                    logger.info(f"More request: user={user_id}, category={category}, cached_seen={len(seen_ids)}, cache_page={cache.get('page')}")
                    # 當開發或測試想要完全跳過本地記憶體快取時，可設置環境變數 DISABLE_MEMORY_CACHE=True
                    # 若設定為 True，將會忽略記憶體快取的 seen_ids（只會採用分頁 page），以確保每次查詢都是新的頁面
                    if DISABLE_MEMORY_CACHE:
                        logger.info("DISABLE_MEMORY_CACHE is enabled - ignoring memory cache seen_ids and only using page")
                        cache = {"category": category, "seen_ids": [], "page": cache.get('page', 1)}
                        user_tender_cache[user_id] = cache

                    # 頁碼：記錄到快取，可透過更多按鈕翻頁
                    current_page = cache.get("page", 1)
                    next_page = current_page + 1
                    
                    logger.info(f"Requesting more {category} tenders, excluding {len(seen_ids)} seen IDs")
                    logger.info(f"First 3 excluded IDs: {seen_ids[:3] if seen_ids else 'None'}")
                    
                    # 取得更多標案，直接排除已看過的ID（只要10筆新的）
                    # 先嘗試使用頁碼 (page) 來取得不重複內容
                    MAX_RETRIES = 3
                    attempt = 0
                    new_tenders = []
                    candidate_page = next_page
                    while attempt < MAX_RETRIES and not new_tenders:
                        logger.info(f"Attempt {attempt+1} fetching page {candidate_page} for {category}")
                        candidate = procurement_processor.get_procurements_by_category(
                            category, limit=10, exclude_ids=seen_ids, page=candidate_page
                        )

                        # 手動過濾以防止因 site 行為或 id 格式差異造成的重複
                        filtered_candidate = []
                        for t in candidate:
                            t_id = t.get('tender_id', '') or t.get('tender_name', '')
                            t_key = f"{t.get('tender_name','')}|{t.get('org_name','')}"
                            if t_id in seen_ids or t_key in seen_ids:
                                continue
                            filtered_candidate.append(t)

                        if filtered_candidate:
                            new_tenders = filtered_candidate[:10]
                            logger.info(f"Found {len(new_tenders)} filtered tenders from page {candidate_page}")
                            break

                        # 下一次嘗試下一頁
                        attempt += 1
                        candidate_page += 1

                    if not new_tenders:
                        new_tenders = procurement_processor.get_procurements_by_category(
                            category, limit=10, exclude_ids=seen_ids
                        )

                    logger.info(f"Received {len(new_tenders)} new tenders (user={user_id}, category={category}, page={next_page})")
                    if new_tenders:
                        new_ids = [t.get('tender_id', '') or t.get('tender_name', '') for t in new_tenders]
                        logger.info(f"First 3 new IDs: {new_ids[:3]}")
                        
                        # 檢查重複（debug用）
                        overlap = set(seen_ids) & set(new_ids)
                        if len(overlap) > 0:
                            logger.error(f"❌ Found {len(overlap)} duplicate IDs: {list(overlap)[:3]}")
                        else:
                            logger.info("✅ No duplicates found")

                    if new_tenders:
                        # 記錄「更多標案」查詢行為
                        analytics.log_query(
                            line_user_id=user_id,
                            query_type="更多標案",
                            query_text=user_message,
                            category=category,
                            result_count=len(new_tenders)
                        )
                        
                        # 記錄新標案瀏覽
                        analytics.log_tender_views_batch(user_id, new_tenders)
                        
                        # 更新已看過的ID
                        new_ids = [t.get('tender_id', '') or t.get('tender_name', '') for t in new_tenders]
                        cache["seen_ids"].extend(new_ids)
                        # 把 page 更新為我們最後實際使用的 candidate_page - 如果沒有修改，使用 next_page
                        cache["page"] = candidate_page if 'candidate_page' in locals() else next_page
                        user_tender_cache[user_id] = cache
                        
                        # 同時更新資料庫的瀏覽狀態
                        ok = analytics.update_browsing_state(user_id, category, cache["seen_ids"], page=cache.get("page", 1))
                        logger.info(f"update_browsing_state returned: {ok} for user={user_id}")
                        if not ok:
                            logger.warning(f"Failed to persist browsing state for {user_id} - cache will be held in memory only")
                        
                        # 顯示新標案，並繼續提供「更多」按鈕
                        quick_reply = QuickReply(items=[
                            QuickReplyButton(action=MessageAction(label=f"📋 更多{category}標案", text=f"更多{category}")),
                            QuickReplyButton(action=MessageAction(label="🔍 其他分類", text="標案查詢"))
                        ])
                        
                        response_text = procurement_processor.format_multiple_tenders(
                            new_tenders, f"{category}採購（續）"
                        )
                        
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=response_text, quick_reply=quick_reply)
                        )
                    else:
                        # 沒有更多新標案了
                        quick_reply = QuickReply(items=[
                            QuickReplyButton(action=MessageAction(label="🔄 重新查詢", text=category)),
                            QuickReplyButton(action=MessageAction(label="🔍 其他分類", text="標案查詢"))
                        ])
                        
                        response_text = f"目前沒有更多{category}標案了。\n\n您可以：\n• 重新查詢以更新資料\n• 查看其他分類的標案"
                        
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=response_text, quick_reply=quick_reply)
                        )
                else:
                    # 沒有快取，重新查詢
                    response_text = f"請先查詢{category}標案"
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=response_text)
                    )
                return

            elif "工程類" in user_message or user_message_lower in ["工程", "1", "1."]:
                # 工程類採購
                handle_category_query(user_id, "工程類", event)
                return
                
            elif "財物類" in user_message or user_message_lower in ["財物", "2", "2."]:
                # 財物類採購
                handle_category_query(user_id, "財物類", event)
                return
                
            elif "勞務類" in user_message or user_message_lower in ["勞務", "3", "3."]:
                # 勞務類採購
                handle_category_query(user_id, "勞務類", event)
                return
            
            # === 處理「更多標案」請求 ===
            elif user_message.startswith("更多") and any(x in user_message for x in ["工程", "財物", "勞務", "工程類", "財物類", "勞務類"]):
                # 解析類別
                if "工程" in user_message:
                    category = "工程類"
                elif "財物" in user_message:
                    category = "財物類"
                elif "勞務" in user_message:
                    category = "勞務類"
                else:
                    category = None
                
                logger.info(f"=== 更多標案請求 === User: {user_id}, Category: {category}")
                
                # 為避免跨進程快取不一致，優先從資料庫取得最新的快取狀態（然後更新記憶體）
                # 這樣不同進程或多台機器能共享同一個 browsing state
                db_state = None if BYPASS_DB_BROWSING else analytics.get_browsing_state(user_id)
                cache = user_tender_cache.get(user_id, {})

                if db_state and db_state.get("category") == category:
                    cache = {
                        "category": db_state["category"],
                        "seen_ids": db_state.get("seen_tender_ids", []),
                        "page": db_state.get("page", 1)
                    }
                    user_tender_cache[user_id] = cache
                    logger.info(f"Loaded browsing state from DB for {user_id}, seen={len(cache['seen_ids'])}, page={cache['page']}")
                else:
                    # fallback to memory cache if DB not available
                    cache = user_tender_cache.get(user_id, {})
                logger.info(f"Memory cache: {cache.get('category') if cache else None}, seen_ids: {len(cache.get('seen_ids', []))}")
                
                # 如果記憶體快取不存在或類別不匹配，從資料庫讀取
                if not cache or cache.get("category") != category:
                    logger.info(f"Memory cache not found for {user_id}, loading from database...")
                    db_state = None if BYPASS_DB_BROWSING else analytics.get_browsing_state(user_id)
                    if db_state and db_state.get("category") == category:
                        cache = {
                            "category": db_state["category"],
                            "seen_ids": db_state.get("seen_tender_ids", []),
                            "page": db_state.get("page", 1)
                        }
                        user_tender_cache[user_id] = cache
                        logger.info(f"Loaded {len(cache['seen_ids'])} seen IDs from database")
                    else:
                        logger.warning(f"No cache found in database either. DB state: {db_state}")
                
                if category and cache.get("category") == category:
                    # 取得已看過的ID
                    seen_ids = cache.get("seen_ids", [])
                    logger.info(f"More request: user={user_id}, category={category}, cached_seen={len(seen_ids)}, cache_page={cache.get('page')}")
                    # 當開發或測試想要完全跳過本地記憶體快取時，可設置環境變數 DISABLE_MEMORY_CACHE=True
                    # 若設定為 True，將會忽略記憶體快取的 seen_ids（只會採用分頁 page），以確保每次查詢都是新的頁面
                    if DISABLE_MEMORY_CACHE:
                        logger.info("DISABLE_MEMORY_CACHE is enabled - ignoring memory cache seen_ids and only using page")
                        cache = {"category": category, "seen_ids": [], "page": cache.get('page', 1)}
                        user_tender_cache[user_id] = cache

                    # 頁碼：記錄到快取，可透過更多按鈕翻頁
                    current_page = cache.get("page", 1)
                    next_page = current_page + 1
                    
                    logger.info(f"Requesting more {category} tenders, excluding {len(seen_ids)} seen IDs")
                    logger.info(f"First 3 excluded IDs: {seen_ids[:3] if seen_ids else 'None'}")
                    
                    # 取得更多標案，直接排除已看過的ID（只要10筆新的）
                    # 先嘗試使用頁碼 (page) 來取得不重複內容
                    # Retry strategy: try up to 3 subsequent pages to avoid duplicates between pages
                    MAX_RETRIES = 3
                    attempt = 0
                    new_tenders = []
                    candidate_page = next_page
                    while attempt < MAX_RETRIES and not new_tenders:
                        logger.info(f"Attempt {attempt+1} fetching page {candidate_page} for {category}")
                        candidate = procurement_processor.get_procurements_by_category(
                            category, limit=10, exclude_ids=seen_ids, page=candidate_page
                        )

                        # 手動過濾以防止因 site 行為或 id 格式差異造成的重複
                        filtered_candidate = []
                        for t in candidate:
                            t_id = t.get('tender_id', '') or t.get('tender_name', '')
                            t_key = f"{t.get('tender_name','')}|{t.get('org_name','')}"
                            if t_id in seen_ids or t_key in seen_ids:
                                continue
                            filtered_candidate.append(t)

                        if filtered_candidate:
                            new_tenders = filtered_candidate[:10]
                            logger.info(f"Found {len(new_tenders)} filtered tenders from page {candidate_page}")
                            break

                        # 下一次嘗試下一頁
                        attempt += 1
                        candidate_page += 1

                    # 如果使用 page 查詢仍然回傳舊資料（或查不到新資料），再退回到多天查詢
                    if not new_tenders:
                        new_tenders = procurement_processor.get_procurements_by_category(
                            category, limit=10, exclude_ids=seen_ids
                        )
                    
                    logger.info(f"Received {len(new_tenders)} new tenders (user={user_id}, category={category}, page={next_page})")
                    if new_tenders:
                        new_ids = [t.get('tender_id', '') or t.get('tender_name', '') for t in new_tenders]
                        logger.info(f"First 3 new IDs: {new_ids[:3]}")
                        
                        # 檢查重複（debug用）
                        overlap = set(seen_ids) & set(new_ids)
                        if len(overlap) > 0:
                            logger.error(f"❌ Found {len(overlap)} duplicate IDs: {list(overlap)[:3]}")
                        else:
                            logger.info("✅ No duplicates found")
                    
                    if new_tenders:
                        # 記錄「更多標案」查詢行為
                        analytics.log_query(
                            line_user_id=user_id,
                            query_type="更多標案",
                            query_text=user_message,
                            category=category,
                            result_count=len(new_tenders)
                        )
                        
                        # 記錄新標案瀏覽
                        analytics.log_tender_views_batch(user_id, new_tenders)
                        
                        # 更新已看過的ID
                        new_ids = [t.get('tender_id', '') or t.get('tender_name', '') for t in new_tenders]
                        cache["seen_ids"].extend(new_ids)
                        # 更新頁碼
                        # 把 page 更新為我們最後實際使用的 candidate_page - 如果沒有修改，使用 next_page
                        cache["page"] = candidate_page if 'candidate_page' in locals() else next_page
                        user_tender_cache[user_id] = cache
                        
                        # 同時更新資料庫的瀏覽狀態
                        ok = analytics.update_browsing_state(user_id, category, cache["seen_ids"], page=cache.get("page", 1))
                        logger.info(f"update_browsing_state returned: {ok} for user={user_id}")
                        if not ok:
                            logger.warning(f"Failed to persist browsing state for {user_id} - cache will be held in memory only")
                        
                        # 顯示新標案，並繼續提供「更多」按鈕
                        # 修正更多按鈕的傳回文字，確保使用者點擊「更多」時會被正確路由
                        quick_reply = QuickReply(items=[
                            QuickReplyButton(action=MessageAction(label=f"📋 更多{category}標案", text=f"更多{category}")),
                            QuickReplyButton(action=MessageAction(label="🔍 其他分類", text="標案查詢"))
                        ])
                        
                        response_text = procurement_processor.format_multiple_tenders(
                            new_tenders, f"{category}採購（續）"
                        )
                        
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=response_text, quick_reply=quick_reply)
                        )
                    else:
                        # 沒有更多新標案了
                        quick_reply = QuickReply(items=[
                            QuickReplyButton(action=MessageAction(label="🔄 重新查詢", text=category)),
                            QuickReplyButton(action=MessageAction(label="🔍 其他分類", text="標案查詢"))
                        ])
                        
                        response_text = f"目前沒有更多{category}標案了。\n\n您可以：\n• 重新查詢以更新資料\n• 查看其他分類的標案"
                        
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=response_text, quick_reply=quick_reply)
                        )
                else:
                    # 沒有快取，重新查詢
                    response_text = f"請先查詢{category}標案"
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=response_text)
                    )
                return
            
            elif user_message_lower in ["如何查詢標案"]:
                response_text = """📝 如何查詢標案

為了在未來得到更好的呈現，請填寫正確的資訊 for 客戶檔案建立：

• 公司
• 聯絡人
• Email
• 職務/職位

請點擊「建立公司檔案」按鈕開始填寫您的資訊！"""
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return
                
            elif user_message_lower in ["我們提供的服務"]:
                response_text = """我們提供的服務

我們整合台灣招標網站的內容，提供以下服務：

🏗️ 工程類：
• 建築工程
• 道路工程  
• 水利工程

🛒 購案類：
• 設備採購
• 軟體採購
• 儀器採購

👥 勞務採購：
• 顧問服務
• 研究服務
• 外包服務

📢 公告招標：
• 即時標案資訊
• 詳細標案內容
• 機關聯絡資訊

讓我們幫您快速找到最適合的政府採購機會！"""
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return
                # 幫助訊息
                response_text = """
🤖 Eazy Procurement Bot 使用指南

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
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return

            elif user_message in ["清除快取", "重設分頁", "clear cache"]:
                # 清除使用者的記憶體快取與資料庫瀏覽狀態，方便在測試時取得不同頁的資料
                cache = user_tender_cache.get(user_id, {})
                category_for_clear = cache.get("category") if cache else ""

                # 更新資料庫瀏覽狀態為清空
                analytics.update_browsing_state(user_id, category_for_clear, [], page=1)

                # 清除記憶體快取
                user_tender_cache.pop(user_id, None)

                response_text = "已清除本地快取並重設分頁 (page=1)。請重新查詢分類以取得最新結果。"
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return
                
            else:
                # 預設回應 - 檢查使用者是否已登錄
                user_data = get_user(supabase_client, user_id)
                
                if user_data:
                    # 已登錄使用者的歡迎訊息
                    quick_reply = QuickReply(items=[
                        QuickReplyButton(action=MessageAction(label="標案查詢", text="標案查詢")),
                        QuickReplyButton(action=MessageAction(label="建立公司檔案", text="建立公司檔案")),
                        QuickReplyButton(action=MessageAction(label="如何查詢標案", text="如何查詢標案")),
                        QuickReplyButton(action=MessageAction(label="我們提供的服務", text="我們提供的服務"))
                    ])
                    
                    response_text = f"""歡迎回來，{user_data['contact_name']}！

🏢 {user_data['company']}
💼 {user_data['position']}

📋 快速開始：
點擊下方按鈕開始查詢標案"""
                    
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
                    
                    response_text = """👋 歡迎使用 Eazy Procurement Bot！

為了提供更好的服務，請先登錄您的公司資料：

✍️ 點擊「開始登錄」填寫資料
• 公司
• 聯絡人
• Email
• 職務/職位

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
        return "Eazy Procurement Bot 正常運行中！"

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

    @app.route("/admin/users")
    def admin_users():
        """管理端點：查看所有使用者資料（需要密碼）"""
        # 簡單的密碼認證
        auth_password = request.args.get('password', '')
        
        if auth_password != ADMIN_PASSWORD:
            return jsonify({
                "status": "error",
                "message": "未授權訪問。請使用正確的密碼參數。",
                "usage": "請訪問: /admin/users?password=YOUR_PASSWORD"
            }), 401
        
        try:
            users = supabase_client.get_all_users()
            
            return jsonify({
                "status": "success",
                "total_users": len(users),
                "users": users
            })
            
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return jsonify({
                "status": "error",
                "message": f"獲取資料失敗: {str(e)}"
            }), 500

    @app.route("/admin/user/<user_id>")
    def admin_user_detail(user_id):
        """管理端點：查看特定使用者資料（需要密碼）"""
        auth_password = request.args.get('password', '')
        
        if auth_password != ADMIN_PASSWORD:
            return jsonify({
                "status": "error",
                "message": "未授權訪問"
            }), 401
        
        try:
            user_data = get_user(supabase_client, user_id)
            
            if user_data:
                return jsonify({
                    "status": "success",
                    "user_id": user_id,
                    "data": user_data
                })
            else:
                return jsonify({
                    "status": "not_found",
                    "message": "找不到此使用者"
                }), 404
                
        except Exception as e:
            logger.error(f"Error fetching user detail: {e}")
            return jsonify({
                "status": "error",
                "message": f"獲取資料失敗: {str(e)}"
            }), 500

    @app.route("/admin/analytics/daily")
    def admin_analytics_daily():
        """管理端點：每日查詢統計（需要密碼）"""
        auth_password = request.args.get('password', '')
        
        if auth_password != ADMIN_PASSWORD:
            return jsonify({
                "status": "error",
                "message": "未授權訪問"
            }), 401
        
        try:
            days = int(request.args.get('days', 7))
            stats = analytics.get_daily_stats(days=days)
            
            return jsonify({
                "status": "success",
                "days": days,
                "data": stats
            })
            
        except Exception as e:
            logger.error(f"Error fetching daily analytics: {e}")
            return jsonify({
                "status": "error",
                "message": f"獲取統計失敗: {str(e)}"
            }), 500

    @app.route("/admin/analytics/popular")
    def admin_analytics_popular():
        """管理端點：熱門標案排行（需要密碼）"""
        auth_password = request.args.get('password', '')
        
        if auth_password != ADMIN_PASSWORD:
            return jsonify({
                "status": "error",
                "message": "未授權訪問"
            }), 401
        
        try:
            limit = int(request.args.get('limit', 10))
            tenders = analytics.get_popular_tenders(limit=limit)
            
            return jsonify({
                "status": "success",
                "total": len(tenders),
                "data": tenders
            })
            
        except Exception as e:
            logger.error(f"Error fetching popular tenders: {e}")
            return jsonify({
                "status": "error",
                "message": f"獲取熱門標案失敗: {str(e)}"
            }), 500

    @app.route("/admin/analytics/active-users")
    def admin_analytics_active_users():
        """管理端點：活躍使用者排行（需要密碼）"""
        auth_password = request.args.get('password', '')
        
        if auth_password != ADMIN_PASSWORD:
            return jsonify({
                "status": "error",
                "message": "未授權訪問"
            }), 401
        
        try:
            limit = int(request.args.get('limit', 10))
            users = analytics.get_active_users(limit=limit)
            
            return jsonify({
                "status": "success",
                "total": len(users),
                "data": users
            })
            
        except Exception as e:
            logger.error(f"Error fetching active users: {e}")
            return jsonify({
                "status": "error",
                "message": f"獲取活躍使用者失敗: {str(e)}"
            }), 500

    @app.route("/admin/analytics/user/<user_id>")
    def admin_analytics_user(user_id):
        """管理端點：特定使用者的統計資料（需要密碼）"""
        auth_password = request.args.get('password', '')
        
        if auth_password != ADMIN_PASSWORD:
            return jsonify({
                "status": "error",
                "message": "未授權訪問"
            }), 401
        
        try:
            stats = analytics.get_user_stats(user_id)
            
            if stats:
                return jsonify({
                    "status": "success",
                    "user_id": user_id,
                    "stats": stats
                })
            else:
                return jsonify({
                    "status": "not_found",
                    "message": "找不到此使用者的統計資料"
                }), 404
                
        except Exception as e:
            logger.error(f"Error fetching user stats: {e}")
            return jsonify({
                "status": "error",
                "message": f"獲取使用者統計失敗: {str(e)}"
            }), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)