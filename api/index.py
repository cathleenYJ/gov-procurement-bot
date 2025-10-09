#!/usr/bin/env python3
import sys
import os

# 添加父目錄到 Python 路徑，以便正確導入模塊
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procurement_bot import create_app

app = create_app()

if __name__ == "__main__":
    # 生產環境設定 - Render 會自動設定 PORT
    port = int(os.environ.get("PORT", 5000))
    debug = False  # 生產環境一律關閉 debug

    app.run(host="0.0.0.0", port=port, debug=debug)