from flask import Flask, request, jsonify, render_template
import crawler_news  # 引入你的爬蟲腳本

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    keyword = request.json.get('keyword')  # 從請求中獲取前端傳來的資料
    if not keyword:
        return jsonify({"status": "error", "message": "請輸入關鍵字"}), 400

    try:
        # 調用爬蟲腳本並獲取結果
        news_results = crawler_news.crawl_news(keyword)  # 修改爬蟲腳本來接受關鍵字
        return jsonify({"status": "success", "news": news_results})  # 將爬取結果返回
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/news', methods=['POST'])
def get_news():
    # 從前端的 POST 請求中獲取新聞資料
    news_data = request.json
    if not news_data:
        return "<h1>400 Bad Request</h1><p>缺少新聞資料。</p>", 400

    # 動態生成 HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{news_data['Title']}</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <h1>{news_data['Title']}</h1>
            <p>{news_data['Content']}</p>
            <a href="/" class="back-button">返回</a>
        </div>
    </body>
    </html>
    """
    return html


if __name__ == '__main__':
    app.run(debug=True)
