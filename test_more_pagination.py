"""
測試「更多」的分頁行為（page）是否能取得不同資料
"""

from procurement_processors import ProcurementProcessor

def test_pagination():
    processor = ProcurementProcessor()
    category = "財物類"

    print("\n📋 第一次查詢（page 1）")
    tenders_1 = processor.get_procurements_by_category(category, limit=10)
    ids_1 = [t.get('tender_id','') or t.get('tender_name','') for t in tenders_1]

    print("📋 第二次查詢（page 2）")
    tenders_2 = processor.get_procurements_by_category(category, limit=10, page=2)
    ids_2 = [t.get('tender_id','') or t.get('tender_name','') for t in tenders_2]

    overlap = set(ids_1) & set(ids_2)
    print(f"第一批: {len(ids_1)}，第二批: {len(ids_2)}，重複: {len(overlap)}")

    if overlap:
        print("⚠️ 注意：分頁結果有重複，可能是因為系統當日資料太少或分頁邏輯未能避免重複")
    else:
        print("✅ 分頁結果無重複")

if __name__ == '__main__':
    test_pagination()
