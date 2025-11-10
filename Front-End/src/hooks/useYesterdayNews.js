import { useQuery } from '@tanstack/react-query';
import { useSupabase } from '../components/supabase';

/**
 * 自定義 Hook: 拉取昨日焦點新聞
 * 使用 React Query 管理快取和狀態
 * @param {string} country - 國家名稱
 * @param {string} dateTime - 日期時間字串，格式: "2025-11-07 00-06"
 * @param {string} currentLanguage - 當前語言
 */
export function useYesterdayNews(country, dateTime, currentLanguage = 'zh-TW') {
  const supabase = useSupabase();

  // 語言欄位後綴映射
  const LANGUAGE_SUFFIX_MAP = {
    'zh-TW': '',           // 中文使用原欄位名稱
    'en': '_en_lang',      // 英文欄位後綴
    'jp': '_jp_lang',      // 日文欄位後綴  
    'id': '_id_lang'       // 印尼文欄位後綴
  };

  const suffix = LANGUAGE_SUFFIX_MAP[currentLanguage] || '';

  return useQuery({
    // Query Key: 用於快取識別,加入語言參數和完整的日期時間
    queryKey: ['yesterday-news', country, dateTime, currentLanguage],
    
    // Query Function: 實際的資料請求
    queryFn: async () => {
      console.log('[useYesterdayNews] 開始載入:', {
        country,
        dateTime,
        currentLanguage,
        語言後綴: suffix
      });
      
      // 1. 拉取 top_ten_news
      console.log('[useYesterdayNews] 執行查詢:', {
        資料表: 'top_ten_news',
        查詢條件: { country, date: dateTime }
      });
      
      const { data: topTenData, error: topTenError } = await supabase
        .from('top_ten_news')
        .select('*')
        .eq('country', country)
        .eq('date', dateTime);

      console.log('[useYesterdayNews] 查詢結果:', {
        成功: !topTenError,
        錯誤: topTenError,
        資料筆數: topTenData?.length,
        原始資料: topTenData
      });

      if (topTenError) {
        console.error('[useYesterdayNews] 查詢錯誤:', topTenError);
        throw topTenError;
      }
      if (!topTenData || topTenData.length === 0) {
        console.warn('[useYesterdayNews] 無資料');
        return [];
      }

      // 2. 解析 story_ids
      const allStoryIds = [];
      topTenData.forEach(item => {
        console.log('[useYesterdayNews] 解析項目:', {
          原始: item.top_ten_news_id,
          型別: typeof item.top_ten_news_id
        });
        const parsedJson = typeof item.top_ten_news_id === 'string' 
          ? JSON.parse(item.top_ten_news_id) 
          : item.top_ten_news_id;
        console.log('[useYesterdayNews] 解析結果:', parsedJson);
        allStoryIds.push(...parsedJson.top_ten_story_ids);
      });

      console.log('[useYesterdayNews] 找到', allStoryIds.length, '個 story_ids:', allStoryIds);

      // 3. 批量拉取新聞基本資料 (文字內容) - 支援多語言
      const titleField = suffix ? `news_title, news_title${suffix}` : 'news_title';
      const summaryField = suffix ? `ultra_short, ultra_short${suffix}` : 'ultra_short';
      
      console.log('[useYesterdayNews] 準備查詢新聞:', {
        欄位: `story_id, ${titleField}, ${summaryField}`,
        story_ids: allStoryIds
      });
      
      const { data: newsData, error: newsError } = await supabase
        .from('single_news')
        .select(`story_id, ${titleField}, ${summaryField}, generated_date`)
        .in('story_id', allStoryIds);

      console.log('[useYesterdayNews] 新聞查詢結果:', {
        成功: !newsError,
        錯誤: newsError,
        資料筆數: newsData?.length,
        第一筆: newsData?.[0]
      });

      if (newsError) {
        console.error('[useYesterdayNews] 新聞查詢錯誤:', newsError);
        throw newsError;
      }

      // 4. 先返回文字資料 (不包含圖片和相關來源)
      const basicNews = newsData.map(news => ({
        id: news.story_id,
        // 優先使用翻譯欄位,沒有則 fallback 到原欄位
        title: suffix ? (news[`news_title${suffix}`] || news.news_title) : news.news_title,
        summary: suffix ? (news[`ultra_short${suffix}`] || news.ultra_short) : news.ultra_short,
        date: news.generated_date,
        // 標記為需要載入
        needsImage: true,
        needsSources: true,
      }));

      console.log('[useYesterdayNews] 基本資料載入完成:', basicNews.length, '筆');
      return basicNews;
    },
    
    // 啟用條件: 只有當 country 和 dateTime 都存在時才執行
    enabled: !!country && !!dateTime,
    
    // 快取設定
    staleTime: 10 * 60 * 1000, // 10分鐘內不重新請求
    cacheTime: 60 * 60 * 1000, // 快取1小時
  });
}

/**
 * 自定義 Hook: 拉取新聞圖片
 * 延遲載入,背景執行
 */
export function useNewsImages(storyIds) {
  const supabase = useSupabase();

  return useQuery({
    queryKey: ['news-images', storyIds],
    queryFn: async () => {
      if (!storyIds || storyIds.length === 0) return {};

      console.log('[useNewsImages] 開始載入圖片:', storyIds.length, '張');

      // 批量拉取圖片
      const { data, error } = await supabase
        .from('generated_image')
        .select('story_id, image')
        .in('story_id', storyIds);

      if (error) throw error;

      // 轉換為 Map 格式
      const imagesMap = {};
      data.forEach(item => {
        if (item.image) {
          const cleanBase64 = item.image.replace(/\s/g, '');
          imagesMap[item.story_id] = `data:image/png;base64,${cleanBase64}`;
        }
      });

      console.log('[useNewsImages] 圖片載入完成:', Object.keys(imagesMap).length, '張');
      return imagesMap;
    },
    enabled: !!storyIds && storyIds.length > 0,
    staleTime: 30 * 60 * 1000, // 圖片快取30分鐘
    cacheTime: 2 * 60 * 60 * 1000, // 快取2小時
  });
}

/**
 * 自定義 Hook: 拉取相關來源
 * 延遲載入,背景執行
 */
export function useRelatedSources(storyIds) {
  const supabase = useSupabase();

  return useQuery({
    queryKey: ['related-sources', storyIds],
    queryFn: async () => {
      if (!storyIds || storyIds.length === 0) return {};

      console.log('[useRelatedSources] 開始載入相關來源:', storyIds.length, '個新聞');

      // 批量拉取相關來源
      const { data, error } = await supabase
        .from('cleaned_news')
        .select('story_id, article_title, article_url, media')
        .in('story_id', storyIds);

      if (error) throw error;

      // 按 story_id 分組
      const sourcesMap = {};
      data.forEach(item => {
        if (!sourcesMap[item.story_id]) {
          sourcesMap[item.story_id] = [];
        }
        sourcesMap[item.story_id].push({
          id: sourcesMap[item.story_id].length + 1,
          media: item.media || new URL(item.article_url).hostname.replace('www.', ''),
          name: item.article_title,
          url: item.article_url,
        });
      });

      console.log('[useRelatedSources] 相關來源載入完成');
      return sourcesMap;
    },
    enabled: !!storyIds && storyIds.length > 0,
    staleTime: 10 * 60 * 1000, // 快取10分鐘
    cacheTime: 60 * 60 * 1000, // 快取1小時
  });
}
