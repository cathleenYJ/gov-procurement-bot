"""
調試「更多標案」功能
檢查快取和查詢邏輯（不導入 procurement_bot 避免啟動 Flask）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from procurement_processors import ProcurementProcessor

# 模擬 user_tender_cache
user_tender_cache = {}

def simulate_user_interaction(user_id="test_user"):
    print("=" * 80)
    print("🔍 調試 Line Bot 「更多標案」功能")
    print("=" * 80)
    
    processor = ProcurementProcessor()
    category = "財物類"
    
    # ===== 第一次：用戶點擊「財物類」 =====
    print(f"\n\n【第一次】用戶點擊：{category}")
    print("-" * 80)
    
    tenders_1 = processor.get_procurements_by_category(category, limit=10)
    
    if not tenders_1:
        print("❌ 沒有資料")
        return
    
    print(f"✅ 查詢到 {len(tenders_1)} 筆標案")
    
    # 建立快取（模擬 Line Bot 的邏輯）
    seen_ids = [t.get('tender_id', '') or t.get('tender_name', '') for t in tenders_1]
    user_tender_cache[user_id] = {
        "category": category,
        "seen_ids": seen_ids
    }
    # 設定初始頁碼
    user_tender_cache[user_id]["page"] = 1
    
    print(f"📝 快取建立：category={category}, seen_ids 數量={len(seen_ids)}")
    print(f"\n前 3 筆標案：")
    for i, tender in enumerate(tenders_1[:3], 1):
        tid = tender.get('tender_id', '')[:20]
        org = tender.get('org_name', '')[:30]
        print(f"   {i}. ID={tid}... Org={org}")
    
    print(f"\n前 3 筆 seen_ids：")
    for i, sid in enumerate(seen_ids[:3], 1):
        print(f"   {i}. {sid[:30]}...")
    
    # ===== 第二次：用戶點擊「更多財物類」 =====
    print(f"\n\n【第二次】用戶點擊：更多{category}")
    print("-" * 80)
    
    # 從快取取得已看過的ID（模擬 Line Bot 的邏輯）
    cache = user_tender_cache.get(user_id, {})
    print(f"📖 讀取快取：category={cache.get('category')}, seen_ids 數量={len(cache.get('seen_ids', []))}")
    
    if category and cache.get("category") == category:
        seen_ids = cache.get("seen_ids", [])
        
        print(f"🔍 查詢新標案（排除 {len(seen_ids)} 筆已看過的）...")
        print(f"   呼叫：get_procurements_by_category('{category}', limit=10, exclude_ids=[...{len(seen_ids)}筆])")
        
        # 這裡是關鍵！使用 exclude_ids 參數
        # 嘗試使用 page 翻頁
        page = user_tender_cache[user_id].get("page", 1)
        next_page = page + 1
        new_tenders = processor.get_procurements_by_category(
            category, limit=10, exclude_ids=seen_ids, page=next_page
        )
        
        if new_tenders:
            print(f"✅ 查詢到 {len(new_tenders)} 筆新標案")
            
            print(f"\n前 3 筆新標案：")
            for i, tender in enumerate(new_tenders[:3], 1):
                tid = tender.get('tender_id', '')[:20]
                org = tender.get('org_name', '')[:30]
                print(f"   {i}. ID={tid}... Org={org}")
            
            # 檢查是否有重複
            new_ids = [t.get('tender_id', '') or t.get('tender_name', '') for t in new_tenders]
            overlap = set(seen_ids) & set(new_ids)
            
            print(f"\n🔎 重複檢查：")
            print(f"   第一批 seen_ids: {len(seen_ids)} 筆")
            print(f"   第二批 new_ids: {len(new_ids)} 筆")
            print(f"   重複: {len(overlap)} 筆")
            
            if len(overlap) > 0:
                print(f"\n❌ 發現重複！重複的ID：")
                for dup_id in list(overlap)[:3]:
                    print(f"      - {dup_id[:40]}...")
            else:
                print(f"\n✅ 沒有重複！")
            
            # 更新快取
            cache["seen_ids"].extend(new_ids)
            user_tender_cache[user_id] = cache
            # 更新頁數
            user_tender_cache[user_id]["page"] = next_page
            
            print(f"\n📝 更新快取：total seen_ids={len(cache['seen_ids'])} 筆")
        else:
            print("⚠️  沒有更多標案")
    else:
        print(f"❌ 快取不匹配或不存在")
        print(f"   cache category: {cache.get('category')}")
        print(f"   requested category: {category}")
    
    # ===== 第三次：用戶再次點擊「更多財物類」 =====
    print(f"\n\n【第三次】用戶再次點擊：更多{category}")
    print("-" * 80)
    
    cache = user_tender_cache.get(user_id, {})
    print(f"📖 讀取快取：seen_ids 數量={len(cache.get('seen_ids', []))}")
    
    if category and cache.get("category") == category:
        seen_ids = cache.get("seen_ids", [])
        
        print(f"🔍 查詢新標案（排除 {len(seen_ids)} 筆已看過的）...")
        
        new_tenders = processor.get_procurements_by_category(
            category, limit=10, exclude_ids=seen_ids
        )
        
        if new_tenders:
            print(f"✅ 查詢到 {len(new_tenders)} 筆新標案")
            
            # 檢查是否有重複
            new_ids = [t.get('tender_id', '') or t.get('tender_name', '') for t in new_tenders]
            overlap = set(seen_ids) & set(new_ids)
            
            print(f"\n🔎 重複檢查：")
            print(f"   已看過: {len(seen_ids)} 筆")
            print(f"   新查詢: {len(new_ids)} 筆")
            print(f"   重複: {len(overlap)} 筆")
            
            if len(overlap) == 0:
                print(f"\n✅ 沒有重複！")
            else:
                print(f"\n❌ 發現 {len(overlap)} 筆重複")
        else:
            print("⚠️  沒有更多標案")
    
    print("\n" + "=" * 80)
    print("🎯 總結")
    print("=" * 80)
    final_cache = user_tender_cache.get(user_id, {})
    print(f"總共看過的標案：{len(final_cache.get('seen_ids', []))} 筆")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    simulate_user_interaction()
