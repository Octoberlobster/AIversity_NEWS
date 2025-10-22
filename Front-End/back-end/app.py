import Hint_Prompt_Search
import Advanced_Search_Service
from flask_cors import CORS
from flask import Flask, request, jsonify
from ChatRoom import ChatRoom
from Hint_Prompt_Single import Hint_Prompt_Single
from Hint_Prompt_Topic import Hint_Prompt_Topic
import Change_experts 
import Change_experts_Topic 
import uuid             

app = Flask(__name__)
CORS(app)
user_sessions = {}

@app.route("/api/chat/single", methods=["POST"])
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

@app.route("/api/hint_prompt/single", methods=["POST"])
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
    
@app.route("/api/chat/search", methods=["POST"])
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

@app.route("/api/hint_prompt/search", methods=["POST"])
def hint_Prompt_search():
    try:
        response = Hint_Prompt_Search.generate_hint_prompt()
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        print("fuck me right now")
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat/topic", methods=["POST"])
def chat_topic():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    topic_id = data.get("topic_id")
    prompt = data.get("prompt")
    categories = data.get("category")

    if not user_id or not room_id or not topic_id or not prompt:
        return jsonify({"error": "Missing required fields"}), 400

    key = (user_id, room_id,"chat_topic")
    if key not in user_sessions:
        user_sessions[key] = ChatRoom()
    room = user_sessions[key]

    try:
        response = room.chat(prompt, categories, topic_id,topic_flag = True)
        if user_sessions[(user_id,room_id,"hint_prompt_topic")]:
            user_sessions[(user_id,room_id,"hint_prompt_topic")].refresh_hint_prompt()
        return jsonify({"response": response})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/hint_prompt/topic", methods=["POST"])
def hint_prompt_topic():
    data = request.json
    topic_id = data.get("topic_id")
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    option = data.get("option")
    chat_content = data.get("chat_content")
    if not topic_id or not user_id or not room_id:
        return jsonify({"error": "Missing 'topic_id', 'user_id' or 'room_id'"}), 400

    key = (user_id, room_id,"hint_prompt_topic")
    if key not in user_sessions:
        user_sessions[key] = Hint_Prompt_Topic()
        user_sessions[key].chat_content = chat_content or ""
    else:
        user_sessions[key].append_to_chat_content(chat_content or "")
    generator = user_sessions[key]
    generator.topic_id = topic_id


    try:
        response = generator.generate_hint_prompt(tuple(option), topic_id, generator.chat_content)
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/Advanced_Search_Service/search",methods=["POST"])
def advanced_search():
    data = request.json
    query = data.get("query")
    try:
        response = Advanced_Search_Service.search(query)
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/experts/change", methods=["POST"])
def change_experts_route():
    data = request.json
    
    # 1. 解析前端傳來的必要欄位
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    story_id = data.get("story_id")
    language = data.get("language")
    current_experts = data.get("current_experts") # 初始的專家列表
    experts_to_regenerate = data.get("experts_to_regenerate") # 要換掉的專家

    # 2. 基礎欄位驗證
    if not all([user_id, room_id, story_id, language, current_experts, experts_to_regenerate]):
        error_payload = {"success": False, "error": "Missing required fields", "error_code": "400"}
        return jsonify({"success_response": None, "error_response": error_payload}), 400

    # 3. 驗證是否"只換一個"
    if len(experts_to_regenerate) != 1:
        error_payload = {"success": False, "error": "Must regenerate exactly one expert per call", "error_code": "400"}
        return jsonify({"success_response": None, "error_response": error_payload}), 400

    try:
        target = experts_to_regenerate[0]
        target_category = target.get("category")
        old_analyze_id = target.get("analyze_id")

        if not target_category or not old_analyze_id:
            error_payload = {"success": False, "error": "Invalid 'experts_to_regenerate' structure", "error_code": "400"}
            return jsonify({"success_response": None, "error_response": error_payload}), 400

        # 4. Session 管理 (使用 story_id 確保 session 是針對特定文章的)
        key = (user_id, room_id, story_id, "expert_regenerator")

        if key not in user_sessions:
            # 如果是第一次請求，建立新的 Regenerator 實例並儲存
            user_sessions[key] = Change_experts.ExpertRegenerator(current_experts, story_id)
        
        generator = user_sessions[key]

        # 5. 呼叫 chat model 產生新專家
        # new_analyze_obj 是一個 NewExpertResponse Pydantic 物件 (包含 Role 和 Analyze)
        new_analyze_obj = generator.regenerate_one_expert(language, target_category)

        # 6. 構建成功回傳格式
        new_id = str(uuid.uuid4())
        response_expert = {
            "analyze_id": new_id,
            "category": target_category,
            "analyze": {
                "Role": new_analyze_obj.Role,
                "Analyze": new_analyze_obj.Analyze
            }
        }

        success_payload = {
            "success": True,
            "experts": [response_expert],
            "replaced_ids": [old_analyze_id]
        }
        
        return jsonify({"success_response": success_payload, "error_response": None})

    except Exception as e:
        # 捕捉 Pydantic 驗證錯誤或 Gemini API 錯誤
        error_payload = {"success": False, "error": str(e), "error_code": "500"}
        return jsonify({"success_response": None, "error_response": error_payload}), 500

