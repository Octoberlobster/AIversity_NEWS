import Hint_Prompt_Search
import Advanced_Search_Service
from flask_cors import CORS
from flask import Flask, request, jsonify
from ChatRoom import ChatRoom
from Hint_Prompt_Single import Hint_Prompt_Single
from Hint_Prompt_Topic import Hint_Prompt_Topic

app = Flask(__name__)
CORS(app)
user_sessions = {}

@app.route("/chat/single", methods=["POST"])
def chat():
    data = request.json  # 取得前端傳來的 JSON
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    prompt = data.get("prompt")
    categories = data.get("category")
    story_id = data.get("story_id")
    print(story_id)

    if not user_id or not room_id or not prompt or not categories or not story_id:
        return jsonify({"error": "Missing required fields"}), 400

    key = (user_id, room_id,"chat")
    if key not in user_sessions:
        user_sessions[key] = ChatRoom()
    room = user_sessions[key]

    if user_sessions[(user_id,room_id,"hint_prompt")]:
        user_sessions[(user_id,room_id,"hint_prompt")].refresh_hint_prompt()


    response = room.chat(prompt, categories,story_id)
    print(response)
    return jsonify({"response": response})

@app.route("/hint_prompt/single", methods=["POST"])
def hint_Prompt():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    option = data.get("option")
    article = data.get("article")
    chat_content = data.get("chat_content")

    if not user_id or not room_id or not option or not article:
        return jsonify({"error": "Missing required fields"}), 400

    # 確保每個 user_id 和 room_id 的組合都有一個 Hint_Prompt_Single 實例
    key = (user_id, room_id,"hint_prompt")
    if key not in user_sessions:
        user_sessions[key] = Hint_Prompt_Single(chat_content or "")
    else:
        # 如果實例已存在，追加新的聊天內容
        user_sessions[key].append_to_chat_content(chat_content or "")

    generator = user_sessions[key]

    try:
        # 調用 generate_hint_prompt 方法
        response = generator.generate_hint_prompt(tuple(option), article, generator.chat_content)
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/chat/search", methods=["POST"])
def chat_search():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    prompt = data.get("prompt")
    categories = data.get("category")

    if not user_id or not room_id or not prompt or not categories:
        return jsonify({"error": "Missing required fields"}), 400
    
    print("yews")

    key = (user_id, room_id,"chat")
    if key not in user_sessions:
        user_sessions[key] = ChatRoom()
    room = user_sessions[key]

    try:
        response = room.chat(prompt, categories)
        print(response)
        return jsonify({"response": response})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/hint_prompt/search", methods=["POST"])
def hint_Prompt_search():
    try:
        response = Hint_Prompt_Search.generate_hint_prompt()
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        print("fuck me right now")
        return jsonify({"error": str(e)}), 500

@app.route("/chat/topic", methods=["POST"])
def chat_topic():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    topic_id = data.get("topic_id")
    prompt = data.get("prompt")

    if not user_id or not room_id or not topic_id or not prompt:
        return jsonify({"error": "Missing required fields"}), 400

    key = (user_id, room_id,"chat")
    if key not in user_sessions:
        user_sessions[key] = ChatRoom()
    room = user_sessions[key]

    try:
        response = room.chat(prompt, ["topic"],topic_id)
        return jsonify({"response": response})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/hint_prompt/topic", methods=["POST"])
def hint_prompt_topic():
    data = request.json
    topic_id = data.get("topic_id")
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    chat_content = data.get("chat_content")
    if not topic_id or not user_id or not room_id:
        return jsonify({"error": "Missing 'topic_id', 'user_id' or 'room_id'"}), 400

    key = (user_id, room_id,"hint_prompt")
    if key not in user_sessions:
        user_sessions[key] = Hint_Prompt_Topic()
    generator = user_sessions[key]
    generator.topic_id = topic_id

    if not chat_content:
        prompt = "幫助使用者開始聊天"
    else:
        prompt = chat_content

    try:
        response = generator.generate_hint_prompt(prompt)
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/Advanced_Search_Service/search",methods=["POST"])
def advanced_search():
    data = request.json
    query = data.get("query")
    try:
        response = Advanced_Search_Service.search(query)
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)