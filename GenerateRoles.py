import google.generativeai as genai
import json
from time import sleep
import os
from supabase import create_client, Client
import uuid

api_key = os.getenv("API_KEY_Ge")
genai.configure(api_key=api_key)

SUPABASE_URL         = os.getenv("API_KEY_URL")
SUPABASE_SERVICE_KEY = os.getenv("API_KEY_supa")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

model = genai.GenerativeModel('gemini-2.0-flash-001')

response_news = (
    supabase.table("generated_news")
    .select("content")
    .execute()
)
data_news = response_news.data
response_id =(
    supabase.table("generated_news")
    .select("generated_id")
    .execute()
)
data_id = response_id.data
data_id = [d["generated_id"] for d in data_id]
for i in range(len(data_news)):
    news=json.dumps(data_news[i], ensure_ascii=False, indent=4)

    Roles = model.generate_content("請根據下列新聞內容，分析該新聞事件可能涉及的重要角色，並生成多個角色。每個角色請包含以下資訊："
                                   "1. 角色名稱：描述該角色在事件中扮演的角色（例如：政府機關、相關人士、專家、受影響民眾等）。"
                                   "2. 角色背景：簡述該角色的專業背景、所屬領域或與事件相關的經歷，說明他們為何對該事件具有影響力或見解。"
                                   "3. 角色觀點：描述該角色可能對事件提出的觀點、立場或分析，並說明他們可能關注的議題。"
                                   "4. 語境：描述該角色所處的環境與上下文，包括角色與事件之間的關係、所在的時空背景、媒體關注度等。"
                                   "請注意：生成的角色必須以第三人稱角度來看待該事件，角色應作為外部觀察者或評論者，而非事件本身的直接參與者。"
                                   "請以 JSON 格式回傳結果，格式範例如下："
                                   "{"
                                   "\"Role1\": {"
                                   "\"Name\": \"……\","
                                   "\"Background\": \"……\","
                                   "\"View\": \"……\","
                                   "\"Context\": \"……\""
                                   "},"
                                   "\"Role2\": {"
                                   "\"Name\": \"……\","
                                   "\"Background\": \"……\","
                                   "\"View\": \"……\","
                                   "\"Context\": \"……\""
                                   "},"
                                   "//依照此格式繼續擴增更多角色"
                                   "}"
                                   "以下是新聞內容："
                                    +news
                                    )
    Roles = Roles.text
    Roles = Roles.replace('```json', '').replace('```', '').strip()
    Roles = json.loads(Roles)

    with open("Roles.json", "a", encoding="utf-8") as file:
        json.dump(Roles, file, ensure_ascii=False, indent=4)
        file.write("\n")
    Roles_str = json.dumps(Roles, ensure_ascii=False, indent=4)

    analyze =model.generate_content("請根據下列新聞內容與角色資訊，請每個角色依據自己的立場與觀點，從第一人稱的角度對該新聞事件進行因果分析。請重點說明以下內容："
                                    "1. 事件發生的主要原因與影響因素。"
                                    "2. 這些因素如何導致當前結果，以及可能產生的後續影響。"
                                    "3. 事件可能引發的社會議題、爭議或其他相關議題。"
                                    "4. 以條列式方式回答，每個角色回答三個條目。"
                                    "5. 控制文章長度，請用40字以內簡潔回答。"
                                    "請以 JSON 格式回傳結果，格式範例如下："
                                    "{"
                                    "\"Role1\": {"
                                    "\"Role_Name\": \"……\","
                                    "\"Analyze\": [\"1.……\",\"2.……\",\"3.……\"]"
                                    "},"
                                    "\"Role2\": {"
                                    "\"Role_Name\": \"……\","
                                    "\"Analyze\": [\"1.……\",\"2.……\",\"3.……\"]"
                                    "},"
                                    "//依照此格式繼續擴增更多角色"
                                    "}"
                                    "以下是新聞內容：" + news + "以下是角色資訊：" + Roles_str)
    analyze = analyze.text
    analyze = analyze.replace('```json', '').replace('```', '').strip()
    analyze = json.loads(analyze)

    with open("RolesAnalyze.json", "a", encoding="utf-8") as file:
        json.dump(analyze, file, ensure_ascii=False, indent=4)
        file.write("\n")

    for role_num in analyze.items():
        role_name = role_num[1]["Role_Name"]
        role_analyze = role_num[1]["Analyze"]
        m_uuid = uuid.uuid4()
        total_analyze = ""
        for j in range(len(role_analyze)):
            total_analyze += role_analyze[j]
            total_analyze += "\n"
        role_analyze = total_analyze

        response = (
            supabase.table("role_causal_analysis")
            .insert(
                {
                    "role_id": str(m_uuid),
                    "generated_id": str(data_id[i]),
                    "role": role_name,
                    "analysis": role_analyze
                }
            )
            .execute()
        )
    
    
