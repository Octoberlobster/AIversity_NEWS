import feedparser
import time
import datetime
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, parse_qs
import schedule
from supabase import create_client, Client
import uuid
import os
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings()

@dataclass
class NewsItem:
    """新聞項目資料類別"""
    source: str
    title: str
    url: str
    date: str
    content: str = ""
    image: str = ""
    sourcecle_id: str = ""

class DatabaseManager:
    """資料庫管理類別"""
    
    def __init__(self):
        self.supabase_url = os.getenv("API_KEY_URL")
        self.supabase_key = os.getenv("API_KEY_supa")
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # 欄位對應表
        self.key_map = {
            "title": "title", "Title": "title",
            "url": "url", "URL": "url",
            "date": "date", "Date": "date",
            "content": "content", "translatedcontent": "content", "Content": "content",
            "source": "sourcecle_media", "Source": "sourcecle_media",
            "image": "image", "Image": "image",
        }
    
    def normalize_key(self, key: str) -> str:
        """標準化鍵名"""
        return self.key_map.get(key.lower(), key.lower())
    
    def transform_item(self, item: Dict) -> Dict:
        """轉換單個項目"""
        if isinstance(item, dict):
            transformed = {self.normalize_key(k): v for k, v in item.items()}
            transformed["sourcecle_id"] = self._generate_uuid(item.get("sourcecle_id", ""))
            return transformed
        return item
    
    def _generate_uuid(self, val: str) -> str:
        """生成或驗證 UUID"""
        try:
            return str(uuid.UUID(val))
        except:
            return str(uuid.uuid4())
    
    def save_to_database(self, news_data: List[NewsItem]) -> None:
        """儲存資料到資料庫"""
        try:
            converted_data = [self.transform_item(item.__dict__) for item in news_data[:400]]
            
            for item in converted_data:
                self.client.table("cleaned_news").upsert(
                    item, on_conflict="title"
                ).execute()
            
            logger.info(f"✅ 資料處理完成，共處理 {len(converted_data)} 筆")
        except Exception as e:
            logger.error(f"❌ 匯入失敗：{e}")

class ContentExtractor(ABC):
    """內容提取器抽象基類"""
    
    @abstractmethod
    def extract_content(self, source_data: str) -> str:
        """提取新聞內容"""
        pass
    
    @abstractmethod
    def extract_image(self, news_url: str) -> str:
        """提取新聞圖片"""
        pass

