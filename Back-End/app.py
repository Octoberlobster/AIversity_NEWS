from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import crawler_news  # 引入你的爬蟲腳本

app = Flask(__name__)
CORS(app)

@app.route('/get_news', methods=['GET'])
def get_news():
    news_data = crawler_news.crawl_news()
    #print(news_data)
    return jsonify(news_data)




if __name__ == '__main__':
    app.run(debug=True)
