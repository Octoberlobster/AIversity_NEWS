import logging
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

# 確保您的模組已正確導入
import Hint_Prompt_Search
import Advanced_Search_Service
from ChatRoom import ChatRoom
from Hint_Prompt_Single import Hint_Prompt_Single
from Hint_Prompt_Topic import Hint_Prompt_Topic
import Change_experts
import Change_experts_Topic
import country_pro_analyze
import media_literacy
from env import supabase

# --- Logging Setup ---
# It's good practice to configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# --- End Logging Setup ---


app = Flask(__name__)
CORS(app)
user_sessions = {} # Session storage for chat instances, hint generators, etc.

@app.route("/api/chat/single", methods=["POST"])
def chat():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    prompt = data.get("prompt")
    # <<< CHANGED: Expect 'categories_data' which is a list of dicts >>>
    categories_data = data.get("categories_data")
    story_id = data.get("story_id")
    language = data.get("language")

    logger.info(f"Received /api/chat/single request for story_id: {story_id}, user_id: {user_id}, room_id: {room_id}")
    # logger.debug(f"categories_data received: {categories_data}") # Optional: Log received data for debugging

    # <<< CHANGED: Validate 'categories_data' >>>
    if not all([user_id, room_id, prompt, story_id, language]) or not categories_data or not isinstance(categories_data, list):
        logger.warning("Missing or invalid required fields in /api/chat/single request.")
        return jsonify({"error": "Missing or invalid required fields (expecting categories_data as a list)"}), 400

    key = (user_id, room_id, "chat")
    if key not in user_sessions:
        logger.info(f"Creating new ChatRoom instance for key: {key}")
        user_sessions[key] = ChatRoom()
    room = user_sessions[key]

    # Optional: Refresh hint prompt cache if needed
    hint_key = (user_id, room_id, "hint_prompt")
    if hint_key in user_sessions and hasattr(user_sessions[hint_key], 'refresh_hint_prompt'):
        try:
            logger.info(f"Refreshing hint prompt cache for key: {hint_key}")
            user_sessions[hint_key].refresh_hint_prompt()
        except Exception as e_hint:
             logger.warning(f"Could not refresh hint prompt for {hint_key}: {e_hint}")


    try:
        logger.info(f"Calling ChatRoom.chat for single news with {len(categories_data)} expert(s).")
        # <<< CHANGED: Pass 'categories_data' directly >>>
        response = room.chat(prompt, categories_data, story_id, topic_flag=False, language=language)
        logger.info("ChatRoom.chat successful.")
        # logger.debug(f"Response from ChatRoom.chat: {response}") # Optional: Log detailed response
        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error during ChatRoom.chat for single news: {e}", exc_info=True) # Log full traceback
        return jsonify({"error": str(e)}), 500


@app.route("/api/hint_prompt/single", methods=["POST"])
def hint_Prompt():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    option = data.get("option") # This should be the list of categories selected
    article = data.get("article")
    chat_content = data.get("chat_content")
    language = data.get("language")

    logger.info(f"Received /api/hint_prompt/single request for user_id: {user_id}, room_id: {room_id}")

    if not user_id or not room_id or not option or not article or not language:
        logger.warning("Missing required fields in /api/hint_prompt/single request.")
        return jsonify({"error": "Missing required fields"}), 400

    key = (user_id, room_id, "hint_prompt")
    if key not in user_sessions:
         logger.info(f"Creating new Hint_Prompt_Single instance for key: {key}")
         user_sessions[key] = Hint_Prompt_Single(chat_content or "")
    else:
        # Append new chat content if the instance exists
        logger.info(f"Appending chat content for key: {key}")
        user_sessions[key].append_to_chat_content(chat_content or "")


    generator = user_sessions[key]

    try:
        # Ensure 'option' is a tuple for caching if it's expected by the function
        option_tuple = tuple(option) if isinstance(option, list) else option
        logger.info(f"Generating single hint prompt for options: {option_tuple}, language: {language}")
        response = generator.generate_hint_prompt(option_tuple, article, generator.chat_content, language=language)
        logger.info("Hint prompt generation successful.")
        # logger.debug(f"Hint prompt response: {response}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error generating single hint prompt: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/search", methods=["POST"])
