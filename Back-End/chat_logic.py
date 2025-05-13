import google.generativeai as genai
import json
import re
import os

# 設定 API 金鑰
API_KEY = os.getenv("API_KEY_Gemini_PAY")
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
        
        schema_lines = [
            '  {',
            '    "name": "<角色名稱>",',
            '    "description": "<立場與觀點>",',
            '    "position": "<角色認為…>",',
            '    "style": "<語氣風格>"',
            '  }'
        ]
        schema = "{\n  \"characters\": [\n" + ",\n".join(schema_lines) + "\n  ]\n}"
        
        prompt = (
            f"""
            "請你幫以下角色{role}，根據新聞全文:"+{news}+"\
            +"請你依照{role}的立場、背景利益、價值觀與語氣風格，詳細描述其觀點與態度。此外，請讓角色能夠展現出各自典型的行事風格與說話方式，並能進行理性但充滿立場張力的對話。"\
            "請你生成立場時，名稱必須與角色名稱一致，不得創造新角色或是隨意改變角色名稱。"\
            "請你使用以下 JSON 格式回覆，角色需包含完整資訊，便於後續角色扮演或模擬對話使用：請你以JSON格式回覆，格式如下\n"\
            f"{schema}\n"\
            "請以繁體中文回答，並且不要有任何的額外說明或是註解。\n"
            """
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