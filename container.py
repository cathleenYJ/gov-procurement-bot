"""
容器設定 - 管理依賴注入和服務創建
現已更新為政府採購資料爬蟲
"""

from procurement_processors import ProcurementProcessor
from clients.procurement_client import ProcurementClient

class ProcurementBotContainer:
    """政府採購機器人的依賴注入容器"""
    
    def __init__(self):
        """初始化容器"""
        self._procurement_client = None
        self._procurement_processor = None

    def create_procurement_client(self) -> ProcurementClient:
        """創建政府採購客戶端"""
        if self._procurement_client is None:
            self._procurement_client = ProcurementClient()
        return self._procurement_client

    def create_procurement_processor(self) -> ProcurementProcessor:
        """創建政府採購處理器"""
        if self._procurement_processor is None:
            self._procurement_processor = ProcurementProcessor()
        return self._procurement_processor

# 使用示例
if __name__ == "__main__":
    container = ProcurementBotContainer()
    processor = container.create_procurement_processor()

    # 測試政府採購資料獲取
    procurements = processor.get_latest_procurements(limit=5)
    print(f"獲取到 {len(procurements)} 筆政府採購資料")