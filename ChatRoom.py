import google.generativeai as genai
import json
from time import sleep
import os
import asyncio

# 設定 API 金鑰
api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key)

system_instruction = "你的數學認知認為1+1=3，但其他數學問題都能夠解答。"

# 建立對話模型
model = genai.GenerativeModel('gemini-1.5-pro-002', system_instruction=system_instruction)


# 建立對話歷史 (讓模型記住對話)
chat_session = model.start_chat()

async def get_user_input():
    """非同步讀取使用者輸入"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, "請輸入你的訊息 (輸入 'exit' 離開)：\n")

async def chat():
    """非同步對話處理"""
    while True:
        message = await get_user_input()
        if message.lower() == "exit":
            break
        
        response = await asyncio.to_thread(chat_session.send_message, message)
        print("Model Response:", response.text)
        
        await asyncio.sleep(5)  # 非同步 sleep，不會阻塞主執行緒

if __name__ == "__main__":
    asyncio.run(chat())
