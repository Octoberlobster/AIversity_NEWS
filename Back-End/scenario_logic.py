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
API_KEY = os.getenv("API_KEY_Gemini_PAY")
genai.configure(api_key=API_KEY)

# ---------- 工具：去掉 ```json ... ``` 區塊 -------------------------------
def strip_triple_backticks(txt: str) -> str:
    """去除 ```json 與 ```，並 strip 空白"""
    return re.sub(r"```json|```", "", txt).strip()

def scenario_chat_logic(body: dict) -> tuple[dict, int]:
    """
    參數: body = { scenario:str, roles:list[str] }
    回傳: (dict 或 list, http_status)
    """
    scenario = body.get("scenario", "").strip()
    roles    = body.get("roles", [])
    news     = body.get("news", "").strip()
    
    print("body:", body)
    print("scenario:", scenario)
    print("roles:", roles)

    # 檢查參數：至少要有 2 個角色
    if not scenario or len(roles) < 2:
        return {"error": "scenario & ≥2 roles required"}, 400

    # 1️⃣ 先用搜尋工具 / Gemini 取得「每個角色」的立場、語氣
    characters_json = get_characters_info(scenario, roles, news)

    # 2️⃣ 依立場資訊，動態產生各角色的 system prompt
    role_prompts = build_role_prompts(characters_json, roles)

    # 3️⃣ 建立主持人 + 各角色 chat_session
    moderator, role_chats = build_models(role_prompts, characters_json)

    # 4️⃣ 進行主持人多輪指派（直到結束為止）
    try :
        messages = drive_dialogue(moderator, role_chats, scenario)
        return {"messages": messages}, 200
    except Exception as e:
        log.error("Error during dialogue: %s", str(e))
        return {"error": "Dialogue error"}, 500

# ---------- 新增：串流版邏輯 -----------------------------------------
def scenario_chat_stream(body: dict):
    """
    生成器：一輪對話就 yield 一條
    body = {scenario:str, roles:list[str], news:str}
    """
    scenario = body["scenario"]
    roles    = body["roles"]
    news     = body["news"]

    # ① 產生角色立場 / system prompt / model
    char_info    = get_characters_info(scenario, roles, news)
    role_prompts = build_role_prompts(char_info, roles)
    moderator, role_chats = build_models(role_prompts, char_info)

    speaker_opts = "/".join(roles) + "/結束"

    # ② 主持人先決定第一位發言
    role_prompt = moderator.send_message(
        f"這是這次多人會談的討論主題"+scenario+"請你決定誰最適合回答，並且引導他們進行良好的溝通"\
                                                            "請你以JSON格式回覆，格式如下\n"\
                                                            "{"\
                                                            "\"speaker\": \"" + speaker_opts + "\""\
                                                            "\"prompt\": \"引導角色發言並讓整體會談流暢發展\""\
                                                            "}"
                                                            "請你以繁體中文回答。\n"
    )

    yield {"role": "SYSTEM", "text": "開始"}   # 前端可忽略 SYSTEM

    while True:
        # 解析主持人 JSON
        msg = json.loads(
            strip_triple_backticks(role_prompt.text.replace("'", '"'))
        )
        speaker = msg["speaker"].strip()
        prompt  = msg["prompt"].strip()

        if speaker == "結束":
            yield {"role": "SYSTEM", "text": "結束"}
            break

        if speaker not in role_chats:
            yield {"role": "SYSTEM", "text": f"未知角色：{speaker}，結束對話"}
            break

        # ③ 該角色回一句
        reply = role_chats[speaker].send_message(prompt).text.strip()
        yield {"role": speaker, "text": reply}

        # ④ 將這句貼回主持人，請他決定下一位
        role_prompt = moderator.send_message(
            f"這是來自{speaker}的發言" + reply + "請你決定誰最適合回答，並且引導他們進行良好的溝通"\
            "請你以JSON格式回覆，格式如下\n"\
            "{"\
            "\"speaker\": \"" + speaker_opts + "\","\
            "\"prompt\": \"引導角色發言並讓整體會談流暢發展\""\
            "}"
            "請你以繁體中文回答。\n"
        )

