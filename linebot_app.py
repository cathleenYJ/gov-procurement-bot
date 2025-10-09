"""
政府採購Line Bot應用程式入口點
已從新聞機器人改造為政府採購資料查詢機器人
"""

from procurement_bot import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=8080)