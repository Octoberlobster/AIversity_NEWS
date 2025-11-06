from env import supabase, gemini_client
from google.genai import types
from pydantic import BaseModel
import json

class singleNewsResponse(BaseModel):
    news_title: str
    ultra_short: str
    long: str

class relativeResponse(BaseModel):
    reason: str  
    
class termResponse(BaseModel):
    term: str
    definition: str
    example: str
    
class positionResponse(BaseModel):
    positive: list[str]
    negative: list[str]

class pro_analyzeResponse(BaseModel):
    Role: str
    Analyze: str
    
class imageDescriptionResponse(BaseModel):
    description: str
    
class keywordResponse(BaseModel):
    keyword: str

class topicResponse(BaseModel):
    topic_title: str
    topic_short: str
    topic_long: str
    report: str

class topicBranchResponse(BaseModel):
    topic_branch_title: str
    topic_branch_content: str
    
class mindMapResponse(BaseModel):
    label: str
    description: str

class Translate:
    def __init__(self, supabase, gemini_client):
        self.supabase = supabase
        self.gemini_client = gemini_client
        self.lang_list = ["en","id","jp"]
        
    def callgemini(self, prompt,config):
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            print(f"翻譯時發生錯誤: {e}")
            return None
    
    def translate_singleNews(self, story_id):
        try:
            response = self.supabase.table("single_news").select("*").eq("story_id", story_id).execute().data
        except Exception as e:
            print(f"取得新聞資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到story_id '{story_id}' 的新聞資料")
            return None
        
        single_news = response[0]
        news_title = single_news.get("news_title", "")
        ultra_short = single_news.get("ultra_short", "")
        long = single_news.get("long", "")
        
        for lang in self.lang_list:
            
            #先找找看該語言的翻譯是否已存在，若存在則跳過翻譯
            title_check = single_news.get(f"news_title_{lang}_lang", "")
            ultra_short_check = single_news.get(f"ultra_short_{lang}_lang", "")
            long_check = single_news.get(f"long_{lang}_lang", "")
            
            if title_check and ultra_short_check and long_check:
                print(f"story_id '{story_id}' 的{lang}新聞資料已存在，跳過翻譯")
                continue
            
            if lang == "id":
                lang = "indonesia"
            
            prompt = f"請將以下新聞標題及內容翻譯成{lang}:\n標題: {news_title}\n簡短內容: {ultra_short}\n詳細內容: {long}\n"
            config = types.GenerateContentConfig(
                system_instruction=f"你是一個專業的翻譯專家，請將提供的新聞標題及內容準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                response_mime_type="application/json",
                response_schema=singleNewsResponse
            )
        
            response_text = self.callgemini(prompt, config)
            if response_text is None:
                print("翻譯失敗")
                return None
            
            if lang == "indonesia":
                lang = "id"
            
            try:
                translated_data = json.loads(response_text)
                translated_news_title = translated_data.get("news_title", "")
                translated_ultra_short = translated_data.get("ultra_short", "")
                translated_long = translated_data.get("long", "")
                update_data = {
                    f"news_title_{lang}_lang": translated_news_title,
                    f"ultra_short_{lang}_lang": translated_ultra_short,
                    f"long_{lang}_lang": translated_long
                }
                self.supabase.table("single_news").update(update_data).eq("story_id", story_id).execute()
                print(f"翻譯成功，已更新story_id '{story_id}' 的{lang}新聞資料")
            except Exception as e:
                print(f"更新翻譯後的新聞資料時發生錯誤: {e}")
                return None
        
    def translate_relativeNews(self, story_id):
        try:
            response = self.supabase.table("relative_news").select("*").eq("src_story_id", story_id).execute().data
        except Exception as e:
            print(f"取得新聞資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到story_id '{story_id}' 的relative_news資料")
               
        for item in response:
            src_story_id = item.get("src_story_id", "")
            dst_story_id = item.get("dst_story_id", "")
            reason = item.get("reason", "")
            for lang in self.lang_list:

                reason_check = item.get(f"reason_{lang}_lang", "")
                if reason_check:
                    print(f"story_id '{story_id}' 的{lang}新聞關聯理由已存在，跳過翻譯")
                    continue

                if lang == "id":
                    lang = "indonesia"
                
                prompt = f"請將以下新聞關聯理由翻譯成{lang}:\n關聯理由: {reason}\n"
                config = types.GenerateContentConfig(
                    system_instruction=f"你是一個專業的翻譯專家，請將提供的新聞關聯理由準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                    response_mime_type="application/json",
                    response_schema=relativeResponse
                )
                response_text = self.callgemini(prompt, config)
                if response_text is None:
                    print("翻譯失敗")
                    return None
                
                if lang == "indonesia":
                    lang = "id"
                
                try:
                    translated_data = json.loads(response_text)
                    translated_reason = translated_data.get("reason", "")
                    update_data = {
                        f"reason_{lang}_lang": translated_reason
                    }
                    self.supabase.table("relative_news").update(update_data).eq("src_story_id", src_story_id).eq("dst_story_id", dst_story_id).execute()
                    print(f"翻譯成功，已更新src_story_id '{src_story_id}' dst_story_id '{dst_story_id}' 的 {lang} relative_news資料")
                except Exception as e:
                    print(f"更新翻譯後的relative_news資料時發生錯誤: {e}")
                    return None
                
    def translate_relativeTopics(self, story_id):
        try:
            response = self.supabase.table("relative_topics").select("*").eq("src_story_id", story_id).execute().data
        except Exception as e:
            print(f"取得新聞資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到story_id '{story_id}' 的relative_topics資料")
            return None
        
        for item in response:
            src_story_id = item.get("src_story_id", "")
            dst_topic_id = item.get("dst_topic_id", "")
            reason = item.get("reason", "")
            for lang in self.lang_list:
                
                reason_check = item.get(f"reason_{lang}_lang", "")
                if reason_check:
                    print(f"story_id '{story_id}' 的{lang}新聞關聯理由已存在，跳過翻譯")
                    continue

                if lang == "id":
                    lang = "indonesia"
                
                prompt = f"請將以下新聞關聯理由翻譯成{lang}:\n關聯理由: {reason}\n"
                config = types.GenerateContentConfig(
                    system_instruction=f"你是一個專業的翻譯專家，請將提供的新聞關聯理由準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                    response_mime_type="application/json",
                    response_schema=relativeResponse
                )
                response_text = self.callgemini(prompt, config)
                if response_text is None:
                    print("翻譯失敗")
                    return None
                
                if lang == "indonesia":
                    lang = "id"
                
                try:
                    translated_data = json.loads(response_text)
                    translated_reason = translated_data.get("reason", "")
                    update_data = {
                        f"reason_{lang}_lang": translated_reason
                    }
                    self.supabase.table("relative_topics").update(update_data).eq("src_story_id", src_story_id).eq("dst_topic_id", dst_topic_id).execute()
                    print(f"翻譯成功，已更新src_story_id '{src_story_id}' dst_topic_id '{dst_topic_id}' 的 {lang} relative_topics資料")
                except Exception as e:
                    print(f"更新翻譯後的relative_topics資料時發生錯誤: {e}")
                    return None

    def translate_terms(self,story_id):
        try:
            response = self.supabase.table("term_map").select("*").eq("story_id", story_id).execute().data
        except Exception as e:
            print(f"取得term_map資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到story_id '{story_id}' 的term_map資料")
            return None
        
        term_id_list = [item.get("term_id", "") for item in response]
        for term_id in term_id_list:
            try:
                response = self.supabase.table("term").select("*").eq("term_id", term_id).execute().data
            except Exception as e:
                print(f"取得term資料時發生錯誤: {e}")
                return None
            
            if not response:
                print(f"未找到term_id '{term_id}' 的term資料")
                return None
            
            term_data = response[0]
            term = term_data.get("term", "")
            definition = term_data.get("definition", "")
            example = term_data.get("example", "")
            
            for lang in self.lang_list:
                
                term_check = term_data.get(f"term_{lang}_lang", "")
                definition_check = term_data.get(f"definition_{lang}_lang", "")
                example_check = term_data.get(f"example_{lang}_lang", "")
                
                if term_check and definition_check and example_check:
                    print(f"term_id '{term_id}' 的{lang} term資料已存在，跳過翻譯")
                    continue
                
                if lang == "id":
                    lang = "indonesia"
                
                prompt = f"請將以下術語及其定義和範例翻譯成{lang}:\n術語: {term}\n定義: {definition}\n範例: {example}\n"
                config = types.GenerateContentConfig(
                    system_instruction=f"你是一個專業的翻譯專家，請將提供的術語及其定義和範例準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                    response_mime_type="application/json",
                    response_schema=termResponse
                )
                response_text = self.callgemini(prompt, config)
                if response_text is None:
                    print("翻譯失敗")
                    return None
                
                if lang == "indonesia":
                    lang = "id"
                
                try:
                    translated_data = json.loads(response_text)
                    translated_term = translated_data.get("term", "")
                    translated_definition = translated_data.get("definition", "")
                    translated_example = translated_data.get("example", "")
                    update_data = {
                        f"term_{lang}_lang": translated_term,
                        f"definition_{lang}_lang": translated_definition,
                        f"example_{lang}_lang": translated_example
                    }
                    self.supabase.table("term").update(update_data).eq("term_id", term_id).execute()
                    print(f"翻譯成功，已更新term_id '{term_id}' 的 {lang} term資料")
                except Exception as e:
                    print(f"更新翻譯後的term資料時發生錯誤: {e}")
                    return None
 
    def translate_position(self,story_id):
        try:
            response = self.supabase.table("position").select("*").eq("story_id", story_id).execute().data
        except Exception as e:
            print(f"取得position資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到story_id '{story_id}' 的position資料")
            return None

        position_data = response[0]
        position_id = position_data.get("position_id", "")
        positive = position_data.get("positive", "")
        negative = position_data.get("negative", "")

        for lang in self.lang_list:
            
            postive_check = position_data.get(f"positive_{lang}_lang", "")
            negative_check = position_data.get(f"negative_{lang}_lang", "")
            
            if postive_check and negative_check:
                print(f"story_id '{story_id}' 的{lang} position資料已存在，跳過翻譯")
                continue
            
            if lang == "id":
                lang = "indonesia"
            
            prompt = f"請將以下立場內容翻譯成{lang}:\n正面立場: {positive}\n負面立場: {negative}\n"
            config = types.GenerateContentConfig(
                system_instruction=f"你是一個專業的翻譯專家，請將提供的立場內容準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                response_mime_type="application/json",
                response_schema=positionResponse
            )
            response_text = self.callgemini(prompt, config)
            if response_text is None:
                print("翻譯失敗")
                return None
            
            if lang == "indonesia":
                lang = "id"
            
            try:
                translated_data = json.loads(response_text)
                translated_positive = translated_data.get("positive", [])
                translated_negative = translated_data.get("negative", [])
                update_data = {
                    f"positive_{lang}_lang": translated_positive,
                    f"negative_{lang}_lang": translated_negative
                }

                self.supabase.table("position").update(update_data).eq("story_id", story_id).execute()
                print(f"翻譯成功，已更新story_id '{story_id}' 的 {lang} position資料")
            except Exception as e:
                print(f"更新翻譯後的position資料時發生錯誤: {e}")
                return None     
                           
    def translate_pro_analyze(self,story_id):
        try:
            response = self.supabase.table("pro_analyze").select("*").eq("story_id", story_id).execute().data
        except Exception as e:
            print(f"取得pro_analyze資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到story_id '{story_id}' 的pro_analyze資料")
            return None
        
        pro_analyze_data = response[0]
        analyze = pro_analyze_data.get("analyze", "")
        Category = analyze.get("Category", "")
        Role = analyze.get("Role", "")
        Analyze = analyze.get("Analyze", "")
        
        for lang in self.lang_list:
            
            pro_analyze_check = pro_analyze_data.get(f"analyze_{lang}_lang", {})
            if pro_analyze_check:
                
                Role_check = pro_analyze_check.get("Role", "")
                Analyze_check = pro_analyze_check.get("Analyze", "")
                
                if Role_check and Analyze_check:
                    print(f"story_id '{story_id}' 的{lang} pro_analyze資料已存在，跳過翻譯")
                    continue

            if lang == "id":
                lang = "indonesia"
            
            prompt = f"請將以下專業分析的角色和分析內容翻譯成{lang}:\n角色: {Role}\n分析內容: {Analyze}\n"
            config = types.GenerateContentConfig(
                system_instruction=f"你是一個專業的翻譯專家，請將提供的專業分析的角色和分析內容準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                response_mime_type="application/json",
                response_schema=pro_analyzeResponse
            )
            response_text = self.callgemini(prompt, config)
            if response_text is None:
                print("翻譯失敗")
                return None
            
            if lang == "indonesia":
                lang = "id"
            
            try:
                translated_data = json.loads(response_text)
                translated_Role = translated_data.get("Role", "")
                translated_Analyze = translated_data.get("Analyze", "")
                update_data = {
                    f"analyze_{lang}_lang": {
                        "Category": Category,
                        "Role": translated_Role,
                        "Analyze": translated_Analyze
                    }
                }
                
                self.supabase.table("pro_analyze").update(update_data).eq("story_id", story_id).execute()
                print(f"翻譯成功，已更新story_id '{story_id}' 的 {lang} pro_analyze資料")
            except Exception as e:
                print(f"更新翻譯後的pro_analyze資料時發生錯誤: {e}")
                return None

    def translate_imagedescription(self, story_id):
        try:
            response = self.supabase.table("generated_image").select("*").eq("story_id", story_id).execute().data
        except Exception as e:
            print(f"取得generated_image資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到story_id '{story_id}' 的generated_image資料")
            return None
        
        image_data = response[0]
        description = image_data.get("description", "")
        
        for lang in self.lang_list:
            
            description_check = image_data.get(f"description_{lang}_lang", "")
            if description_check:
                print(f"story_id '{story_id}' 的{lang} generated_image資料已存在，跳過翻譯")
                continue
            
            if lang == "id":
                lang = "indonesia"
            
            prompt = f"請將以下圖片描述翻譯成{lang}:\n圖片描述: {description}\n"
            config = types.GenerateContentConfig(
                system_instruction=f"你是一個專業的翻譯專家，請將提供的圖片描述準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                response_mime_type="application/json",
                response_schema=imageDescriptionResponse
            )
            response_text = self.callgemini(prompt, config)
            if response_text is None:
                print("翻譯失敗")
                return None
            
            if lang == "indonesia":
                lang = "id"
            
            try:
                translated_data = json.loads(response_text)
                translated_description = translated_data.get("description", "")
                update_data = {
                    f"description_{lang}_lang": translated_description
                }
                
                self.supabase.table("generated_image").update(update_data).eq("story_id", story_id).execute()
                print(f"翻譯成功，已更新story_id '{story_id}' 的 {lang} generated_image資料")
            except Exception as e:
                print(f"更新翻譯後的generated_image資料時發生錯誤: {e}")
                return None
        
    def translate_keyword(self, story_id):
        try:
            response = self.supabase.table("keywords_map").select("*").eq("story_id", story_id).execute().data
        except Exception as e:
            print(f"取得keywords_map資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到story_id '{story_id}' 的keywords_map資料")
            return None
        
        print("取得的keywords_map資料:", response)
        keyword_list = [item.get("keyword", "") for item in response]
        
        for keyword in keyword_list:
            for lang in self.lang_list:
                
                keyword_check = self.supabase.table("keywords_map").select(f"keyword_{lang}_lang").eq("story_id", story_id).eq("keyword", keyword).execute().data
                if keyword_check:
                    print(f"story_id '{story_id}' 的{lang} keywords_map資料已存在，跳過翻譯")
                    continue

                if lang == "id":
                    lang = "indonesia"
                
                prompt = f"請將以下關鍵字翻譯成{lang}:\n關鍵字: {keyword}\n"
                config = types.GenerateContentConfig(
                    system_instruction=f"你是一個專業的翻譯專家，請將提供的關鍵字準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                    response_mime_type="application/json",
                    response_schema=keywordResponse
                )
                response_text = self.callgemini(prompt, config)
                if response_text is None:
                    print("翻譯失敗")
                    return None
                
                if lang == "indonesia":
                    lang = "id"
                
                try:
                    translated_data = json.loads(response_text)
                    translated_keyword = translated_data.get("keyword", "")
                    update_data = {
                        f"keyword_{lang}_lang": translated_keyword
                    }
                    
                    self.supabase.table("keywords_map").update(update_data).eq("story_id", story_id).eq("keyword", keyword).execute()
                    print(f"翻譯成功，已更新story_id '{story_id}' keyword '{keyword}' 的 {lang} keywords_map資料")
                except Exception as e:
                    print(f"更新翻譯後的keywords_map資料時發生錯誤: {e}")
                    return None 
            
    def translate_topic(self, topic_id):
        try:
            response = self.supabase.table("topic").select("*").eq("topic_id", topic_id).execute().data
        except Exception as e:
            print(f"取得topic資料時發生錯誤: {e}")
            return None

        if not response:
            print(f"未找到id '{topic_id}' 的topic資料")
            return None
        topic_data = response[0]
        topic_title = topic_data.get("topic_title", "")
        topic_short = topic_data.get("topic_short", "")
        topic_long = topic_data.get("topic_long", "")
        report = topic_data.get("report", "")
        
        for lang in self.lang_list:
            
            topic_title_check = topic_data.get(f"topic_title_{lang}_lang", "")
            topic_short_check = topic_data.get(f"topic_short_{lang}_lang", "")
            topic_long_check = topic_data.get(f"topic_long_{lang}_lang", "")
            
            report_check = topic_data.get(f"report_{lang}_lang", "")
            
            if topic_title_check and topic_short_check and topic_long_check and report_check:
                print(f"topic_id '{topic_id}' 的{lang} topic資料已存在，跳過翻譯")
                continue
            
            if lang == "id":
                lang = "indonesia"
            
            prompt = f"請將以下主題標題、短描述、長描述和報告翻譯成{lang}:\n標題: {topic_title}\n短描述: {topic_short}\n長描述: {topic_long}\n報告: {report}\n"
            config = types.GenerateContentConfig(
                system_instruction=f"你是一個專業的翻譯專家，請將提供的主題標題、短描述、長描述和報告準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                response_mime_type="application/json",
                response_schema=topicResponse
            )
            response_text = self.callgemini(prompt, config)
            if response_text is None:
                print("翻譯失敗")
                return None
            
            if lang == "indonesia":
                lang = "id"
            try:
                translated_data = json.loads(response_text)
                translated_topic_title = translated_data.get("topic_title", "")
                translated_topic_short = translated_data.get("topic_short", "")
                translated_topic_long = translated_data.get("topic_long", "")
                translated_report = translated_data.get("report", "")
                update_data = {
                    f"topic_title_{lang}_lang": translated_topic_title,
                    f"topic_short_{lang}_lang": translated_topic_short,
                    f"topic_long_{lang}_lang": translated_topic_long,
                    f"report_{lang}_lang": translated_report
                }
                
                self.supabase.table("topic").update(update_data).eq("topic_id", topic_id).execute()
                print(f"翻譯成功，已更新topic_id '{topic_id}' 的 {lang} topic資料")
            except Exception as e:
                print(f"更新翻譯後的topic資料時發生錯誤: {e}")
                return None

    def translate_topic_branch(self, topic_id):
        try:
            response = self.supabase.table("topic_branch").select("*").eq("topic_id", topic_id).execute().data
        except Exception as e:
            print(f"取得topic_branch資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到id '{topic_id}' 的topic_branch資料")
            return None
                
        topic_branch_data = response
        
        for branch in topic_branch_data:
            topic_branch_id = branch.get("topic_branch_id", "")
            topic_branch_title = branch.get("topic_branch_title", "")
            topic_branch_content = branch.get("topic_branch_content", "")
            
            for lang in self.lang_list:

                topic_branch_title_check = branch.get(f"topic_branch_title_{lang}_lang", "")
                topic_branch_content_check = branch.get(f"topic_branch_content_{lang}_lang", "")

                if topic_branch_title_check and topic_branch_content_check:
                    print(f"topic_branch_id '{topic_branch_id}' 的{lang} topic_branch資料已存在，跳過翻譯")
                    continue

                if lang == "id":
                    lang = "indonesia"
                    
                prompt = f"請將以下主題分支標題和內容翻譯成{lang}:\n標題: {topic_branch_title}\n內容: {topic_branch_content}\n"
                config = types.GenerateContentConfig(
                    system_instruction=f"你是一個專業的翻譯專家，請將提供的主題分支標題和內容準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                    response_mime_type="application/json",
                    response_schema=topicBranchResponse
                )
                response_text = self.callgemini(prompt, config)
                if response_text is None:
                    print("翻譯失敗")
                    return None
                
                if lang == "indonesia":
                    lang = "id"
                
                try:
                    translated_data = json.loads(response_text)
                    translated_title = translated_data.get("topic_branch_title", "")
                    translated_content = translated_data.get("topic_branch_content", "")
                    update_data = {
                        f"topic_branch_title_{lang}_lang": translated_title,
                        f"topic_branch_content_{lang}_lang": translated_content
                    }
                    
                    self.supabase.table("topic_branch").update(update_data).eq("topic_branch_id", topic_branch_id).eq("topic_id", topic_id).execute()
                    print(f"翻譯成功，已更新topic_branch_id '{topic_branch_id}' 的 {lang} topic_branch資料")
                except Exception as e:
                    print(f"更新翻譯後的topic_branch資料時發生錯誤: {e}")
                    return None
    
    def translate_mindmap(self, topic_id):
        try:
            response = self.supabase.table("topic").select("mind_map_detail").eq("topic_id", topic_id).execute().data
        except Exception as e:
            print(f"取得topic資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到id '{topic_id}' 的topic資料")
            return None
        
        mind_map_detail = response[0].get("mind_map_detail", {})
        center_node = mind_map_detail.get("center_node", {})
        main_nodes = mind_map_detail.get("main_nodes", [])
        detailed_nodes = mind_map_detail.get("detailed_nodes", {})
        
        main_id,main_label,main_description = center_node.get("id",""),center_node.get("label",""),center_node.get("description","")
        for lang in self.lang_list:
            
            translated = True
            
            center_node_check = mind_map_detail.get(f"center_node_{lang}_lang", {})
            main_nodes_check = mind_map_detail.get(f"main_nodes_{lang}_lang", [])
            detailed_nodes_check = mind_map_detail.get(f"detailed_nodes_{lang}_lang", {})
            
            if center_node_check and main_nodes_check and detailed_nodes_check:
                center_node_label_check = center_node_check.get("label","")
                center_node_description_check = center_node_check.get("description","")
                if center_node_label_check == "" or center_node_description_check == "":
                    translated = False
                
                for main_node in main_nodes_check:
                    main_node_label_check = main_node.get("label","")
                    main_node_description_check = main_node.get("description","")
                    if main_node_label_check == "" or main_node_description_check == "":
                        translated = False
                        break
                    
                for key, nodes in detailed_nodes_check.items():
                    for node in nodes:
                        node_label_check = node.get("label","")
                        node_description_check = node.get("description","")
                        if node_label_check == "" or node_description_check == "":
                            translated = False
                            break
            else:
                translated = False
            
            if translated:
                print(f"topic_id '{topic_id}' 的{lang} mind_map_detail資料已存在，跳過翻譯")
                continue
            
            if lang == "id":
                lang = "indonesia"
            
            update_data = {}
            
            # 翻譯中心節點
            prompt = f"請將以下心智圖中心節點的標籤和描述翻譯成{lang}:\n標籤: {main_label}\n描述: {main_description}\n"
            config = types.GenerateContentConfig(
                system_instruction=f"你是一個專業的翻譯專家，請將提供的心智圖中心節點的標籤和描述準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                response_mime_type="application/json",
                response_schema=mindMapResponse
            )
            response_text = self.callgemini(prompt, config)
            if response_text is None:
                print("翻譯失敗")
                return None
            
            try:
                translated_data = json.loads(response_text)
                translated_main_label = translated_data.get("label", "")
                translated_main_description = translated_data.get("description", "")
                update_data.update({
                    'center_node': {
                        'id': main_id,
                        'label': translated_main_label,
                        'description': translated_main_description
                    }
                })
                print(f"翻譯成功，已更新topic_id '{topic_id}' 的mind_map_detail_{lang}_lang中心節點資料")
            except Exception as e:
                print(f"更新翻譯後的mind_map_detail_{lang}_lang中心節點資料時發生錯誤: {e}")
                return None
            
            # 翻譯主要節點
            translated_main_nodes = []
            for main_node in main_nodes:
                main_node_id = main_node.get("id", "")
                main_node_label = main_node.get("label", "")
                main_node_description = main_node.get("description", "")
                prompt = f"請將以下心智圖主要節點的標籤和描述翻譯成{lang}:\n標籤: {main_node_label}\n描述: {main_node_description}\n"
                config = types.GenerateContentConfig(
                    system_instruction=f"你是一個專業的翻譯專家，請將提供的心智圖主要節點的標籤和描述準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                    response_mime_type="application/json",
                    response_schema=mindMapResponse
                )
                response_text = self.callgemini(prompt, config)
                if response_text is None:
                    print("翻譯失敗")
                    return None
                try:
                    translated_data = json.loads(response_text)
                    translated_label = translated_data.get("label", "")
                    translated_description = translated_data.get("description", "")
                    translated_main_nodes.append({
                        'id': main_node_id,
                        'label': translated_label,
                        'description': translated_description
                    })
                    print(f"翻譯成功，已更新topic_id '{topic_id}' 的mind_map_detail_{lang}_lang主要節點{main_node_id}資料")
                except Exception as e:
                    print(f"更新翻譯後的mind_map_detail_{lang}_lang主要節點{main_node_id}資料時發生錯誤: {e}")
                    return None
                
            update_data.update({'main_nodes': translated_main_nodes})
            
            # 翻譯詳細節點
            translated_detailed_nodes = {}
            for key, nodes in detailed_nodes.items():
                translated_nodes = []
                for node in nodes:
                    node_id = node.get("id", "")
                    node_label = node.get("label", "")
                    node_description = node.get("description", "")
                    prompt = f"請將以下心智圖詳細節點的標籤和描述翻譯成{lang}:\n標籤: {node_label}\n描述: {node_description}\n"
                    config = types.GenerateContentConfig(
                        system_instruction=f"你是一個專業的翻譯專家，請將提供的心智圖詳細節點的標籤和描述準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                        response_mime_type="application/json",
                        response_schema=mindMapResponse
                    )
                    response_text = self.callgemini(prompt, config)
                    if response_text is None:
                        print("翻譯失敗")
                        return None
                    try:
                        translated_data = json.loads(response_text)
                        translated_label = translated_data.get("label", "")
                        translated_description = translated_data.get("description", "")
                        translated_nodes.append({
                            'id': node_id,
                            'label': translated_label,
                            'description': translated_description
                        })
                        print(f"翻譯成功，已更新topic_id '{topic_id}' 的mind_map_detail_{lang}_lang詳細節點{node_id}資料")
                    except Exception as e:
                        print(f"更新翻譯後的mind_map_detail_{lang}_lang詳細節點{node_id}資料時發生錯誤: {e}")
                        return None
                translated_detailed_nodes[key] = translated_nodes
            update_data.update({'detailed_nodes': translated_detailed_nodes})
            
            if lang == "indonesia":
                lang = "id"
            
            try:
                self.supabase.table("topic").update({f"mind_map_detail_{lang}_lang": update_data}).eq("topic_id", topic_id).execute()
                print(f"翻譯成功，已更新topic_id '{topic_id}' 的mind_map_detail_{lang}_lang資料")
            except Exception as e:
                print(f"更新mind_map_detail_{lang}_lang資料時發生錯誤: {e}")
                return None

    def translate_pro_analyze_topic(self, topic_id):
        try:
            response = self.supabase.table("pro_analyze_topic").select("*").eq("topic_id", topic_id).execute().data
        except Exception as e:
            print(f"取得pro_analyze資料時發生錯誤: {e}")
            return None
        
        if not response:
            print(f"未找到story_id '{story_id}' 的pro_analyze資料")
            return None
        
        pro_analyze_data = response[0]
        analyze = pro_analyze_data.get("analyze", "")
        Category = analyze.get("Category", "")
        Role = analyze.get("Role", "")
        Analyze = analyze.get("Analyze", "")
        
        for lang in self.lang_list:
            
            pro_analyze_check = pro_analyze_data.get(f"analyze_{lang}_lang", {})
            if pro_analyze_check:
                Role_check = pro_analyze_check.get("Role", "")
                Analyze_check = pro_analyze_check.get("Analyze", "")
                
                if Role_check and Analyze_check:
                    print(f"topic_id '{topic_id}' 的{lang} pro_analyze資料已存在，跳過翻譯")
                    continue
            
            if lang == "id":
                lang = "indonesia"
            
            prompt = f"請將以下專業分析的角色和分析內容翻譯成{lang}:\n角色: {Role}\n分析內容: {Analyze}\n"
            config = types.GenerateContentConfig(
                system_instruction=f"你是一個專業的翻譯專家，請將提供的專業分析的角色和分析內容準確且流暢地翻譯成{lang}。請確保翻譯後的文本符合{lang}語法和用詞習慣，並保持原文的意思和風格。",
                response_mime_type="application/json",
                response_schema=pro_analyzeResponse
            )
            response_text = self.callgemini(prompt, config)
            if response_text is None:
                print("翻譯失敗")
                return None
            
            if lang == "indonesia":
                lang = "id"
            
            try:
                translated_data = json.loads(response_text)
                translated_Role = translated_data.get("Role", "")
                translated_Analyze = translated_data.get("Analyze", "")
                update_data = {
                    f"analyze_{lang}_lang": {
                        "Category": Category,
                        "Role": translated_Role,
                        "Analyze": translated_Analyze
                    }
                }

                self.supabase.table("pro_analyze_topic").update(update_data).eq("topic_id", topic_id).execute()
                print(f"翻譯成功，已更新topic_id '{topic_id}' 的 {lang} pro_analyze資料")
            except Exception as e:
                print(f"更新翻譯後的pro_analyze資料時發生錯誤: {e}")
                return None