def build_schema_with_names(roles: list[str]) -> str:
    """產生固定角色名的 JSON 雛形"""
    parts = []
    for r in roles:
        parts.append(
            f'''  {{
                "name": "{r}",
                "description": "<立場與觀點>",
                "position": "<角色認為…>",
                "style": "<語氣風格>"
            }}'''
        )
    return "{\n  \"characters\": [\n" + ",\n".join(parts) + "\n  ]\n}"

def get_characters_info(scenario: str, roles: list[str], news: str) -> dict:
    SYSTEM_RULE = (
        "### 規則（務必遵守，違者重來）\n"
        "1. 角色名稱只能使用清單中出現的字串，嚴禁新增、翻譯或改寫。\n"
        "2. 請直接填入雛形 JSON，不要刪除或移動任何欄位。\n"
        "3. 禁止在 JSON 之外輸出任何文字、註解、Markdown。\n"
        "4. 若無法遵守規則，請回傳 `ERROR_NAME_MISMATCH`。\n"
        "5. 先利用搜尋工具後取得相關角色資訊，然後再進行回答"
    )

    search_model = genai.GenerativeModel(
        'gemini-1.5-pro-002',
        system_instruction=SYSTEM_RULE
    )

    roles_content = "、".join(roles)
    print("角色：", roles_content)
    schema = build_schema_with_names(roles)
    print("schema:", schema)

    prompt = (
        f"以下是情境：{scenario}\n"
        f"新聞全文（可作參考，不可改名）：{news}\n\n"
        "請根據情境及新聞內容，填寫每位角色的立場與語氣，"
        f"角色名稱只能選用：{roles_content}\n\n"
        "### 請以『完全相同的 JSON 雛形』回覆：\n"
        f"{schema}\n\n"
        "（禁止輸出 JSON 之外的任何文字，禁止修改 name 欄位）"
    )

    resp = search_model.generate_content(prompt, tools=["google_search_retrieval"])
    data = json.loads(strip_triple_backticks(resp.text))
    
    for c in data["characters"]:
        print(f"角色：{c['name']}")
        print(f"立場：{c['description']}")
        print(f"語氣：{c['style']}")
        print(f"觀點：{c['position']}")
        print("-" * 40)
    
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
            f"你是 {r}，與會成員有 {other(r)}。\n"
            f"立場：{info['description']}\n"
            f"語氣：{info['style']}\n\n"
            "【發言規範】\n"
            "1. 每次最多 2 句、總長不超過 100 字。\n"
            "2. 可使用口語、破折號、語氣詞，像真實對話。\n"
            "3. 切忌長篇大論；必要時分段多輪講。\n"
            "4. 回覆直接輸出對話，不要任何說明。\n"
        )
    return prompts