def chat_search():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    prompt = data.get("prompt")
    categories = data.get("category") # Expecting ["search"]
    language = data.get("language")

    logger.info(f"Received /api/chat/search request for user_id: {user_id}, room_id: {room_id}")

    if not user_id or not room_id or not prompt or not categories or not language:
        logger.warning("Missing required fields in /api/chat/search request.")
        return jsonify({"error": "Missing required fields"}), 400

    # Validate that the category is indeed 'search' for this endpoint
    if not isinstance(categories, list) or categories != ["search"]:
        logger.warning(f"Invalid category for /api/chat/search: {categories}")
        return jsonify({"error": "Invalid category for search endpoint, expected ['search']"}), 400

    # Use a consistent key or a specific one for search chat
    key = (user_id, room_id, "chat_search") # Or reuse "chat" key: (user_id, room_id, "chat")
    if key not in user_sessions:
        logger.info(f"Creating new ChatRoom instance for key: {key} (search)")
        user_sessions[key] = ChatRoom()
    room = user_sessions[key]

    try:
        logger.info("Calling ChatRoom.chat for search.")
        # <<< MODIFIED: Construct categories_data for the 'search' case >>>
        search_category_data = [{"category": "search"}] # role/analyze not needed for search
        response = room.chat(prompt, search_category_data, id=None, topic_flag=False, language=language)
        logger.info("ChatRoom.chat successful for search.")
        # logger.debug(f"Response from ChatRoom.chat (search): {response}")
        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error during ChatRoom.chat for search: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/hint_prompt/search", methods=["POST"])
def hint_Prompt_search():
    data = request.json
    language = data.get("language")

    logger.info(f"Received /api/hint_prompt/search request for language: {language}")

    if not language:
        logger.warning("Missing language field in /api/hint_prompt/search request.")
        return jsonify({"error": "Missing required field: language"}), 400

    try:
        logger.info("Generating search hint prompt.")
        response = Hint_Prompt_Search.generate_hint_prompt(language=language)
        logger.info("Search hint prompt generation successful.")
        # logger.debug(f"Search hint prompt response: {response}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error generating search hint prompt: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/topic", methods=["POST"])
def chat_topic():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    topic_id = data.get("topic_id")
    prompt = data.get("prompt")
    # <<< CHANGED: Expect 'categories_data' >>>
    categories_data = data.get("categories_data")
    language = data.get("language")

    logger.info(f"Received /api/chat/topic request for topic_id: {topic_id}, user_id: {user_id}, room_id: {room_id}")
    # logger.debug(f"categories_data received: {categories_data}")

    # <<< CHANGED: Validate 'categories_data' >>>
    if not all([user_id, room_id, topic_id, prompt, language]) or not categories_data or not isinstance(categories_data, list):
        logger.warning("Missing or invalid required fields in /api/chat/topic request.")
        return jsonify({"error": "Missing or invalid required fields (expecting categories_data as a list)"}), 400

    key = (user_id, room_id, "chat_topic")
    if key not in user_sessions:
        logger.info(f"Creating new ChatRoom instance for key: {key}")
        user_sessions[key] = ChatRoom()
    room = user_sessions[key]

    try:
        logger.info(f"Calling ChatRoom.chat for topic with {len(categories_data)} expert(s).")
        # <<< CHANGED: Pass 'categories_data' directly >>>
        response = room.chat(prompt, categories_data, topic_id, topic_flag = True, language=language)

        # Optional: Refresh hint prompt cache if needed
        hint_key = (user_id, room_id, "hint_prompt_topic")
        if hint_key in user_sessions and hasattr(user_sessions[hint_key], 'refresh_hint_prompt'):
            try:
                logger.info(f"Refreshing topic hint prompt cache for key: {hint_key}")
                user_sessions[hint_key].refresh_hint_prompt()
            except Exception as e_hint:
                 logger.warning(f"Could not refresh topic hint prompt for {hint_key}: {e_hint}")

        logger.info("ChatRoom.chat successful for topic.")
        # logger.debug(f"Response from ChatRoom.chat (topic): {response}")
        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error during ChatRoom.chat for topic: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/hint_prompt/topic", methods=["POST"])