if __name__ == "__main__":
    
    #宣告Translate物件
    translate = Translate(supabase, gemini_client)  
    
    #跑所有新聞的翻譯

    # story_id_list = supabase.table("single_news").select("story_id").range(1,2000).order("generated_date", desc=True).execute().data
    # story_id_list = [item.get("story_id", "") for item in story_id_list]
    # for num, story_id in enumerate(story_id_list, start=1):
    #     print(f"{num}.開始翻譯story_id '{story_id}' 的新聞資料")
    #     translate.translate_singleNews(story_id)
    #     translate.translate_relativeNews(story_id)
    #     translate.translate_relativeTopics(story_id)
    #     translate.translate_terms(story_id)
    #     translate.translate_position(story_id)
    #     translate.translate_pro_analyze(story_id)
    #     translate.translate_imagedescription(story_id)
    #     translate.translate_keyword(story_id)
    
    
    #跑所有topic的翻譯

    topic_id_list = supabase.table("topic").select("topic_id").execute().data
    topic_id_list = [item.get("topic_id", "") for item in topic_id_list]
    for topic_id in topic_id_list:
        print(f"開始翻譯topic_id '{topic_id}' 的主題資料")
        translate.translate_topic(topic_id)
        translate.translate_topic_branch(topic_id)
        translate.translate_mindmap(topic_id)
        translate.translate_pro_analyze_topic(topic_id)