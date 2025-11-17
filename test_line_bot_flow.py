"""
模擬 Line Bot 的「更多標案」流程
"""

from procurement_processors import ProcurementProcessor

def simulate_line_bot_flow():
    print("=" * 80)
    print("🤖 模擬 Line Bot 「更多標案」流程")
    print("=" * 80)
    
    processor = ProcurementProcessor()
    category = "財物類"
    
    # 模擬用戶快取
    user_cache = {
        "category": category,
        "seen_ids": []
    }
    
    # 第一次：用戶點擊「財物類」
    print(f"\n👤 用戶點擊：{category}")
    print("-" * 80)
    tenders_1 = processor.get_procurements_by_category(category, limit=10)
    
    print(f"✅ 顯示 {len(tenders_1)} 筆標案")
    for i, tender in enumerate(tenders_1[:3], 1):
        name = tender.get('tender_name', '') or f"標案ID: {tender.get('tender_id', '')[:20]}"
        org = tender.get('org_name', '未知')[:25]
        budget = tender.get('budget_text', '未知')
        print(f"   {i}. ({budget}) - {org}")
        print(f"      {name[:50]}...")
    print(f"   ... 還有 {len(tenders_1) - 3} 筆")
    
    # 記錄已看過的ID
    for t in tenders_1:
        tender_id = t.get('tender_id', '') or t.get('tender_name', '')
        user_cache["seen_ids"].append(tender_id)
    
    print(f"\n📝 記錄：已看過 {len(user_cache['seen_ids'])} 筆標案")
    
    # 第二次：用戶點擊「更多財物類」
    print(f"\n\n👤 用戶點擊：更多{category}")
    print("-" * 80)
    print(f"🔍 查詢新標案（排除已看過的 {len(user_cache['seen_ids'])} 筆）...")
    
    tenders_2 = processor.get_procurements_by_category(
        category, limit=10, exclude_ids=user_cache["seen_ids"]
    )
    
    print(f"✅ 顯示 {len(tenders_2)} 筆新標案")
    for i, tender in enumerate(tenders_2[:3], 1):
        name = tender.get('tender_name', '') or f"標案ID: {tender.get('tender_id', '')[:20]}"
        org = tender.get('org_name', '未知')[:25]
        budget = tender.get('budget_text', '未知')
        print(f"   {i}. ({budget}) - {org}")
        print(f"      {name[:50]}...")
    print(f"   ... 還有 {len(tenders_2) - 3} 筆")
    
    # 檢查是否有重複
    ids_1 = set(user_cache["seen_ids"][:10])
    ids_2 = set()
    for t in tenders_2:
        tender_id = t.get('tender_id', '') or t.get('tender_name', '')
        ids_2.add(tender_id)
    
    overlap = ids_1 & ids_2
    
    # 更新快取
    for t in tenders_2:
        tender_id = t.get('tender_id', '') or t.get('tender_name', '')
        user_cache["seen_ids"].append(tender_id)
    
    print(f"\n📝 記錄：總共已看過 {len(user_cache['seen_ids'])} 筆標案")
    
    # 第三次：用戶再次點擊「更多財物類」
    print(f"\n\n👤 用戶再次點擊：更多{category}")
    print("-" * 80)
    print(f"🔍 查詢新標案（排除已看過的 {len(user_cache['seen_ids'])} 筆）...")
    
    tenders_3 = processor.get_procurements_by_category(
        category, limit=10, exclude_ids=user_cache["seen_ids"]
    )
    
    print(f"✅ 顯示 {len(tenders_3)} 筆新標案")
    for i, tender in enumerate(tenders_3[:3], 1):
        name = tender.get('tender_name', '') or f"標案ID: {tender.get('tender_id', '')[:20]}"
        org = tender.get('org_name', '未知')[:25]
        budget = tender.get('budget_text', '未知')
        print(f"   {i}. ({budget}) - {org}")
        print(f"      {name[:50]}...")
    
    # 檢查第三批是否有重複
    ids_3 = set()
    for t in tenders_3:
        tender_id = t.get('tender_id', '') or t.get('tender_name', '')
        ids_3.add(tender_id)
    
    all_previous_ids = set(user_cache["seen_ids"])
    overlap_3 = all_previous_ids & ids_3
    
    print(f"\n" + "=" * 80)
    print("📊 測試結果")
    print("=" * 80)
    print(f"第一次查詢：{len(tenders_1)} 筆")
    print(f"第二次查詢：{len(tenders_2)} 筆（重複：{len(overlap)} 筆）")
    print(f"第三次查詢：{len(tenders_3)} 筆（重複：{len(overlap_3)} 筆）")
    print(f"總共看過：{len(user_cache['seen_ids'])} 筆標案")
    
    if len(overlap) == 0 and len(overlap_3) == 0:
        print("\n🎉 完美！每次都顯示不重複的新標案")
        print("✅ 「更多標案」功能正常運作")
    else:
        print(f"\n⚠️  發現重複標案")
        if len(overlap) > 0:
            print(f"   - 第二次有 {len(overlap)} 筆重複")
        if len(overlap_3) > 0:
            print(f"   - 第三次有 {len(overlap_3)} 筆重複")
    
    print("=" * 80 + "\n")

if __name__ == "__main__":
    simulate_line_bot_flow()
