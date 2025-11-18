#!/usr/bin/env python3
"""
Supabase 資料庫資料匯出工具
將所有資料表匯出為 CSV 檔案
"""

import os
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseDataExporter:
    """Supabase 資料匯出器"""

    def __init__(self):
        """初始化匯出器"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("請在 .env 文件中設置 SUPABASE_URL 和 SUPABASE_KEY")

        # 移除 URL 結尾的斜槓
        self.supabase_url = self.supabase_url.rstrip('/')

        # 設定 API headers
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }

        logger.info("Supabase 匯出器初始化完成")

    def get_table_data(self, table_name: str, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        從 Supabase 取得資料表資料

        Args:
            table_name: 資料表名稱
            limit: 最大取得筆數

        Returns:
            list: 資料列表
        """
        try:
            url = f"{self.supabase_url}/rest/v1/{table_name}"
            params = {
                'select': '*',
                'limit': limit
            }

            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(f"從 {table_name} 取得 {len(data)} 筆資料")
            return data

        except Exception as e:
            logger.error(f"取得 {table_name} 資料時發生錯誤: {e}")
            return []

    def export_table_to_csv(self, table_name: str, output_dir: str = 'exports') -> str:
        """
        將資料表匯出為 CSV 檔案

        Args:
            table_name: 資料表名稱
            output_dir: 輸出目錄

        Returns:
            str: CSV 檔案路徑
        """
        # 建立輸出目錄
        os.makedirs(output_dir, exist_ok=True)

        # 取得資料
        data = self.get_table_data(table_name)

        if not data:
            logger.warning(f"{table_name} 沒有資料，跳過匯出")
            return ""

        # 產生檔案名稱
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{table_name}_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)

        # 取得所有欄位名稱
        if data:
            fieldnames = list(data[0].keys())
        else:
            fieldnames = []

        # 寫入 CSV
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"成功匯出 {table_name} 到 {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"匯出 {table_name} 時發生錯誤: {e}")
            return ""

    def export_all_tables(self, output_dir: str = 'exports') -> Dict[str, str]:
        """
        匯出所有資料表

        Args:
            output_dir: 輸出目錄

        Returns:
            dict: 資料表名稱 -> CSV 檔案路徑的映射
        """
        # 定義要匯出的資料表和視圖
        tables_and_views = [
            # 主要資料表
            'users',
            'user_query_logs',
            'tender_views',
            'user_browsing_state',
            'user_activity_stats',
            # 分析視圖
            'daily_query_stats',
            'user_activity_ranking',
            'popular_tenders'
        ]

        results = {}

        logger.info("開始匯出所有資料表...")

        for table_name in tables_and_views:
            filepath = self.export_table_to_csv(table_name, output_dir)
            if filepath:
                results[table_name] = filepath

        logger.info(f"匯出完成，共處理 {len(results)} 個資料表")
        return results

    def get_table_info(self) -> Dict[str, Dict[str, Any]]:
        """
        取得所有資料表的資訊

        Returns:
            dict: 資料表資訊
        """
        tables_and_views = [
            'users', 'user_query_logs', 'tender_views',
            'user_browsing_state', 'user_activity_stats',
            'daily_query_stats', 'user_activity_ranking', 'popular_tenders'
        ]

        info = {}

        for table_name in tables_and_views:
            data = self.get_table_data(table_name, limit=1)  # 只取一筆來看欄位
            if data:
                info[table_name] = {
                    'row_count': len(self.get_table_data(table_name)),
                    'columns': list(data[0].keys())
                }
            else:
                info[table_name] = {
                    'row_count': 0,
                    'columns': []
                }

        return info


def main():
    """主函數"""
    try:
        # 初始化匯出器
        exporter = SupabaseDataExporter()

        # 顯示資料表資訊
        print("📊 資料庫資料表資訊：")
        table_info = exporter.get_table_info()
        for table_name, info in table_info.items():
            print(f"  {table_name}: {info['row_count']} 筆資料，欄位: {', '.join(info['columns'])}")

        print("\n🚀 開始匯出資料...")

        # 匯出所有資料表
        results = exporter.export_all_tables()

        print("\n✅ 匯出完成！")
        print("📁 匯出的檔案：")
        for table_name, filepath in results.items():
            print(f"  {table_name} -> {filepath}")

        # 顯示總結
        total_files = len(results)
        print(f"\n📈 總計匯出 {total_files} 個 CSV 檔案")

    except Exception as e:
        logger.error(f"匯出過程發生錯誤: {e}")
        print(f"❌ 錯誤: {e}")


if __name__ == "__main__":
    main()