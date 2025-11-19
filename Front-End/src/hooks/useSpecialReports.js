import { useQuery } from '@tanstack/react-query';
import { useSupabase } from '../components/supabase';
import { useLanguageFields } from '../utils/useLanguageFields';

/**
 * 自定義 Hook: 拉取專題報導列表 (SpecialReportPage)
 * 分階段載入: 基本資訊 → 新聞數量統計
 */
export function useSpecialReportsList() {
  const supabase = useSupabase();
  const { getMultiLanguageSelect } = useLanguageFields();

  // 階段 1: 獲取專題新聞對應關係
  const topicCountsQuery = useQuery({
    queryKey: ['topic-news-counts'],
    queryFn: async () => {
      console.log('[useSpecialReportsList] 載入專題新聞對應關係');

      const { data, error } = await supabase
        .from('topic_news_map')
        .select('topic_id, story_id');

      if (error) {
        throw new Error(`無法獲取專題新聞對應關係: ${error.message}`);
      }

      if (!data || data.length === 0) {
        return { topicCounts: {}, validTopicIds: [] };
      }

      console.log('[useSpecialReportsList] topic_news_map 原始資料筆數:', data.length);

      // 計算每個 topic_id 的不重複 story_id 數量
      const topicStoryMap = {};
      data.forEach(item => {
        if (item.topic_id && item.story_id) {
          if (!topicStoryMap[item.topic_id]) {
            topicStoryMap[item.topic_id] = new Set();
          }
          topicStoryMap[item.topic_id].add(item.story_id);
        }
      });

      // 轉換為數量
      const topicCounts = {};
      Object.entries(topicStoryMap).forEach(([topicId, storySet]) => {
        topicCounts[topicId] = storySet.size;
        console.log(`[useSpecialReportsList] 專題 ${topicId}: ${storySet.size} 篇文章 (不重複)`);
      });

      const validTopicIds = Object.keys(topicCounts).filter(id => id.trim() !== '');

      console.log('[useSpecialReportsList] 專題統計:', validTopicIds.length, '個專題');
      console.log('[useSpecialReportsList] topicCounts:', topicCounts);
      return { topicCounts, validTopicIds };
    },
    enabled: !!supabase,
    staleTime: 0, // 改為 0,強制重新載入
    cacheTime: 30 * 60 * 1000,
  });

  // 階段 2: 獲取專題基本資訊 (依賴階段 1)
  const topicDetailsQuery = useQuery({
    queryKey: ['topic-details', topicCountsQuery.data?.validTopicIds],
    queryFn: async () => {
      const validTopicIds = topicCountsQuery.data?.validTopicIds || [];
      
      if (validTopicIds.length === 0) {
        console.log('[useSpecialReportsList] 沒有有效的專題 ID');
        return [];
      }

      console.log('[useSpecialReportsList] 載入專題詳細資訊:', validTopicIds.length, '個');

      const multiLangFields = ['topic_title', 'topic_short'];
      const selectFields = getMultiLanguageSelect(multiLangFields);

      const { data, error } = await supabase
        .from('topic')
        .select(`topic_id, ${selectFields}, generated_date, update_date`)
        .in('topic_id', validTopicIds);

      if (error) {
        throw new Error(`無法獲取專題詳細資訊: ${error.message}`);
      }

      console.log('[useSpecialReportsList] 載入完成:', data?.length || 0, '個專題');
      return data || [];
    },
    enabled: !!supabase && !!topicCountsQuery.data?.validTopicIds,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });

  return {
    // 資料
    topicCounts: topicCountsQuery.data?.topicCounts || {},
    topicDetails: topicDetailsQuery.data || [],
    
    // 載入狀態
    isLoading: topicCountsQuery.isLoading || topicDetailsQuery.isLoading,
    
    // 錯誤狀態
    error: topicCountsQuery.error || topicDetailsQuery.error,
    
    // 重試函數
    refetch: () => {
      topicCountsQuery.refetch();
      topicDetailsQuery.refetch();
    }
  };
}

/**
 * 自定義 Hook: 拉取單個專題詳細資訊 (SpecialReportDetail)
 * 分階段載入: 專題基本資訊 → 分支列表 → 每個分支的新聞
 */
