# scenario_app.py  ─ 情境模式後端  http://localhost:5001/scenario
# ===========================================================
# 流程：
#   1. 前端 POST  {scenario, roles[]} 進 /scenario
#   2. 先用 Gemini+搜尋工具產生三角色的「立場 / 語氣」JSON
#   3. 動態組出每位角色的 system_prompt；主持人也有自己的 system
#   4. 主持人 -> 指定 speaker (只能一位) -> 角色回一句 -> 回給主持人
#      如主持人回 {"speaker":"結束"} 就立即結束
#   5. 將所有 messages 以 [{role,text},…] 一次回傳給前端
# ===========================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json, os, re, logging
from time import sleep

# ---------- 日誌設定 ---------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

# ---------- 基本設定 ---------------------------------------------------------
API_KEY = "AIzaSyBlEmBuz6y9ZhJ9S6mm2c1v5xWkmfaKtIc"
genai.configure(api_key=API_KEY)

app = Flask(__name__)
CORS(app)                               # 允許所有來源跨域

# ---------- 載入新聞 (作為背景資料) -----------------------------------------
with open("GenerateNews_EachEvent/News.json", encoding="utf-8") as f:
    NEWS_CONTENT = json.load(f)["Content"]

# ---------- 工具：去掉 ```json ... ``` 區塊 -------------------------------
def strip_triple_backticks(txt: str) -> str:
    """去除 ```json 與 ```，並 strip 空白"""
    return re.sub(r"```json|```", "", txt).strip()

# ---------- 端點 /scenario ---------------------------------------------------
@app.post("/scenario")
def scenario_chat():
    body     = request.get_json(force=True)
    scenario = body.get("scenario", "").strip()
    roles    = body.get("roles", [])

    # 檢查參數：至少要有 3 個角色
    if not scenario or len(roles) < 3:
        return jsonify({"error": "scenario & ≥3 roles required"}), 400

    # 1️⃣ 先用搜尋工具 / Gemini 取得「每個角色」的立場、語氣
    characters_json = get_characters_info(scenario, roles)

    # 2️⃣ 依立場資訊，動態產生各角色的 system prompt
    role_prompts = build_role_prompts(characters_json, roles)

    # 3️⃣ 建立主持人 + 各角色 chat_session
    moderator, role_chats = build_models(role_prompts, characters_json)

    # 4️⃣ 進行主持人多輪指派（直到結束為止）
    try :
        messages = drive_dialogue(moderator, role_chats, scenario)
        return jsonify(messages), 200
    except Exception as e:
        log.error("Error during dialogue: %s", str(e))
        return jsonify({"error": "Dialogue error"}), 500

# ---------------------------------------------------------------------------
# ↓↓↓ 以下函式各自負責一段邏輯，全部都有中文註解 ↓↓↓
# ---------------------------------------------------------------------------

def get_characters_info(scenario: str, roles: list[str]) -> dict:
    """
    呼叫 Gemini + google_search_retrieval，產生如下結構：
    {
        "美國政府": {"description": "...", "position": "...", "style": "..."},
        "烏克蘭政府": {...},
        "俄羅斯政府": {...}
    }
    """
    search_model = genai.GenerativeModel(
        'gemini-1.5-pro-002',
        system_instruction="先利用搜尋工具後取得相關角色資訊，然後再進行回答"
    )

    prompt = (
        "請你幫這三個角色分別為美國政府、烏克蘭政府與俄羅斯政府，在這篇新聞中"+NEWS_CONTENT+"，針對如下情境"+scenario\
        +"請你依照各角色的立場、背景利益、價值觀與語氣風格，詳細描述其觀點與態度。此外，請讓三方角色能夠展現出各自典型的行事風格與說話方式，並能進行理性但充滿立場張力的對話。"\
        "請你使用以下 JSON 格式回覆，每位角色需包含完整資訊，便於後續角色扮演或模擬對話使用：請你以JSON格式回覆，格式如下\n"\
        """
        {
            "characters": [
                {
                "name": "美國政府",
                "description": "美國政府的立場與觀點",
                "position": "美國政府認為...",
                "style": "語氣風格"
                },
                {
                "name": "烏克蘭政府",
                "description": "烏克蘭政府的立場與觀點",
                "position": "烏克蘭政府認為...",
                "style": "語氣風格"
                },
                {
                "name": "俄羅斯政府",
                "description": "俄羅斯政府的立場與觀點",
                "position": "俄羅斯政府認為...",
                "style": "語氣風格"
                }
            ]
        }"""
    )

    resp = search_model.generate_content(prompt, tools="google_search_retrieval")
    data = json.loads(strip_triple_backticks(resp.text))
    # 轉成 dict，方便後續查詢
    return {c["name"]: c for c in data["characters"]}

