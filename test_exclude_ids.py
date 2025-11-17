"""
測試「更多標案」功能 - 驗證 exclude_ids 參數是否有效
"""

from procurement_processors import ProcurementProcessor

def test_exclude_ids():
    print("=" * 80)
    print("🧪 測試「更多標案」exclude_ids 功能")
    print("=" * 80)
    
    processor = ProcurementProcessor()
    category = "財物類"
    
    # 第一次查詢：10筆
    print(f"\n📋 第一次查詢：{category} - 10筆")
    print("-" * 80)
    tenders_1 = processor.get_procurements_by_category(category, limit=10)
    
    if not tenders_1:
        print("❌ 沒有查詢到資料")
        return
    
    print(f"✅ 取得 {len(tenders_1)} 筆標案")
    
    # 收集第一批的標案ID
    ids_1 = []
    for t in tenders_1:
        tender_id = t.get('tender_id', '') or t.get('tender_name', '')
        ids_1.append(tender_id)
    
    print(f"\n前 3 筆標案ID：")
    for i, tender_id in enumerate(ids_1[:3], 1):
        tender = tenders_1[i-1]
        org = tender.get('org_name', '未知')[:30]
        print(f"   {i}. {tender_id[:15]}... ({org})")
    
    # 第二次查詢：使用 exclude_ids 參數
    print(f"\n\n📋 第二次查詢：{category} - 10筆（排除已看過的 {len(ids_1)} 筆）")
    print("-" * 80)
    tenders_2 = processor.get_procurements_by_category(
        category, limit=10, exclude_ids=ids_1
    )
    
    if not tenders_2:
        print("❌ 沒有查詢到資料")
        return
    
    print(f"✅ 取得 {len(tenders_2)} 筆標案")
    
    # 收集第二批的標案ID
    ids_2 = []
    for t in tenders_2:
        tender_id = t.get('tender_id', '') or t.get('tender_name', '')
        ids_2.append(tender_id)
    
    print(f"\n前 3 筆標案ID：")
    for i, tender_id in enumerate(ids_2[:3], 1):
        tender = tenders_2[i-1]
        org = tender.get('org_name', '未知')[:30]
        print(f"   {i}. {tender_id[:15]}... ({org})")
    
    # 檢查是否有重複
    overlap = set(ids_1) & set(ids_2)
    
    print(f"\n" + "=" * 80)
    print("📊 結果分析")
    print("=" * 80)
    print(f"第一批標案數量：{len(tenders_1)}")
    print(f"第二批標案數量：{len(tenders_2)}")
    print(f"重複的標案ID：{len(overlap)} 筆")
    
    if len(overlap) == 0:
        print("\n✅ 測試通過！第二批完全沒有重複的標案")
        print("✅ exclude_ids 參數正常運作")
    else:
        print(f"\n❌ 測試失敗！發現 {len(overlap)} 筆重複標案")
        print("重複的ID：")
        for dup_id in list(overlap)[:3]:
            print(f"   - {dup_id}")
    
    # 第三次查詢：排除前兩批
    print(f"\n\n📋 第三次查詢：{category} - 10筆（排除已看過的 {len(ids_1) + len(ids_2)} 筆）")
    print("-" * 80)
    all_seen_ids = ids_1 + ids_2
    tenders_3 = processor.get_procurements_by_category(
        category, limit=10, exclude_ids=all_seen_ids
    )
    
    if tenders_3:
        print(f"✅ 取得 {len(tenders_3)} 筆標案")
        
        ids_3 = []
        for t in tenders_3:
            tender_id = t.get('tender_id', '') or t.get('tender_name', '')
            ids_3.append(tender_id)
        
        overlap_3 = set(all_seen_ids) & set(ids_3)
        
        print(f"重複的標案ID：{len(overlap_3)} 筆")
        
        if len(overlap_3) == 0:
            print("✅ 第三批也完全沒有重複！")
        else:
            print(f"❌ 第三批有 {len(overlap_3)} 筆重複")
    else:
        print("⚠️  沒有更多標案了")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_exclude_ids()