def hint_prompt_topic():
    data = request.json
    topic_id = data.get("topic_id")
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    option = data.get("option") # List of categories
    chat_content = data.get("chat_content")
    language = data.get("language")

    logger.info(f"Received /api/hint_prompt/topic request for topic_id: {topic_id}, user_id: {user_id}, room_id: {room_id}")

    if not topic_id or not user_id or not room_id or not language: # Option can be empty initially
        logger.warning("Missing required fields in /api/hint_prompt/topic request.")
        return jsonify({"error": "Missing 'topic_id', 'user_id', 'room_id', or 'language'"}), 400

    key = (user_id, room_id,"hint_prompt_topic")
    if key not in user_sessions:
        logger.info(f"Creating new Hint_Prompt_Topic instance for key: {key}")
        user_sessions[key] = Hint_Prompt_Topic() # Assuming Hint_Prompt_Topic doesn't need chat_content in constructor
        user_sessions[key].chat_content = chat_content or "" # Set it after creation
    else:
        logger.info(f"Appending chat content for key: {key}")
        user_sessions[key].append_to_chat_content(chat_content or "")

    generator = user_sessions[key]
    generator.topic_id = topic_id # Ensure topic_id is set/updated

    try:
        # Ensure 'option' is a tuple for caching
        option_tuple = tuple(option) if isinstance(option, list) else () # Use empty tuple if option is missing/not list
        logger.info(f"Generating topic hint prompt for options: {option_tuple}, language: {language}")
        response = generator.generate_hint_prompt(option_tuple, topic_id, generator.chat_content, language=language)
        logger.info("Topic hint prompt generation successful.")
        # logger.debug(f"Topic hint prompt response: {response}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error generating topic hint prompt: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/Advanced_Search_Service/search",methods=["POST"])
def advanced_search():
    data = request.json
    query = data.get("query")
    if not query:
        logger.warning("Missing query in /api/Advanced_Search_Service/search request.")
        return jsonify({"error": "Missing query field"}), 400

    logger.info(f"Received /api/Advanced_Search_Service/search request with query: '{query}'")
    try:
        response = Advanced_Search_Service.search(query)
        logger.info("Advanced search successful.")
        # logger.debug(f"Advanced search response: {response}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error during advanced search: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# --- Expert Change Routes (Remain largely the same, just logging added) ---
