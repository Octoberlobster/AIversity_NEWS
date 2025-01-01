import google.generativeai as genai

def analysis_news(clean_news):
    
    api_key = "你的API" 
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    #response = model.generate_content(input_news+"根據以上的眾多新聞中，生成一篇新聞報導，以供主播報導。")
    #response = model.generate_content(clean_news+"根據以上的新聞，生成一篇因果分析報告，以5w1h方式呈現。")
    
    prompt = f"""
    以下是一則新聞的內容：
    {clean_news}
    
    根據這則新聞，請生成一篇因果分析報告，並以以下格式呈現：
    1. 每個因果關係以清晰的標題開頭。
    2. 使用分段的方式，每段不超過 3-4 行。
    3. 語氣應簡潔且吸引讀者注意力。
    
    """
    
    response = model.generate_content(prompt)
    
    return response.text

