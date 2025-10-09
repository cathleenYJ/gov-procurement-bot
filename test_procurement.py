#!/usr/bin/env python3
"""
政府採購爬蟲測試腳本
用於測試政府採購資料獲取功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from procurement_processors import ProcurementProcessor
from clients.procurement_client import ProcurementClient

def test_procurement_client():
    """測試政府採購客戶端"""
    print("=" * 50)
    print("測試政府採購客戶端")
    print("=" * 50)
    
    client = ProcurementClient()
    
    try:
        # 測試基本搜尋
        print("1. 測試基本搜尋（當日工程類）...")
        result = client.search_tenders(
            page_size=5,
            date_type="isNow",
            procurement_nature="RAD_PROCTRG_CATE_1"
        )
        
        if result.get('success'):
            print(f"   ✓ 成功獲取 {len(result.get('data', []))} 筆資料")
            if result.get('data'):
                sample = result['data'][0]
                print(f"   樣本資料：{sample.get('tender_name', 'N/A')[:50]}...")
        else:
            print(f"   ✗ 搜尋失敗：{result.get('error', '未知錯誤')}")
            
    except Exception as e:
        print(f"   ✗ 測試失敗：{e}")

def test_procurement_processor():
    """測試政府採購處理器"""
    print("\n" + "=" * 50)
    print("測試政府採購處理器")
    print("=" * 50)
    
    processor = ProcurementProcessor()
    
    try:
        # 測試獲取最新採購
        print("1. 測試獲取最新採購...")
        tenders = processor.get_latest_procurements(limit=3)
        print(f"   ✓ 獲取到 {len(tenders)} 筆採購資料")
        
        if tenders:
            print("   採購案例：")
            for i, tender in enumerate(tenders[:2], 1):
                print(f"   {i}. {tender.get('tender_name', 'N/A')[:40]}...")
                print(f"      機關：{tender.get('org_name', 'N/A')}")
                print(f"      金額：{tender.get('budget_amount', 0):,}")
        
        # 測試關鍵字搜尋
        print("\n2. 測試關鍵字搜尋（搜尋'資訊系統'）...")
        search_tenders = processor.search_procurements_by_keywords(["資訊系統"], limit=2)
        print(f"   ✓ 搜尋到 {len(search_tenders)} 筆相關資料")
        
        # 測試格式化
        print("\n3. 測試訊息格式化...")
        if tenders:
            formatted = processor.format_multiple_tenders(tenders[:2], "測試採購資訊")
            print("   ✓ 格式化成功")
            print("   格式化結果：")
            print("   " + "\n   ".join(formatted.split("\n")[:5]) + "...")
        
        # 測試統計
        print("\n4. 測試統計資訊...")
        stats = processor.get_procurement_statistics()
        if stats:
            print(f"   ✓ 統計成功")
            print(f"   今日標案：{stats.get('today_count', 0)} 筆")
            print(f"   本週標案：{stats.get('week_count', 0)} 筆")
        else:
            print("   ⚠ 統計資料為空")
            
    except Exception as e:
        print(f"   ✗ 測試失敗：{e}")

def test_keyword_search():
    """測試關鍵字搜尋功能"""
    print("\n" + "=" * 50)
    print("測試關鍵字搜尋功能")
    print("=" * 50)
    
    processor = ProcurementProcessor()
    
    keywords_to_test = ["AI", "資訊", "系統", "工程"]
    
    for keyword in keywords_to_test:
        try:
            print(f"搜尋關鍵字：'{keyword}'")
            results = processor.search_procurements_by_keywords([keyword], limit=2)
            print(f"   ✓ 找到 {len(results)} 筆相關資料")
            
            if results:
                for i, tender in enumerate(results, 1):
                    print(f"   {i}. {tender.get('tender_name', 'N/A')[:30]}...")
                    
        except Exception as e:
            print(f"   ✗ 搜尋 '{keyword}' 失敗：{e}")

def main():
    """主測試函數"""
    print("政府採購爬蟲功能測試")
    print("開始時間：", str(os.popen('date').read()).strip())
    
    try:
        test_procurement_client()
        test_procurement_processor()
        test_keyword_search()
        
        print("\n" + "=" * 50)
        print("測試完成！")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n測試被中斷")
    except Exception as e:
        print(f"\n測試過程中發生錯誤：{e}")

if __name__ == "__main__":
    main()