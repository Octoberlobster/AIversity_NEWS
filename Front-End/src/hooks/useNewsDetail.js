import { useQuery } from '@tanstack/react-query';
import { useSupabase } from '../components/supabase';
import { useLanguageFields } from '../utils/useLanguageFields';

/**
 * 自定義 Hook: 拉取新聞基本資料 (NewsDetail)
 * 第一階段: 載入新聞標題、內容、分類等基本資訊
 */
export function useNewsData(storyId) {
  const supabase = useSupabase();
  const { getMultiLanguageSelect, getFieldName, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['news-data', storyId, currentLanguage],
    queryFn: async () => {
      const multiLangFields = ['news_title', 'ultra_short', 'long'];
      const selectFields = getMultiLanguageSelect(multiLangFields);

      const { data, error } = await supabase
        .from('single_news')
        .select(`${selectFields}, generated_date, updated_date, category, story_id, who_talk, position_flag, attribution, suicide_flag`)
        .eq('story_id', storyId);

      if (error) {
        throw new Error(`載入新聞資料失敗: ${error.message}`);
      }

      const row = data?.[0];
      if (!row) {
        throw new Error('找不到新聞資料');
      }

      // 使用多語言欄位
      const longContent = row[getFieldName('long')] || row.long;
      
      const newsData = {
        title: row[getFieldName('news_title')] || row.news_title,
        date: row.generated_date,
        updateDate: row.updated_date,
        author: 'Gemini',
        short: row[getFieldName('ultra_short')] || row.short,
        long: longContent,
        category: row.category,
        story_id: row.story_id,
        who_talk: row.who_talk,
        position_flag: row.position_flag,
        suicide_flag: row.suicide_flag || false
      };

      // 解析 attribution 資料
      let attributionData = null;
      if (row.attribution) {
        try {
          attributionData = typeof row.attribution === 'string' 
            ? JSON.parse(row.attribution) 
            : row.attribution;
        } catch (e) {
          console.error('解析歸因資料失敗:', e);
        }
      }

      return {
        newsData,
        attribution: attributionData
      };
    },
    enabled: !!supabase && !!storyId,
    staleTime: 10 * 60 * 1000, // 10 分鐘
    cacheTime: 30 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取新聞圖片
 * 第二階段: 背景載入新聞圖片
 */
export function useNewsImage(storyId) {
  const supabase = useSupabase();
  const { getFieldName, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['news-image', storyId, currentLanguage],
    queryFn: async () => {
      //console.log('[useNewsImage] 載入新聞圖片:', storyId);

      const { data, error } = await supabase
        .from('generated_image')
        .select('image, description')
        .eq('story_id', storyId);

      if (error) {
        //console.warn('載入圖片失敗:', error);
        return [];
      }

      if (!data || data.length === 0) {
        //console.log('[useNewsImage] 沒有圖片');
        return [];
      }

      // 轉換為舊格式的陣列 (向後兼容)
      const processed = data.map(item => {
        const src = item.image ? `data:image/png;base64,${item.image.replace(/\s/g, '')}` : '';
        const description = item[getFieldName('description')] || item.description || '';
        return {
          src,
          description,
        };
      });

      //console.log('[useNewsImage] 圖片載入完成:', processed.length, '張');
      return processed;
    },
    enabled: !!supabase && !!storyId,
    staleTime: 30 * 60 * 1000, // 圖片快取 30 分鐘
    cacheTime: 2 * 60 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取新聞來源 URL (從 cleaned_news 表)
 * 第三階段: 背景載入新聞來源 URL
 */
export function useNewsUrl(storyId) {
  const supabase = useSupabase();

  return useQuery({
    queryKey: ['news-url', storyId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('cleaned_news')
        .select('article_title, article_url, media, write_date')
        .eq('story_id', storyId);

      if (error) {
        console.warn('載入來源 URL 失敗:', error);
        return null;
      }

      if (!data || data.length === 0) {
        return null;
      }

      return data; // 回傳陣列格式
    },
    enabled: !!supabase && !!storyId,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取新聞關鍵字
 * 第四階段: 背景載入關鍵字
 */
export function useNewsKeywords(storyId) {
  const supabase = useSupabase();
  const { getFieldName, getMultiLanguageSelect, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['news-keywords', storyId, currentLanguage],
    queryFn: async () => {
      //console.log('[useNewsKeywords] 載入關鍵字:', storyId);

      // 查詢關鍵字,支援多語言
      const keywordMultiLangFields = ['keyword'];
      const keywordSelectFields = getMultiLanguageSelect(keywordMultiLangFields);

      const { data, error } = await supabase
        .from('keywords_map')
        .select(keywordSelectFields)
        .eq('story_id', storyId)
        .limit(3);

      if (error) {
        console.warn('載入關鍵字失敗:', error);
        return [];
      }

      // 回傳物件陣列格式 [{keyword: 'xxx'}] 以符合組件期望
      const keywords = (data || [])
        .map(item => ({ 
          keyword: item[getFieldName('keyword')] || item.keyword 
        }))
        .filter(item => item.keyword);

     //console.log('[useNewsKeywords] 關鍵字載入完成:', keywords.length, '個');
      return keywords;
    },
    enabled: !!supabase && !!storyId,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取新聞術語
 * 第五階段: 背景載入術語
 */
export function useNewsTerms(storyId) {
  const supabase = useSupabase();
  const { getFieldName, getMultiLanguageSelect, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['news-terms', storyId, currentLanguage],
    queryFn: async () => {
      //console.log('[useNewsTerms] 載入術語:', storyId);

      // 步驟 1: 獲取術語映射
      const { data: termMapData, error: mapError } = await supabase
        .from('term_map')
        .select('term_id')
        .eq('story_id', storyId);

      if (mapError) {
        console.warn('載入術語映射失敗:', mapError);
        return { terms: [], definitions: {} };
      }

      const termIds = (termMapData || [])
        .map(item => item.term_id)
        .filter(Boolean);

      if (termIds.length === 0) {
        //console.log('[useNewsTerms] 沒有術語');
        return { terms: [], definitions: {} };
      }

      // 步驟 2: 獲取術語定義,支援多語言
      const termMultiLangFields = ['term', 'definition', 'example'];
      const termSelectFields = getMultiLanguageSelect(termMultiLangFields);

      const { data: termData, error: termError } = await supabase
        .from('term')
        .select(`term_id, ${termSelectFields}`)
        .in('term_id', termIds);

      if (termError) {
        console.warn('載入術語定義失敗:', termError);
        return { terms: termIds, definitions: {} };
      }

      // 轉換為物件格式
      const definitions = {};
      const termsArray = [];
      
      (termData || []).forEach(item => {
        // 使用多語言欄位
        const term = item[getFieldName('term')] || item.term;
        const definition = item[getFieldName('definition')] || item.definition;
        const example = item[getFieldName('example')] || item.example;

        if (term && definition) {
          // 加入術語物件 (包含 term, definition, example)
          termsArray.push({
            term: term,
            definition: definition,
            example: example || null
          });
          
          // 同時建立 term 為 key 的映射
          definitions[term] = {
            definition: definition,
            example: example || null
          };
        }
      });

      //console.log('[useNewsTerms] 術語載入完成:', termsArray.length, '個');
      return { terms: termsArray, definitions };
    },
    enabled: !!supabase && !!storyId,
    staleTime: 30 * 60 * 1000, // 術語定義較少變動
    cacheTime: 2 * 60 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取來源文章詳細資訊
 * 第六階段: 背景載入來源文章
 */
export function useSourceArticles(storyId, attribution) {
  const supabase = useSupabase();

  return useQuery({
    queryKey: ['source-articles', storyId],
    queryFn: async () => {
      //console.log('[useSourceArticles] 載入來源文章');

      // 收集所有的 article_id
      const allArticleIds = new Set();
      Object.values(attribution || {}).forEach(ids => {
        if (Array.isArray(ids)) {
          ids.forEach(articleId => allArticleIds.add(articleId));
        }
      });

      if (allArticleIds.size === 0) {
        //console.log('[useSourceArticles] 沒有來源文章');
        return {};
      }

      const articleIdsArray = Array.from(allArticleIds);
      //console.log('[useSourceArticles] 載入', articleIdsArray.length, '篇來源文章');

      // 從 cleaned_news 表獲取來源文章資訊
      const { data, error } = await supabase
        .from('cleaned_news')
        .select('article_id, article_title, article_url, media')
        .in('article_id', articleIdsArray);

      if (error) {
        //console.warn('載入來源文章失敗:', error);
        return {};
      }

      // 轉換為物件格式 {article_id: {title, url, media}}
      const articlesMap = {};
      if (data) {
        data.forEach(article => {
          articlesMap[article.article_id] = {
            title: article.article_title || '無標題',
            url: article.article_url || '#',
            media: article.media || '未知來源'
          };
        });
      }

      //console.log('[useSourceArticles] 來源文章載入完成:', Object.keys(articlesMap).length, '篇');
      return articlesMap;
    },
    enabled: !!supabase && !!storyId && !!attribution && Object.keys(attribution || {}).length > 0,
    staleTime: 30 * 60 * 1000, // 來源文章資訊較穩定
    cacheTime: 2 * 60 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取立場資料 (正反方觀點)
 * 第七階段: 背景載入立場資料
 */
export function usePositionData(storyId, shouldLoad) {
  const supabase = useSupabase();
  const { getFieldName, getMultiLanguageSelect, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['position-data', storyId, currentLanguage],
    queryFn: async () => {
      //console.log('[usePositionData] 載入立場資料');

      // 查詢正反方立場,支援多語言
      const positionMultiLangFields = ['positive', 'negative'];
      const positionSelectFields = getMultiLanguageSelect(positionMultiLangFields);

      const { data, error } = await supabase
        .from('position')
        .select(positionSelectFields)
        .eq('story_id', storyId);

      if (error) {
        console.warn('載入立場資料失敗:', error);
        return { positive: [], negative: [] };
      }

      const positionRow = data?.[0];
      if (positionRow) {
        // 處理多語言立場資料
        const positive = positionRow[getFieldName('positive')] || positionRow.positive;
        const negative = positionRow[getFieldName('negative')] || positionRow.negative;

        //console.log('[usePositionData] 立場資料載入完成');
        return {
          positive: positive || [],
          negative: negative || []
        };
      }

      //console.log('[usePositionData] 沒有立場資料');
      return { positive: [], negative: [] };
    },
    enabled: !!supabase && !!storyId && shouldLoad,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取專家分析資料
 * 第八階段: 背景載入專家分析
 */
export function useExpertAnalysis(storyId, shouldLoad) {
  const supabase = useSupabase();
  const { getFieldName, getMultiLanguageSelect, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['expert-analysis', storyId, currentLanguage],
    queryFn: async () => {
      //console.log('[useExpertAnalysis] 載入專家分析');

      // 查詢專家分析,支援多語言
      const analyzeMultiLangFields = ['analyze'];
      const analyzeSelectFields = getMultiLanguageSelect(analyzeMultiLangFields);

      const { data, error } = await supabase
        .from('pro_analyze')
        .select(`analyze_id, category, ${analyzeSelectFields}`)
        .eq('story_id', storyId);

      if (error) {
        console.warn('載入專家分析失敗:', error);
        return [];
      }

      // 處理多語言分析資料
      const analysisData = (data || []).map(item => ({
        analyze_id: item.analyze_id,
        category: item.category,
        analyze: item[getFieldName('analyze')] || item.analyze
      }));

      //console.log('[useExpertAnalysis] 專家分析載入完成:', analysisData.length, '個');
      return analysisData;
    },
    enabled: !!supabase && !!storyId && shouldLoad,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取相關新聞
 * 第九階段: 背景載入相關新聞
 */
export function useRelatedNews(storyId) {
  const supabase = useSupabase();
  const { getFieldName, getMultiLanguageSelect, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['related-news', storyId, currentLanguage],
    queryFn: async () => {
      //console.log('[useRelatedNews] 載入相關新聞');

      // 準備 reason 的多語言欄位查詢
      const reasonMultiLangFields = ['reason'];
      const reasonSelectFields = getMultiLanguageSelect(reasonMultiLangFields);

      // 查詢相關新聞 - 找出以當前新聞為 src_story_id 的相關新聞
      const { data: relatedData, error: relatedError } = await supabase
        .from('relative_news')
        .select(`
          dst_story_id,
          ${reasonSelectFields}
        `)
        .eq('src_story_id', storyId)
        .limit(3);

      if (relatedError) {
        console.warn('載入相關新聞失敗:', relatedError);
        return [];
      }

      // 如果沒有相關新聞
      if (!relatedData || relatedData.length === 0) {
        //console.log('[useRelatedNews] 沒有相關新聞');
        return [];
      }

      // 獲取所有目標新聞的 story_id
      const targetStoryIds = relatedData.map(item => item.dst_story_id);

      // 查詢目標新聞的詳細資料,支援多語言
      const newsMultiLangFields = ['news_title'];
      const newsSelectFields = getMultiLanguageSelect(newsMultiLangFields);

      const { data: newsData, error: newsError } = await supabase
        .from('single_news')
        .select(`story_id, ${newsSelectFields}`)
        .in('story_id', targetStoryIds);

      if (newsError) {
        console.warn('載入相關新聞標題失敗:', newsError);
        return [];
      }

      // 合併資料並進行資料清理
      const related = relatedData.map(relatedItem => {
        const newsItem = newsData?.find(n => n.story_id === relatedItem.dst_story_id);

        // 資料清理:如果 reason 過長,可能是錯誤的內容,截短它
        let reason = relatedItem[getFieldName('reason')] || relatedItem.reason || '無相關性說明';
        if (reason.length > 200) {
          reason = reason.substring(0, 200) + '...';
        }

        // 使用多語言標題,如果不存在則使用原標題作為 fallback
        let title = newsItem ? (newsItem[getFieldName('news_title')] || newsItem.news_title) : '';
        if (!title || !title.trim()) {
          title = `新聞 ID: ${relatedItem.dst_story_id}`;
        }

        return {
          id: relatedItem.dst_story_id, // 使用 id 而非 story_id 以符合組件期望
          title: title.trim(),
          relevance: reason.trim() // 使用 relevance 而非 reason 以符合組件期望
        };
      }).filter(item => item.title && !item.title.startsWith('新聞 ID:')); // 過濾掉沒有標題的項目

      //console.log('[useRelatedNews] 相關新聞載入完成:', related.length, '篇');
      return related;
    },
    enabled: !!supabase && !!storyId,
    staleTime: 15 * 60 * 1000, // 相關新聞較穩定
    cacheTime: 60 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取相關專題
 * 第十階段: 背景載入相關專題 (從 topic_news_map 查詢)
 */
export function useRelatedTopics(storyId) {
  const supabase = useSupabase();
  const { getFieldName, getMultiLanguageSelect, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['related-topics', storyId, currentLanguage],
    queryFn: async () => {
      //console.log('[useRelatedTopics] 載入相關專題');

      // 從 topic_news_map 查詢當前新聞所屬的專題
      const { data: topicMapData, error: mapError } = await supabase
        .from('topic_news_map')
        .select('topic_id')
        .eq('story_id', storyId);

      if (mapError) {
        console.warn('載入專題映射失敗:', mapError);
        return [];
      }

      // 如果沒有相關專題
      if (!topicMapData || topicMapData.length === 0) {
        //console.log('[useRelatedTopics] 沒有相關專題');
        return [];
      }

      // 獲取所有專題的 topic_id
      const topicIds = topicMapData.map(item => item.topic_id);

      // 查詢專題的詳細資料,支援多語言
      const topicMultiLangFields = ['topic_title'];
      const topicSelectFields = getMultiLanguageSelect(topicMultiLangFields);

      const { data: topicData, error: topicError } = await supabase
        .from('topic')
        .select(`topic_id, ${topicSelectFields}`)
        .in('topic_id', topicIds);

      if (topicError) {
        console.warn('載入專題標題失敗:', topicError);
        return [];
      }

      // 轉換為組件需要的格式
      const topics = (topicData || []).map(topicItem => {
        // 使用多語言標題,如果不存在則使用原標題作為 fallback
        let title = topicItem[getFieldName('topic_title')] || topicItem.topic_title || '';
        
        return {
          id: topicItem.topic_id,
          title: title.trim()
        };
      }).filter(item => item.title); // 過濾掉沒有標題的項目

      //console.log('[useRelatedTopics] 相關專題載入完成:', topics.length, '個');
      return topics;
    },
    enabled: !!supabase && !!storyId,
    staleTime: 15 * 60 * 1000, // 相關專題較穩定
    cacheTime: 60 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 查詢國家觀點分析
 * 統一從台灣觀點分析新聞，不管新聞所屬國家
 */
export function useCountryAnalysis(storyId) {
  const supabase = useSupabase();
  const { getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['country-analysis', storyId, currentLanguage],
    queryFn: async () => {
      //console.log('[useCountryAnalysis] 開始查詢台灣觀點:', storyId);

      // 直接查詢 country_pro_analyze 表，固定使用 Taiwan
      const { data: analysisData, error: analysisError } = await supabase
        .from('country_pro_analyze')
        .select('analyze_id, country, analyze, analyze_en_lang, analyze_id_lang, analyze_jp_lang')
        .eq('story_id', storyId)
        .eq('country', 'Taiwan');

      if (analysisError) {
        console.error('[useCountryAnalysis] 查詢分析錯誤:', analysisError);
        throw new Error(`載入台灣觀點失敗: ${analysisError.message}`);
      }

      const analysis = analysisData?.[0];
      
      if (!analysis) {
        //console.log('[useCountryAnalysis] 沒有找到台灣觀點資料');
        return { country: 'Taiwan', analysis: null };
      }

      //console.log('[useCountryAnalysis] 台灣觀點載入完成');
      return { country: 'Taiwan', analysis };
    },
    enabled: !!supabase && !!storyId,
    staleTime: 15 * 60 * 1000, // 15 分鐘
    cacheTime: 30 * 60 * 1000,
  });
}

/**
 * 載入媒體素養提醒
 * @param {string} storyId - 新聞 ID
 * @returns {UseQueryResult} React Query 結果
 */
export function useMediaLiteracy(storyId) {
  const supabase = useSupabase();
  const { getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useQuery({
    queryKey: ['media-literacy', storyId, currentLanguage],
    queryFn: async () => {
      //console.log('[useMediaLiteracy] 開始查詢媒體素養提醒:', storyId);

      // 查詢 media_literacy 表
      const { data: literacyData, error: literacyError } = await supabase
        .from('media_literacy')
        .select('media_literacy_id, alert, alert_en_lang, alert_id_lang, alert_jp_lang')
        .eq('story_id', storyId);

      if (literacyError) {
        console.error('[useMediaLiteracy] 查詢錯誤:', literacyError);
        throw new Error(`載入媒體素養提醒失敗: ${literacyError.message}`);
      }

      const literacy = literacyData?.[0];
      
      if (!literacy) {
        //console.log('[useMediaLiteracy] 沒有找到媒體素養提醒資料');
        return { literacy: null };
      }

      //console.log('[useMediaLiteracy] 媒體素養提醒載入完成');
      return { literacy };
    },
    enabled: !!supabase && !!storyId,
    staleTime: 15 * 60 * 1000, // 15 分鐘
    cacheTime: 30 * 60 * 1000,
  });
}