@app.route("/api/experts/change", methods=["POST"])
def change_experts_route():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    story_id = data.get("story_id")
    language = data.get("language")
    current_experts = data.get("current_experts")
    experts_to_regenerate = data.get("experts_to_regenerate")

    logger.info(f"Received /api/experts/change request for story_id: {story_id}, user_id: {user_id}")

    if not all([user_id, room_id, story_id, language, current_experts, experts_to_regenerate]):
        logger.warning("Missing required fields in /api/experts/change request.")
        error_payload = {"success": False, "error": "Missing required fields", "error_code": "400"}
        return jsonify({"success_response": None, "error_response": error_payload}), 400

    if len(experts_to_regenerate) != 1:
        logger.warning("Invalid number of experts to regenerate in /api/experts/change request.")
        error_payload = {"success": False, "error": "Must regenerate exactly one expert per call", "error_code": "400"}
        return jsonify({"success_response": None, "error_response": error_payload}), 400

    try:
        target = experts_to_regenerate[0]
        target_category_to_replace = target.get("category")
        old_analyze_id = target.get("analyze_id")

        if not target_category_to_replace or not old_analyze_id:
            logger.warning("Invalid 'experts_to_regenerate' structure in /api/experts/change request.")
            error_payload = {"success": False, "error": "Invalid 'experts_to_regenerate' structure", "error_code": "400"}
            return jsonify({"success_response": None, "error_response": error_payload}), 400

        key = (user_id, room_id, story_id, "expert_regenerator")

        if key not in user_sessions:
            logger.info(f"Creating new ExpertRegenerator instance for key: {key}")
            user_sessions[key] = Change_experts.ExpertRegenerator(current_experts, story_id)

        generator = user_sessions[key]

        logger.info(f"Regenerating single expert for category: {target_category_to_replace}")
        generation_result = generator.regenerate_one_expert(language, target_category_to_replace)

        new_analyze_obj = generation_result["new_expert"]
        new_category = generation_result["new_category"]

        new_id = str(uuid.uuid4())
        response_expert = {
            "analyze_id": new_id,
            "category": new_category,
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
        logger.info("Single expert regeneration successful.")
        return jsonify({"success_response": success_payload, "error_response": None})

    except Exception as e:
        logger.error(f"Error changing single expert: {e}", exc_info=True)
        error_payload = {"success": False, "error": str(e), "error_code": "500"}
        return jsonify({"success_response": None, "error_response": error_payload}), 500


@app.route("/api/experts/change_topic", methods=["POST"])
def change_experts_topic_route():
    data = request.json
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    topic_id = data.get("topic_id")
    language = data.get("language")
    current_experts = data.get("current_experts")
    experts_to_regenerate = data.get("experts_to_regenerate")

    logger.info(f"Received /api/experts/change_topic request for topic_id: {topic_id}, user_id: {user_id}")

    if not all([user_id, room_id, topic_id, language, current_experts, experts_to_regenerate]):
        logger.warning("Missing required fields in /api/experts/change_topic request.")
        error_payload = {"success": False, "error": "Missing required fields", "error_code": "400"}
        return jsonify({"success_response": None, "error_response": error_payload}), 400

    if len(experts_to_regenerate) != 1:
        logger.warning("Invalid number of experts to regenerate in /api/experts/change_topic request.")
        error_payload = {"success": False, "error": "Must regenerate exactly one expert per call", "error_code": "400"}
        return jsonify({"success_response": None, "error_response": error_payload}), 400

    try:
        target = experts_to_regenerate[0]
        target_category_to_replace = target.get("category")
        old_analyze_id = target.get("analyze_id")

        if not target_category_to_replace or not old_analyze_id:
             logger.warning("Invalid 'experts_to_regenerate' structure in /api/experts/change_topic request.")
             error_payload = {"success": False, "error": "Invalid 'experts_to_regenerate' structure", "error_code": "400"}
             return jsonify({"success_response": None, "error_response": error_payload}), 400

        key = (user_id, room_id, topic_id, "topic_expert_regenerator")

        if key not in user_sessions:
            logger.info(f"Creating new TopicExpertRegenerator instance for key: {key}")
            user_sessions[key] = Change_experts_Topic.TopicExpertRegenerator(current_experts, topic_id)

        generator = user_sessions[key]

        logger.info(f"Regenerating topic expert for category: {target_category_to_replace}")
        # Assuming regenerate_one_expert in Change_experts_Topic also returns a dict like {"new_expert": ..., "new_category": ...}
        generation_result = generator.regenerate_one_expert(language, target_category_to_replace)

        new_analyze_obj = generation_result["new_expert"]
        new_category = generation_result["new_category"]

        new_id = str(uuid.uuid4())
        response_expert = {
            "analyze_id": new_id,
            "category": new_category,
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
        logger.info("Topic expert regeneration successful.")
        return jsonify({"success_response": success_payload, "error_response": None})

    except Exception as e:
        logger.error(f"Error changing topic expert: {e}", exc_info=True)
        error_payload = {"success": False, "error": str(e), "error_code": "500"}
        return jsonify({"success_response": None, "error_response": error_payload}), 500


@app.route("/api/experts/feedback", methods=["POST"])
def expert_feedback():
    """
    接收專家分析反饋（有益/無益），並更新資料庫中的計數
    """
    data = request.json
    analyze_id = data.get("analyze_id")
    feedback_type = data.get("feedback_type")  # "useful" or "useless"

    logger.info(f"Received /api/experts/feedback request for analyze_id: {analyze_id}, feedback_type: {feedback_type}")

    # 驗證必要欄位
    if not analyze_id or not feedback_type:
        logger.warning("Missing required fields in /api/experts/feedback request.")
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    # 驗證 feedback_type 的值
    if feedback_type not in ["useful", "useless"]:
        logger.warning(f"Invalid feedback_type: {feedback_type}")
        return jsonify({"success": False, "error": "Invalid feedback_type. Must be 'useful' or 'useless'"}), 400

    try:
        # 先獲取當前值
        response = supabase.table('pro_analyze').select('useful, useless').eq('analyze_id', analyze_id).execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"Analyze ID not found: {analyze_id}")
            return jsonify({"success": False, "error": "Analyze ID not found"}), 404

        current_data = response.data[0]
        current_useful = current_data.get('useful', 0) or 0
        current_useless = current_data.get('useless', 0) or 0

        # 更新對應的計數器
        if feedback_type == "useful":
            new_useful = current_useful + 1
            update_response = supabase.table('pro_analyze').update({
                'useful': new_useful
            }).eq('analyze_id', analyze_id).execute()
            
            logger.info(f"Updated useful count to {new_useful} for analyze_id: {analyze_id}")
            return jsonify({
                "success": True,
                "useful": new_useful,
                "useless": current_useless
            })
        else:  # useless
            new_useless = current_useless + 1
            update_response = supabase.table('pro_analyze').update({
                'useless': new_useless
            }).eq('analyze_id', analyze_id).execute()
            
            logger.info(f"Updated useless count to {new_useless} for analyze_id: {analyze_id}")
            return jsonify({
                "success": True,
                "useful": current_useful,
                "useless": new_useless
            })

    except Exception as e:
        logger.error(f"Error submitting expert feedback: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/experts/country_analyze", methods=["POST"])
def country_analyze_route():
    """
    提供針對特定國家的即時新聞分析 (目前固定為台灣)。
    """
    data = request.json
    story_id = data.get("story_id")
    country = data.get("country") # 應為 "Taiwan"

    logger.info(f"Received /api/experts/country_analyze request for story_id: {story_id}, country: {country}")

    if not story_id or not country:
        logger.warning("Missing 'story_id' or 'country' in /api/experts/country_analyze request.")
        return jsonify({"error": "Missing 'story_id' or 'country'"}), 400

    if country != "Taiwan":
        logger.warning(f"Unsupported country: {country}. Only 'Taiwan' is supported.")
        return jsonify({"error": "Only 'Taiwan' is currently supported"}), 400

    try:
        # 1. 呼叫 Gemini 生成分析 (回傳扁平的 dict)
        analysis_result = country_pro_analyze.generate_country_analysis(story_id, country)
        
        # 2. 呼叫函式將分析結果插入資料庫 (此函式內部會處理錯誤，不會中斷流程)
        # 即使插入失敗，我們仍然希望將分析結果回傳給前端
        try:
            country_pro_analyze.insert_analysis_data(story_id, country, analysis_result)
        except Exception as db_e:
            # 記錄插入錯誤，但不中斷
            logger.error(f"DB insert failed for {story_id}, but analysis will be returned. Error: {db_e}", exc_info=True)

        # 3. 將扁平的 JSON 分析結果回傳給前端
        logger.info(f"Successfully processed country analysis for {story_id}. Returning analysis.")
        return jsonify(analysis_result)

    except Exception as e:
        logger.error(f"Error during country analysis generation for {story_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/media_literacy/generate", methods=["POST"])
def media_literacy_route():
    """
    提供針對特定新聞的即時媒體識讀提醒。
    """
    data = request.json
    story_id = data.get("story_id")

    logger.info(f"Received /api/media_literacy/generate request for story_id: {story_id}")

    if not story_id:
        logger.warning("Missing 'story_id' in /api/media_literacy/generate request.")
        return jsonify({"error": "Missing 'story_id'"}), 400

    try:
        # 1. 呼叫 Gemini 生成提醒 (回傳扁平的 dict)
        alert_result = media_literacy.generate_media_literacy_alert(story_id)
        
        # 2. 呼叫函式將提醒結果插入資料庫 (此函式內部會處理錯誤，不會中斷流程)
        #    這樣下次就可以直接從 'media_literacy' 表中讀取，不需重覆生成
        try:
            media_literacy.insert_media_literacy_data(story_id, alert_result)
        except Exception as db_e:
            # 記錄插入錯誤，但不中斷
            logger.error(f"DB insert failed for {story_id} (media literacy), but alert will be returned. Error: {db_e}", exc_info=True)

        # 3. 將扁平的 JSON 提醒結果回傳給前端
        logger.info(f"Successfully processed media literacy alert for {story_id}. Returning alert.")
        return jsonify(alert_result)

    except Exception as e:
        logger.error(f"Error during media literacy generation for {story_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Consider removing debug=True for production
    app.run(host="0.0.0.0", port=5000, debug=True)