export function useSpecialReportDetail(topicId) {
  const supabase = useSupabase();
  const { getMultiLanguageSelect, getFieldName } = useLanguageFields();

  // 階段 1: 獲取專題基本資訊
  const topicQuery = useQuery({
    queryKey: ['topic-detail', topicId],
    queryFn: async () => {
      console.log('[useSpecialReportDetail] 載入專題基本資訊:', topicId);

      const multiLangFields = ['topic_title', 'topic_short', 'topic_long', 'report'];
      const selectFields = getMultiLanguageSelect(multiLangFields);

      const { data, error } = await supabase
        .from('topic')
        .select(`topic_id, ${selectFields}, generated_date, who_talk`)
        .eq('topic_id', topicId)
        .single();

      if (error) throw new Error(`無法獲取專題資訊: ${error.message}`);
      if (!data) throw new Error('專題不存在');

      console.log('[useSpecialReportDetail] 專題基本資訊載入完成');
      return data;
    },
    enabled: !!supabase && !!topicId,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });

  // 階段 2: 獲取專題新聞數量
  const newsCountQuery = useQuery({
    queryKey: ['topic-news-count', topicId],
    queryFn: async () => {
      console.log('[useSpecialReportDetail] 載入新聞數量');

      const { data, error } = await supabase
        .from('topic_news_map')
        .select('topic_id')
        .eq('topic_id', topicId);

      if (error) {
        console.warn('無法獲取新聞數量:', error);
        return 0;
      }

      const count = data?.length || 0;
      console.log('[useSpecialReportDetail] 新聞數量:', count);
      return count;
    },
    enabled: !!supabase && !!topicId,
    staleTime: 5 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });

  // 階段 3: 獲取分支列表
  const branchesQuery = useQuery({
    queryKey: ['topic-branches', topicId],
    queryFn: async () => {
      console.log('[useSpecialReportDetail] 載入分支列表');

      const multiLangFields = ['topic_branch_title', 'topic_branch_content'];
      const selectFields = getMultiLanguageSelect(multiLangFields);

      const { data, error } = await supabase
        .from('topic_branch')
        .select(`topic_branch_id, topic_id, ${selectFields}`)
        .eq('topic_id', topicId);

      if (error) {
        console.warn('無法獲取分支列表:', error);
        return [];
      }

      const branches = (data || []).map((b, idx) => ({
        id: b.topic_branch_id,
        name: b[getFieldName('topic_branch_title')] || b.topic_branch_title || `分支 ${idx + 1}`,
        summary: b[getFieldName('topic_branch_content')] || b.topic_branch_content || ''
      }));

      console.log('[useSpecialReportDetail] 分支列表載入完成:', branches.length, '個分支');
      return branches;
    },
    enabled: !!supabase && !!topicId,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });

  return {
    // 資料
    topicData: topicQuery.data,
    newsCount: newsCountQuery.data || 0,
    branches: branchesQuery.data || [],
    
    // 載入狀態
    isLoading: topicQuery.isLoading || newsCountQuery.isLoading || branchesQuery.isLoading,
    
    // 錯誤狀態
    error: topicQuery.error || newsCountQuery.error || branchesQuery.error,
    
    // 重試函數
    refetch: () => {
      topicQuery.refetch();
      newsCountQuery.refetch();
      branchesQuery.refetch();
    }
  };
}

/**
 * 自定義 Hook: 拉取分支的新聞列表
 * 背景載入,不阻塞 UI
 */
