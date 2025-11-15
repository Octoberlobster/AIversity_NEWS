import React, { useState, useEffect, useMemo, useRef} from 'react';
import { useParams, Link} from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './../css/NewsDetail.css';
import ChatRoom from './ChatRoom';
import TermTooltip from './TermTooltip';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { useLanguageFields} from '../utils/useLanguageFields';
import { changeExperts as changeExpertsAPI, generateCountryAnalysis, generateMediaLiteracy } from './api.js';
import { getSuicideWarningText } from '../config/suicideWarningConfig';
import { 
  useNewsData, 
  useNewsImage, 
  useNewsUrl, 
  useNewsKeywords, 
  useNewsTerms,
  useSourceArticles,
  usePositionData,
  useExpertAnalysis,
  useRelatedNews,
  useRelatedTopics,
  useCountryAnalysis,
  useMediaLiteracy
} from '../hooks/useNewsDetail';

function NewsDetail() {
  const { t } = useTranslation();
  const { id } = useParams();
  
  // 多語言相關 hooks
  const { getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [showAllSources, setShowAllSources] = useState(false);
  const [newsData, setNewsData] = useState(null);
  const [newsImage, setNewsImage] = useState(null);
  const [newsUrl, setNewsUrl] = useState(null);
  const [newsKeywords, setNewsKeywords] = useState([]);
  const [attribution, setAttribution] = useState(null); // 歸因資料 {"part1": ["article_id1"], ...}
  const [sourceArticles, setSourceArticles] = useState({}); // 來源文章詳細資訊 {article_id: {title, url, media}}
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
  const [feedbackStatus, setFeedbackStatus] = useState({}); // 記錄每個專家的反饋狀態 {analyze_id: {useful: count, useless: count, userVoted: 'useful'|'useless'|null}}
  const [countryAnalysis, setCountryAnalysis] = useState(null); // 國家觀點資料
  const [generatingCountryAnalysis, setGeneratingCountryAnalysis] = useState(false); // 生成國家觀點中
  const [mediaLiteracy, setMediaLiteracy] = useState(null); // 媒體素養提醒資料
  const [generatingMediaLiteracy, setGeneratingMediaLiteracy] = useState(false); // 生成媒體素養提醒中
  
  // 正反方立場彈窗相關狀態
  const [showPositionModal, setShowPositionModal] = useState(false);
  const [modalContent, setModalContent] = useState({ type: '', content: '' });
  
  // ChatRoom組件的ref
  const chatRoomRef = useRef(null);

  // 🚀 使用 React Query Hook 載入新聞基本資料
  const { data: newsDataResult } = useNewsData(id);
  
  // 🚀 使用 React Query Hook 載入圖片 (背景載入)
  const { data: imageData } = useNewsImage(id);
  
  // 🚀 使用 React Query Hook 載入 URL (背景載入)
  const { data: urlData } = useNewsUrl(id);
  
  // 🚀 使用 React Query Hook 載入關鍵字 (背景載入)
  const { data: keywordsData = [] } = useNewsKeywords(id);
  
  // 🚀 使用 React Query Hook 載入術語 (背景載入)
  const { data: termsData } = useNewsTerms(id);
  
  // 🚀 使用 React Query Hook 載入來源文章 (背景載入,依賴 attribution)
  const { data: sourceArticlesData } = useSourceArticles(id, attribution);
  
  // 🚀 使用 React Query Hook 載入立場資料 (條件載入)
  const shouldLoadPosition = showContent === 'loadPosition' || showContent === 'loadBoth';
  const { data: positionDataResult } = usePositionData(id, shouldLoadPosition);
  
  // 🚀 使用 React Query Hook 載入專家分析 (條件載入)
  const shouldLoadExpert = showContent === 'loadExpert' || showContent === 'loadExpertForBoth';
  const { data: expertAnalysisData } = useExpertAnalysis(id, shouldLoadExpert);
  
  // 🚀 使用 React Query Hook 載入相關新聞 (背景載入)
  const { data: relatedNewsData = [] } = useRelatedNews(id);
  
  // 🚀 使用 React Query Hook 載入相關專題 (背景載入)
  const { data: relatedTopicsData = [] } = useRelatedTopics(id);
  
  // 🚀 使用 React Query Hook 載入國家觀點 (背景載入)
  const { data: countryAnalysisResult } = useCountryAnalysis(id);
  
  // 🚀 使用 React Query Hook 載入媒體素養提醒 (背景載入)
  const { data: mediaLiteracyResult } = useMediaLiteracy(id);
  
  // 🚀 從 hook 結果中提取資料 (向後兼容舊的狀態)
  useEffect(() => {
    if (newsDataResult) {
      setNewsData(newsDataResult.newsData);
      setAttribution(newsDataResult.attribution);
      
      // 根據 position_flag 決定要載入的內容類型
      if (newsDataResult.newsData.position_flag) {
        setShowContent('loadBoth');
      } else {
        setShowContent('loadExpert');
      }
    }
  }, [newsDataResult]);

  // 🚀 更新圖片資料
  useEffect(() => {
    if (imageData) {
      setNewsImage(imageData); // imageData 已經是陣列格式
    }
  }, [imageData]);

  // 🚀 更新 URL 資料
  useEffect(() => {
    if (urlData) {
      setNewsUrl(urlData);
    }
  }, [urlData]);

  // 🚀 更新關鍵字資料
  useEffect(() => {
    setNewsKeywords(keywordsData);
  }, [keywordsData]);

  // 🚀 更新術語資料
  useEffect(() => {
    if (termsData) {
      setNewsTerms(termsData.terms);
      setTermDefinitions(termsData.definitions);
    }
  }, [termsData]);

  // 🚀 更新來源文章資料
  useEffect(() => {
    if (sourceArticlesData) {
      setSourceArticles(sourceArticlesData);
    }
  }, [sourceArticlesData]);

  // 🚀 更新立場資料
  useEffect(() => {
    if (positionDataResult) {
      setPositionData(positionDataResult);
      setPositionLoading(false);
      
      // 根據載入模式決定顯示內容
      if (showContent === 'loadBoth') {
        setShowContent('loadExpertForBoth'); // 觸發專家分析載入
      } else if (showContent === 'loadPosition') {
        setShowContent('position');
      }
    }
  }, [positionDataResult, showContent]);

  // 🚀 更新專家分析資料
  useEffect(() => {
    if (expertAnalysisData) {
      setExpertAnalysis(expertAnalysisData);
      setChatExperts(expertAnalysisData);
      setAnalysisLoading(false);
      
      // 初始化反饋狀態(只在首次載入或專家列表變化時)
      setFeedbackStatus(prev => {
        const newFeedback = {};
        expertAnalysisData.forEach(expert => {
          // 如果已經有狀態(用戶已投票),保留原狀態
          if (prev[expert.analyze_id]) {
            newFeedback[expert.analyze_id] = prev[expert.analyze_id];
          } else {
            // 否則從 localStorage 讀取
            const localStorageKey = `expert_feedback_${expert.analyze_id}`;
            const savedVote = localStorage.getItem(localStorageKey);
            
            newFeedback[expert.analyze_id] = {
              useful: expert.useful || 0,
              useless: expert.useless || 0,
              userVoted: savedVote || null
            };
          }
        });
        return newFeedback;
      });
      
      // 根據載入模式決定要顯示什麼
      if (showContent === 'loadExpertForBoth') {
        setShowContent('position'); // 保持顯示正反方立場
      } else if (showContent === 'loadExpert') {
        if (expertAnalysisData.length > 0) {
          setShowContent('expert');
        } else {
          setShowContent('none');
        }
      }
    }
  }, [expertAnalysisData, showContent]);

  // 🚀 更新相關新聞資料
  useEffect(() => {
    setRelatedNews(relatedNewsData);
  }, [relatedNewsData]);

  // 🚀 更新相關專題資料
  useEffect(() => {
    setRelatedTopics(relatedTopicsData);
  }, [relatedTopicsData]);

  // 🚀 更新台灣觀點資料
  useEffect(() => {
    if (countryAnalysisResult) {
      setCountryAnalysis(countryAnalysisResult.analysis);
      //console.log('台灣觀點資料更新:', countryAnalysisResult);
    }
  }, [countryAnalysisResult]);

  // 🚀 更新媒體素養提醒資料
  useEffect(() => {
    if (mediaLiteracyResult) {
      setMediaLiteracy(mediaLiteracyResult.literacy);
      //console.log('媒體素養提醒資料更新:', mediaLiteracyResult);
    }
  }, [mediaLiteracyResult]);

  // 計算要顯示的文章內容 (包含防自殺聲明)
  const articleContent = useMemo(() => {
    if (!newsData?.long) return '';
    
    if (newsData.suicide_flag) {
      return newsData.long + getSuicideWarningText(currentLanguage);
    }
    return newsData.long;
  }, [newsData?.long, newsData?.suicide_flag, currentLanguage]);

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
      //console.log('=== 開始更換專家流程 ===');
      //console.log('要更換的專家:', expertsToRegenerate);
      
      // 標記正在生成的專家
      const regenerateIds = expertsToRegenerate.map(e => e.analyze_id);
      setGeneratingExperts(prev => new Set([...prev, ...regenerateIds]));

      // 生成或取得 user_id 和 room_id
      const userId = getOrCreateUserId();
      const roomId = createRoomId(userId, id);
      /*
      console.log('userId:', userId);
      console.log('roomId:', roomId);
      console.log('storyId:', id);
      console.log('language:', mapLanguageCode(currentLanguage));
      */

      // 準備當前專家資料
      const currentExperts = expertAnalysis.map(expert => ({
        analyze_id: expert.analyze_id,
        category: expert.category,
        analyze: expert.analyze
      }));
      //console.log('當前所有專家:', currentExperts);

      // 呼叫 api.js 中的函數
      //console.log('準備呼叫 changeExpertsAPI...');
      const result = await changeExpertsAPI(
        userId,
        roomId,
        id,
        mapLanguageCode(currentLanguage),
        currentExperts,
        expertsToRegenerate
      );
      /*
      console.log('=== 收到 API 回傳結果 ===');
      console.log('result:', result);
      console.log('result.success:', result.success);
      console.log('result.experts:', result.experts);
      console.log('result.replaced_ids:', result.replaced_ids);
      */

      if (result.success && result.experts && result.experts.length > 0) {
        //console.log('✅ API 呼叫成功，開始更新狀態');
        
        // 建立新專家的映射表 (用 replaced_ids 來對應)
        const newExpertsMap = new Map();
        if (result.replaced_ids && result.replaced_ids.length === result.experts.length) {
          result.replaced_ids.forEach((oldId, index) => {
            newExpertsMap.set(oldId, result.experts[index]);
            //console.log(`映射: ${oldId} → ${result.experts[index].analyze_id}`);
          });
        }
        
        //console.log('新專家映射表:', newExpertsMap);
        
        // 更新專家分析狀態
        setExpertAnalysis(prevExperts => {
          const updated = prevExperts.map(expert => 
            newExpertsMap.has(expert.analyze_id) 
              ? newExpertsMap.get(expert.analyze_id) 
              : expert
          );
          //console.log('更新後的 expertAnalysis:', updated);
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
      //console.log('=== 更換專家流程結束 ===');
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
      //console.log('=== 開始批量更換所有專家 ===');
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
        //console.log(`正在更換專家: ${expert.category} (${expert.analyze_id})`);
        
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
            //console.log(`✅ 專家 ${expert.category} 更換成功:`, result);
            return {
              success: true,
              oldId: expert.analyze_id,
              newExpert: result.success_response?.experts?.[0] || result.experts?.[0],
            };
          })
          .catch((error) => {
            //console.error(`❌ 專家 ${expert.category} 更換失敗:`, error);
            return {
              success: false,
              oldId: expert.analyze_id,
              error: error.message,
            };
          });
      };

      // 🧠 2️⃣ 平行發送所有請求
      //console.log('平行發送 API 請求...');
      const allPromises = expertAnalysis.map(fetchSingleExpert);
      const results = await Promise.all(allPromises);

      //console.log('所有 API 請求完成:', results);

      // 🧠 3️⃣ 處理結果並更新狀態
      const successResults = results.filter(r => r.success);

      if (successResults.length > 0) {
        // 建立新專家的映射表
        const newExpertsMap = new Map();
        successResults.forEach(({ oldId, newExpert }) => {
          if (newExpert) {
            newExpertsMap.set(oldId, newExpert);
            //console.log(`映射: ${oldId} → ${newExpert.analyze_id}`);
          }
        });

        // 更新專家分析狀態
        setExpertAnalysis(prevExperts => {
          const updated = prevExperts.map(expert =>
            newExpertsMap.has(expert.analyze_id)
              ? newExpertsMap.get(expert.analyze_id)
              : expert
          );
          //console.log('批量更新後的 expertAnalysis:', updated);
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
      //console.log('=== 批量更換專家流程結束 ===');
    }
  };

  // 處理專家分析反饋（只在本地記錄，不接資料庫）
  const handleExpertFeedback = (analyzeId, feedbackType) => {
    // 檢查用戶是否已經投過票
    const localStorageKey = `expert_feedback_${analyzeId}`;
    const existingVote = localStorage.getItem(localStorageKey);
    
    if (existingVote) {
      //console.log(`用戶已經對專家 ${analyzeId} 投過票: ${existingVote}`);
      return; // 已經投過票，不執行任何操作
    }

    //console.log(`記錄反饋: analyzeId=${analyzeId}, feedbackType=${feedbackType}`);
    
    // 更新本地狀態
    setFeedbackStatus(prev => ({
      ...prev,
      [analyzeId]: {
        ...prev[analyzeId],
        [feedbackType]: (prev[analyzeId]?.[feedbackType] || 0) + 1,
        userVoted: feedbackType
      }
    }));

    // 保存到 localStorage
    localStorage.setItem(localStorageKey, feedbackType);
    
    //console.log('反饋已記錄到本地');
  };

  // 處理生成台灣觀點
  const handleGenerateCountryAnalysis = async () => {
    if (generatingCountryAnalysis) {
      return;
    }

    try {
      //console.log('=== 開始生成台灣觀點 ===');
      setGeneratingCountryAnalysis(true);

      // 固定使用 'Taiwan' 調用 API 生成觀點
      const result = await generateCountryAnalysis(id, 'Taiwan');
      
      //console.log('台灣觀點生成成功:', result);
      
      // 將 API 返回的扁平結構轉換為資料庫格式
      const formattedResult = {
        analyze: { content: result.analyze },
        analyze_en_lang: { content: result.analyze_en_lang },
        analyze_id_lang: { content: result.analyze_id_lang },
        analyze_jp_lang: { content: result.analyze_jp_lang },
        country: 'Taiwan'
      };
      
      setCountryAnalysis(formattedResult);
      
    } catch (error) {
      //console.error('生成台灣觀點失敗:', error);
    } finally {
      setGeneratingCountryAnalysis(false);
      //console.log('=== 生成台灣觀點流程結束 ===');
    }
  };

  // 處理生成媒體素養提醒
  const handleGenerateMediaLiteracy = async () => {
    if (generatingMediaLiteracy) {
      return;
    }

    try {
      //console.log('=== 開始生成媒體素養提醒 ===');
      setGeneratingMediaLiteracy(true);

      // 調用 API 生成媒體素養提醒
      const result = await generateMediaLiteracy(id);
      
      //console.log('媒體素養提醒生成成功:', result);
      
      // 將 API 返回的扁平結構轉換為資料庫格式
      const formattedResult = {
        alert: result.alert,
        alert_en_lang: result.alert_en_lang,
        alert_id_lang: result.alert_id_lang,
        alert_jp_lang: result.alert_jp_lang
      };
      
      setMediaLiteracy(formattedResult);
      
    } catch (error) {
      console.error('生成媒體素養提醒失敗:', error);
    } finally {
      setGeneratingMediaLiteracy(false);
      //console.log('=== 生成媒體素養提醒流程結束 ===');
    }
  };

  // 確保頁面載入時滾動到頂部，語言切換時也要重置
  useEffect(() => {
    window.scrollTo(0, 0);
    setShowAllSources(false);
    setPositionLoading(true);
    setAnalysisLoading(true);
  }, [id, currentLanguage]);

  // 根據當前語言獲取國家觀點內容
  const getCountryAnalysisContent = () => {
    if (!countryAnalysis) return null;
    
    const languageFieldMap = {
      'zh-TW': 'analyze',
      'en': 'analyze_en_lang',
      'jp': 'analyze_jp_lang',
      'id': 'analyze_id_lang'
    };
    
    const fieldName = languageFieldMap[currentLanguage] || 'analyze';
    const content = countryAnalysis[fieldName];
    
    // 處理兩種格式：資料庫的 {content: "..."} 和 API 的 "..."
    if (typeof content === 'object' && content.content) {
      return content.content;
    }
    return content;
  };

  // 根據當前語言獲取媒體素養內容
  const getMediaLiteracyContent = () => {
    if (!mediaLiteracy) return null;
    
    const languageFieldMap = {
      'zh-TW': 'alert',
      'en': 'alert_en_lang',
      'jp': 'alert_jp_lang',
      'id': 'alert_id_lang'
    };
    
    const fieldName = languageFieldMap[currentLanguage] || 'alert';
    return mediaLiteracy[fieldName];
  };

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

    const highlightTermsInLine = (line) => {
      if (!termsPattern) return line;

      // 只處理術語（terms），不再處理 highlights
      return line.split(termsPattern).map((part, i) => {
        if (terms.includes(part)) {
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
            return <React.Fragment key={`txt-${i}`}>{part}</React.Fragment>;
          }
        }
        return <React.Fragment key={`txt-${i}`}>{part}</React.Fragment>;
      });
    };

    // 渲染：每段用 <p> 包起來，段內單行換行 → <br/>
    return paragraphs.map((para, pi) => {
      const lines = para.split(/\r?\n/);
      
      // 判斷是否為防自殺聲明的最後一段 (最後一個段落)
      const isLastParagraph = pi === paragraphs.length - 1;
      const isSuicideWarningLastPara = isLastParagraph && newsData?.suicide_flag;
      
      // 獲取該段落的來源資訊 (part1, part2, ...)
      const partKey = `part${pi + 1}`;
      const articleIds = attribution?.[partKey] || [];
      
      // 過濾出真實存在的來源
      const validSources = articleIds
        .map((articleId) => sourceArticles[articleId])
        .filter(article => article && article.url && article.url !== '#');
      
      return (
        <p 
          key={`p-${pi}`}
          style={isSuicideWarningLastPara ? { 
            color: '#dc2626',
            fontWeight: '600',
          } : {}}
        >
          {lines.map((line, li) => (
            <React.Fragment key={`l-${pi}-${li}`}>
              {highlightTermsInLine(line)}
              {li < lines.length - 1 && <br />}
            </React.Fragment>
          ))}
          
          {/* 在段落內部顯示來源連結圖標 */}
          {validSources.length > 0 && (() => {
            return (
              <span className="paragraph-sources-inline">
                <span 
                  className="source-badge-wrapper"
                  onMouseEnter={(e) => {
                    const wrapper = e.currentTarget;
                    const tooltip = wrapper.querySelector('.source-tooltip');
                    const arrow = tooltip.querySelector('.source-tooltip-arrow');
                    const rect = wrapper.getBoundingClientRect();
                    const tooltipWidth = 420;
                    
                    // 計算位置
                    let left = rect.left + rect.width / 2;
                    let transformX = '-50%';
                    let arrowLeft = '50%';
                    
                    if (left - tooltipWidth / 2 < 10) {
                      const offset = rect.left + rect.width / 2 - 10;
                      left = 10;
                      transformX = '0';
                      arrowLeft = `${Math.max(20, offset)}px`;
                    } else if (left + tooltipWidth / 2 > window.innerWidth - 10) {
                      const offset = rect.left + rect.width / 2 - (window.innerWidth - 10);
                      left = window.innerWidth - 10;
                      transformX = '-100%';
                      arrowLeft = `${tooltipWidth + offset - 20}px`;
                    }
                    
                    tooltip.style.left = `${left}px`;
                    tooltip.style.top = `${rect.top - 10}px`;
                    tooltip.style.transform = `translate(${transformX}, -100%)`;
                    arrow.style.left = arrowLeft;
                    
                    // 添加 active 類
                    tooltip.classList.add('tooltip-active');
                    
                    // 設置定時器ID到元素上
                    if (wrapper._hideTimer) {
                      clearTimeout(wrapper._hideTimer);
                      delete wrapper._hideTimer;
                    }
                  }}
                  onMouseLeave={(e) => {
                    const wrapper = e.currentTarget;
                    const tooltip = wrapper.querySelector('.source-tooltip');
                    
                    // 延遲隱藏
                    wrapper._hideTimer = setTimeout(() => {
                      tooltip.classList.remove('tooltip-active');
                    }, 100);
                  }}
                >
                  <span className="source-badge" title={`參考 ${validSources.length} 個來源`}>
                    [{validSources.length}]
                  </span>
                  <span 
                    className="source-tooltip"
                    onMouseEnter={(e) => {
                      const wrapper = e.currentTarget.closest('.source-badge-wrapper');
                      const tooltip = e.currentTarget;
                      
                      // 取消隱藏定時器
                      if (wrapper._hideTimer) {
                        clearTimeout(wrapper._hideTimer);
                        delete wrapper._hideTimer;
                      }
                      
                      // 確保顯示
                      tooltip.classList.add('tooltip-active');
                    }}
                    onMouseLeave={(e) => {
                      const wrapper = e.currentTarget.closest('.source-badge-wrapper');
                      const tooltip = e.currentTarget;
                      
                      // 延遲隱藏
                      wrapper._hideTimer = setTimeout(() => {
                        tooltip.classList.remove('tooltip-active');
                      }, 50);
                    }}
                  >
                    <span className="source-tooltip-header">參考來源</span>
                    <span className="source-tooltip-list">{validSources.map((article, idx) => (
                      <a
                        key={`source-link-${pi}-${idx}`}
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="source-tooltip-item"
                      ><span className="source-tooltip-media">{article.media}</span><span className="source-tooltip-title">{article.title}</span></a>
                    ))}</span>
                    <span className="source-tooltip-arrow"></span>
                  </span>
                </span>
              </span>
            );
          })()}
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
        <div className="newsDetail__loadingContainer">
          <div className="newsDetail__loadingSpinner"></div>
          <p className="newsDetail__loadingText">
            {t('newsDetail.loading.generating')}
          </p>
        </div>
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
                <span className="articleDate">
                  {t('newsDetail.publishedDate')}: {newsData.date}
                </span>
                {newsData.updateDate && (
                  <span className="articleDate">
                    {t('newsDetail.updatedDate')}: {newsData.updateDate}
                  </span>
                )}
                {newsKeywords && newsKeywords.length > 0 && (
                  <div className="articleKeywords">
                    {newsKeywords.map((kw, index) => (
                      <Link 
                        to={getLanguageRoute(`/search/${encodeURIComponent(kw.keyword)}`)} 
                        className="keywordChip" 
                        key={index}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ textDecoration: 'none' }}
                      >
                        {kw.keyword}
                      </Link>
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
                {renderArticleText(articleContent)}
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
              <>
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
                
                {/* 台灣觀點區塊 - 在正反方觀點下方 */}
                <div className="countryAnalysisSection countryAnalysisSection--inline">
                  <h4 className="countryAnalysisTitle">{t('newsDetail.taiwanPerspective.title')}</h4>
                  
                  {countryAnalysis ? (
                    <div className="countryAnalysisContent">
                      <div className="countryAnalysisText">
                        {getCountryAnalysisContent()}
                      </div>
                    </div>
                  ) : (
                    <div className="countryAnalysisPlaceholder">
                      <button 
                        className="generateCountryAnalysisBtn"
                        onClick={handleGenerateCountryAnalysis}
                        disabled={generatingCountryAnalysis}
                      >
                        {generatingCountryAnalysis ? (
                          <>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="rotating">
                              <path d="M1 4v6h6M23 20v-6h-6" />
                              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                            </svg>
                            {t('newsDetail.taiwanPerspective.generating')}
                          </>
                        ) : (
                          <>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M12 5v14M5 12h14" />
                            </svg>
                            {t('newsDetail.taiwanPerspective.generateButton')}
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
                
                {/* 媒體素養提醒區塊 - 在台灣觀點下方 */}
                <div className="mediaLiteracySection mediaLiteracySection--inline">
                  <h4 className="mediaLiteracyTitle">{t('newsDetail.mediaLiteracy.title')}</h4>
                  
                  {mediaLiteracy ? (
                    <div className="mediaLiteracyContent">
                      <div className="mediaLiteracyText">
                        {getMediaLiteracyContent()}
                      </div>
                    </div>
                  ) : (
                    <div className="mediaLiteracyPlaceholder">
                      <button 
                        className="generateMediaLiteracyBtn"
                        onClick={handleGenerateMediaLiteracy}
                        disabled={generatingMediaLiteracy}
                      >
                        {generatingMediaLiteracy ? (
                          <>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="rotating">
                              <path d="M1 4v6h6M23 20v-6h-6" />
                              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                            </svg>
                            {t('newsDetail.mediaLiteracy.generating')}
                          </>
                        ) : (
                          <>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M12 5v14M5 12h14" />
                            </svg>
                            {t('newsDetail.mediaLiteracy.generateButton')}
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : showContent === 'expert' ? (
              <div className="expertAnalysisSection">
                <div className="expertAnalysisTitleBar">
                  <h4 className="expertAnalysisTitle">{t('newsDetail.expertAnalysis.title')}</h4>
                  <button 
                    className="refreshAllExpertsBtn"
                    onClick={handleRefreshAllExperts}
                    disabled={batchGenerating || generatingExperts.size > 0}
                    title={t('newsDetail.expertAnalysis.refreshAllTitle')}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" 
                         className={batchGenerating ? 'rotating' : ''}>
                      <path d="M1 4v6h6M23 20v-6h-6" />
                      <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                    </svg>
                    {batchGenerating ? t('newsDetail.expertAnalysis.generating') : t('newsDetail.expertAnalysis.refreshAll')}
                  </button>
                </div>
                <div className="expertAnalysisContent">
                  {expertAnalysis && expertAnalysis.length > 0 ? (
                    expertAnalysis.map((analysis, index) => {
                      const isGenerating = generatingExperts.has(analysis.analyze_id);
                      const feedback = feedbackStatus[analysis.analyze_id] || { useful: 0, useless: 0, userVoted: null };
                      
                      return (
                        <div className="analysisItem" key={analysis.analyze_id || index}>
                          <div className="analysisHeader">
                            <div className="analysisCategory">
                              <span className="categoryTag">{analysis.analyze.Role}</span>
                            </div>
                            {/* 反饋按鈕區域 - 放在換專家按鈕左邊 */}
                            <div className="analysisFeedback">
                              <button 
                                className={`feedbackBtn feedbackBtn--useful ${feedback.userVoted === 'useful' ? 'voted' : ''}`}
                                onClick={() => handleExpertFeedback(analysis.analyze_id, 'useful')}
                                disabled={feedback.userVoted !== null}
                                title={feedback.userVoted === 'useful' ? '已標記為有益' : '標記為有益'}
                              >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill={feedback.userVoted === 'useful' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
                                  <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
                                </svg>
                              </button>
                              <button 
                                className={`feedbackBtn feedbackBtn--useless ${feedback.userVoted === 'useless' ? 'voted' : ''}`}
                                onClick={() => handleExpertFeedback(analysis.analyze_id, 'useless')}
                                disabled={feedback.userVoted !== null}
                                title={feedback.userVoted === 'useless' ? '已標記為無益' : '標記為無益'}
                              >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill={feedback.userVoted === 'useless' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
                                  <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
                                </svg>
                              </button>
                            </div>
                            <button 
                              className="changeExpertBtn"
                              onClick={() => handleChangeExpert(analysis.analyze_id, analysis.category)}
                              disabled={isGenerating || batchGenerating}
                              title={t('newsDetail.expertAnalysis.changeExpertTitle')}
                            >
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                                   className={isGenerating ? 'rotating' : ''}>
                                <path d="M1 4v6h6M23 20v-6h-6" />
                                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                              </svg>
                              {isGenerating ? t('newsDetail.expertAnalysis.generating') : t('newsDetail.expertAnalysis.changeExpert')}
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
                
                {/* 台灣觀點區塊 - 在專家分析內部 */}
                <div className="countryAnalysisSection countryAnalysisSection--inline">
                  <h4 className="countryAnalysisTitle">{t('newsDetail.taiwanPerspective.title')}</h4>
                  
                  {countryAnalysis ? (
                    <div className="countryAnalysisContent">
                      <div className="countryAnalysisText">
                        {getCountryAnalysisContent()}
                      </div>
                    </div>
                  ) : (
                    <div className="countryAnalysisPlaceholder">
                      <button 
                        className="generateCountryAnalysisBtn"
                        onClick={handleGenerateCountryAnalysis}
                        disabled={generatingCountryAnalysis}
                      >
                        {generatingCountryAnalysis ? (
                          <>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="rotating">
                              <path d="M1 4v6h6M23 20v-6h-6" />
                              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                            </svg>
                            {t('newsDetail.taiwanPerspective.generating')}
                          </>
                        ) : (
                          <>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M12 5v14M5 12h14" />
                            </svg>
                            {t('newsDetail.taiwanPerspective.generateButton')}
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
                
                {/* 媒體素養提醒區塊 - 在台灣觀點下方 */}
                <div className="mediaLiteracySection mediaLiteracySection--inline">
                  <h4 className="mediaLiteracyTitle">{t('newsDetail.mediaLiteracy.title')}</h4>
                  
                  {mediaLiteracy ? (
                    <div className="mediaLiteracyContent">
                      <div className="mediaLiteracyText">
                        {getMediaLiteracyContent()}
                      </div>
                    </div>
                  ) : (
                    <div className="mediaLiteracyPlaceholder">
                      <button 
                        className="generateMediaLiteracyBtn"
                        onClick={handleGenerateMediaLiteracy}
                        disabled={generatingMediaLiteracy}
                      >
                        {generatingMediaLiteracy ? (
                          <>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="rotating">
                              <path d="M1 4v6h6M23 20v-6h-6" />
                              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                            </svg>
                            {t('newsDetail.mediaLiteracy.generating')}
                          </>
                        ) : (
                          <>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M12 5v14M5 12h14" />
                            </svg>
                            {t('newsDetail.mediaLiteracy.generateButton')}
                          </>
                        )}
                      </button>
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
      {((relatedNews && relatedNews.length > 0)) && (
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
              {relatedTopics && relatedTopics.length > 0 && (
                <div className="relatedColumn">
                  <h5 className="sectionTitle">{t('newsDetail.related.topics')}</h5>
                  <div className="relatedItems">
                    {relatedTopics.map(item => (
                      <div className="relatedItem" key={`topic-${item.id}`}>
                        <Link to={getLanguageRoute(`/special-report/${item.id}`)}>
                          {item.title}
                        </Link>
                        <div className="relevanceText">{t('newsDetail.related.topicRelation')}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 資料來源區塊 - 放在頁面底部,使用 newsUrl 或 newsData.source */}
      {(newsUrl || newsData.source) && (() => {
        const MAX = 3;
        
        // 處理從 cleaned_news 來的資料 (包含媒體、標題、URL、日期)
        let sources = [];
        if (newsUrl && Array.isArray(newsUrl)) {
          sources = newsUrl.filter(item => item.article_url && item.article_title).map(item => ({
            url: item.article_url,
            title: item.article_title,
            media: item.media || t('newsDetail.sources.unknownMedia'),
            date: item.write_date || null
          }));
          
          // 按 write_date 由新到舊排序
          sources.sort((a, b) => {
            if (!a.date) return 1;
            if (!b.date) return -1;
            return new Date(b.date) - new Date(a.date);
          });
        }
        
        // 如果沒有 newsUrl 資料,使用 newsData.source 作為後備
        if (sources.length === 0 && newsData.source) {
          const all = Array.isArray(newsData.source)
            ? newsData.source.filter(Boolean)
            : (newsData.source ? [newsData.source] : []);
          sources = all.map(url => ({
            url: url,
            title: url,
            media: t('newsDetail.sources.unknownMedia'),
            date: null
          }));
          //console.log('後備 sources:', sources);
        }
        
        //console.log('最終 sources:', sources, '總數:', sources.length);

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
                    <span className="sourceMedia">
                      {source.media}
                      {source.date && (
                        <span className="sourceDate"> ({source.date})</span>
                      )}
                    </span>
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
          getLanguageRoute={getLanguageRoute}
        />
      )}
    </div>
  );
}

export default NewsDetail;