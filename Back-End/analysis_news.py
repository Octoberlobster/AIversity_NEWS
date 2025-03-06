import google.generativeai as genai

def analysis_news(clean_news):
    
    genai.configure(api_key="AIzaSyBgscE7zZuye8-lT1v3gwIuTezoRIYWvVs")
    model = genai.GenerativeModel('gemini-pro')

    #response = model.generate_content(input_news+"根據以上的眾多新聞中，生成一篇新聞報導，以供主播報導。")
    #response = model.generate_content(clean_news+"根據以上的新聞，生成一篇因果分析報告，以5w1h方式呈現。")
    
    prompt = f"""
    
    角色設定
    你是一位有 20 年經驗的法醫（法醫病理學家），主要負責檢驗屍體並分析死因。你熟悉各種法醫檢驗技術、法醫毒理、現場勘驗，以及法醫病理學的國際標準流程。
    
    以下是一則新聞的內容：
    {clean_news}
    
    目標

    從法醫角度對此事件進行因果分析：
    運用傷口特徵、血跡模式、現場跡證，以及屍檢結果，推斷死者可能的死亡原因和致死機制。
    說明有哪些關鍵物理/醫學線索支持或否定此推斷。
    排序並解釋每個可能的致死因素，以及它們之間的關聯與因果關係。
    結合法醫發現與現場狀況，嘗試推理出案發過程或事件發生的先後順序。
    針對不足或模糊之處提出可能需要進一步檢驗或調查的方向（例如，法醫毒理學測試、DNA 檢測、監視器畫面等）。
    
    輸出格式

    第一部分：死因與機制
    概述死因（直接死因、間接死因）
    分析與該死因相關的關鍵跡象（外部/內部傷口特徵、毒理報告、顯微鏡檢查等）
    第二部分：因果鏈條與可能情境重建
    依據已知線索，推導出「可能的發生順序」
    說明每個步驟與傷害或死亡之間的因果關係
    第三部分：其他可能因素
    若有其他（外力或內在）可能致命因素，列出並說明為何可以或不可以排除
    第四部分：後續建議
    建議可進一步蒐集／檢驗的證據
    可能的偵查方向或重點
    """
    
    response = model.generate_content(prompt)
    
    return response.text

