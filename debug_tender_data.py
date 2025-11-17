"""
檢查標案資料結構，找出正確的日期欄位
"""

from procurement_processors import ProcurementProcessor
import json

processor = ProcurementProcessor()
category = "工程類"

print("=" * 80)
print("🔍 檢查標案資料結構")
print("=" * 80)

tenders = processor.get_procurements_by_category(category, limit=1)

if tenders:
    print(f"\n✅ 取得 {len(tenders)} 筆標案\n")
    print("完整資料結構：")
    print("-" * 80)
    print(json.dumps(tenders[0], indent=2, ensure_ascii=False))
else:
    print("❌ 沒有查詢到資料")
