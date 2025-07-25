import ChatRoom
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json  # 取得前端傳來的 JSON
    prompt = data.get("prompt")
    categories = data.get("category")

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