def build_role_prompts(char_info: dict, roles: list[str]) -> dict:
    """
    根據 get_characters_info() 產出的資訊，為每位角色組 system prompt
    """
    def other(r):               # 除了自己以外的成員
        return "、".join([x for x in roles if x != r])

    prompts = {}
    for r in roles:
        info = char_info[r]
        prompts[r] = (
            f"你現在扮演的角色為{r}，與會成員有{other(r)}。\n"
            f"遵循以下背景與立場：{info['description']}。\n"
            f"你認為：{info['position']}。\n"
            f"請以{info['style']}語氣，用一句對話式回答。"
        )
    return prompts

def build_models(role_prompts: dict, char_info: dict):
    """
    建立：
      • 主持人 chat_session
      • 角色名 ➜ chat_session 的 dict
    """
    Am_description = char_info["美國政府"]["description"]
    Uk_description = char_info["烏克蘭政府"]["description"]
    Ru_description = char_info["俄羅斯政府"]["description"]

    moderator_system = (
        "你是一位多方會談的主持人，你的目的是在這三位角色中分別為美國政府、烏克蘭政府與俄羅斯政府選擇一位當下最適合回答的人"\
                                "並且由你的回答來引導他們進行良好的溝通，在最後如果你覺得各方的對話應該告一段落了則請你以「結束」這兩個字當作回覆，以下是關於三位角色的立場與看法提供給你參考，"\
                                "美國政府:"+Am_description+\
                                "烏克蘭政府:"+Uk_description+\
                                "俄羅斯政府:"+Ru_description+"請你以繁體中文回答並要求與會者也如此"
    )

    # 主持人
    mod_chat = genai.GenerativeModel(
        'gemini-1.5-pro-002',
        system_instruction=moderator_system
    ).start_chat()

    # 各角色
    role_chats = {
        r: genai.GenerativeModel(
            'gemini-1.5-pro-002',
            system_instruction=role_prompts[r]
        ).start_chat()
        for r in role_prompts
    }
    return mod_chat, role_chats

def drive_dialogue(moderator, role_chats, scenario: str):
    """
    • 主持人 ➜ speaker / prompt
    • 指定角色回一句
    • 回給主持人
    • 若 speaker == 結束 → break
    """
    messages = []
    
    messages.append({"role": "SYSTEM", "text": "開始"})
    
    count = 0
    while True:
        if count == 0:
            # 開場：請主持人指定第一位
            role_prompt = moderator.send_message("這是這次多人會談的討論主題"+scenario+"請你決定誰最適合回答，並且引導他們進行良好的溝通"\
                                                            "請你以JSON格式回覆，格式如下\n"\
                                                            "{"\
                                                            "\"speaker\": \"美國政府/烏克蘭政府/俄羅斯政府/結束\""\
                                                            "\"prompt\": \"引導角色發言並讓整體會談流暢發展\""\
                                                            "}"
                                                            )
            count += 1
            continue
        my_json = role_prompt.text
        my_json = my_json.replace('```json', '').replace('```', '').strip()
        my_json = json.loads(my_json)
        speaker = my_json["speaker"]
        message = my_json["prompt"]
        # --- 主持人指定發言者 ---------------------------------------
        log.info("[主持人 ➜ %s] %s", speaker, message)

        # --- 主持人宣布結束 -------------------------------------------
        if speaker == "結束":
            messages.append({"role": "SYSTEM", "text": "結束"})
            break

        # --- 主持人指定未知角色 ---------------------------------------
        if speaker not in role_chats:
            err = f"未知角色 {speaker}"
            log.error(err)
            messages.append({"role": "SYSTEM", "text": err})
            break
        
        # --- 角色發言 -------------------------------------------------
        reply = role_chats[speaker].send_message(message).text
        log.info("[%s] %s", speaker, reply)
        messages.append({"role": speaker, "text": reply})
        
        
        # --- 將角色回覆貼回主持人，要求下一人 -------------------------
        role_prompt = moderator.send_message(
            f"這是來自{speaker}的發言" + reply + "請你決定誰最適合回答，並且引導他們進行良好的溝通"\
            "請你以JSON格式回覆，格式如下\n"\
            "{"\
            "\"speaker\": \"美國政府/烏克蘭政府/俄羅斯政府/結束\""\
            "\"prompt\": \"引導角色發言並讓整體會談流暢發展\""\
            "}"
        )
        sleep(5)
        

    return messages

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(port=5001, debug=True)
