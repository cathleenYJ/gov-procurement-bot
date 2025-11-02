#!/bin/bash

# 政府採購爬蟲 Line Bot 開發工具腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數定義
print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}  🏛️ 政府採購爬蟲 Line Bot 開發工具${NC}"
    echo -e "${BLUE}======================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 檢查虛擬環境
check_venv() {
    if [ ! -d "venv" ]; then
        print_error "虛擬環境不存在，請先運行 setup"
        exit 1
    fi
}

# 激活虛擬環境
activate_venv() {
    source venv/bin/activate
    print_success "虛擬環境已激活"
}

# 主要命令
case "$1" in
    "setup")
        print_header
        print_info "設定開發環境..."

        # 創建虛擬環境
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            print_success "虛擬環境已創建"
        else
            print_info "虛擬環境已存在"
        fi

        # 激活並安裝依賴
        activate_venv
        pip install -r requirements.txt
        print_success "依賴已安裝"

        # 檢查 .env 文件
        if [ ! -f ".env" ]; then
            cp .env.example .env
            print_info ".env 文件已創建，請編輯其中的配置"
        fi

        print_success "環境設定完成！"
        ;;

    "run")
        print_header
        check_venv
        activate_venv
        print_info "啟動本地開發服務器..."
        python procurement_bot.py
        ;;

    "test")
        print_header
        check_venv
        activate_venv
        print_info "運行政府採購功能測試..."
        python test_procurement.py
        print_success "功能測試完成"
        ;;

    "procurement")
        print_header
        check_venv
        activate_venv
        print_info "測試政府採購 API..."
        python -c "
from clients.procurement_client import ProcurementClient
client = ProcurementClient()
print('🔍 測試搜尋功能...')
results = client.search_tenders(tender_name='資訊', page_size=10)
print(f'✅ 找到 {len(results.get(\"data\", []))} 筆資料')
for i, tender in enumerate(results.get('data', [])[:3]):
    print(f'{i+1}. {tender.get(\"title\", \"未知標題\")}')
"
        print_success "採購 API 測試完成"
        ;;

    "bot")
        print_header
        check_venv
        activate_venv
        print_info "啟動政府採購 Line Bot..."
        echo "Bot 將運行在 http://localhost:5000"
        echo "測試端點：http://localhost:5000/test"
        echo "按 Ctrl+C 停止"
        python procurement_bot.py
        ;;

    "api")
        print_header
        check_venv
        activate_venv
        print_info "測試 API 端點..."
        
        python -c "
from procurement_bot import create_app

app = create_app()

@app.route('/')
def health():
    return {'status': 'ok', 'message': '政府採購爬蟲 API 運行中'}

print('測試健康檢查端點...')
with app.test_client() as client:
    response = client.get('/')
    data = response.get_json()
    if data and data.get('status') == 'ok':
        print('✅ 健康檢查通過')
    else:
        print('❌ 健康檢查失敗')
    
    print('測試採購資料端點...')
    response = client.get('/test')
    data = response.get_json()
    if data and data.get('status') == 'success':
        print(f'✅ 採購資料測試通過 - 獲取到 {data.get(\"data_count\", 0)} 筆資料')
        sample = data.get('sample_data', {})
        if sample:
            print(f'   樣本：{sample.get(\"tender_name\", \"無標題\")} - {sample.get(\"org_name\", \"未知機關\")}')
    else:
        print(f'❌ 採購資料測試失敗: {data.get(\"message\", \"未知錯誤\") if data else \"無回應\"}')
"
        print_success "API 測試完成"
        ;;

    "linebot")
        print_header
        check_venv
        activate_venv
        print_info "測試 Line Bot 模組載入..."
        python -c "
from procurement_bot import create_app
print('✅ Line Bot 模組載入成功')
app = create_app()
print('✅ Flask 應用建立成功')
print('✅ Line Bot 準備就緒')
"
        print_success "Line Bot 測試完成"
        ;;

    "clean")
        print_header
        print_info "清理臨時文件..."
        rm -rf __pycache__
        rm -rf .pytest_cache
        rm -rf *.pyc
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
        print_success "清理完成"
        ;;

    "deps")
        print_header
        check_venv
        activate_venv
        print_info "檢查依賴..."
        pip list --outdated
        ;;

    "help"|*)
        print_header
        echo "使用方法: $0 <command>"
        echo ""
        echo "🏛️ 政府採購爬蟲功能:"
        echo "  test        運行政府採購功能完整測試"
        echo "  procurement 測試政府採購 API 連線"
        echo "  bot         啟動政府採購 Line Bot"
        echo "  api         測試 API 端點"
        echo "  linebot     測試 Line Bot 模組載入"
        echo ""
        echo "⚙️ 系統管理:"
        echo "  setup       設定開發環境（創建虛擬環境，安裝依賴）"
        echo "  run         運行本地開發服務器（舊版）"
        echo "  clean       清理臨時文件"
        echo "  deps        檢查依賴更新"
        echo "  help        顯示此幫助信息"
        echo ""
        echo "💡 快速開始:"
        echo "  1. $0 setup        # 設定環境"
        echo "  2. 編輯 .env 設定 Line Bot 憑證"
        echo "  3. $0 linebot      # 測試模組"
        echo "  4. $0 bot          # 啟動 Bot"
        echo ""
        echo "📖 詳細說明請參考 LINEBOT_GUIDE.md"
        ;;
esac