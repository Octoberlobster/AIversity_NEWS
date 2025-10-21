import React, { useState, useEffect, useMemo, useRef} from 'react';
import { useParams, Link} from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './../css/NewsDetail.css';
import ChatRoom from './ChatRoom';
import TermTooltip from './TermTooltip';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { useSupabase } from './supabase';
import { useLanguageFields} from '../utils/useLanguageFields';
import { changeExperts as changeExpertsAPI } from './api.js';

// 從資料庫動態載入術語定義的函數
const loadTermDefinitions = async (supabase) => {
  try {
    const { data, error } = await supabase
      .from('term')
      .select('term, term_id, definition, example');
    
    if (error) {
      console.error('載入術語定義時發生錯誤:', error);
    }

    // 轉換為物件格式
    const definitions = {};
    data.forEach(item => {
      if (item.term && item.definition) {
        definitions[item.term_id] = {
          term: item.term,
          definition: item.definition,
          example: item.example || null
        };
      }
    });

    return definitions
  } catch (error) {
    console.error('載入術語定義時發生錯誤:', error);
  }
};

function NewsDetail() {
  const { t } = useTranslation();
  const { id } = useParams();
  
  // 多語言相關 hooks
  const { getCurrentLanguage, getFieldName, getMultiLanguageSelect } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [showAllSources, setShowAllSources] = useState(false);
  const [newsData, setNewsData] = useState(null);
  const [newsImage, setNewsImage] = useState(null);
  const [newsUrl, setNewsUrl] = useState(null);
  const [newsKeywords, setNewsKeywords] = useState([]);
  const [highlights, setHighlights] = useState([]);
  const [termDefinitions, setTermDefinitions] = useState({});
  const [newsTerms, setNewsTerms] = useState([]);
  const [relatedNews, setRelatedNews] = useState([]);
  const [relatedTopics, setRelatedTopics] = useState([]);
  const [positionData, setPositionData] = useState({ positive: [], negative: [] }); // 正反方立場資料
  const [positionLoading, setPositionLoading] = useState(true); // 正反方立場載入狀態
  const [expertAnalysis, setExpertAnalysis] = useState([]); // 專家分析資料
  const [analysisLoading, setAnalysisLoading] = useState(true); // 專家分析載入狀態
  const [showContent, setShowContent] = useState('loading'); // 'loading', 'position', 'expert', 'none'
  const [isChatOpen, setIsChatOpen] = useState(false); // 聊天室開關狀態
  const [chatExperts, setChatExperts] = useState([null]); // 聊天室選擇的專家
  const [generatingExperts, setGeneratingExperts] = useState(new Set()); // 正在生成的專家 ID
  const [batchGenerating, setBatchGenerating] = useState(false); // 批量生成中
  
  // 正反方立場彈窗相關狀態
  const [showPositionModal, setShowPositionModal] = useState(false);
  const [modalContent, setModalContent] = useState({ type: '', content: '' });
  
  // ChatRoom組件的ref
  const chatRoomRef = useRef(null);

  // 生成帶語言前綴的路由
  const getLanguageRoute = (path) => {
    const langPrefix = currentLanguage === 'zh-TW' ? '/zh-TW' : 
                      currentLanguage === 'en' ? '/en' : 
                      currentLanguage === 'jp' ? '/jp' : 
                      currentLanguage === 'id' ? '/id' : '/zh-TW';
    return `${langPrefix}${path}`;
  };

  // 文字截斷函數 - 限制30字並添加省略號
  const truncateText = (text, maxLength = 30) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  // 處理正反方立場點擊事件
  const handlePositionClick = (content, type) => {
    setModalContent({ type, content });
    setShowPositionModal(true);
  };

  // 關閉彈窗
  const closeModal = () => {
    setShowPositionModal(false);
    setModalContent({ type: '', content: '' });
  };

  // 語言代碼映射 (前端 -> 後端)
  const mapLanguageCode = (frontendLang) => {
    const languageMap = {
      'zh-TW': 'zh-TW',
      'en': 'en-US',
      'jp': 'ja-JP',
      'id': 'id-ID'
    };
    return languageMap[frontendLang] || 'zh-TW';
  };

  // 通用的專家更換函數 - 支援單個或批量更換
  const changeExperts = async (expertsToRegenerate) => {
    try {
      console.log('=== 開始更換專家流程 ===');
      console.log('要更換的專家:', expertsToRegenerate);
      
      // 標記正在生成的專家
      const regenerateIds = expertsToRegenerate.map(e => e.analyze_id);
      setGeneratingExperts(prev => new Set([...prev, ...regenerateIds]));

      // 生成或取得 user_id 和 room_id
      const userId = getOrCreateUserId();
      const roomId = createRoomId(userId, id);
      console.log('userId:', userId);
      console.log('roomId:', roomId);
      console.log('storyId:', id);
      console.log('language:', mapLanguageCode(currentLanguage));

      // 準備當前專家資料
      const currentExperts = expertAnalysis.map(expert => ({
        analyze_id: expert.analyze_id,
        category: expert.category,
        analyze: expert.analyze
      }));
      console.log('當前所有專家:', currentExperts);

      // 呼叫 api.js 中的函數
      console.log('準備呼叫 changeExpertsAPI...');
      const result = await changeExpertsAPI(
        userId,
        roomId,
        id,
        mapLanguageCode(currentLanguage),
        currentExperts,
        expertsToRegenerate
      );

      console.log('=== 收到 API 回傳結果 ===');
      console.log('result:', result);
      console.log('result.success:', result.success);
      console.log('result.experts:', result.experts);
      console.log('result.replaced_ids:', result.replaced_ids);

      if (result.success && result.experts && result.experts.length > 0) {
        console.log('✅ API 呼叫成功，開始更新狀態');
        
        // 建立新專家的映射表 (用 replaced_ids 來對應)
        const newExpertsMap = new Map();
        if (result.replaced_ids && result.replaced_ids.length === result.experts.length) {
          result.replaced_ids.forEach((oldId, index) => {
            newExpertsMap.set(oldId, result.experts[index]);
            console.log(`映射: ${oldId} → ${result.experts[index].analyze_id}`);
          });
        }
        
        console.log('新專家映射表:', newExpertsMap);
        
        // 更新專家分析狀態
        setExpertAnalysis(prevExperts => {
          const updated = prevExperts.map(expert => 
            newExpertsMap.has(expert.analyze_id) 
              ? newExpertsMap.get(expert.analyze_id) 
              : expert
          );
          console.log('更新後的 expertAnalysis:', updated);
          return updated;
        });

        // 同步更新聊天室專家狀態
        setChatExperts(prevExperts => 
          prevExperts.map(expert => 
            expert && newExpertsMap.has(expert.analyze_id)
              ? newExpertsMap.get(expert.analyze_id)
              : expert
          )
        );
      } else {
        console.error('❌ API 回傳格式錯誤');
        console.error('完整 result:', JSON.stringify(result, null, 2));
        throw new Error('API 回傳資料格式錯誤');
      }
    } catch (error) {
      console.error('❌ 更換專家失敗:', error);
      console.error('錯誤堆疊:', error.stack);
    } finally {
      // 移除所有生成標記
      const regenerateIds = expertsToRegenerate.map(e => e.analyze_id);
      setGeneratingExperts(prev => {
        const newSet = new Set(prev);
        regenerateIds.forEach(id => newSet.delete(id));
        return newSet;
      });
      console.log('=== 更換專家流程結束 ===');
    }
  };

  // 處理更換單個專家
  const handleChangeExpert = async (analyzeId, category) => {
    // 防止重複生成
    if (generatingExperts.has(analyzeId) || batchGenerating) {
      return;
    }

    // 呼叫通用函數,傳入單個專家的陣列
    await changeExperts([
      {
        analyze_id: analyzeId,
        category: category
      }
    ]);
  };

  // 處理換一批專家 (平行發送多個 API 請求)
  const handleRefreshAllExperts = async () => {
    if (batchGenerating || expertAnalysis.length === 0 || generatingExperts.size > 0) {
      return;
    }

    try {
      console.log('=== 開始批量更換所有專家 ===');
      setBatchGenerating(true);

      // 標記所有專家為生成中
      const allExpertIds = expertAnalysis.map(e => e.analyze_id);
      setGeneratingExperts(new Set(allExpertIds));

      // 生成或取得 user_id 和 room_id
      const userId = getOrCreateUserId();
      const roomId = createRoomId(userId, id);

      // 準備當前專家資料
      const currentExperts = expertAnalysis.map(expert => ({
        analyze_id: expert.analyze_id,
        category: expert.category,
        analyze: expert.analyze
      }));

      // 🧠 1️⃣ 為每個專家建立單獨的 API 請求
      const fetchSingleExpert = async (expert) => {
        console.log(`正在更換專家: ${expert.category} (${expert.analyze_id})`);
        
        return changeExpertsAPI(
          userId,
          roomId,
          id,
          mapLanguageCode(currentLanguage),
          currentExperts,
          [{
            analyze_id: expert.analyze_id,
            category: expert.category
          }]
        )
          .then((result) => {
            console.log(`✅ 專家 ${expert.category} 更換成功:`, result);
            return {
              success: true,
              oldId: expert.analyze_id,
              newExpert: result.success_response?.experts?.[0] || result.experts?.[0],
            };
          })
          .catch((error) => {
            console.error(`❌ 專家 ${expert.category} 更換失敗:`, error);
            return {
              success: false,
              oldId: expert.analyze_id,
              error: error.message,
            };
          });
      };

      // 🧠 2️⃣ 平行發送所有請求
      console.log('平行發送 API 請求...');
      const allPromises = expertAnalysis.map(fetchSingleExpert);
      const results = await Promise.all(allPromises);

      console.log('所有 API 請求完成:', results);

      // 🧠 3️⃣ 處理結果並更新狀態
      const successResults = results.filter(r => r.success);

      if (successResults.length > 0) {
        // 建立新專家的映射表
        const newExpertsMap = new Map();
        successResults.forEach(({ oldId, newExpert }) => {
          if (newExpert) {
            newExpertsMap.set(oldId, newExpert);
            console.log(`映射: ${oldId} → ${newExpert.analyze_id}`);
          }
        });

        // 更新專家分析狀態
        setExpertAnalysis(prevExperts => {
          const updated = prevExperts.map(expert =>
            newExpertsMap.has(expert.analyze_id)
              ? newExpertsMap.get(expert.analyze_id)
              : expert
          );
          console.log('批量更新後的 expertAnalysis:', updated);
          return updated;
        });

        // 同步更新聊天室專家狀態
        setChatExperts(prevExperts =>
          prevExperts.map(expert =>
            expert && newExpertsMap.has(expert.analyze_id)
              ? newExpertsMap.get(expert.analyze_id)
              : expert
          )
        );
      }

    } catch (error) {
      console.error('❌ 批量更換專家失敗:', error);
      console.error('錯誤堆疊:', error.stack);
    } finally {
      // 清除所有生成標記
      setGeneratingExperts(new Set());
      setBatchGenerating(false);
      console.log('=== 批量更換專家流程結束 ===');
    }
  };

  // 確保頁面載入時滾動到頂部，語言切換時也要重置
  useEffect(() => {
    window.scrollTo(0, 0);
    setShowAllSources(false);
    setPositionLoading(true); // 重置載入狀態
    setAnalysisLoading(true); // 重置專家分析載入狀態
    setShowContent('loading'); // 重置顯示狀態
  }, [id, currentLanguage]); // 當 id 或語言改變時執行

  // 使用 Supabase 客戶端獲取新聞數據
  const supabaseClient = useSupabase();

  // 載入術語定義 - 支援多語言
  useEffect(() => {
    const initTermDefinitions = async () => {
      const definitions = await loadTermDefinitions(supabaseClient);
      setTermDefinitions(definitions);
    };
    initTermDefinitions();
  }, [supabaseClient, currentLanguage]); // 語言改變時重新載入術語

  // 載入特定新聞的術語 - 支援多語言
  useEffect(() => {
    const fetchNewsTerms = async () => {
      if (!id || !supabaseClient) return;
      
      try {
        // 先從 term_map 獲取 term_id 列表
        const { data: termMapData, error: termMapError } = await supabaseClient
          .from('term_map')
          .select('term_id')
          .eq('story_id', id);
        
        if (termMapError) {
          console.error(`Error fetching term mapping for story ${id}:`, termMapError);
          setNewsTerms([]);
          return;
        }

        const termIds = termMapData?.map(item => item.term_id) || [];
        
        if (termIds.length === 0) {
          setNewsTerms([]);
          return;
        }

        // 根據 term_id 獲取實際的術語文字，支援多語言
        const termMultiLangFields = ['term', 'definition', 'example'];
        const termSelectFields = getMultiLanguageSelect(termMultiLangFields);
        
        const { data: termsData, error: termsError } = await supabaseClient
          .from('term')
          .select(`term_id, ${termSelectFields}`)
          .in('term_id', termIds);
        
        if (termsError) {
          console.error(`Error fetching terms for story ${id}:`, termsError);
          setNewsTerms([]);
          return;
        }

        // 使用多語言欄位，如果不存在則使用原欄位作為 fallback
        const terms = termsData?.map(item => ({
          term: item[getFieldName('term')] || item.term,
          definition: item[getFieldName('definition')] || item.definition,
          example: item[getFieldName('example')] || item.example
        })) || [];
        
        setNewsTerms(terms);
      } catch (error) {
        console.error(`Error fetching terms for story ${id}:`, error);
        setNewsTerms([]);
      }
    };

    fetchNewsTerms();
  }, [id, supabaseClient, currentLanguage, getFieldName, getMultiLanguageSelect]); // 語言改變時重新載入

  // 載入正反方立場資料 - 支援多語言
  useEffect(() => {
    const fetchPositionData = async () => {
      if (!id || !supabaseClient || (showContent !== 'loadPosition' && showContent !== 'loadBoth')) {
        return;
      }
      setPositionLoading(true);
      
      try {
        // 查詢正反方立場，支援多語言
        const positionMultiLangFields = ['positive', 'negative'];
        const positionSelectFields = getMultiLanguageSelect(positionMultiLangFields);
        
        const { data, error } = await supabaseClient
          .from('position')
          .select(positionSelectFields)
          .eq('story_id', id);
        
        if (error) {
          console.error(`Error fetching position data for story ${id}:`, error);
          setPositionData({ positive: [], negative: [] });
          setPositionLoading(false);
          // 如果正反方立場載入失敗，回退到專家分析
          setShowContent('loadExpert');
          return;
        }

        const positionRow = data?.[0];
        if (positionRow) {
          // 處理多語言立場資料
          const positive = positionRow[getFieldName('positive')] || positionRow.positive;
          const negative = positionRow[getFieldName('negative')] || positionRow.negative;

          // 因為 position_flag 為 true，所以直接設定資料並顯示正反方立場
          setPositionData({
            positive: positive || [],
            negative: negative || []
          });
          
          // 如果是 loadBoth 模式，載入專家分析但顯示正反方立場
          if (showContent === 'loadBoth') {
            setShowContent('loadExpertForBoth'); // 觸發專家分析載入
          } else {
            setShowContent('position');
          }
        } else {
          // 沒有找到正反方資料，回退到專家分析
          setPositionData({ positive: [], negative: [] });
          setShowContent('loadExpert');
        }
      } catch (error) {
        console.error(`Error fetching position data for story ${id}:`, error);
        setPositionData({ positive: [], negative: [] });
        setShowContent('loadExpert');
      } finally {
        setPositionLoading(false);
      }
    };

    fetchPositionData();
  }, [id, supabaseClient, showContent, currentLanguage, getFieldName, getMultiLanguageSelect]); // 語言改變時重新載入

  // 載入專家分析資料 - 只在沒有正反方立場時載入
  useEffect(() => {
    const fetchExpertAnalysis = async () => {
      if (!id || !supabaseClient || (showContent !== 'loadExpert' && showContent !== 'loadExpertForBoth')) {
        return;
      }
      
      setAnalysisLoading(true);
      
      try {
        // 查詢專家分析，支援多語言
        const analyzeMultiLangFields = ['analyze'];
        const analyzeSelectFields = getMultiLanguageSelect(analyzeMultiLangFields);
        
        const { data, error } = await supabaseClient
          .from('pro_analyze')
          .select(`analyze_id, category, ${analyzeSelectFields}`)
          .eq('story_id', id);
        
        if (error) {
          console.error(`Error fetching expert analysis for story ${id}:`, error);
          setExpertAnalysis([]);
          setAnalysisLoading(false);
          setShowContent('none');
          return;
        }

        // 處理多語言分析資料
        const analysisData = (data || []).map(item => ({
          analyze_id: item.analyze_id,
          category: item.category,
          analyze: item[getFieldName('analyze')] || item.analyze
        }));
        
        if (analysisData.length > 0) {
          // 先設定資料
          setExpertAnalysis(analysisData);
          setChatExperts(analysisData);
          
          // 根據載入模式決定要顯示什麼
          if (showContent === 'loadExpertForBoth') {
            // 如果是 loadExpertForBoth 模式，保持顯示正反方立場，但專家分析資料已載入供聊天室使用
            setShowContent('position');
          } else {
            // 正常的專家分析載入模式，顯示專家分析
            setShowContent('expert');
          }
        } else {
          setExpertAnalysis([]);
          if (showContent === 'loadExpertForBoth') {
            setShowContent('position'); // 回到正反方立場顯示
          } else {
            setShowContent('none');
          }
        }
      } catch (error) {
        console.error(`Error fetching expert analysis for story ${id}:`, error);
        setExpertAnalysis([]);
        setShowContent('none');
      } finally {
        setAnalysisLoading(false);
      }
    };

    fetchExpertAnalysis();
  }, [id, supabaseClient, showContent, currentLanguage, getFieldName, getMultiLanguageSelect]); // 語言改變時重新載入

  useEffect(() => {
    const fetchNewsData = async () => {
      if (!id || !supabaseClient) return;
      
      // 設定需要多語言支援的欄位
      const multiLangFields = ['news_title', 'ultra_short', 'long'];
      const selectFields = getMultiLanguageSelect(multiLangFields);
      
      // 同時選取原欄位和多語言欄位
      const { data, error } = await supabaseClient
        .from('single_news')
        .select(`${selectFields}, generated_date, category, story_id, who_talk, position_flag`)
        .eq('story_id', id);
        
      if (error) {
        console.error('Error fetching news data:', error);
      } else {
        const row = data?.[0];
        if (row) {
          // 使用多語言欄位，如果不存在則使用原欄位作為 fallback
          const title = row[getFieldName('news_title')] || row.news_title;
          const short = row[getFieldName('ultra_short')] || row.short;
          const long = row[getFieldName('long')] || row.long;
          
          // 多語言資料處理完成
          
          setNewsData({
            title: title,
            date: row.generated_date,
            author: 'Gemini',
            short: short,
            long: long,
            terms: [],
            keywords: [],
            source: [],
            category: row.category,
            story_id: row.story_id,
            who_talk: row.who_talk,
            position_flag: row.position_flag
          });
          
          // 根據 position_flag 決定要載入的內容類型
          if (row.position_flag) {
            // 有正反方立場，同時載入正反方資料和專家分析，但優先顯示正反方
            setShowContent('loadBoth');
          } else {
            // 沒有正反方立場，只載入專家分析並顯示
            setShowContent('loadExpert');
          }
        } else {
          setNewsData(null);
        }
      }
    };

    fetchNewsData();
  }, [id, supabaseClient, currentLanguage, getMultiLanguageSelect, getFieldName]); // 語言改變時重新載入

  // 載入新聞圖片
  useEffect(() => {
    const fetchNewsImage = async () => {
      const { data, error } = await supabaseClient
        .from('generated_image')
        .select('*')
        .eq('story_id', id);

      if (error) {
        console.error('Error fetching news image:', error);
        setNewsImage([]);
        return;
      }

      const processed = (data || []).map(item => {
        // 將純 base64 字串轉換為完整的 data URL
        const src = item.image ? `data:image/png;base64,${item.image}` : '';
        // 使用多語言描述，如果不存在則使用原欄位
        const description = item[getFieldName('description')] || item.description || '';
        return {
          src,
          description,
        };
      });

      setNewsImage(processed);
    };

    fetchNewsImage();
  }, [id, supabaseClient, currentLanguage, getFieldName]); // 語言改變時重新載入

  // 載入 highlight（重點）資料 - 支援多語言
  useEffect(() => {
    const fetchHighlights = async () => {
      if (!id || !supabaseClient) return;

      try {
        const multiLangFields = ['highlight'];
        const selectFields = getMultiLanguageSelect(multiLangFields);

        const { data, error } = await supabaseClient
          .from('highlight')
          .select(selectFields)
          .eq('story_id', id);

        // log raw response for debugging
        console.log('fetchHighlights response for story', id, { selectFields, data, error });
        console.log('highlights data:', data);

        if (error) {
          console.error(`Error fetching highlights for story ${id}:`, error);
          setHighlights([]);
          return;
        }

        const row = data?.[0];
        if (!row) {
          setHighlights([]);
          return;
        }

        const raw = row[getFieldName('highlight')] || row.highlight || [];
        // 如果 raw 是陣列，直接使用；如果是物件且有 highlight 屬性，則使用該屬性
        const highlightArray = Array.isArray(raw) ? raw : (raw.highlight || []);
        console.log('processed highlights array:', highlightArray);
        setHighlights(highlightArray);
      } catch (error) {
        console.error(`Error fetching highlights for story ${id}:`, error);
        setHighlights([]);
      }

    };

    fetchHighlights();
  }, [id, supabaseClient, currentLanguage, getFieldName, getMultiLanguageSelect]);

  // 載入新聞來源 URL
  useEffect(() => {
    const fetchNewsUrl = async () => {
      const { data, error } = await supabaseClient
        .from('cleaned_news')
        .select('article_title, article_url, media')
        .eq('story_id', id);

      if (error) {
        console.error('Error fetching news url:', error);
        setNewsUrl(null);
        return;
      }
      setNewsUrl(data);
    };

    fetchNewsUrl();
  }, [id, supabaseClient, currentLanguage]); // 語言改變時重新載入

  // 載入新聞關鍵字
  useEffect(() => {
    const fetchNewsKeywords = async () => {
      if (!id || !supabaseClient) return;
      
      // 獲取關鍵字，支援多語言
      const keywordMultiLangFields = ['keyword'];
      const keywordSelectFields = getMultiLanguageSelect(keywordMultiLangFields);
      
      const { data, error } = await supabaseClient
        .from('keywords_map')
        .select(keywordSelectFields)
        .eq('story_id', id)
        .limit(3); // 限制為 3 個關鍵字

      if (error) {
        console.error('Error fetching news keywords:', error);
        setNewsKeywords([]);
        return;
      }
      
      // 處理多語言關鍵字
      const processedData = (data || []).map(item => ({
        keyword: item[getFieldName('keyword')] || item.keyword
      }));
      
      setNewsKeywords(processedData);
    };

    fetchNewsKeywords();
  }, [id, supabaseClient, currentLanguage, getFieldName, getMultiLanguageSelect]); // 語言改變時重新載入

  // 載入相關新聞
  useEffect(() => {
    const fetchRelatedNews = async () => {
      if (!id || !supabaseClient) return;
      
      try {
        // 準備 reason 的多語言欄位查詢
        const reasonMultiLangFields = ['reason'];
        const reasonSelectFields = getMultiLanguageSelect(reasonMultiLangFields);
        
        // 查詢相關新聞 - 找出以當前新聞為 src_story_id 的相關新聞
        const { data: relatedData, error: relatedError } = await supabaseClient
          .from('relative_news')
          .select(`
            dst_story_id,
            ${reasonSelectFields}
          `)
          .eq('src_story_id', id);

        if (relatedError) {
          console.error('Error fetching related news:', relatedError);
          setRelatedNews([]);
          return;
        }

        // 如果有相關新聞，再查詢對應的新聞標題
        if (!relatedData || relatedData.length === 0) {
          setRelatedNews([]);
          return;
        }

        // 獲取所有目標新聞的 story_id
        const targetStoryIds = relatedData.map(item => item.dst_story_id);
        
        // 查詢目標新聞的詳細資料，支援多語言
        const newsMultiLangFields = ['news_title'];
        const newsSelectFields = getMultiLanguageSelect(newsMultiLangFields);
        
        const { data: newsData, error: newsError } = await supabaseClient
          .from('single_news')
          .select(`story_id, ${newsSelectFields}`)
          .in('story_id', targetStoryIds);

        if (newsError) {
          console.error('Error fetching related news titles:', newsError);
          setRelatedNews([]);
          return;
        }

        // 合併資料並進行資料清理
        const related = relatedData.map(relatedItem => {
          const newsItem = newsData?.find(n => n.story_id === relatedItem.dst_story_id);
          
          // 資料清理：如果 reason 過長，可能是錯誤的內容，截短它
          let reason = relatedItem[getFieldName('reason')] || relatedItem.reason || '無相關性說明';
          if (reason.length > 200) {
            reason = reason.substring(0, 200) + '...';
          }
          
          // 使用多語言標題，如果不存在則使用原標題作為 fallback
          let title = newsItem ? (newsItem[getFieldName('news_title')] || newsItem.news_title) : '';
          if (!title || !title.trim()) {
            title = `新聞 ID: ${relatedItem.dst_story_id}`;
          }
          
          return {
            id: relatedItem.dst_story_id,
            title: title.trim(),
            relevance: reason.trim()
          };
        });
        setRelatedNews(related);
      } catch (error) {
        console.error('Error fetching related news:', error);
        setRelatedNews([]);
      }
    };

    fetchRelatedNews();
  }, [id, supabaseClient, currentLanguage, getFieldName, getMultiLanguageSelect]); // 語言改變時重新載入

  // 載入相關專題
  useEffect(() => {
    const fetchRelatedTopics = async () => {
      if (!id || !supabaseClient) return;
      
      try {
        // 準備 reason 的多語言欄位查詢
        const reasonMultiLangFields = ['reason'];
        const reasonSelectFields = getMultiLanguageSelect(reasonMultiLangFields);
        
        // 查詢相關專題 - 找出以當前新聞為 src_story_id 的相關專題
        const { data: relatedData, error: relatedError } = await supabaseClient
          .from('relative_topics')
          .select(`
            dst_topic_id,
            ${reasonSelectFields}
          `)
          .eq('src_story_id', id);

        if (relatedError) {
          console.error('Error fetching related topics:', relatedError);
          setRelatedTopics([]);
          return;
        }

        // 如果有相關專題，再查詢對應的專題標題
        if (!relatedData || relatedData.length === 0) {
          setRelatedTopics([]);
          return;
        }

        // 獲取所有目標專題的 topic_id
        const targetTopicIds = relatedData.map(item => item.dst_topic_id);
        
        // 查詢目標專題的詳細資料，支援多語言
        const topicMultiLangFields = ['topic_title'];
        const topicSelectFields = getMultiLanguageSelect(topicMultiLangFields);
        
        const { data: topicData, error: topicError } = await supabaseClient
          .from('topic')
          .select(`topic_id, ${topicSelectFields}`)
          .in('topic_id', targetTopicIds);

        if (topicError) {
          console.error('Error fetching related topic titles:', topicError);
          setRelatedTopics([]);
          return;
        }

        // 合併資料並進行資料清理
        const related = relatedData.map(relatedItem => {
          const topicItem = topicData?.find(t => t.topic_id === relatedItem.dst_topic_id);
          
          // 資料清理：如果 reason 過長，可能是錯誤的內容，截短它
          let reason = relatedItem[getFieldName('reason')] || relatedItem.reason || '無相關性說明';
          if (reason.length > 200) {
            reason = reason.substring(0, 200) + '...';
          }
          
          // 使用多語言標題，如果不存在則使用原標題作為 fallback
          let title = topicItem ? (topicItem[getFieldName('topic_title')] || topicItem.topic_title) : '';
          if (!title || !title.trim()) {
            title = `專題 ID: ${relatedItem.dst_topic_id}`;
          }
          
          return {
            id: relatedItem.dst_topic_id,
            title: title.trim(),
            relevance: reason.trim()
          };
        });
        setRelatedTopics(related);
      } catch (error) {
        console.error('Error fetching related topics:', error);
        setRelatedTopics([]);
      }
    };

    fetchRelatedTopics();
  }, [id, supabaseClient, currentLanguage, getFieldName, getMultiLanguageSelect]); // 語言改變時重新載入

  // 名詞解釋 tooltip
  const handleTermClick = (term, e) => {
    const rect = e.target.getBoundingClientRect();
    setTooltipTerm(term);
    setTooltipPosition({ x: rect.left + rect.width / 2, y: rect.top - 10 });
  };

  const renderArticleText = (text) => {
    if (!text) return null;

    // 以「空一行」分段；段內的單一換行會轉成 <br/>
    const paragraphs = String(text).split(/\r?\n\s*\r?\n/);

    const terms = sortedTerms; // 直接用 useMemo 的排序結果
    const escapeReg = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const termsPattern = terms.length
      ? new RegExp(`(${terms.map(escapeReg).join('|')})`, 'g')
      : null;
    const seenTerms = new Set(); // 記錄已經高亮過的 terms

    // 創建 highlights 的正則表達式模式
    const highlightsPattern = highlights.length
      ? new RegExp(`(${highlights.map(escapeReg).join('|')})`, 'g')
      : null;
    
    // 調試信息
    console.log('highlights for rendering:', highlights);
    console.log('highlightsPattern:', highlightsPattern);

    const highlightTermsInLine = (line) => {
      if (!termsPattern && !highlightsPattern) return line;

      // 先處理 highlights（畫重點）
      let processedLine = line;
      if (highlightsPattern) {
        processedLine = processedLine.split(highlightsPattern).map((part, i) => {
          if (highlights.includes(part)) {
            return (
              <mark
                key={`highlight-${i}`}
                className="highlight-text"
              >
                {part}
              </mark>
            );
          }
          return <React.Fragment key={`highlight-txt-${i}`}>{part}</React.Fragment>;
        });
      }

      // 再處理 terms（術語）
      if (termsPattern && Array.isArray(processedLine)) {
        processedLine = processedLine.map((part, partIndex) => {
          if (React.isValidElement(part)) {
            // 如果已經是 React 元素（highlight），需要檢查其內容是否包含術語
            const highlightText = part.props.children;
            if (typeof highlightText === 'string') {
              // 檢查 highlight 文字中是否包含術語
              const hasTerms = terms.some(term => highlightText.includes(term));
              if (hasTerms) {
                // 如果包含術語，需要重新處理這個 highlight 文字
                // 保持整個 highlight 為一個連續的方框
                const processedParts = highlightText.split(termsPattern).map((termPart, termIndex) => {
                  if (terms.includes(termPart)) {
                    // 只有第一次出現的 term 才高亮
                    if (!seenTerms.has(termPart)) {
                      seenTerms.add(termPart);
                      return (
                        <strong
                          key={`highlight-term-${partIndex}-${termIndex}`}
                          className="term term--clickable"
                          onClick={(e) => handleTermClick(termPart, e)}
                        >
                          {termPart}
                        </strong>
                      );
                    } else {
                      // 已經出現過的 term 不高亮
                      return <React.Fragment key={`highlight-text-${partIndex}-${termIndex}`}>{termPart}</React.Fragment>;
                    }
                  }
                  // 非術語部分
                  return <React.Fragment key={`highlight-text-${partIndex}-${termIndex}`}>{termPart}</React.Fragment>;
                });
                
                // 用一個連續的 mark 包裝所有內容
                return (
                  <mark
                    key={`highlight-container-${partIndex}`}
                    className="highlight-text"
                  >
                    {processedParts}
                  </mark>
                );
              }
            }
            // 如果不包含術語，直接返回原 highlight
            return part;
          }
          
          // 處理文字部分中的術語
          const textContent = typeof part === 'string' ? part : String(part);
          return textContent.split(termsPattern).map((termPart, termIndex) => {
            if (terms.includes(termPart)) {
              // 只有第一次出現的 term 才高亮
              if (!seenTerms.has(termPart)) {
                seenTerms.add(termPart);
                return (
                  <strong
                    key={`term-${partIndex}-${termIndex}`}
                    className="term term--clickable"
                    onClick={(e) => handleTermClick(termPart, e)}
                  >
                    {termPart}
                  </strong>
                );
              } else {
                // 已經出現過的 term 不高亮
                return <React.Fragment key={`term-txt-${partIndex}-${termIndex}`}>{termPart}</React.Fragment>;
              }
            }
            return <React.Fragment key={`term-txt-${partIndex}-${termIndex}`}>{termPart}</React.Fragment>;
          });
        });
      } else if (termsPattern && typeof processedLine === 'string') {
        // 如果沒有 highlights，直接處理術語
        processedLine = processedLine.split(termsPattern).map((part, i) => {
          if (terms.includes(part)) {
            // 只有第一次出現的 term 才高亮
            if (!seenTerms.has(part)) {
              seenTerms.add(part);
              return (
                <strong
                  key={`term-${i}`}
                  className="term term--clickable"
                  onClick={(e) => handleTermClick(part, e)}
                >
                  {part}
                </strong>
              );
            } else {
              // 已經出現過的 term 不高亮
              return <React.Fragment key={`txt-${i}`}>{part}</React.Fragment>;
            }
          }
          return <React.Fragment key={`txt-${i}`}>{part}</React.Fragment>;
        });
      }

      return processedLine;
    };

    // 渲染：每段用 <p> 包起來，段內單行換行 → <br/>
    return paragraphs.map((para, pi) => {
      const lines = para.split(/\r?\n/);
      return (
        <p key={`p-${pi}`}>
          {lines.map((line, li) => (
            <React.Fragment key={`l-${pi}-${li}`}>
              {highlightTermsInLine(line)}
              {li < lines.length - 1 && <br />}
            </React.Fragment>
          ))}
        </p>
      );
    });
  };

  const { sortedTerms, termDefinitionsFromDB } = useMemo(() => {
    // 使用從資料庫載入的術語，如果沒有則使用 newsData.terms 作為後備
    const raw = newsTerms.length > 0 ? newsTerms : (Array.isArray(newsData?.terms) ? newsData.terms : []);
    
    // 如果 newsTerms 是物件陣列（包含 definition 和 example）
    if (newsTerms.length > 0 && typeof newsTerms[0] === 'object') {
      const termStrings = newsTerms.map(item => item.term);
      const definitions = {};
      newsTerms.forEach(item => {
        definitions[item.term] = {
          definition: item.definition,
          example: item.example
        };
      });
      
      return {
        sortedTerms: Array.from(new Set(termStrings)).sort((a, b) => b.length - a.length),
        termDefinitionsFromDB: definitions
      };
    }
    
    // 如果是字串陣列（舊格式或 newsData.terms）
    const termStrings = Array.isArray(raw) ? raw : [];
    return {
      sortedTerms: Array.from(new Set(termStrings)).sort((a, b) => b.length - a.length),
      termDefinitionsFromDB: {}
    };
  }, [newsData, newsTerms]);


  if (!newsData) {
    return (
      <div className="newsDetail">
        <Link to={getLanguageRoute("/")} className="backButton">{t('newsDetail.backToHome')}</Link>
        <p>找不到該新聞</p>
      </div>
    );
  }

  return (
    <div className="newsDetail">
      <button 
        className={`chat-toggle-btn ${isChatOpen ? 'hidden' : ''}`}
        onClick={() => setIsChatOpen(!isChatOpen)}
        title={isChatOpen ? t('newsDetail.chat.close') : t('newsDetail.chat.open')}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path 
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
        </svg>
      </button>



      <div className={`article-container articleContainer ${isChatOpen ? 'chat-open' : ''}`}>
        {/* 主要內容區域 - 左右佈局 */}
        <div className="content-layout">
          {/* 左側：新聞主要內容 */}
          <div className="main-content">
            <div className="articleContent">
              <h2 className="articleTitle">{newsData.title}</h2>
              <div className="articleInfo">
                <span className="articleDate">{newsData.date}</span>
                <span className="articleAuthor">{t('newsDetail.author')}{newsData.author}</span>
                {newsKeywords && newsKeywords.length > 0 && (
                  <div className="articleKeywords">
                    {newsKeywords.map((kw, index) => (
                      <span className="keywordChip" key={index}>{kw.keyword}</span>
                    ))}
                  </div>
                )}
              </div>

              {newsImage?.map((img, i) => (
                <div className="articleImage" key={i}>
                  <img src={img.src} alt={img.description} />
                  {img.description && (
                    <div className="imageCaption">{img.description}</div>
                  )}
                </div>
              ))}
              <div className="articleText" style={{ userSelect: 'text' }}>
                {renderArticleText(newsData.long)}
              </div>
            </div>
          </div>

          {/* 右側：正反方立場 或 專家分析 */}
          <div className="sidebar-content">
            {/* 載入中狀態：只在真正載入資料時顯示 */}
            {(showContent === 'loading') || 
             (showContent === 'loadPosition' && positionLoading) || 
             (showContent === 'loadExpert' && analysisLoading) || 
             (showContent === 'loadBoth' && (positionLoading || analysisLoading)) || 
             (showContent === 'loadExpertForBoth' && analysisLoading) ? (
              <div className="prosConsSection">
                <h4 className="prosConsTitle">{t('newsDetail.loading.positions')}</h4>
                <div className="loadingMessage">{t('newsDetail.loading.data')}</div>
              </div>
            ) : showContent === 'position' ? (
              <div className="prosConsSection">
                <h4 className="prosConsTitle">{t('newsDetail.positions.positive')} / {t('newsDetail.positions.negative')}</h4>
                <div className="prosConsGrid">
                  {/* 正方立場 */}
                  <div className="prosColumn">
                    <div className="prosHeader">
                      <h5 className="prosTitle">{t('newsDetail.positions.positive')}</h5>
                    </div>
                    <div className="prosContent">
                      {positionData.positive && positionData.positive.length > 0 ? (
                        positionData.positive.map((point, index) => (
                          <div 
                            className="prosPoint clickable-point" 
                            key={index}
                            onClick={() => handlePositionClick(point, 'positive')}
                            title="點擊查看完整內容"
                          >
                            {truncateText(point)}
                          </div>
                        ))
                      ) : (
                        <div className="prosPoint">
                          {t('newsDetail.positions.noPositive')}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 反方立場 */}
                  <div className="consColumn">
                    <div className="consHeader">
                      <h5 className="consTitle">{t('newsDetail.positions.negative')}</h5>
                    </div>
                    <div className="consContent">
                      {positionData.negative && positionData.negative.length > 0 ? (
                        positionData.negative.map((point, index) => (
                          <div 
                            className="consPoint clickable-point" 
                            key={index}
                            onClick={() => handlePositionClick(point, 'negative')}
                            title="點擊查看完整內容"
                          >
                            {truncateText(point)}
                          </div>
                        ))
                      ) : (
                        <div className="consPoint">
                          {t('newsDetail.positions.noNegative')}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : showContent === 'expert' ? (
              <div className="expertAnalysisSection">
                <div className="expertAnalysisTitleBar">
                  <h4 className="expertAnalysisTitle">{t('newsDetail.expertAnalysis.title')}</h4>
                  <button 
                    className="refreshAllExpertsBtn"
                    onClick={handleRefreshAllExperts}
                    disabled={batchGenerating || generatingExperts.size > 0}
                    title="重新生成所有專家觀點"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" 
                         className={batchGenerating ? 'rotating' : ''}>
                      <path d="M1 4v6h6M23 20v-6h-6" />
                      <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                    </svg>
                    {batchGenerating ? '生成中...' : '換一批'}
                  </button>
                </div>
                <div className="expertAnalysisContent">
                  {expertAnalysis && expertAnalysis.length > 0 ? (
                    expertAnalysis.map((analysis, index) => {
                      const isGenerating = generatingExperts.has(analysis.analyze_id);
                      
                      return (
                        <div className="analysisItem" key={analysis.analyze_id || index}>
                          <div className="analysisHeader">
                            <div className="analysisCategory">
                              <span className="categoryTag">{analysis.analyze.Role}</span>
                            </div>
                            <button 
                              className="changeExpertBtn"
                              onClick={() => handleChangeExpert(analysis.analyze_id, analysis.category)}
                              disabled={isGenerating || batchGenerating}
                              title="更換專家觀點"
                            >
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                                   className={isGenerating ? 'rotating' : ''}>
                                <path d="M1 4v6h6M23 20v-6h-6" />
                                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                              </svg>
                              {isGenerating ? '生成中...' : '換專家'}
                            </button>
                          </div>
                          <div className="analysisText">
                            {analysis.analyze.Analyze}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="noAnalysisMessage">
                      {t('newsDetail.expertAnalysis.noData')}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="prosConsSection">
                <h4 className="prosConsTitle">{t('newsDetail.expertAnalysis.noAnalysis')}</h4>
                <div className="noAnalysisMessage">
                  {t('newsDetail.expertAnalysis.noContent')}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 相關內容區塊 - 移動到資料來源上面 */}
      {((relatedNews && relatedNews.length > 0) || (relatedTopics && relatedTopics.length > 0)) && (
        <div className="relatedSection relatedSection--main">
          <div className="container">
            <div className="relatedGrid relatedGrid--horizontal">
              {/* 相關新聞 */}
              {relatedNews && relatedNews.length > 0 && (
                <div className="relatedColumn">
                  <h5 className="sectionTitle">{t('newsDetail.related.news')}</h5>
                  <div className="relatedItems">
                    {relatedNews.map(item => (
                      <div className="relatedItem" key={`news-${item.id}`}>
                        <Link to={getLanguageRoute(`/news/${item.id}`)}>
                          {item.title}
                        </Link>
                        <div className="relevanceText">{item.relevance}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* 相關專題 */}
              {relatedTopics && relatedTopics.length > 0 && (
                <div className="relatedColumn">
                  <h5 className="sectionTitle">{t('newsDetail.related.topics')}</h5>
                  <div className="relatedItems">
                    {relatedTopics.map(item => (
                      <div className="relatedItem" key={`topic-${item.id}`}>
                        <Link to={getLanguageRoute(`/special-report/${item.id}`)}>
                          {item.title}
                        </Link>
                        <div className="relevanceText">{item.relevance}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 資料來源區塊 - 放在頁面底部 */}
      {(newsUrl || newsData.source) && (() => {
        const MAX = 3;
        
        // 處理從 Supabase 來的資料 (包含媒體、標題、URL)
        let sources = [];
        if (newsUrl && Array.isArray(newsUrl)) {
          sources = newsUrl.filter(item => item.article_url && item.article_title).map(item => ({
            url: item.article_url,
            title: item.article_title,
            media: item.media || t('newsDetail.sources.unknownMedia')
          }));
        }
        
        // 如果沒有 Supabase 資料，使用原本的 source 資料
        if (sources.length === 0 && newsData.source) {
          const all = Array.isArray(newsData.source)
            ? newsData.source.filter(Boolean)
            : (newsData.source ? [newsData.source] : []);
          sources = all.map(url => ({
            url: url,
            title: url,
            media: t('newsDetail.sources.unknownMedia')
          }));
        }

        // 去重，避免重複網址
        const uniq = sources.filter((source, index, self) => 
          index === self.findIndex(s => s.url === source.url)
        );
        const total = uniq.length;
        const visible = showAllSources ? uniq : uniq.slice(0, MAX);
        const hasMore = total > MAX;

        return (
          <div className="sourceBlock">
            <div className="sourceTitle">{t('newsDetail.sources.title')}</div>

            {visible.length > 0 ? (
              <ul className="sourceList">
                {visible.map((source, i) => (
                  <li key={i}>
                    <span className="sourceMedia">{source.media}</span>
                    <span className="sourceSeparator">：</span>
                    <a href={source.url} target="_blank" rel="noopener noreferrer" className="sourceLink">
                      {source.title}
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="sourceEmpty">{t('newsDetail.sources.noSources')}</div>
            )}

            {hasMore && (
              <button
                className="sourceToggleButton"
                onClick={() => setShowAllSources(s => !s)}
              >
                {showAllSources ? t('newsDetail.sources.showLess') : t('newsDetail.sources.showMore', { count: total - MAX })}
              </button>
            )}
          </div>
        );
      })()}

      {/* 側邊聊天室 */}
      <div className={`chat-sidebar ${isChatOpen ? 'open' : ''}`}>
        <div className="chat-sidebar-content" style={{ flex: 1, overflow: 'hidden' }}>
          <ChatRoom ref={chatRoomRef} newsData={newsData} onClose={() => setIsChatOpen(false)} chatExperts={chatExperts}/>
        </div>
      </div>

      {/* 正反方立場彈窗 */}
      {showPositionModal && (
        <div className="position-modal-overlay" onClick={closeModal}>
          <div className="position-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="position-modal-header">
              <h3 className={`position-modal-title ${modalContent.type}`}>
                {modalContent.type === 'positive' ? t('newsDetail.positions.positiveModal') : t('newsDetail.positions.negativeModal')}
              </h3>
              <button className="position-modal-close" onClick={closeModal}>
                X
              </button>
            </div>
            <div className="position-modal-body">
              <p>{modalContent.content}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tooltip */}
      {tooltipTerm && (
        <TermTooltip
          term={tooltipTerm}
          definition={
            termDefinitionsFromDB[tooltipTerm]?.definition || 
            termDefinitions[tooltipTerm]?.definition || 
            `未找到「${tooltipTerm}」的定義`
          }
          example={
            termDefinitionsFromDB[tooltipTerm]?.example || 
            termDefinitions[tooltipTerm]?.example
          }
          position={tooltipPosition}
          onClose={() => setTooltipTerm(null)}
        />
      )}
    </div>
  );
}

export default NewsDetail;