export function useBranchNews(branchId) {
  const supabase = useSupabase();
  const { getMultiLanguageSelect, getFieldName } = useLanguageFields();

  return useQuery({
    queryKey: ['branch-news', branchId],
    queryFn: async () => {
      console.log('[useBranchNews] 載入分支新聞:', branchId);

      // 步驟 1: 獲取 story_id 映射
      const { data: mapRows, error: mapError } = await supabase
        .from('topic_branch_news_map')
        .select('story_id')
        .eq('topic_branch_id', branchId);

      if (mapError) {
        console.warn(`無法獲取分支 ${branchId} 的故事映射:`, mapError);
        return [];
      }

      const storyIds = (mapRows || []).map(r => r.story_id).filter(Boolean);
      
      if (!storyIds || storyIds.length === 0) {
        console.log('[useBranchNews] 分支沒有新聞');
        return [];
      }

      // 步驟 2: 獲取新聞內容
      const multiLangFields = ['news_title', 'ultra_short'];
      const selectFields = getMultiLanguageSelect(multiLangFields);

      const { data: stories, error: storiesError } = await supabase
        .from('single_news')
        .select(`story_id, ${selectFields}, category, generated_date, total_articles`)
        .in('story_id', storyIds);

      if (storiesError) {
        console.warn(`無法獲取分支 ${branchId} 的新聞內容:`, storiesError);
        return [];
      }

      // 步驟 3: 格式化為 UnifiedNewsCard 需要的格式
      const customData = (stories || []).map(s => ({
        story_id: s.story_id,
        title: s[getFieldName('news_title')] || s.news_title,
        category: s.category,
        generated_date: s.generated_date,
        author: 'Gemini',
        sourceCount: s.total_articles,
        shortSummary: s[getFieldName('ultra_short')] || s.ultra_short,
        relatedNews: [],
        views: 0,
        keywords: [],
        terms: []
      }));

      console.log('[useBranchNews] 分支新聞載入完成:', customData.length, '篇');
      return customData;
    },
    enabled: !!supabase && !!branchId,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取專家分析 (SpecialReportDetail)
 * 背景載入
 */
export function useExpertAnalysis(topicId) {
  const supabase = useSupabase();
  const { getMultiLanguageSelect, getFieldName } = useLanguageFields();

  return useQuery({
    queryKey: ['expert-analysis', topicId],
    queryFn: async () => {
      console.log('[useExpertAnalysis] 載入專家分析:', topicId);

      const multiLangFields = ['analyze'];
      const selectFields = getMultiLanguageSelect(multiLangFields);

      const { data, error } = await supabase
        .from('pro_analyze_topic')
        .select(`analyze_id, category, ${selectFields}`)
        .eq('topic_id', topicId);

      if (error) {
        console.error('獲取專家分析失敗:', error);
        return [];
      }

      const analysisData = (data || []).map(item => ({
        analyze_id: item.analyze_id,
        category: item.category,
        analyze: item[getFieldName('analyze')] || item.analyze
      }));

      console.log('[useExpertAnalysis] 專家分析載入完成:', analysisData.length, '位專家');
      return analysisData;
    },
    enabled: !!supabase && !!topicId,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });
}

/**
 * 自定義 Hook: 拉取最新專題 (LatestTopics)
 * 分階段載入: 基本資訊 → 新聞統計 → 圖片 → 分支
 */
export function useLatestTopics() {
  const supabase = useSupabase();
  const { getMultiLanguageSelect, getFieldName, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  // 階段 1: 獲取專題基本資訊(支援多語言)
  const topicsQuery = useQuery({
    queryKey: ['latest-topics-basic', currentLanguage],
    queryFn: async () => {
      console.log('[useLatestTopics] 載入專題基本資訊');

      const multiLangFields = ['topic_title', 'topic_short'];
      const selectFields = getMultiLanguageSelect(multiLangFields);

      const { data, error } = await supabase
        .from('topic')
        .select(`topic_id, ${selectFields}, generated_date, update_date`)
        .not('topic_title', 'is', null)
        .neq('topic_title', '')
        .not('topic_short', 'is', null)
        .neq('topic_short', '')
        .not('generated_date', 'is', null)
        .eq('alive', 1)
        .order('update_date', { ascending: false })
        .limit(10);

      if (error) throw error;

      console.log('[useLatestTopics] 專題基本資訊載入完成:', data?.length || 0, '個');
      return data || [];
    },
    enabled: !!supabase,
    staleTime: 5 * 60 * 1000, // 5 分鐘
    cacheTime: 30 * 60 * 1000,
  });

  // 階段 2: 獲取新聞映射 (依賴階段 1)
  const newsMapQuery = useQuery({
    queryKey: ['latest-topics-news-map', topicsQuery.data?.map(t => t.topic_id)],
    queryFn: async () => {
      const topicIds = topicsQuery.data?.map(t => t.topic_id) || [];
      
      if (topicIds.length === 0) {
        console.log('[useLatestTopics] 沒有專題 ID');
        return {};
      }

      console.log('[useLatestTopics] 載入新聞映射:', topicIds.length, '個專題');

      const { data, error } = await supabase
        .from('topic_news_map')
        .select('topic_id, story_id')
        .in('topic_id', topicIds);

      if (error) {
        console.error('載入新聞映射失敗:', error);
        return {};
      }

      // 組織成 { topic_id: [story_ids] } 格式
      const newsMapByTopic = {};
      (data || []).forEach(item => {
        if (!newsMapByTopic[item.topic_id]) {
          newsMapByTopic[item.topic_id] = [];
        }
        newsMapByTopic[item.topic_id].push(item.story_id);
      });

      console.log('[useLatestTopics] 新聞映射載入完成');
      return newsMapByTopic;
    },
    enabled: !!supabase && !!topicsQuery.data && topicsQuery.data.length > 0,
    staleTime: 5 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });

  // 階段 3: 獲取圖片 (依賴階段 2) - 分批載入避免超時
  const imagesQuery = useQuery({
    queryKey: ['latest-topics-images', newsMapQuery.data],
    queryFn: async () => {
      const newsMap = newsMapQuery.data || {};
      
      // 收集每個專題的第一個 story_id
      const storyIdsForImages = [];
      const topicToStoryMap = {};
      
      Object.entries(newsMap).forEach(([topicId, storyIds]) => {
        if (storyIds && storyIds.length > 0) {
          const firstStoryId = storyIds[0];
          storyIdsForImages.push(firstStoryId);
          topicToStoryMap[topicId] = firstStoryId;
        }
      });

      if (storyIdsForImages.length === 0) {
        console.log('[useLatestTopics] 沒有需要載入的圖片');
        return { imageMap: {}, topicToStoryMap };
      }

      console.log('[useLatestTopics] 載入圖片:', storyIdsForImages.length, '張');

      // 🔧 分批載入圖片避免超時
      const BATCH_SIZE = 3;
      const imageMap = {};

      for (let i = 0; i < storyIdsForImages.length; i += BATCH_SIZE) {
        const batch = storyIdsForImages.slice(i, i + BATCH_SIZE);
        
        try {
          const { data, error } = await supabase
            .from('generated_image')
            .select('story_id, image, description')
            .in('story_id', batch);

          if (error) {
            console.warn('[useLatestTopics] 批次載入圖片失敗:', error);
            continue;
          }

          // 處理這批圖片
          (data || []).forEach(imageItem => {
            if (imageItem.image) {
              try {
                const cleanBase64 = imageItem.image.replace(/\s/g, '');
                imageMap[imageItem.story_id] = {
                  imageUrl: `data:image/png;base64,${cleanBase64}`,
                  description: imageItem.description || ''
                };
              } catch (e) {
                console.error('[useLatestTopics] 圖片處理失敗:', imageItem.story_id, e);
              }
            }
          });

          console.log('[useLatestTopics] 批次完成,已載入:', Object.keys(imageMap).length, '/', storyIdsForImages.length, '張');
        } catch (err) {
          console.error('[useLatestTopics] 批次異常:', err);
          continue;
        }

        // 批次間添加小延遲
        if (i + BATCH_SIZE < storyIdsForImages.length) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      console.log('[useLatestTopics] 圖片載入完成:', Object.keys(imageMap).length, '張');
      return { imageMap, topicToStoryMap };
    },
    enabled: !!supabase && !!newsMapQuery.data,
    staleTime: 30 * 60 * 1000, // 圖片快取 30 分鐘
    cacheTime: 2 * 60 * 60 * 1000,
    retry: 1, // 只重試 1 次
  });

  // 階段 4: 獲取分支 (背景載入,支援多語言)
  const branchesQuery = useQuery({
    queryKey: ['latest-topics-branches', currentLanguage, topicsQuery.data?.map(t => t.topic_id)],
    queryFn: async () => {
      const topicIds = topicsQuery.data?.map(t => t.topic_id) || [];
      
      if (topicIds.length === 0) {
        console.log('[useLatestTopics] 沒有專題 ID');
        return {};
      }

      console.log('[useLatestTopics] 載入分支:', topicIds.length, '個專題');

      const multiLangFields = ['topic_branch_title'];
      const selectFields = getMultiLanguageSelect(multiLangFields);

      // 批量獲取所有專題的分支(支援多語言)
      const { data, error } = await supabase
        .from('topic_branch')
        .select(`topic_id, topic_branch_id, ${selectFields}`)
        .in('topic_id', topicIds)
        .not('topic_branch_title', 'is', null)
        .neq('topic_branch_title', '');

      if (error) {
        console.warn('載入分支失敗:', error);
        return {};
      }

      // 組織成 { topic_id: [branches] } 格式
      const branchesByTopic = {};
      (data || []).forEach(branch => {
        if (!branchesByTopic[branch.topic_id]) {
          branchesByTopic[branch.topic_id] = [];
        }
        
        // 根據當前語言選擇正確的欄位
        const titleFieldName = getFieldName('topic_branch_title');
        const title = branch[titleFieldName] || branch.topic_branch_title;
        
        branchesByTopic[branch.topic_id].push({
          id: branch.topic_branch_id,
          title: title
        });
      });

      console.log('[useLatestTopics] 分支載入完成');
      return branchesByTopic;
    },
    enabled: !!supabase && !!topicsQuery.data && topicsQuery.data.length > 0,
    staleTime: 10 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
  });

  return {
    topics: topicsQuery.data || [],
    newsMap: newsMapQuery.data || {},
    imageData: imagesQuery.data || { imageMap: {}, topicToStoryMap: {} },
    branches: branchesQuery.data || {},
    
    isLoading: topicsQuery.isLoading || newsMapQuery.isLoading,
    error: topicsQuery.error || newsMapQuery.error,
    
    refetch: () => {
      topicsQuery.refetch();
      newsMapQuery.refetch();
      imagesQuery.refetch();
      branchesQuery.refetch();
    }
  };
}

