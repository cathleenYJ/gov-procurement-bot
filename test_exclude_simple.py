"""
直接測試 exclude_ids 是否真的在運作
"""

from procurement_processors import ProcurementProcessor

processor = ProcurementProcessor()
category = "財物類"

print("=" * 80)
print("🔍 測試 exclude_ids 參數")
print("=" * 80)

# 第一次查詢
print(f"\n第一次查詢：{category} - 10筆")
tenders_1 = processor.get_procurements_by_category(category, limit=10)

print(f"取得 {len(tenders_1)} 筆")
ids_1 = []
for i, t in enumerate(tenders_1, 1):
    tid = t.get('tender_id', '')
    org = t.get('org_name', '')[:25]
    budget = t.get('budget_text', '')
    ids_1.append(tid)
    print(f"  {i}. {tid[:20]}... ({budget}) - {org}")

print(f"\n收集到的 IDs: {len(ids_1)} 個")
print(f"前3個ID: {ids_1[:3]}")

# 第二次查詢 - 使用 exclude_ids
print(f"\n\n第二次查詢：{category} - 10筆（exclude_ids={len(ids_1)}個）")
print(f"傳入的 exclude_ids: {ids_1[:3]} ...")

tenders_2 = processor.get_procurements_by_category(
    category, limit=10, exclude_ids=ids_1
)

print(f"取得 {len(tenders_2)} 筆")
ids_2 = []
for i, t in enumerate(tenders_2, 1):
    tid = t.get('tender_id', '')
    org = t.get('org_name', '')[:25]
    budget = t.get('budget_text', '')
    ids_2.append(tid)
    print(f"  {i}. {tid[:20]}... ({budget}) - {org}")

# 檢查重複
overlap = set(ids_1) & set(ids_2)

print(f"\n\n結果分析：")
print(f"  第一批: {len(ids_1)} 個ID")
print(f"  第二批: {len(ids_2)} 個ID")
print(f"  重複: {len(overlap)} 個")

if len(overlap) > 0:
    print(f"\n❌ 錯誤！發現重複的ID:")
    for dup in overlap:
        print(f"     - {dup}")
else:
    print(f"\n✅ 正確！沒有重複")

print("=" * 80)
