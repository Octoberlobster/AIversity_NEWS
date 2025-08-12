import ChatRoom
import Hint_Prompt
from flask_cors import CORS
from flask import Flask, request, jsonify


app = Flask(__name__)
CORS(app)

#目前想到問題，同個使用者的情況下，換看的新聞會有上次聊天的history，ChatRoom的實作要改為class

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json  # 取得前端傳來的 JSON
    prompt = data.get("prompt")
    categories = data.get("category")
    Hint_Prompt.refresh_hint_prompt()

    if not prompt:
        return jsonify({"error": "Missing 'prompt'"}), 400

    try:
        # 呼叫 Gemini 模型
        response = ChatRoom.chat(prompt, categories)
        print(jsonify({"response": response}))
        return jsonify({"response": response})
    except Exception as e:
        print(f"Error: {e}")
        print("fuck yourself")
        return jsonify({"error": str(e)}), 500

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
