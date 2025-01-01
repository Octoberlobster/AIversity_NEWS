from flask import Flask, request, jsonify, render_template
import crawler_news  # 引入你的爬蟲腳本
import analysis_news  # 引入你的因果分析腳本

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
        news_results_df = crawler_news.crawl_news(keyword)# 修改爬蟲腳本來接受關鍵字
        news_results_df.to_csv('news_results.csv', index=False)
        news_results = news_results_df.to_dict(orient='records')
        return jsonify({"status": "success", "news": news_results})  # 將爬取結果返回
    except Exception as e:
        print(f"爬取新聞時出錯: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/read', methods=['POST'])
def read():
    try:
        clean_news = request.json.get('clean_news')
        if not clean_news:
            return jsonify({"status": "error", "message": "缺少新聞內容"}), 400
        analysis = analysis_news.analysis_news(clean_news)
        return jsonify({"status": "success", "analysis": analysis})
    except Exception as e:
        print(f"生成因果分析時出錯: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/news', methods=['POST'])
def get_news():
    # 從前端的 POST 請求中獲取新聞資料
    news_data = request.json
    content = format_content(news_data['Content'], max_length=100)
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
            <div id="content">
                {content} <!-- 格式化後的新聞內容 -->
            </div>
            <br>
            <button onclick="generateReport('{news_data['Content']}')">生成分析報告</button>
            <div id="analysis-container" class="analysis-container"></div> <!-- 用於顯示分析報告 -->
            <br>
            <a href="/" class="back-button">返回</a>
        </div>
    </body>
    </html>
    """
    return html

def format_content(content, max_length=100):
    """
    根據固定字數對新聞內容進行分段，並在段落之間加入空行。
    
    Args:
        content (str): 清洗後的新聞內容（無句號）。
        max_length (int): 每段最大字數。
    
    Returns:
        str: 格式化後的 HTML 內容。
    """
    # 按固定字數分段
    formatted_content = ""
    for i in range(0, len(content), max_length):
        segment = content[i:i + max_length].strip()
        if segment:  # 確保段落不為空
            formatted_content += f"<p>{segment}</p>\n"

    return formatted_content.strip()



if __name__ == '__main__':
    app.run(debug=True)
