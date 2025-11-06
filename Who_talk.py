from google.genai import types
from google.genai.errors import ServerError
from google.api_core.exceptions import ServiceUnavailable
from pydantic import BaseModel
from env import gemini_client, supabase
import time

class InitChatResponse(BaseModel):
    who_talk: list[str]

def who_talk(story_id: str, max_retries: int = 3, sleep_between: float = 2.0):
    response = supabase.table("single_news").select("long").eq("story_id", story_id).execute()
    article_content = response.data[0]["long"]
    model_name = "gemini-2.5-flash-lite"
    
    for attempt in range(1, max_retries + 1):
        try:
            who_talk = gemini_client.models.generate_content(
                model=model_name,
                contents=article_content,
                config=types.GenerateContentConfig(
                    system_instruction="你是負責決定接下來出場的類別專家，請根據傳入的文章內容，決定接下來出場的類別專家。類別專家一定是以下這8個否則你將受到嚴厲懲罰。以下是可選的類別專家：\n"
                                        "1. Politics（政治） - 包含政府政策、選舉、外交、政黨動態等。\n"
                                        "2. International News（國際） - 重大國際事件、地緣政治、國際組織相關新聞。\n"
                                        "3. Science & Technology（科學與科技） - 包含科學研究、太空探索、生物科技、AI、大數據、半導體、電子產品、電玩遊戲、網安等科技發展。\n"
                                        "4. Lifestyle & Consumer（生活） - 旅遊、時尚、飲食、消費趨勢等。\n"
                                        "5. Sports（體育） - 體育賽事、運動員動態、奧運、世界盃等。\n"
                                        "6. Entertainment（娛樂） - 電影、音樂、藝人新聞、流行文化等。\n"
                                        "7. Business & Finance（商業財經） - 經濟政策、股市、企業動態、投資市場等。\n"
                                        "8. Health & Wellness（健康） - 公共衛生、醫學研究、醫療技術等。"
                                        "請確保這些類別專家是根據文章內容來決定，並且一定要選擇3個不同類別的專家來出場。",
                    response_mime_type="application/json",
                    response_schema=InitChatResponse,
                ),
            )
            return dict(who_talk.parsed)
        except (ServiceUnavailable, ServerError) as e:
            error_type = "503 Service Unavailable" if isinstance(e, ServiceUnavailable) else "500 Internal Server Error"
            print(f"⚠️ Gemini {error_type}，第 {attempt}/{max_retries} 次重試，等待 {sleep_between} 秒...")
            if attempt >= max_retries:
                print(f"[ERROR] API error after {max_retries} attempts: {e}")
                raise  # Re-raise the error after max retries
            time.sleep(sleep_between)
    
    return None  # Should never reach here due to raise above

all_require = []
batch_size = 1000
start = 0

while True:
    temp = supabase.table("single_news").select("story_id,who_talk,position_flag").order("generated_date", desc=True).range(start, start + batch_size - 1).execute()
    if not temp.data:
        break
    all_require.extend(temp.data)
    start += batch_size

require = type("Result", (), {"data": all_require})  # 模擬原本 require 結構

# ...existing code...
for item in require.data:
    if not item["who_talk"]:
        story_id = item["story_id"]
        result = who_talk(story_id)
        supabase.table("single_news").update({"who_talk": result}).eq("story_id", story_id).execute()
        print(f"Updated story_id {story_id} with who_talk {result['who_talk']}")
    else:
        print(f"story_id {item['story_id']} already has who_talk {item['who_talk']}")
    #break
print("All done.")