def build_models(role_prompts: dict, char_info: dict):
    """
    建立：
      • 主持人 chat_session
      • 角色名 ➜ chat_session 的 dict
    """
    role_desc = "\n".join(f"{r}:{char_info[r]['description']}" for r in role_prompts)

    moderator_system = (
        # ───────── 角色與任務 ─────────
        "你是一位多方會談的主持人。你的工作流程：\n"
        "  1. 在下面角色中，挑選「最適合下一個發言」的人。\n"
        "  2. 提供該角色一段 ≤100 字的口語提示，引導對話自然深入。\n"
        "  3. 生成唯一 JSON 物件作回覆。\n\n"

        # ───────── 規則 ─────────
        "【主持規範】\n"
        "  ‣ 前 6 輪禁止結束。\n"
        "  ‣ 至少讓每位角色各發言 2 次。\n"
        "  ‣ 如未滿足條件而你想結束，請改為選擇下一位適合發言的角色。\n"
        "  ‣ 真正結束時，僅輸出：{\"speaker\":\"結束\",\"prompt\":\"\"}\n"
        "  ‣ 絕不可更改、翻譯或創造角色名稱。\n"
        "  ‣ 除 JSON 之外，不得輸出任何額外字元、註解、Markdown。\n\n"

        # ───────── 角色立場與看法 ─────────
        "以下為所有角色的立場與看法，僅供參考，嚴禁修改角色名稱：\n"
        f"{role_desc}\n\n"
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

# ---------- JSON 容錯解析 ----------
def safe_json_extract(text: str) -> dict:
    """
    從 LLM 回覆中抽出最像 JSON 的部分並解析。
    • 去掉 ```json ... ``` 區塊
    • 單引號 → 雙引號
    • 若解析失敗則拋出例外
    """
    # 刪掉 Markdown code fence
    cleaned = re.sub(r"```json|```", "", text).strip()

    # 嘗試直接解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # 將單引號改成雙引號再試一次
        fixed = cleaned.replace("'", '"')
        return json.loads(fixed)

# ---------- 參數設定 ----------
MIN_TURNS = 6          # 最少輪數
MAX_TURNS = 40         # 最多輪數
CLOSE_BUFFER = 2        # 剩下幾輪觸發收尾預告
MAX_REPLY_CHARS = 60   # 角色單句最長字數
def drive_dialogue(moderator, role_chats, scenario: str):
    messages = [{"role": "SYSTEM", "text": "開始"}]
    speaker_opts = "/".join(role_chats) + "/結束"

    turns = 0
    end_warn_sent = False   # 尚未觸發收尾提醒
    closing_phase = False   # 收尾人已提醒，主持人下次可結束

    # ① 開場
    role_prompt = moderator.send_message(
        f"討論主題：{scenario}\n請依規範輸出首位 JSON。"
    )

    # ② 迴圈對話
    while turns < MAX_TURNS:
        # ---------- 解析主持人 JSON ----------
        try:
            data = safe_json_extract(role_prompt.text)
        except Exception as e:
            log.error("主持人 JSON 錯誤：%s", e)
            role_prompt = moderator.send_message("格式錯誤，請重新輸出純 JSON。")
            continue

        speaker = data.get("speaker", "").strip()
        prompt  = data.get("prompt", "").strip()

        # ---------- 是否要結束 ----------
        if speaker == "結束":
            if closing_phase or turns >= MIN_TURNS:
                messages.append({"role": "SYSTEM", "text": "結束"})
                break
            # 未到收尾階段：請主持人換人
            role_prompt = moderator.send_message(
                f"目前僅 {turns} 輪，或尚未收尾，請重新指定 speaker。"
            )
            continue

        # ---------- 未知角色 ----------
        if speaker not in role_chats:
            role_prompt = moderator.send_message(
                f"角色「{speaker}」不存在，請從 {speaker_opts} 選擇。"
            )
            continue

        # ---------- 角色發言 ----------
        reply = role_chats[speaker].send_message(prompt).text.strip()
        if len(reply) > MAX_REPLY_CHARS:
            reply = reply[:MAX_REPLY_CHARS] + "…"

        log.info("[%s] %s", speaker, reply)
        messages.append({"role": speaker, "text": reply})
        turns += 1

        # ---------- 是否進入「收尾預告」 ----------
        if not end_warn_sent and turns >= MAX_TURNS - CLOSE_BUFFER:
            # 要主持人挑一位角色來喊停
            role_prompt = moderator.send_message(
                "我們即將達到最大輪數，請挑選一位角色用 ≤20 字提醒大家準備收尾，"
                "並以 JSON 回覆："
                "{ \"speaker\": \"" + speaker_opts + "\", "
                "\"prompt\": \"<收尾提醒>\" }"
            )
            end_warn_sent = True
            closing_phase = True
            continue

        # ---------- 常規：請主持人挑下一位 ----------
        role_prompt = moderator.send_message(
            f"以下為 {speaker} 的回覆：{reply}\n請依規範輸出下一位 JSON。"
        )

    # ③ 若超過 MAX_TURNS 強制結束
    if turns >= MAX_TURNS:
        messages.append({"role": "SYSTEM", "text": "已達最長回合，自動結束"})

    return messages
