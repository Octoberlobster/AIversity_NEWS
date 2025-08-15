import Hint_Prompt
import Knowledge_Base
from flask_cors import CORS
from flask import Flask, request, jsonify
from ChatRoom import ChatRoom
#這邊讀檔要改成database抓
Knowledge_Base.set_knowledge_base("./demo/news-platform/back-end/cleaned_final_news.json")

app = Flask(__name__)
CORS(app)
user_sessions = {}

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json  # 取得前端傳來的 JSON
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    prompt = data.get("prompt")
    categories = data.get("category")
    article = data.get("article")
    Hint_Prompt.refresh_hint_prompt()

    if not user_id or not room_id or not prompt or not categories:
        return jsonify({"error": "Missing required fields"}), 400
    
    key = (user_id, room_id)
    if key not in user_sessions:
        user_sessions[key] = ChatRoom()
    room = user_sessions[key]

    prompt = f"目前正在閱讀的文章是：{article}，請根據這篇文章回答使用者。以下是使用者的提問：{prompt}"

    response = room.chat(prompt, categories)
    print(response)
    return jsonify({"response": response})

@app.route("/api/hint_prompt", methods=["POST"])
def hint_Prompt():
    data = request.json
    option = data.get("option")
    article = data.get("article")
    if not option or not article:
        return jsonify({"error": "Missing 'option' or 'article'"}), 400
    try:
        response = Hint_Prompt.genernate_hint_prompt(tuple(option), article)
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        print("fuck myself")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)