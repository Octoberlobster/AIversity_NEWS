import google.generativeai as genai
import json
import re
import os

# 設定 API 金鑰
api_key = os.getenv("API_KEY_Gemini_PAY")
genai.configure(api_key=api_key)
# 聊天會話存儲
chat_sessions = {}

def strip_triple_backticks(txt: str) -> str:
    """去除 ```json 與 ```，並 strip 空白"""
    return re.sub(r"```json|```", "", txt).strip()

def interactive_chat_logic(body: dict) -> tuple[dict, int]:
    """
    參數: body = { role:str, message:str }
    回傳: (dict, http_status)
    """
    role    = body.get("role", "").strip()
    message = body.get("message", "").strip()
    news   = body.get("news", "").strip()
    
    if not role or not message:
        return {"error": "Missing role or message"}, 400
    
    # 獲取或創建聊天會話
    if role not in chat_sessions:
        
        search_model = genai.GenerativeModel(
            'gemini-1.5-pro-002',
            system_instruction="先利用搜尋工具後取得相關角色資訊，然後再進行回答"
        )
        
        schema = """{
            "characters": [
                {
                "name": "<角色名稱>",
                "description": "<立場與觀點>",
                "position": "<角色認為…>",
                "style": "<語氣風格>"
                }
            ]
        }"""
        
        prompt = f"""
                你正在閱讀以下新聞全文：
                {news}

                ### 角色名稱（固定，禁止更動）
                {role}

                ### 你要做什麼
                1. 依照上述新聞內容，站在 **{role}** 的角度，寫出立場、觀點與語氣風格。
                2. 讓角色能表現典型的行事作風，並保有張力與說服力。

                ### ⚠️ 生成規則（務必遵守）
                - `name` 欄位 **只能** 是 `{role}`，大小寫、標點必須完全一致。
                - 不得新增或修改角色名稱。
                - 若無法遵守，請直接回覆 **ERROR_DO_NOT_RENAME**。
                - 回覆必須「完全符合」下列 JSON 結構，且不得包含任何多餘文字或註解。

                ### JSON 格式
                {schema}

                （請使用繁體中文）
                """
        
        resp = search_model.generate_content(prompt, tools=["google_search_retrieval"])
        data = json.loads(strip_triple_backticks(resp.text))
        
        
        for c in data["characters"]:
            print(f"角色：{c['name']}")
            print(f"立場：{c['description']}")
            print(f"語氣：{c['style']}")
            print(f"觀點：{c['position']}")
            print("-" * 40)
            
        # 轉成 dict，方便後續查詢
        role_info = {c["name"]: c for c in data["characters"]}
        
        system_instruction = f"""
        你正在閱讀以下新聞：
        
        {news}
        
        你現在要扮演{role}。請以{role}的身份回應用戶的問題或評論。
        
        {role}的立場和觀點是：
        {role_info[role]}
        
        請以簡短的幾句話來進行對話式的回答，保持在{role}的角色中，並根據上述立場和觀點來回應。
        回答時根據用戶輸入的語言回應，並且要簡潔有力，每次回應不超過3-4句話。
        """
        
        model = genai.GenerativeModel('gemini-1.5-pro-002', system_instruction=system_instruction)
        chat_sessions[role] = model.start_chat()
    
    try:
        # 發送消息並獲取回覆
        response = chat_sessions[role].send_message(message)
        return {"response": response.text}, 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}, 500