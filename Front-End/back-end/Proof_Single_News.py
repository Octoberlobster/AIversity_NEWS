from env import supabase, gemini_client
from pydantic import BaseModel
from google import genai

class ProofSentence(BaseModel):
    sentence: str
    source_id: list[str]

class ProofNewsResponse(BaseModel):
    proof_response: list[ProofSentence]

def generate_proof(story_id: str) -> str:
    response = supabase.table("cleaned_news").select("content,article_url,media,article_title").eq("story_id", story_id).execute()
    response = response.data
    original_new = supabase.table("single_news").select("short,long").eq("story_id", story_id).execute()
    original_new = original_new.data[0]["short"] + "\n" + original_new.data[0]["long"]
    contents = "\n".join(f"{i+1}. {item['content']}" for i, item in enumerate(response))
    urls = [item["article_url"] for item in response]
    medias = [item["media"] for item in response]
    titles = [item["article_title"] for item in response]

    prompt = f"""
你是一個新聞分析助手。
我會提供一則「當前新聞」和多則「相關新聞」。
從「當前新聞」中，找出重要且需要被證實的句子，並從「相關新聞」中，找出能夠證實這些句子的內容，隨後回傳「相關新聞」的編號。
請確保每個被證實的句子，都有對應的「相關新聞」編號。
當前新聞：
{original_new}
相關新聞：
{contents}
"""
    completion = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ProofNewsResponse,
        ),
    )

    result = completion.parsed.proof_response
    # Format the output
    # [{sentence,source:[{url1,media1},{url2,media2}]}]

    formatted_result = []
    for item in result:
        sentence = item.sentence
        sources = [urls[int(source_id)-1] for source_id in item.source_id ]
        media_item = [medias[int(source_id)-1] for source_id in item.source_id ]
        title_item = [titles[int(source_id)-1] for source_id in item.source_id ]
        formatted_result.append({
            "sentence": sentence,
            "source": [{"url": url, "media": media, "title": title} for url, media, title in zip(sources, media_item, title_item)]
        })

    return formatted_result

# result = generate_proof_article("cbda2f9b-3d4f-40c5-91a8-acb55229df02")
# print(result)