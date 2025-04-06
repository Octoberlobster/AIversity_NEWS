import google.generativeai as genai
import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 啟用CORS以允許前端訪問

# 設定 API 金鑰
api_key = "YOUR_GEMINI_KEY"
genai.configure(api_key=api_key)

# 讀取新聞內容
with open("GenerateNews_EachEvent/news.json", "r", encoding="utf-8") as f:
    news_data = json.load(f)
content = news_data["Content"]

# 讀取角色信息
with open("Roles/Roles.json", "r", encoding="utf-8") as f:
    roles_data = json.load(f)

# 創建角色觀點字典，方便查詢
role_viewpoints = {role_info["Role"]: role_info["Viewpoint"] for role_info in roles_data["Roles"]}

# 聊天會話存儲
chat_sessions = {}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    role = data.get('role', '')
    message = data.get('message', '')
    
    if not role or not message:
        return jsonify({"error": "Missing role or message"}), 400
    
    # 檢查角色是否有效
    if role not in role_viewpoints:
        return jsonify({"error": "Invalid role"}), 400
    
    # 獲取或創建聊天會話
    if role not in chat_sessions:
        system_instruction = f"""
        你正在閱讀以下新聞：
        
        {content}
        
        你現在要扮演{role}。請以{role}的身份回應用戶的問題或評論。
        
        {role}的立場和觀點是：
        {role_viewpoints[role]}
        
        請以簡短的幾句話來進行對話式的回答，保持在{role}的角色中，並根據上述立場和觀點來回應。
        回答時根據用戶輸入的語言回應，並且要簡潔有力，每次回應不超過3-4句話。
        """
        
        model = genai.GenerativeModel('gemini-1.5-pro-002', system_instruction=system_instruction)
        chat_sessions[role] = model.start_chat()
    
    try:
        # 發送消息並獲取回覆
        response = chat_sessions[role].send_message(message)
        return jsonify({"response": response.text})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
