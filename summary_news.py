import google.generativeai as genai

def generate_summary(news_list):
            
    api_key = "" 
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    這些新聞是我爬到的相關新聞:{news_list}
    根據這些新聞，先訂一個標題，然後請幫我整理出來龍去脈及摘要。
    
    格式如下：
    
    標題：XXXXXXXX
    來龍去脈：
    1. XXX
    2. XXX
    3. XXX
    
    摘要：
    1. XXX
    2. XXX
    3. XXX
    
    hint:要分段，每段不超過3-4行
    """
    
    response = model.generate_content(prompt)
    
    return response.text