class UDNContentExtractor(ContentExtractor):
    """UDN 內容提取器"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            'Connection': 'close',
        }
        self.excluded_keywords = [
            "延伸閱讀", "責任編輯", "核稿編輯", "▪", "不用抽", "【", 
            "一手掌握經濟脈動", "本網站之文字", "APP", "點我下載APP", 
            "活動辦法", "請繼續往下閱讀", "圖／", "資料照／", "中央社記者",
            "記者宋健生/攝影", "／攝影", "／翻攝", "／台南報導", "／台中報導",
            "／綜合報導", "／新北報導", "／高雄報導", "／彰化報導", "▲",
            "圖文／CTWANT", "／編譯", "／桃園報導", "／台東報導", "／台北報導"
        ]
    
    def extract_content(self, news_url: str) -> str:
        """提取 UDN 新聞內容"""
        try:
            response = requests.get(news_url, headers=self.headers, timeout=10)
            response.encoding = "utf-8"
            
            logger.info(f"訪問新聞: {news_url}，狀態碼: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning("❌ 無法訪問新聞內文")
                return ""
            
            return self._parse_content(response.text)
            
        except Exception as e:
            logger.error(f"❌ 提取內容時發生錯誤: {e}")
            return ""
    
    def _parse_content(self, html_text: str) -> str:
        """解析 HTML 內容"""
        content_selectors = [
            {'tag': 'div', 'attrs': {'data-desc': '內文'}},
            {'tag': 'div', 'attrs': {'data-desc': '內容頁'}},
            {'tag': 'div', 'class_': 'text boxTitle boxText'},
            {'tag': 'div', 'class_': 'paragraph'},
            {'tag': 'section', 'class_': 'article-content__editor'},
            {'tag': 'div', 'class_': 'story'}
        ]
        
        content_sections = self._find_content_sections(html_text, content_selectors)
        
        if not content_sections:
            # 嘗試從特定位置開始解析
            content_sections = self._find_content_sections(html_text[50000:], content_selectors)
        
        return self._extract_text_from_sections(content_sections)
    
    def _find_content_sections(self, html_text: str, selectors: List[Dict]) -> List:
        """尋找內容區塊"""
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            for selector in selectors:
                if 'attrs' in selector:
                    sections = soup.find_all(selector['tag'], attrs=selector['attrs'])
                else:
                    sections = soup.find_all(selector['tag'], class_=selector['class_'])
                if sections:
                    return sections
        except Exception as e:
            logger.error(f"❌ 解析 HTML 時發生錯誤: {e}")
        return []
    
    def _extract_text_from_sections(self, content_sections: List) -> str:
        """從內容區塊提取文字"""
        content = []
        
        for section in content_sections:
            paragraphs = section.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                
                # 檢查是否為結束關鍵字
                if any(kw in text for kw in self.excluded_keywords[:6]):
                    break
                
                # 檢查是否為排除內容
                if self._should_exclude_paragraph(p, text):
                    continue
                
                content.append(text)
        
        return " ".join(content)
    
    def _should_exclude_paragraph(self, paragraph, text: str) -> bool:
        """判斷段落是否應該排除"""
        if paragraph.find('iframe'):
            return True
        
        return any(kw in text for kw in self.excluded_keywords[6:])
    
    def extract_image(self, news_url: str) -> str:
        """提取 UDN 新聞圖片"""
        return self._extract_image_from_url(news_url)
    
    def _extract_image_from_url(self, news_url: str) -> str:
        """從 URL 提取圖片"""
        try:
            response = requests.get(news_url, headers=self.headers, timeout=10)
            response.encoding = "utf-8"
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text[30000:], 'html.parser')
                return self._find_main_image(soup)
                
        except Exception as e:
            logger.error(f"❌ 提取圖片時發生錯誤: {e}")
        return ""
    
    def _find_main_image(self, soup) -> str:
        """尋找主要圖片"""
        # 尋找特定的圖片容器
        img_containers = [
            soup.find("div", class_="image-popup-vertical-fit"),
            soup.find("div", class_="fullPic")
        ]
        
        for container in img_containers:
            if container:
                img_url = self._extract_image_from_container(container)
                if img_url:
                    return img_url
        
        # 在文章內容中尋找圖片
        for p in soup.select('div.text.boxTitle.boxText p'):
            img = p.find('img')
            if img:
                img_url = img.get('data-src') or img.get('src')
                if img_url:
                    return img_url
        
        return ""
    
    def _extract_image_from_container(self, container) -> str:
        """從容器中提取圖片 URL"""
        if container.has_attr('href'):
            return container["href"]
        
        img_element = container.find('img')
        if img_element:
            return img_element.get('data-src') or img_element.get('src', '')
        
        return ""

class NewTalkContentExtractor(ContentExtractor):
    """NewTalk 內容提取器"""
    
    def extract_content(self, content_str: str) -> str:
        """提取 NewTalk 新聞內容"""
        content = []
        soup = BeautifulSoup(content_str, 'html.parser')
        
        if soup:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                
                if any(kw in text for kw in ["延伸閱讀", "責任編輯", "核稿編輯", "▪", "本網站之文字"]):
                    break
                elif '中央社記者' in text or '圖為' in text:
                    continue
                
                content.append(text)
        
        return " ".join(content)
    
    def extract_image(self, news_url: str) -> str:
        """提取 NewTalk 新聞圖片"""
        return UDNContentExtractor()._extract_image_from_url(news_url)

class NewsSource:
    """新聞來源配置"""
    
    SOURCES = {
        "UDN": "https://udn.com/news/rssfeed/",
        "ETtoday": "https://feeds.feedburner.com/ettoday/realtime",
        "NewTalk": "https://newtalk.tw/rss/all/",
        "CNA": [
            "https://feeds.feedburner.com/rsscna/politics",
            "https://feeds.feedburner.com/rsscna/intworld",
            "https://feeds.feedburner.com/rsscna/mainland",
            "https://feeds.feedburner.com/rsscna/finance",
            "https://feeds.feedburner.com/rsscna/technology",
            "https://feeds.feedburner.com/rsscna/lifehealth",
            "https://feeds.feedburner.com/rsscna/social",
            "https://feeds.feedburner.com/rsscna/local",
            "https://feeds.feedburner.com/rsscna/culture",
            "https://feeds.feedburner.com/rsscna/sport",
            "https://feeds.feedburner.com/rsscna/stars",
        ],
    }

class NewsCrawler:
    """新聞爬蟲主類別"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.extractors = {
            "UDN": UDNContentExtractor(),
            "ETtoday": UDNContentExtractor(),
            "LTN": UDNContentExtractor(),
            "CNA": UDNContentExtractor(),
            "NewTalk": NewTalkContentExtractor(),
        }
    
    def crawl_news(self) -> None:
        """爬取新聞主函數"""
        logger.info("開始爬取新聞...")
        
        news_data = []
        time_filter = self._get_time_filter()
        
        for source, urls in NewsSource.SOURCES.items():
            if isinstance(urls, str):
                urls = [urls]
            
            for url in urls:
                news_items = self._process_rss_feed(source, url, time_filter)
                news_data.extend(news_items)
        
        # 儲存到檔案
        self._save_to_json(news_data)
        
        # 儲存到資料庫
        self.db_manager.save_to_database(news_data)
        
        logger.info(f"爬取完成，共處理 {len(news_data)} 則新聞")
    
    def _get_time_filter(self) -> datetime.datetime:
        """取得時間過濾器（一小時前）"""
        current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        return current_time - datetime.timedelta(hours=1)
    
    def _process_rss_feed(self, source: str, url: str, time_filter: datetime.datetime) -> List[NewsItem]:
        """處理 RSS 源"""
        news_items = []
        
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                if "現場直播中" in entry.get("title", ""):
                    logger.info(f"跳過現場直播新聞: {entry.title}")
                    continue
                
                # 解析發布時間
                publish_time = self._parse_publish_time(entry, source)
                if not publish_time or publish_time < time_filter:
                    continue
                
                # 建立新聞項目
                news_item = self._create_news_item(source, entry, publish_time)
                if not news_item.content:
                    logger.warning(f"⚠️ 無法提取內容: {news_item.title}")
                    continue
                news_items.append(news_item)
                
                logger.info(f"處理新聞: {news_item.title}")
                
        except Exception as e:
            logger.error(f"處理 RSS 源 {url} 時發生錯誤: {e}")
        
        return news_items
    
    def _parse_publish_time(self, entry, source: str) -> Optional[datetime.datetime]:
        """解析發布時間"""
        dt = None
        
        if entry.get("published_parsed"):
            t = entry.published_parsed
            dt = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
        elif entry.get("published"):
            try:
                date_str = entry.published.replace(',', ', ')
                t_struct = time.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                dt = datetime.datetime.fromtimestamp(time.mktime(t_struct))
            except Exception as e:
                logger.warning(f"⚠️ 無法解析 published 字串: {entry.published}，錯誤: {e}")
        
        # 時區補正
        if dt and source in ["CNA", "UDN", "NewTalk"]:
            dt = dt + datetime.timedelta(hours=8)
            logger.info(f"發布時間：{dt.strftime('%Y/%m/%d %H:%M')}")
        
        return dt
    
    def _create_news_item(self, source: str, entry, publish_time: datetime.datetime) -> NewsItem:
        """建立新聞項目"""
        # 基本資訊
        news_item = NewsItem(
            source=source,
            title=entry.title,
            url=entry.link,
            date=entry.get("pubDate", publish_time.strftime("%Y/%m/%d %H:%M"))
        )
        
        # 提取圖片
        news_item.image = self._extract_image(entry, source)
        
        # 提取內容
        news_item.content = self._extract_content(source, entry)
        
        return news_item
    
    def _extract_image(self, entry, source: str) -> str:
        """提取圖片 URL"""
        image_url = None
        
        # 從 RSS 中提取圖片
        if "enclosures" in entry and entry.enclosures:
            image_url = entry.enclosures[0].href
        elif "media_content" in entry:
            image_url = entry.media_content[0]["url"][5:]
        elif "description" in entry:
            soup = BeautifulSoup(entry.description, "html.parser")
            img_tag = soup.find("img")
            if img_tag:
                parsed_url = urlparse(img_tag["src"])
                query_params = parse_qs(parsed_url.query)
                image_url = query_params.get("u", [""])[0]
        
        # 如果沒有找到圖片，嘗試從新聞頁面提取
        if not image_url and source in self.extractors:
            image_url = self.extractors[source].extract_image(entry.link)
        
        return image_url or ""
    
    def _extract_content(self, source: str, entry) -> str:
        """提取新聞內容"""
        if source not in self.extractors:
            return ""
        
        extractor = self.extractors[source]
        
        if source == "NewTalk":
            return extractor.extract_content(entry.description)
        else:
            return extractor.extract_content(entry.link)
    
    def _save_to_json(self, news_data: List[NewsItem]) -> None:
        """儲存到 JSON 檔案"""
        timestamp = time.strftime("%Y_%m_%d_%H", time.localtime())
        json_path = f"json/{timestamp}.json"
        
        # 確保目錄存在
        os.makedirs("json", exist_ok=True)
        
        # 轉換為字典格式
        data_dict = [item.__dict__ for item in news_data]
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=4)
        
        logger.info(f"新聞資料已儲存至 {json_path}，共 {len(news_data)} 則新聞")

def main():
    """主函數"""
    crawler = NewsCrawler()
    
    # 立即執行一次
    crawler.crawl_news()
    
    # 設定排程（每 59 分鐘執行一次）
    schedule.every(59).minutes.do(crawler.crawl_news)
    
    # 持續運行排程
    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    main()
