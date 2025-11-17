"""
測試「更多標案」是否返回不同的資料
優先抓取當天資料的策略
"""

from procurement_processors import ProcurementProcessor
from datetime import datetime

def roc_to_ad_date(roc_date: str) -> str:
    """將民國年轉換為西元年"""
    try:
        parts = roc_date.split('/')
        if len(parts) == 3:
            year = int(parts[0]) + 1911
            return f"{year}/{parts[1]}/{parts[2]}"
    except:
        pass
    return roc_date

def test_different_tenders():
    print("=" * 80)
    print("🧪 測試「更多標案」功能 - 驗證當天資料優先策略")
    print("=" * 80)
    
    processor = ProcurementProcessor()
    category = "工程類"
    
    # 第一次查詢：10筆
    print(f"\n📋 第一次查詢：{category} - 10筆")
    print("-" * 80)
    tenders_1 = processor.get_procurements_by_category(category, limit=10)
    
    if not tenders_1:
        print("❌ 沒有查詢到資料")
        return
    
    print(f"✅ 取得 {len(tenders_1)} 筆標案")
    print(f"\n前 5 筆：")
    for i, tender in enumerate(tenders_1[:5], 1):
        name = tender.get('tender_name', '未知')[:50] or f"標案ID: {tender.get('tender_id', '未知')}"
        org = tender.get('org_name', '未知')[:25]
        date = roc_to_ad_date(tender.get('announcement_date', '未知'))
        print(f"   {i}. [{date}] {name}... ({org})")
    
    # 收集第一批的標案ID
    ids_1 = set()
    for t in tenders_1:
        tender_id = t.get('tender_id', '') or t.get('tender_name', '')
        ids_1.add(tender_id)
    
    # 統計第一批的日期分布
    dates_1 = {}
    for t in tenders_1:
        date = roc_to_ad_date(t.get('announcement_date', '未知'))
        dates_1[date] = dates_1.get(date, 0) + 1
    
    print(f"\n第一批日期分布：")
    for date, count in sorted(dates_1.items(), reverse=True):
        print(f"   {date}: {count} 筆")
    
    # 第二次查詢：50筆（模擬點擊「更多標案」）
    print(f"\n\n📋 第二次查詢：{category} - 50筆（模擬點擊「更多標案」）")
    print("-" * 80)
    tenders_2 = processor.get_procurements_by_category(category, limit=50)
    
    if not tenders_2:
        print("❌ 沒有查詢到資料")
        return
    
    print(f"✅ 取得 {len(tenders_2)} 筆標案")
    
    # 統計第二批的日期分布
    dates_2 = {}
    for t in tenders_2:
        date = roc_to_ad_date(t.get('announcement_date', '未知'))
        dates_2[date] = dates_2.get(date, 0) + 1
    
    print(f"\n第二批日期分布：")
    for date, count in sorted(dates_2.items(), reverse=True):
        print(f"   {date}: {count} 筆")
    
    # 收集第二批的標案ID
    ids_2 = set()
    for t in tenders_2:
        tender_id = t.get('tender_id', '') or t.get('tender_name', '')
        ids_2.add(tender_id)
    
    # 分析重疊情況
    overlap_ids = ids_1 & ids_2
    unique_in_2 = ids_2 - ids_1
    
    print(f"\n" + "=" * 80)
    print("📊 結果分析")
    print("=" * 80)
    print(f"第一批標案數量：{len(tenders_1)}")
    print(f"第二批標案數量：{len(tenders_2)}")
    print(f"重複的標案：{len(overlap_ids)} 筆 ({len(overlap_ids)/len(tenders_1)*100:.1f}%)")
    print(f"第二批中的新標案：{len(unique_in_2)} 筆 ({len(unique_in_2)/len(tenders_2)*100:.1f}%)")
    
    # 測試過濾機制（模擬實際使用情境）
    print(f"\n\n🔍 模擬實際使用：過濾已看過的標案")
    print("-" * 80)
    
    # 從第二批中過濾掉第一批已看過的
    new_tenders = []
    for tender in tenders_2:
        tender_id = tender.get('tender_id', '') or tender.get('tender_name', '')
        if tender_id not in ids_1:
            new_tenders.append(tender)
            if len(new_tenders) >= 10:  # 只要10筆新的
                break
    
    print(f"已看過的標案：{len(ids_1)} 筆")
    print(f"過濾後的新標案：{len(new_tenders)} 筆")
    
    if new_tenders:
        print(f"\n過濾後的前 5 筆（這些是用戶點擊「更多標案」會看到的）：")
        for i, tender in enumerate(new_tenders[:5], 1):
            name = tender.get('tender_name', '未知')[:50] or f"標案ID: {tender.get('tender_id', '未知')}"
            org = tender.get('org_name', '未知')[:25]
            date = roc_to_ad_date(tender.get('announcement_date', '未知'))
            print(f"   {i}. [{date}] {name}... ({org})")
        
        # 統計新標案的日期分布
        new_dates = {}
        for t in new_tenders:
            date = roc_to_ad_date(t.get('announcement_date', '未知'))
            new_dates[date] = new_dates.get(date, 0) + 1
        
        print(f"\n新標案日期分布：")
        for date, count in sorted(new_dates.items(), reverse=True):
            print(f"   {date}: {count} 筆")
    
    # 驗證當天資料優先策略
    print(f"\n\n✨ 驗證「當天資料優先」策略")
    print("-" * 80)
    
    today = datetime.now().strftime("%Y/%m/%d")
    
    # 找出第二批中最多的日期（應該是當天或最近的日期）
    most_common_date = max(dates_2.items(), key=lambda x: x[1])[0] if dates_2 else None
    
    print(f"今天日期：{today}")
    print(f"第二批最多的日期：{most_common_date} ({dates_2.get(most_common_date, 0)} 筆)")
    
    if new_tenders:
        new_most_common_date = max(new_dates.items(), key=lambda x: x[1])[0] if new_dates else None
        print(f"新標案最多的日期：{new_most_common_date} ({new_dates.get(new_most_common_date, 0)} 筆)")
        
        # 檢查新標案是否優先來自同一天
        if new_most_common_date == most_common_date:
            print(f"✅ 優先顯示當天資料策略有效！新標案優先來自 {most_common_date}")
    
    print(f"\n" + "=" * 80)
    if len(new_tenders) >= 10:
        print("🎉 測試通過！「更多標案」功能正常運作")
        print("✅ 能夠提供不重複的新標案")
        if new_tenders and new_most_common_date == most_common_date:
            print(f"✅ 優先返回 {most_common_date} 的資料")
    else:
        print(f"⚠️  新標案數量不足：只有 {len(new_tenders)} 筆")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    test_different_tenders()
