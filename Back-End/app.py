from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import crawler_news  # 引入你的爬蟲腳本
import GenerateRoles
import json

app = Flask(__name__)
CORS(app)

@app.route('/get_news', methods=['GET'])
def get_news():
    news_data = crawler_news.crawl_news()
    #print(news_data)
    return jsonify(news_data)

@app.route('/get_roles', methods=['POST'])
def get_roles():
    news_data = request.get_json()
    if(news_data):
        roles_data = GenerateRoles.get_roles(news_data)
        #dict = {title,roles_data}
        print("roles_data:",roles_data)
        #dict轉換成json
        return jsonify(roles_data)
    else:
        return jsonify({"error": "No news data found"})
    


if __name__ == '__main__':
    app.run(debug=True)
