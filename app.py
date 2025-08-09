import ChatRoom
import Hint_Prompt
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
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
        reply = dict(response)
        print(jsonify({"response": reply}))
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/hint_prompt", methods=["POST"])
def Hint_Prompt():
    data = request.json
    option = data.get("option")
    article = data.get("article")
    if not option or not article:
        return jsonify({"error": "Missing 'option' or 'article'"}), 400
    try:
        response = Hint_Prompt.genernate_hint_prompt(tuple(option), article)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500