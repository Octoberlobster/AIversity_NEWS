import os
import asyncio
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import jieba
import jieba.analyse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer  # 重新啟用
import json
import datetime

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsClassifier:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
        # 初始化 jieba
        jieba.initialize()
        
        # TF-IDF 向量化器
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # 我們將使用自定義的中文停用詞
            ngram_range=(1, 2)
        )
        
        # 預載入資料
        self.topics = None
        self.topic_embeddings = {}
        self.embedding_model = None
        
    async def initialize(self):
        """初始化分類器，載入必要資料"""
        logger.info("正在初始化新聞分類器...")
        
        # 載入 topics
        await self.load_topics()
        
        # 初始化嵌入模型
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        logger.info("新聞分類器初始化完成")
    
    async def load_topics(self):
        """載入所有主題"""
        try:
            response = self.supabase.table("topic").select("*").execute()
            self.topics = response.data
            logger.info(f"載入了 {len(self.topics)} 個主題")
        except Exception as e:
            logger.error(f"載入主題時發生錯誤: {e}")
            self.topics = []
    
    async def get_news_with_features(self, story_id: str) -> Dict:
        """取得新聞及其特徵資料"""
        try:
            # 取得基本新聞資料
            news_response = self.supabase.table("single_news").select("*").eq("story_id", story_id).execute()
            if not news_response.data:
                return None
                
            news = news_response.data[0]
            
            # 取得關鍵字
            keywords_response = self.supabase.table("keywords_map").select(
                "keyword"
            ).eq("story_id", story_id).execute()
            keywords = [k["keyword"] for k in keywords_response.data]
            
            # 取得專有名詞
            terms_response = self.supabase.table("term_map").select(
                "term"
            ).eq("story_id", story_id).execute()
            terms = [t["term"] for t in terms_response.data]
            
            return {
                "story_id": story_id,
                "title": news.get("news_title", ""),
                "content": news.get("short", ""),
                "category": news.get("category", ""),
                "keywords": keywords,
                "terms": terms
            }
            
        except Exception as e:
            logger.error(f"取得新聞特徵時發生錯誤: {e}")
            return None
    
    def extract_keywords(self, text: str, topK: int = 10) -> List[str]:
        """使用 jieba 提取關鍵字"""
        if not text:
            return []
        
        # 使用 TF-IDF 提取關鍵字
        keywords = jieba.analyse.extract_tags(text, topK=topK, withWeight=False)
        return keywords
    
    def extract_named_entities(self, text: str) -> Dict[str, List[str]]:
        """動態提取命名實體，不使用硬編碼模式"""
        entities = {
            'important_terms': [],
            'locations': [],
            'organizations': [],
            'events': [],
            'numbers': []
        }
        
        words = jieba.lcut(text)
        
        for i, word in enumerate(words):
            # 動態識別重要詞彙
            if len(word) >= 2 and not word.isdigit():
                # 基於詞長度和位置的重要性判斷
                if len(word) >= 3:
                    entities['important_terms'].append(word)
                
                # 基於後綴的動態識別
                if word.endswith(('國', '省', '市', '縣', '區')):
                    entities['locations'].append(word)
                elif word.endswith(('黨', '會', '院', '部', '局', '司')):
                    entities['organizations'].append(word)
                elif word.endswith(('案', '事件', '戰爭', '衝突', '颱風')):
                    entities['events'].append(word)
            
            # 提取數字和年份
            if word.isdigit() and len(word) >= 2:
                entities['numbers'].append(word)
        
        # 去重並保留最相關的詞彙
        for key in entities:
            entities[key] = list(set(entities[key]))[:10]  # 限制數量
        
        return entities
    
    def calculate_entity_match_score(self, news_entities: Dict[str, List[str]], topic_entities: Dict[str, List[str]]) -> float:
        """計算實體匹配分數，使用動態權重"""
        total_score = 0.0
        total_categories = 0
        
        for category in news_entities:
            if category in topic_entities:
                news_items = news_entities[category]
                topic_items = topic_entities[category]
                
                if news_items and topic_items:
                    matches = 0
                    for news_item in news_items:
                        for topic_item in topic_items:
                            if news_item == topic_item:
                                matches += 1.0
                            elif news_item in topic_item or topic_item in news_item:
                                matches += 0.7
                            elif len(set(news_item) & set(topic_item)) >= 2:
                                matches += 0.3
                    
                    if news_items or topic_items:
                        category_score = matches / max(len(news_items), len(topic_items))
                        total_score += category_score
                        total_categories += 1
        
        return total_score / max(total_categories, 1)
    
    def calculate_keyword_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """計算關鍵字集合的相似度"""
        if not keywords1 or not keywords2:
            return 0.0
        
        set1 = set(keywords1)
        set2 = set(keywords2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """使用 TF-IDF 計算文本相似度"""
        if not text1 or not text2:
            return 0.0
        
        try:
            # 組合文本進行向量化
            texts = [text1, text2]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # 計算餘弦相似度
            similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return float(similarity_matrix[0][0])
            
        except Exception as e:
            logger.error(f"計算文本相似度時發生錯誤: {e}")
            return 0.0
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """使用 SentenceTransformer 計算語義相似度"""
        if not text1 or not text2 or not self.embedding_model:
            return 0.0
        
        try:
            # 生成句子嵌入
            embeddings = self.embedding_model.encode([text1, text2])
            
            # 計算餘弦相似度
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])
            return float(similarity[0][0])
            
        except Exception as e:
            logger.error(f"計算語義相似度時發生錯誤: {e}")
            return 0.0
    
    def learn_topic_features_from_data(self, topic_title: str) -> Dict[str, float]:
        """從主題標題中動態學習特徵"""
        features = {}
        
        # 提取主題關鍵詞
        keywords = self.extract_keywords(topic_title, topK=10)
        
        # 為每個關鍵詞分配權重（基於詞長和位置）
        for i, keyword in enumerate(keywords):
            # 越前面的關鍵詞權重越高
            weight = (len(keywords) - i) / len(keywords)
            # 越長的詞權重越高
            weight *= min(len(keyword) / 3, 2.0)
            features[keyword] = weight
        
        # 提取實體
        entities = self.extract_named_entities(topic_title)
        for category, items in entities.items():
            for item in items:
                features[item] = 1.5  # 實體權重較高
        
        return features
    
    def calculate_dynamic_topic_match(self, text: str, topic_features: Dict[str, float]) -> float:
        """使用動態學習的特徵計算匹配分數"""
        if not topic_features:
            return 0.0
        
        text_lower = text.lower()
        total_score = 0.0
        max_possible_score = sum(topic_features.values())
        
        for feature, weight in topic_features.items():
            if feature.lower() in text_lower:
                total_score += weight
        
        return total_score / max_possible_score if max_possible_score > 0 else 0.0
    
    def calculate_learned_feature_match(self, text: str, topic_title: str) -> float:
        """計算與動態學習特徵的匹配分數"""
        # 為每個主題動態生成特徵
        topic_features = self.learn_topic_features_from_data(topic_title)
        return self.calculate_dynamic_topic_match(text, topic_features)
    
    def classify_news_lightweight(self, news_data: Dict) -> Tuple[str, float]:
        """改進的新聞分類（使用動態學習特徵）"""
        if not news_data or not self.topics:
            return None, 0.0
        
        best_topic_id = None
        best_score = 0.0
        
        # 提取新聞的關鍵字和實體
        news_title_keywords = self.extract_keywords(news_data.get("title", ""), topK=5)
        news_content_keywords = self.extract_keywords(news_data.get("content", ""), topK=10)
        news_existing_keywords = news_data.get("keywords", [])
        news_terms = news_data.get("terms", [])
        
        # 組合新聞文本
        news_full_text = f"{news_data.get('title', '')} {news_data.get('content', '')}"
        
        for topic in self.topics:
            topic_title = topic.get("topic_title", "")
            topic_keywords = self.extract_keywords(topic_title, topK=8)
            
            # 計算語義相似度（如果模型可用）
            semantic_title_sim = 0.0
            semantic_content_sim = 0.0
            if self.embedding_model:
                semantic_title_sim = self.calculate_semantic_similarity(news_data.get("title", ""), topic_title)
                semantic_content_sim = self.calculate_semantic_similarity(news_full_text, topic_title)
            
            # 計算動態學習特徵匹配分數
            learned_feature_score = self.calculate_learned_feature_match(news_full_text, topic_title)
            
            # 調整權重，重點使用動態學習特徵
            scores = {
                "learned_features": learned_feature_score * 0.50,  # 動態學習特徵權重最高
                "keyword_match": self.calculate_keyword_similarity(news_existing_keywords, topic_keywords) * 0.25,
                "title_keyword_match": self.calculate_keyword_similarity(news_title_keywords, topic_keywords) * 0.15,
                "semantic_title": semantic_title_sim * 0.06,
                "semantic_content": semantic_content_sim * 0.04
            }
            
            total_score = sum(scores.values())
            
            # 如果動態特徵匹配度很高，給予額外加分
            if learned_feature_score > 0.4:
                total_score += 0.1
            
            if total_score > best_score:
                best_score = total_score
                best_topic_id = topic["topic_id"]
        
        return best_topic_id, best_score
    
    async def classify_single_news(self, story_id: str, confidence_threshold: float = 0.3) -> Dict:
        """分類單一新聞"""
        # 取得新聞資料
        news_data = await self.get_news_with_features(story_id)
        if not news_data:
            return {
                "story_id": story_id,
                "success": False,
                "error": "無法取得新聞資料"
            }
        
        # 執行分類
        topic_id, confidence = self.classify_news_lightweight(news_data)
        
        # 找出對應的主題標題
        topic_title = "未找到主題"
        if topic_id and self.topics:
            for topic in self.topics:
                if topic["topic_id"] == topic_id:
                    topic_title = topic.get("topic_title", "未命名主題")
                    break
        
        result = {
            "story_id": story_id,
            "success": True,
            "topic_id": topic_id,
            "topic_title": topic_title,
            "confidence": confidence,
            "classification_method": "lightweight",
            "news_title": news_data.get("title", ""),
            "news_content": news_data.get("content", "")[:200] + "..." if len(news_data.get("content", "")) > 200 else news_data.get("content", ""),
            "news_category": news_data.get("category", ""),
            "keywords": news_data.get("keywords", []),
            "terms": news_data.get("terms", [])
        }
        
        # 不儲存到資料庫，只記錄分類結果
        if topic_id and confidence >= confidence_threshold:
            result["classification_status"] = "成功分類"
            logger.info(f"新聞 '{news_data.get('title', '')}' 已分類到主題 '{topic_title}'，信心度: {confidence:.3f}")
        else:
            result["classification_status"] = f"信心度不足 ({confidence:.3f} < {confidence_threshold})"
        
        return result
    
    async def batch_classify_news(self, limit: int = 100, confidence_threshold: float = 0.3) -> Dict:
        """批次分類新聞"""
        logger.info(f"開始批次分類新聞，限制: {limit}")
        
        try:
            # 取得所有新聞
            all_news_response = self.supabase.table("single_news").select("story_id").execute()
            all_news = [n["story_id"] for n in all_news_response.data]
            
            # 如果有限制，則只處理指定數量，否則處理全部
            if limit and limit > 0:
                news_to_classify = all_news[:limit]
            else:
                news_to_classify = all_news
            
            logger.info(f"找到 {len(all_news)} 篇新聞，將處理 {len(news_to_classify)} 篇")
            
            results = {
                "total_processed": len(news_to_classify),
                "successful_classifications": 0,
                "high_confidence": 0,  # >= 0.3
                "medium_confidence": 0,  # 0.1 - 0.3
                "low_confidence": 0,  # < 0.1
                "errors": 0,
                "details": []
            }
            
            for i, story_id in enumerate(news_to_classify):
                if i % 10 == 0:
                    logger.info(f"處理進度: {i}/{len(news_to_classify)}")
                
                result = await self.classify_single_news(story_id, confidence_threshold)
                results["details"].append(result)
                
                if result["success"]:
                    results["successful_classifications"] += 1
                    confidence = result.get("confidence", 0)
                    if confidence >= 0.3:
                        results["high_confidence"] += 1
                    elif confidence >= 0.1:
                        results["medium_confidence"] += 1
                    else:
                        results["low_confidence"] += 1
                else:
                    results["errors"] += 1
            
            logger.info(f"批次分類完成: {results['high_confidence']} 篇高信心度分類")
            return results
            
        except Exception as e:
            logger.error(f"批次分類時發生錯誤: {e}")
            return {"error": str(e)}
    
    def save_results_to_file(self, results: Dict, filename: str = "classification_results.json"):
        """將分類結果儲存到檔案"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"分類結果已儲存到 {filename}")
        except Exception as e:
            logger.error(f"儲存結果到檔案時發生錯誤: {e}")
    
    def generate_html_report(self, results: Dict, filename: str = "classification_report.html"):
        """生成HTML報告"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新聞分類結果報告</title>
    <style>
        body {{ font-family: 'Microsoft JhengHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .news-item {{ border: 1px solid #ddd; margin-bottom: 20px; border-radius: 8px; overflow: hidden; }}
        .news-header {{ background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }}
        .news-content {{ padding: 15px; }}
        .confidence-high {{ border-left: 4px solid #28a745; }}
        .confidence-medium {{ border-left: 4px solid #ffc107; }}
        .confidence-low {{ border-left: 4px solid #dc3545; }}
        .topic-match {{ background: #e7f3ff; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        .keywords {{ margin: 10px 0; }}
        .keyword {{ display: inline-block; background: #007bff; color: white; padding: 2px 8px; margin: 2px; border-radius: 3px; font-size: 0.8em; }}
        .confidence-bar {{ width: 100%; background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; }}
        .confidence-fill {{ height: 100%; transition: width 0.3s ease; }}
        .confidence-fill.high {{ background: #28a745; }}
        .confidence-fill.medium {{ background: #ffc107; }}
        .confidence-fill.low {{ background: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>新聞分類結果報告</h1>
            <p>生成時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{results.get('total_processed', 0)}</div>
                <div>總處理數量</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{results.get('successful_classifications', 0)}</div>
                <div>成功分類</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{results.get('high_confidence', 0)}</div>
                <div>高信心度</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{results.get('low_confidence', 0)}</div>
                <div>低信心度</div>
            </div>
        </div>
        
        <h2>分類詳細結果</h2>
"""
            
            for item in results.get('details', []):
                confidence = item.get('confidence', 0)
                confidence_class = 'high' if confidence >= 0.5 else 'medium' if confidence >= 0.3 else 'low'
                confidence_percent = confidence * 100
                
                html_content += f"""
        <div class="news-item confidence-{confidence_class}">
            <div class="news-header">
                <h3>{item.get('news_title', '未知標題')}</h3>
                <div class="topic-match">
                    <strong>分類結果:</strong> {item.get('topic_title', '未分類')} 
                    (信心度: {confidence:.3f})
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill {confidence_class}" style="width: {confidence_percent}%"></div>
                </div>
            </div>
            <div class="news-content">
                <p><strong>內容:</strong> {item.get('news_content', '無內容')}</p>
                <p><strong>分類:</strong> {item.get('news_category', '未知')}</p>
                <p><strong>狀態:</strong> {item.get('classification_status', '未知')}</p>
                
                <div class="keywords">
                    <strong>關鍵字:</strong>
                    {' '.join([f'<span class="keyword">{kw}</span>' for kw in item.get('keywords', [])])}
                </div>
                
                <div class="keywords">
                    <strong>專有名詞:</strong>
                    {' '.join([f'<span class="keyword">{term}</span>' for term in item.get('terms', [])])}
                </div>
            </div>
        </div>
"""
            
            html_content += """
    </div>
</body>
</html>
"""
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML報告已生成: {filename}")
            
        except Exception as e:
            logger.error(f"生成HTML報告時發生錯誤: {e}")
    
    async def get_classification_stats(self) -> Dict:
        """取得分類統計資訊"""
        try:
            # 統計總新聞數
            total_news = self.supabase.table("single_news").select("story_id", count="exact").execute()
            total_count = total_news.count
            
            # 統計已分類新聞數
            classified_news = self.supabase.table("topic_news_map").select("story_id", count="exact").execute()
            classified_count = classified_news.count
            
            # 統計各主題的新聞數量
            topic_stats = {}
            for topic in self.topics:
                topic_id = topic["topic_id"]
                topic_news_count = self.supabase.table("topic_news_map").select(
                    "story_id", count="exact"
                ).eq("topic_id", topic_id).execute()
                
                topic_stats[topic["topic_title"]] = {
                    "topic_id": topic_id,
                    "news_count": topic_news_count.count
                }
            
            return {
                "total_news": total_count,
                "classified_news": classified_count,
                "unclassified_news": total_count - classified_count,
                "classification_rate": f"{(classified_count/total_count*100):.1f}%" if total_count > 0 else "0%",
                "topic_distribution": topic_stats
            }
            
        except Exception as e:
            logger.error(f"取得統計資訊時發生錯誤: {e}")
            return {"error": str(e)}


# 測試函數
async def main():
    classifier = NewsClassifier()
    await classifier.initialize()
    
    # 取得統計資訊
    stats = await classifier.get_classification_stats()
    print("=== 分類統計 ===")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 執行批次分類（處理所有新聞，或者您可以設定限制數量）
    print("\n=== 開始批次分類測試 ===")
    # 如果要處理所有新聞，設定 limit=0 或 limit=None
    # 如果只想測試一部分，可以設定如 limit=50
    results = await classifier.batch_classify_news(limit=0, confidence_threshold=0.1)  # 降低閾值到 0.1
    
    # 儲存結果到檔案
    classifier.save_results_to_file(results, "classification_results.json")
    
    # 生成HTML報告
    classifier.generate_html_report(results, "classification_report.html")
    
    print("批次分類結果:")
    print(json.dumps({k: v for k, v in results.items() if k != 'details'}, indent=2, ensure_ascii=False))
    
    print(f"\n結果已儲存到:")
    print(f"- JSON檔案: classification_results.json")
    print(f"- HTML報告: classification_report.html")
    
    # 顯示前幾個分類結果的簡要資訊
    print(f"\n前5個分類結果:")
    for i, detail in enumerate(results.get('details', [])[:5]):
        print(f"{i+1}. {detail.get('news_title', '未知')} -> {detail.get('topic_title', '未分類')} (信心度: {detail.get('confidence', 0):.3f})")


if __name__ == "__main__":
    asyncio.run(main())