@app.route("/api/experts/change_topic", methods=["POST"])
def change_experts_topic_route():
    data = request.json
    
    # 1. 解析前端傳來的必要欄位
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    topic_id = data.get("topic_id") # <-- 修改
    language = data.get("language")
    current_experts = data.get("current_experts") # 初始的專家列表
    experts_to_regenerate = data.get("experts_to_regenerate") # 要換掉的專家

    # 2. 基礎欄位驗證
    if not all([user_id, room_id, topic_id, language, current_experts, experts_to_regenerate]): # <-- 修改
        error_payload = {"success": False, "error": "Missing required fields", "error_code": "400"}
        return jsonify({"success_response": None, "error_response": error_payload}), 400

    # 3. 驗證是否"只換一個"
    if len(experts_to_regenerate) != 1:
        error_payload = {"success": False, "error": "Must regenerate exactly one expert per call", "error_code": "400"}
        return jsonify({"success_response": None, "error_response": error_payload}), 400

    try:
        target = experts_to_regenerate[0]
        target_category = target.get("category")
        old_analyze_id = target.get("analyze_id")

        if not target_category or not old_analyze_id:
            error_payload = {"success": False, "error": "Invalid 'experts_to_regenerate' structure", "error_code": "400"}
            return jsonify({"success_response": None, "error_response": error_payload}), 400

        # 4. Session 管理 (使用 topic_id 確保 session 是針對特定專題的)
        key = (user_id, room_id, topic_id, "topic_expert_regenerator") # <-- 修改 key

        if key not in user_sessions:
            # 如果是第一次請求，建立新的 Regenerator 實例並儲存
            user_sessions[key] = Change_experts_Topic.TopicExpertRegenerator(current_experts, topic_id) # <-- 修改 Class
        
        generator = user_sessions[key]

        # 5. 呼叫 chat model 產生新專家
        new_analyze_obj = generator.regenerate_one_expert(language, target_category)

        # 6. 構建成功回傳格式
        new_id = str(uuid.uuid4())
        response_expert = {
            "analyze_id": new_id,
            "category": target_category,
            "analyze": {
                "Role": new_analyze_obj.Role,
                "Analyze": new_analyze_obj.Analyze
            }
        }

        success_payload = {
            "success": True,
            "experts": [response_expert],
            "replaced_ids": [old_analyze_id]
        }
        
        return jsonify({"success_response": success_payload, "error_response": None})

    except Exception as e:
        # 捕捉 Pydantic 驗證錯誤或 Gemini API 錯誤
        error_payload = {"success": False, "error": str(e), "error_code": "500"}
        return jsonify({"success_response": None, "error_response": error_payload}), 500
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
