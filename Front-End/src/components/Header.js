import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { translateTexts } from './api';
import './../css/Header.css';

const domains = [
  { id: '/', label: '首頁', path: '/'},
  { id: 'politics', label: '政治', path: '/category/Politics' },
  { id: 'taiwan', label: '台灣', path: '/category/Taiwan News' },
  { id: 'international', label: '國際', path: '/category/International News' },
  { id: 'scienceandtech', label: '科學與科技', path: '/category/Science & Technology' },
  { id: 'life', label: '生活', path: '/category/Lifestyle & Consumer' },
  { id: 'sports', label: '體育', path: '/category/Sports' },
  { id: 'entertainment', label: '娛樂', path: '/category/Entertainment' },
  { id: 'finance', label: '商業財經', path: '/category/Business & Finance' },
  { id: 'health', label: '健康', path: '/category/Health & Wellness' },
  { id: 'project', label: '專題報導', path: '/special-reports'}
];

const languages = [
  { name: '中文', code: 'zh' },
  { name: 'English', code: 'en' },
  { name: '日文', code: 'ja' },
  { name: '韓文', code: 'ko' },
  { name: '越南文', code: 'vi' },
  { name: '菲律賓文', code: 'fil' },
  { name: '印尼文', code: 'id' },
  { name: '西班牙文', code: 'es' },
  { name: '法文', code: 'fr' },
  { name: '德文', code: 'de' },
];

function Header() {
  const [activeDomain, setActiveDomain] = useState(domains[0].id);
  const [search, setSearch] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('zh');
  const [isTranslating, setIsTranslating] = useState(false);
  const [originalTextNodes, setOriginalTextNodes] = useState([]);
  const [isOriginalContentBackedUp, setIsOriginalContentBackedUp] = useState(false);
  
  // 新增：翻譯快取狀態
  const [translationCache, setTranslationCache] = useState({});
  const translationCacheRef = useRef({});
  const [currentPageKey, setCurrentPageKey] = useState('');
  
  // 新增：DOM 變化觀察器
  const [domObserver, setDomObserver] = useState(null);
  
  // 使用 ref 來保存當前語言狀態，避免 useEffect 依賴問題
  const selectedLanguageRef = useRef('zh');
  
  const location = useLocation();
  const navigate = useNavigate();



  // 提取文字節點的函數  
  const extractTextNodes = () => {
    const textNodes = [];
    const carouselTexts = [];
    const headerTexts = [];
    const contentTexts = [];
    
    console.log('🔍 開始提取頁面文字節點...');
    console.log('📍 當前頁面URL:', window.location.pathname);
    
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(node) {
          const text = node.textContent.trim();
          const parent = node.parentElement;
          
          // 基本過濾條件
          if (!text || 
              parent.tagName === 'SCRIPT' || 
              parent.tagName === 'STYLE' ||
              parent.tagName === 'NOSCRIPT' ||
              parent.style.display === 'none' ||
              parent.hidden) {
            return NodeFilter.FILTER_REJECT;
          }
          
          // 只處理包含中文字元的文字節點
          if (!/[\u4e00-\u9fff]/.test(text)) {
            return NodeFilter.FILTER_REJECT;
          }
          
          // 排除資料來源區塊
          let currentElement = parent;
          while (currentElement && currentElement !== document.body) {
            if (currentElement.classList) {
              // 排除資料來源相關的 CSS 類別
              if (currentElement.classList.contains('sourceBlock') ||
                  currentElement.classList.contains('sourceTitle') ||
                  currentElement.classList.contains('sourceList') ||
                  currentElement.classList.contains('sourceMedia') ||
                  currentElement.classList.contains('sourceLink') ||
                  currentElement.classList.contains('sourceEmpty') ||
                  currentElement.classList.contains('sourceToggleButton')) {
                return NodeFilter.FILTER_REJECT;
              }
            }
            currentElement = currentElement.parentElement;
          }
          
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );
    
    let node;
    while ((node = walker.nextNode())) {
      const text = node.textContent.trim();
      const parent = node.parentElement;
      
      // 分類文字來源
      let textCategory = '其他';
      let currentElement = parent;
      
      while (currentElement && currentElement !== document.body) {
        if (currentElement.classList) {
          // ChatRoom 相關
          if (currentElement.classList.contains('chat-sidebar') ||
              currentElement.classList.contains('chat__expertSelector') ||
              currentElement.classList.contains('dropdown') ||
              currentElement.classList.contains('dropdown__btn') ||
              currentElement.classList.contains('dropdown__menu') ||
              currentElement.classList.contains('dropdown__item')) {
            textCategory = 'ChatRoom';
            break;
          }
          
          // 專題報導相關
          if (currentElement.classList.contains('srp-page') ||
              currentElement.classList.contains('srp-header') ||
              currentElement.classList.contains('srp-title') ||
              currentElement.classList.contains('srp-subtitle') ||
              currentElement.classList.contains('srp-grid') ||
              currentElement.classList.contains('srp-card') ||
              currentElement.classList.contains('srp-card-title') ||
              currentElement.classList.contains('srp-card-description') ||
              currentElement.classList.contains('srp-card-meta')) {
            textCategory = '專題報導';
            console.log(`🎯 檢測到專題報導內容: "${text}" (類別: ${currentElement.className})`);
            break;
          }
          
          // 5W1H 視覺化相關
          if (currentElement.classList.contains('fivew1h-container') ||
              currentElement.classList.contains('fivew1h-title') ||
              currentElement.classList.contains('fivew1h-subtitle') ||
              currentElement.classList.contains('fivew1h-instructions') ||
              currentElement.classList.contains('fivew1h-legend') ||
              currentElement.classList.contains('fivew1h-controls') ||
              currentElement.classList.contains('text-5w1h') ||
              currentElement.classList.contains('text-center') ||
              currentElement.classList.contains('srd5W1HModal') ||
              currentElement.classList.contains('srd5W1HModal__content') ||
              currentElement.classList.contains('srd5W1HModal__title') ||
              currentElement.classList.contains('srd5W1HModal__visualization') ||
              currentElement.id === 'header-mindmap' ||
              currentElement.id === 'expanded-mindmap') {
            textCategory = '5W1H視覺化';
            console.log(`🗺️ 檢測到5W1H內容: "${text}" (類別: ${currentElement.className || currentElement.id})`);
            break;
          }
          
          // 專題報告模態框相關
          if (currentElement.classList.contains('srdReportModal') ||
              currentElement.classList.contains('srdReportModal__content') ||
              currentElement.classList.contains('srdReportModal__header') ||
              currentElement.classList.contains('srdReportModal__title') ||
              currentElement.classList.contains('srdReportModal__body') ||
              currentElement.classList.contains('srdReportModal__loading') ||
              currentElement.classList.contains('srdReportModal__report')) {
            textCategory = '專題報告';
            console.log(`📊 檢測到專題報告模態框內容: "${text}" (類別: ${currentElement.className})`);
            break;
          }
          
          // 跑馬燈相關
          if (currentElement.classList.contains('latest-topics') || 
              currentElement.classList.contains('topic-carousel') ||
              currentElement.classList.contains('carousel-slide') ||
              currentElement.classList.contains('slide-content') ||
              currentElement.classList.contains('slide-title') ||
              currentElement.classList.contains('slide-summary')) {
            textCategory = '跑馬燈';
            carouselTexts.push(text);
            break;
          }
          // Header相關
          else if (currentElement.classList.contains('header') ||
                   currentElement.classList.contains('brandSection') ||
                   currentElement.classList.contains('tagline') ||
                   currentElement.classList.contains('domainTagBar')) {
            textCategory = 'Header';
            headerTexts.push(text);
            break;
          }
          // 主要內容
          else if (currentElement.classList.contains('mainContent') ||
                   currentElement.classList.contains('news-section') ||
                   currentElement.classList.contains('sectionTitle')) {
            textCategory = '主要內容';
            contentTexts.push(text);
            break;
          }
        }
        currentElement = currentElement.parentElement;
      }
      
      textNodes.push({
        node: node,
        originalText: text,
        category: textCategory,
        index: textNodes.length
      });
    }
    
    // 詳細統計資訊
    console.log('📊 文字提取統計:');
    console.log(`🎠 跑馬燈文字 (${carouselTexts.length}個):`, carouselTexts);
    console.log(`🧭 Header文字 (${headerTexts.length}個):`, headerTexts);
    console.log(`📰 主要內容文字 (${contentTexts.length}個):`, contentTexts);
    console.log(`📝 總計文字節點: ${textNodes.length}個`);
    console.log(`🔤 總字元數: ${textNodes.map(item => item.originalText).join('').length}字元`);
    
    return textNodes;
  };

  // 取得分類圖示
  const getCategoryIcon = (category) => {
    const icons = {
      '跑馬燈': '🎠',
      'Header': '🧭', 
      '主要內容': '📰',
      'ChatRoom': '💬',
      '專題報導': '📊',
      '5W1H視覺化': '🗺️',
      '其他': '📄'
    };
    return icons[category] || '📄';
  };

  // 備份原始中文內容
  const backupOriginalContent = () => {
    if (!isOriginalContentBackedUp) {
      const textNodes = extractTextNodes();
      setOriginalTextNodes(textNodes);
      setIsOriginalContentBackedUp(true);
      
      console.log('✅ 原始內容備份完成');
      console.log(`📋 備份節點總數: ${textNodes.length}個`);
      
      // 按分類顯示備份內容
      const categories = ['跑馬燈', 'Header', '主要內容', 'ChatRoom', '專題報導', '5W1H視覺化', '其他'];
      categories.forEach(category => {
        const categoryNodes = textNodes.filter(item => item.category === category);
        if (categoryNodes.length > 0) {
          console.log(`${getCategoryIcon(category)} ${category}內容 (${categoryNodes.length}個):`, 
                     categoryNodes.map(item => item.originalText));
        }
      });
    }
  };

  // 恢復原始中文內容
  const restoreOriginalContent = () => {
    // 停止 DOM 觀察器
    if (domObserver) {
      domObserver.disconnect();
      setDomObserver(null);
    }
    
    if (originalTextNodes.length > 0) {
      originalTextNodes.forEach(item => {
        if (item.node && item.node.parentNode) {
          item.node.textContent = item.originalText;
        }
      });
      console.log('已恢復原始中文內容');
    }
  };

  // 替換文字節點
  const replaceTextNodes = (translatedTexts) => {
    if (originalTextNodes.length > 0 && translatedTexts.length === originalTextNodes.length) {
      originalTextNodes.forEach((item, index) => {
        if (item.node && item.node.parentNode && translatedTexts[index]) {
          item.node.textContent = translatedTexts[index];
        }
      });
    }
  };

  // 保存翻譯結果到快取
  const saveTranslationToCache = (pageKey, languageCode, translatedTexts) => {
    // 同步更新 ref
    if (!translationCacheRef.current[pageKey]) {
      translationCacheRef.current[pageKey] = {};
    }
    translationCacheRef.current[pageKey][languageCode] = translatedTexts;
    
    // 異步更新狀態
    setTranslationCache(prev => {
      const newCache = {
        ...prev,
        [pageKey]: {
          ...prev[pageKey],
          [languageCode]: translatedTexts
        }
      };
      return newCache;
    });
    
    console.log(`✅ 已快取 ${languageCode} 翻譯，共 ${translatedTexts.length} 個文字片段`);
    console.log(`🗂️ 快取更新後狀態:`, Object.keys(translationCacheRef.current));
  };

  // 從快取載入翻譯結果
  const loadTranslationFromCache = (pageKey, languageCode) => {
    console.log(`🔍 載入快取: pageKey=${pageKey}, languageCode=${languageCode}`);
    console.log(`🗂️ 當前快取狀態 (ref):`, Object.keys(translationCacheRef.current));
    console.log(`🗂️ 當前快取狀態 (state):`, Object.keys(translationCache));
    
    // 優先使用 ref 中的快取，因為它是同步更新的
    const cached = translationCacheRef.current[pageKey]?.[languageCode];
    if (cached) {
      console.log(`✅ 從快取載入 ${languageCode} 翻譯，共 ${cached.length} 個文字片段`);
      return cached;
    }
    console.log(`❌ 快取中未找到 ${pageKey} 的 ${languageCode} 翻譯`);
    return null;
  };

  // 翻譯新增的動態內容
  const translateNewContent = async (newNodes) => {
    if (selectedLanguage === 'zh' || newNodes.length === 0) {
      console.log(`⏭️ 跳過動態內容翻譯: 語言=${selectedLanguage}, 節點數=${newNodes.length}`);
      return;
    }

    try {
      const textsToTranslate = newNodes.map(node => node.textContent.trim());
      console.log(`🔄 翻譯新增的動態內容: ${textsToTranslate.length} 個片段`);
      console.log(`📝 動態內容列表:`, textsToTranslate);
      
      const translatedTexts = await translateTexts(textsToTranslate, selectedLanguage);
      
      if (translatedTexts && translatedTexts.length === newNodes.length) {
        newNodes.forEach((node, index) => {
          if (translatedTexts[index]) {
            const originalText = node.textContent;
            node.textContent = translatedTexts[index];
            console.log(`   ✅ "${originalText}" → "${translatedTexts[index]}"`);
          }
        });
        console.log(`✅ 成功翻譯 ${translatedTexts.length} 個動態內容片段`);
      } else {
        console.error(`❌ 翻譯結果數量不匹配: 期望 ${newNodes.length}, 得到 ${translatedTexts?.length || 0}`);
      }
    } catch (error) {
      console.error('翻譯動態內容失敗:', error);
    }
  };

  // 調試：檢查頁面上所有可能的元素
  const debugPageElements = () => {
    console.log('🔍 調試：檢查頁面上的元素結構...');
    
    // 檢查專題報導相關元素
    const srpElements = document.querySelectorAll('[class*="srp"], [class*="special"]');
    console.log(`📊 找到 ${srpElements.length} 個可能的專題報導元素:`);
    srpElements.forEach((el, index) => {
      console.log(`   ${index + 1}. ${el.tagName}.${el.className} - "${el.textContent?.trim().substring(0, 50)}..."`);
    });
    
    // 檢查5W1H相關元素
    const fivew1hElements = document.querySelectorAll('[class*="fivew1h"], [class*="5w1h"], [id*="mindmap"], [class*="mindmap"], [class*="srd5W1HModal"]');
    console.log(`🗺️ 找到 ${fivew1hElements.length} 個可能的5W1H元素:`);
    fivew1hElements.forEach((el, index) => {
      console.log(`   ${index + 1}. ${el.tagName}.${el.className || el.id} - "${el.textContent?.trim().substring(0, 50)}..."`);
    });
    
    // 檢查專題報告模態框相關元素
    const reportModalElements = document.querySelectorAll('[class*="srdReportModal"]');
    console.log(`📊 找到 ${reportModalElements.length} 個可能的專題報告模態框元素:`);
    reportModalElements.forEach((el, index) => {
      console.log(`   ${index + 1}. ${el.tagName}.${el.className} - "${el.textContent?.trim().substring(0, 50)}..."`);
    });
    
    // 檢查所有包含中文的元素
    const allElements = document.querySelectorAll('*');
    const chineseElements = Array.from(allElements).filter(el => {
      const text = el.textContent?.trim();
      return text && /[\u4e00-\u9fff]/.test(text) && el.children.length === 0; // 只要葉子節點
    });
    
    console.log(`🔤 找到 ${chineseElements.length} 個包含中文的葉子元素:`);
    chineseElements.slice(0, 20).forEach((el, index) => { // 只顯示前20個
      console.log(`   ${index + 1}. ${el.tagName}.${el.className} - "${el.textContent?.trim().substring(0, 30)}..."`);
    });
  };

  // 手動翻譯專題報導和5W1H內容
  const translateSpecialContent = async () => {
    if (selectedLanguage === 'zh') return;
    
    console.log('🔍 手動檢查專題報導和5W1H內容...');
    
    // 先調試頁面元素
    debugPageElements();
    
    const specialNodes = [];
    
    // 更廣泛地查找元素
    const allPossibleElements = document.querySelectorAll('*');
    const relevantElements = Array.from(allPossibleElements).filter(el => {
      const className = el.className || '';
      const id = el.id || '';
      
      // 專題報導相關
      if (className.includes('srp') || className.includes('special') || className.includes('report')) {
        return true;
      }
      
      // 5W1H相關
      if (className.includes('fivew1h') || className.includes('5w1h') || 
          className.includes('mindmap') || id.includes('mindmap') ||
          className.includes('srd5W1HModal')) {
        return true;
      }
      
      // 專題報告模態框相關
      if (className.includes('srdReportModal')) {
        return true;
      }
      
      return false;
    });
    
    console.log(`🔍 找到 ${relevantElements.length} 個可能相關的元素`);
    
    relevantElements.forEach(element => {
      const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: function(textNode) {
            const text = textNode.textContent.trim();
            if (!text || !/[\u4e00-\u9fff]/.test(text)) {
              return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );
      
      let textNode;
      while ((textNode = walker.nextNode())) {
        if (!specialNodes.includes(textNode)) {
          specialNodes.push(textNode);
        }
      }
    });
    
    if (specialNodes.length > 0) {
      console.log(`🎯 找到 ${specialNodes.length} 個專題報導/5W1H文字節點`);
      specialNodes.forEach((node, index) => {
        console.log(`   ${index + 1}. "${node.textContent.trim()}"`);
      });
      
      await translateNewContent(specialNodes);
    } else {
      console.log('❌ 未找到專題報導/5W1H中文內容');
    }
  };

  // 最後的全頁面掃描，翻譯所有遺漏的中文內容
  const translateAllMissedContent = async () => {
    if (selectedLanguage === 'zh') return;
    
    console.log('🔄 執行最終全頁面掃描，查找遺漏的中文內容...');
    
    const allMissedNodes = [];
    
    // 遍歷整個頁面，找到所有包含中文但可能被遺漏的文字節點
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(textNode) {
          const text = textNode.textContent.trim();
          
          // 基本過濾
          if (!text || 
              textNode.parentElement.tagName === 'SCRIPT' || 
              textNode.parentElement.tagName === 'STYLE' ||
              textNode.parentElement.tagName === 'NOSCRIPT') {
            return NodeFilter.FILTER_REJECT;
          }
          
          // 必須包含中文
          if (!/[\u4e00-\u9fff]/.test(text)) {
            return NodeFilter.FILTER_REJECT;
          }
          
          // 排除資料來源區塊
          let currentElement = textNode.parentElement;
          while (currentElement && currentElement !== document.body) {
            if (currentElement.classList) {
              if (currentElement.classList.contains('sourceBlock') ||
                  currentElement.classList.contains('sourceTitle') ||
                  currentElement.classList.contains('sourceList') ||
                  currentElement.classList.contains('sourceMedia') ||
                  currentElement.classList.contains('sourceLink') ||
                  currentElement.classList.contains('sourceEmpty') ||
                  currentElement.classList.contains('sourceToggleButton')) {
                return NodeFilter.FILTER_REJECT;
              }
            }
            currentElement = currentElement.parentElement;
          }
          
          // 檢查是否已經被翻譯過（簡單檢查：如果不包含中文了，可能已經翻譯過）
          if (!/[\u4e00-\u9fff]/.test(text)) {
            return NodeFilter.FILTER_REJECT;
          }
          
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );
    
    let textNode;
    while ((textNode = walker.nextNode())) {
      allMissedNodes.push(textNode);
    }
    
    if (allMissedNodes.length > 0) {
      console.log(`🎯 最終掃描找到 ${allMissedNodes.length} 個可能遺漏的中文文字節點`);
      
      // 按父元素分組顯示
      const nodesByParent = {};
      allMissedNodes.forEach((node, index) => {
        const parentClass = node.parentElement?.className || 'unknown';
        if (!nodesByParent[parentClass]) {
          nodesByParent[parentClass] = [];
        }
        nodesByParent[parentClass].push(node.textContent.trim());
      });
      
      Object.entries(nodesByParent).forEach(([parentClass, texts]) => {
        console.log(`   📍 ${parentClass}: ${texts.length}個節點`);
        texts.slice(0, 3).forEach((text, i) => {
          console.log(`      ${i + 1}. "${text.substring(0, 30)}..."`);
        });
      });
      
      await translateNewContent(allMissedNodes);
    } else {
      console.log('✅ 最終掃描：沒有找到遺漏的中文內容');
    }
  };

  // 手動翻譯 ChatRoom 內容
  const translateChatRoomContent = async () => {
    if (selectedLanguage === 'zh') return;
    
    console.log('🔍 手動檢查 ChatRoom 內容...');
    
    // 查找 ChatRoom 相關的元素
    const chatSidebar = document.querySelector('.chat-sidebar');
    if (!chatSidebar) {
      console.log('❌ 未找到 ChatRoom 側邊欄');
      return;
    }
    
    const chatRoomNodes = [];
    const walker = document.createTreeWalker(
      chatSidebar,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(textNode) {
          const text = textNode.textContent.trim();
          if (!text || !/[\u4e00-\u9fff]/.test(text)) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );
    
    let textNode;
    while ((textNode = walker.nextNode())) {
      chatRoomNodes.push(textNode);
    }
    
    if (chatRoomNodes.length > 0) {
      console.log(`🎯 找到 ${chatRoomNodes.length} 個 ChatRoom 文字節點`);
      chatRoomNodes.forEach((node, index) => {
        console.log(`   ${index + 1}. "${node.textContent.trim()}"`);
      });
      
      await translateNewContent(chatRoomNodes);
    } else {
      console.log('❌ 未找到 ChatRoom 中文內容');
    }
  };

  // 設置 DOM 變化監聽器
  const setupDomObserver = () => {
    if (domObserver) {
      domObserver.disconnect();
    }

    const observer = new MutationObserver((mutations) => {
      if (selectedLanguage === 'zh') return;

      const newTextNodes = [];
      
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.TEXT_NODE) {
              const text = node.textContent.trim();
              if (text && /[\u4e00-\u9fff]/.test(text)) {
                // 檢查是否在資料來源區塊內
                let currentElement = node.parentElement;
                let isInSourceBlock = false;
                while (currentElement && currentElement !== document.body) {
                  if (currentElement.classList) {
                    if (currentElement.classList.contains('sourceBlock') ||
                        currentElement.classList.contains('sourceTitle') ||
                        currentElement.classList.contains('sourceList') ||
                        currentElement.classList.contains('sourceMedia') ||
                        currentElement.classList.contains('sourceLink') ||
                        currentElement.classList.contains('sourceEmpty') ||
                        currentElement.classList.contains('sourceToggleButton')) {
                      isInSourceBlock = true;
                      break;
                    }
                  }
                  currentElement = currentElement.parentElement;
                }
                
                if (!isInSourceBlock) {
                  newTextNodes.push(node);
                }
              }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
              // 遍歷新增元素的所有文字節點
              const walker = document.createTreeWalker(
                node,
                NodeFilter.SHOW_TEXT,
                {
                  acceptNode: function(textNode) {
                    const text = textNode.textContent.trim();
                    if (!text || 
                        textNode.parentElement.tagName === 'SCRIPT' || 
                        textNode.parentElement.tagName === 'STYLE' ||
                        textNode.parentElement.tagName === 'NOSCRIPT') {
                      return NodeFilter.FILTER_REJECT;
                    }
                    
                    if (!/[\u4e00-\u9fff]/.test(text)) {
                      return NodeFilter.FILTER_REJECT;
                    }
                    
                    // 排除資料來源區塊，但包含專題報導和5W1H內容
                    let currentElement = textNode.parentElement;
                    while (currentElement && currentElement !== document.body) {
                      if (currentElement.classList) {
                        // 排除資料來源相關的 CSS 類別
                        if (currentElement.classList.contains('sourceBlock') ||
                            currentElement.classList.contains('sourceTitle') ||
                            currentElement.classList.contains('sourceList') ||
                            currentElement.classList.contains('sourceMedia') ||
                            currentElement.classList.contains('sourceLink') ||
                            currentElement.classList.contains('sourceEmpty') ||
                            currentElement.classList.contains('sourceToggleButton')) {
                          return NodeFilter.FILTER_REJECT;
                        }
                        
                        // 確保專題報導、5W1H和報告模態框內容被包含
                        if (currentElement.classList.contains('srp-page') ||
                            currentElement.classList.contains('fivew1h-container') ||
                            currentElement.classList.contains('srd5W1HModal') ||
                            currentElement.classList.contains('srdReportModal') ||
                            currentElement.id === 'header-mindmap' ||
                            currentElement.id === 'expanded-mindmap') {
                          return NodeFilter.FILTER_ACCEPT;
                        }
                      }
                      currentElement = currentElement.parentElement;
                    }
                    
                    return NodeFilter.FILTER_ACCEPT;
                  }
                }
              );
              
              let textNode;
              while ((textNode = walker.nextNode())) {
                newTextNodes.push(textNode);
              }
            }
          });
        }
      });

      if (newTextNodes.length > 0) {
        console.log(`🔍 檢測到 ${newTextNodes.length} 個新的中文文字節點待翻譯`);
        newTextNodes.forEach((node, index) => {
          console.log(`   ${index + 1}. "${node.textContent.trim()}" (父元素: ${node.parentElement?.className || 'unknown'})`);
        });
        
        // 延遲一點執行翻譯，避免頻繁觸發
        setTimeout(() => {
          translateNewContent(newTextNodes);
        }, 300);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true
    });

    setDomObserver(observer);
    return observer;
  };

  // 處理搜尋功能
  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter' && search.trim() !== '') {
      navigate(`/search/${encodeURIComponent(search.trim())}`);
    }
  };

  // 處理語言翻譯功能
  const handleLanguageChange = async (e) => {
    const targetLanguage = e.target.value;
    setSelectedLanguage(targetLanguage);
    selectedLanguageRef.current = targetLanguage;
    
    // 如果選擇中文，恢復原始內容
    if (targetLanguage === 'zh') {
      console.log('選擇中文，恢復原始內容');
      restoreOriginalContent();
      return;
    }
    
    const pageKey = currentPageKey;
    
    // 先檢查快取
    const cachedTranslation = loadTranslationFromCache(pageKey, targetLanguage);
    if (cachedTranslation && originalTextNodes.length > 0) {
      console.log(`使用快取的 ${targetLanguage} 翻譯`);
      replaceTextNodes(cachedTranslation);
      // 啟動 DOM 觀察器來監聽動態內容
      setupDomObserver();
      
      // 手動檢查並翻譯特殊內容
      setTimeout(() => {
        translateSpecialContent();
        translateChatRoomContent();
        // 最後再做一次全頁面掃描，確保沒有遺漏
        translateAllMissedContent();
      }, 1500);
      
      return;
    }
    
    // 沒有快取，進行翻譯
    setIsTranslating(true);
    
    try {
      // 等待一下確保動態內容（如跑馬燈）完全載入
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // 確保原始內容已備份（重新提取以防頁面內容變化）
      if (!isOriginalContentBackedUp || originalTextNodes.length === 0) {
        console.log('重新提取並備份原始內容...');
        backupOriginalContent();
        
        // 如果仍然沒有找到內容，再等一下重試
        if (originalTextNodes.length === 0) {
          console.log('第一次提取失敗，等待1秒後重試...');
          await new Promise(resolve => setTimeout(resolve, 1000));
          backupOriginalContent();
        }
        
        // 最後檢查
        if (originalTextNodes.length === 0) {
          console.log('第二次提取失敗，強制重新提取...');
          const textNodes = extractTextNodes();
          setOriginalTextNodes(textNodes);
          setIsOriginalContentBackedUp(true);
        }
      }
      
      console.log(`開始翻譯到 ${languages.find(lang => lang.code === targetLanguage)?.name}...`);
      console.log(`🔍 當前 originalTextNodes 數量: ${originalTextNodes.length}`);
      console.log(`🔍 isOriginalContentBackedUp: ${isOriginalContentBackedUp}`);
      
      if (originalTextNodes.length === 0) {
        console.error('❌ originalTextNodes 為空，嘗試最後一次強制提取...');
        
        // 最後一次嘗試
        const emergencyNodes = extractTextNodes();
        console.log(`🚨 緊急提取到 ${emergencyNodes.length} 個節點`);
        
        if (emergencyNodes.length > 0) {
          setOriginalTextNodes(emergencyNodes);
          console.log('✅ 緊急提取成功，繼續翻譯...');
        } else {
          throw new Error('沒有找到可翻譯的內容，請稍後再試');
        }
      }
      
      // 確保我們有有效的文字節點進行翻譯
      let currentTextNodes = originalTextNodes;
      if (currentTextNodes.length === 0) {
        console.log('🔧 狀態中的 originalTextNodes 為空，直接使用新提取的節點');
        currentTextNodes = extractTextNodes();
      }
      
      console.log(`📊 最終用於翻譯的節點數量: ${currentTextNodes.length}`);
      
      // 提取原始中文文字陣列並提供詳細統計
      const textsToTranslate = currentTextNodes.map(item => item.originalText);
      const totalChars = textsToTranslate.join('').length;
      
      console.log(`🔄 開始翻譯到 ${languages.find(lang => lang.code === targetLanguage)?.name}`);
      console.log(`📊 翻譯統計資訊:`);
      console.log(`   • 文字片段數: ${textsToTranslate.length}個`);
      console.log(`   • 總字元數: ${totalChars}字元`);
      
      // 顯示前10個要翻譯的文字片段
      console.log(`📝 要翻譯的前10個文字片段:`);
      textsToTranslate.slice(0, 10).forEach((text, index) => {
        console.log(`   ${index + 1}. "${text}"`);
      });
      
      // 按分類統計翻譯內容
      const categories = ['跑馬燈', 'Header', '主要內容', 'ChatRoom', '專題報導', '5W1H視覺化', '其他'];
      categories.forEach(category => {
        const categoryTexts = currentTextNodes
          .filter(item => item.category === category)
          .map(item => item.originalText);
        if (categoryTexts.length > 0) {
          const categoryChars = categoryTexts.join('').length;
          console.log(`   ${getCategoryIcon(category)} ${category}: ${categoryTexts.length}個片段, ${categoryChars}字元`);
        }
      });
      
      console.log(`📝 要翻譯的完整文字列表:`, textsToTranslate);
      
      // 發送到後端翻譯
      const translationResult = await translateTexts(textsToTranslate, targetLanguage);

      if (translationResult && translationResult.length === textsToTranslate.length) {
        // 替換頁面上的文字
        if (currentTextNodes.length > 0 && translationResult.length === currentTextNodes.length) {
          currentTextNodes.forEach((item, index) => {
            if (item.node && item.node.parentNode && translationResult[index]) {
              item.node.textContent = translationResult[index];
            }
          });
        }
        
        // 更新狀態
        setOriginalTextNodes(currentTextNodes);
        setIsOriginalContentBackedUp(true);

        // 保存到快取
        saveTranslationToCache(pageKey, targetLanguage, translationResult);

        // 啟動 DOM 觀察器來監聽動態內容
        setupDomObserver();

        // 手動檢查並翻譯特殊內容
        setTimeout(() => {
          translateSpecialContent();
          translateChatRoomContent();
          // 最後再做一次全頁面掃描，確保沒有遺漏
          translateAllMissedContent();
        }, 1500);

        console.log(`翻譯完成並已快取，已替換 ${translationResult.length} 個文字片段`);
      } else {
        throw new Error('翻譯結果數量不匹配');
      }
      
    } catch (error) {
      console.error('翻譯失敗:', error);
      alert('翻譯失敗: ' + error.message);
      restoreOriginalContent();
      setSelectedLanguage('zh');
    } finally {
      setIsTranslating(false);
    }
  };

  // 當路由改變時，處理翻譯狀態
  useEffect(() => {
    const newPageKey = location.pathname + location.search;
    const previousLanguage = selectedLanguageRef.current;
    
    console.log(`頁面變更: ${newPageKey}, 之前的語言: ${previousLanguage}`);
    
    // 停止之前的 DOM 觀察器
    if (domObserver) {
      domObserver.disconnect();
      setDomObserver(null);
    }
    
    // 更新頁面識別符
    setCurrentPageKey(newPageKey);
    
    // 重置當前頁面的翻譯狀態
    setIsOriginalContentBackedUp(false);
    setOriginalTextNodes([]);
    
    // 設定當前 active 的類別
    if (location.pathname === '/') {
      setActiveDomain('/');
    } else if (location.pathname.startsWith('/special-reports')) {
      setActiveDomain('project');
    } else if (location.pathname.startsWith('/category/')) {
      const categoryFromPath = decodeURIComponent(location.pathname.substring(10));
      const domain = domains.find((d) => {
        const categoryFromDomain = d.path.substring(10);
        return categoryFromDomain === categoryFromPath;
      });
      if (domain) setActiveDomain(domain.id);
    }

    // 如果之前選擇的不是中文，需要自動翻譯新頁面
    if (previousLanguage !== 'zh') {
      console.log(`頁面變更後自動翻譯到: ${previousLanguage}`);
      
      // 延遲執行翻譯，確保新頁面內容已載入
      setTimeout(() => {
        // 直接觸發翻譯
        const fakeEvent = { target: { value: previousLanguage } };
        handleLanguageChange(fakeEvent);
      }, 1000); // 給頁面足夠時間載入
    } else {
      // 如果是中文，確保語言選擇器顯示正確
      setSelectedLanguage('zh');
      selectedLanguageRef.current = 'zh';
    }
  }, [location.pathname, location.search]); // eslint-disable-line react-hooks/exhaustive-deps



  // 定期清理快取
  useEffect(() => {
    const cacheKeys = Object.keys(translationCache);
    if (cacheKeys.length > 10) { // 只保留最近10個頁面的快取
      const keysToDelete = cacheKeys.slice(0, cacheKeys.length - 10);
      setTranslationCache(prev => {
        const newCache = { ...prev };
        keysToDelete.forEach(key => delete newCache[key]);
        return newCache;
      });
      console.log(`清理了 ${keysToDelete.length} 個舊快取`);
    }
  }, [translationCache]);

  // 組件卸載時清理 DOM 觀察器
  useEffect(() => {
    return () => {
      if (domObserver) {
        domObserver.disconnect();
      }
    };
  }, [domObserver]);

  // 監聽模態框和按鈕點擊事件
  useEffect(() => {
    const handleModalAndButtonClicks = (event) => {
      const target = event.target;
      
      // 檢測聊天室按鈕
      if (target.classList.contains('chat-toggle-btn') || 
          target.closest('.chat-toggle-btn')) {
        if (selectedLanguage !== 'zh') {
          console.log('🎯 檢測到聊天室打開，延遲翻譯內容...');
          setTimeout(() => {
            translateChatRoomContent();
          }, 1500);
        }
      }
      
      // 檢測專題報告按鈕
      if (target.classList.contains('srdHeader__reportBtn') || 
          target.closest('.srdHeader__reportBtn') ||
          target.textContent?.includes('專題報告')) {
        if (selectedLanguage !== 'zh') {
          console.log('📊 檢測到專題報告按鈕點擊，檢查快取或翻譯...');
          
          // 建立快取鍵
          const modalCacheKey = `${currentPageKey}_srdReportModal`;
          const cachedTranslation = loadTranslationFromCache(modalCacheKey, selectedLanguage);
          console.log(`🔍 檢查快取鍵: ${modalCacheKey}, 語言: ${selectedLanguage}`);
          console.log(`📦 快取狀態:`, cachedTranslation ? `找到 ${cachedTranslation.length} 個翻譯` : '無快取');
          
          if (cachedTranslation) {
            console.log('📦 專題報告有快取，等待模態框出現後應用...');
            setTimeout(() => {
              applyModalTranslation('srdReportModal', cachedTranslation);
            }, 2500);
          } else {
            console.log('🔄 專題報告無快取，等待模態框出現後翻譯...');
            setTimeout(() => {
              translateModalContent('srdReportModal');
            }, 2500);
          }
        }
      }
      
      // 檢測5W1H圖表點擊（整個圖表區域）
      if (target.closest('#header-mindmap') || 
          target.classList.contains('srdHeader__image') ||
          target.closest('.srdHeader__image')) {
        if (selectedLanguage !== 'zh') {
          console.log('🗺️ 檢測到5W1H圖表點擊，延遲翻譯模態框內容...');
          setTimeout(() => {
            translateModalContent('srd5W1HModal');
          }, 1200);
        }
      }
    };

    // 監聽整個文檔的點擊，檢測5W1H節點點擊
    const handleDocumentClick = (event) => {
      if (selectedLanguage === 'zh') return;
      
      // 檢測是否點擊了SVG中的節點（5W1H圖表中的圓圈）
      const target = event.target;
      if (target.tagName === 'circle' || 
          (target.closest && target.closest('svg')) ||
          target.classList?.contains('node')) {
        console.log('🎯 可能點擊了5W1H節點，檢查模態框...');
        
        // 多次檢查模態框是否出現，因為創建需要時間
        let checkCount = 0;
        const checkModal = () => {
          checkCount++;
          const nodeDetailModal = document.getElementById('node-detail-modal');
          if (nodeDetailModal) {
            console.log('🗺️ 檢測到5W1H節點詳情模態框，開始翻譯...');
            translateNodeDetailModal();
          } else if (checkCount < 5) {
            // 最多檢查5次，每次間隔200ms
            setTimeout(checkModal, 200);
          } else {
            console.log('⏰ 未檢測到節點詳情模態框出現');
          }
        };
        
        setTimeout(checkModal, 100);
      }
    };

    // 設置MutationObserver來監聽節點詳情模態框的出現
    const modalObserver = new MutationObserver((mutations) => {
      if (selectedLanguage === 'zh') return;
      
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE && node.id === 'node-detail-modal') {
              console.log('🎯 MutationObserver檢測到節點詳情模態框出現！');
              setTimeout(() => {
                translateNodeDetailModal();
              }, 200);
            }
          });
        }
      });
    });

    modalObserver.observe(document.body, {
      childList: true,
      subtree: true
    });

    document.addEventListener('click', handleModalAndButtonClicks);
    document.addEventListener('click', handleDocumentClick);
    
    return () => {
      document.removeEventListener('click', handleModalAndButtonClicks);
      document.removeEventListener('click', handleDocumentClick);
      modalObserver.disconnect();
    };
  }, [selectedLanguage]);

  // 翻譯5W1H節點詳情模態框
  const translateNodeDetailModal = async () => {
    if (selectedLanguage === 'zh') return;
    
    console.log('🔍 開始翻譯5W1H節點詳情模態框...');
    console.log('📍 當前語言:', selectedLanguage);
    console.log('📍 當前頁面鍵:', currentPageKey);
    
    // 建立節點詳情模態框專用的快取鍵
    const modalCacheKey = `${currentPageKey}_node-detail-modal`;
    
    // 先檢查快取
    const cachedModalTranslation = loadTranslationFromCache(modalCacheKey, selectedLanguage);
    if (cachedModalTranslation) {
      console.log('📦 使用快取的節點詳情模態框翻譯');
      // 應用快取的翻譯
      setTimeout(() => {
        applyNodeDetailTranslation(cachedModalTranslation);
      }, 300);
      return;
    }
    
    const modal = document.getElementById('node-detail-modal');
    if (!modal) {
      console.log('❌ 未找到節點詳情模態框');
      return;
    }
    
    const modalNodes = [];
    const originalTexts = [];
    
    const walker = document.createTreeWalker(
      modal,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(textNode) {
          const text = textNode.textContent.trim();
          if (!text || !/[\u4e00-\u9fff]/.test(text)) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );
    
    let textNode;
    while ((textNode = walker.nextNode())) {
      modalNodes.push(textNode);
      originalTexts.push(textNode.textContent.trim());
    }
    
    if (modalNodes.length > 0) {
      console.log(`🎯 在節點詳情模態框中找到 ${modalNodes.length} 個中文文字節點`);
      modalNodes.forEach((node, index) => {
        console.log(`   ${index + 1}. "${node.textContent.trim()}"`);
      });
      
      try {
        // 翻譯文字
        const translatedTexts = await translateTexts(originalTexts, selectedLanguage);
        
        if (translatedTexts && translatedTexts.length === modalNodes.length) {
          // 應用翻譯
          modalNodes.forEach((node, index) => {
            if (translatedTexts[index]) {
              const originalText = node.textContent;
              node.textContent = translatedTexts[index];
              console.log(`   ✅ "${originalText}" → "${translatedTexts[index]}"`);
            }
          });
          
          // 保存到快取 - 保存翻譯文字陣列
          saveTranslationToCache(modalCacheKey, selectedLanguage, translatedTexts);
          console.log(`✅ 節點詳情模態框翻譯完成並已快取，快取鍵: ${modalCacheKey}`);
        }
      } catch (error) {
        console.error('❌ 節點詳情模態框翻譯失敗:', error);
      }
    } else {
      console.log('❌ 在節點詳情模態框中未找到中文內容');
    }
  };

  // 應用節點詳情模態框快取翻譯
  const applyNodeDetailTranslation = (translatedTexts) => {
    const modal = document.getElementById('node-detail-modal');
    if (!modal) {
      console.log('❌ 應用快取時未找到節點詳情模態框');
      return;
    }
    
    const modalNodes = [];
    const walker = document.createTreeWalker(
      modal,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(textNode) {
          const text = textNode.textContent.trim();
          if (!text || !/[\u4e00-\u9fff]/.test(text)) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );
    
    let textNode;
    while ((textNode = walker.nextNode())) {
      modalNodes.push(textNode);
    }
    
    if (modalNodes.length === translatedTexts.length) {
      modalNodes.forEach((node, index) => {
        if (translatedTexts[index]) {
          node.textContent = translatedTexts[index];
        }
      });
      console.log('✅ 成功應用節點詳情模態框快取翻譯');
    } else {
      console.log('⚠️ 節點詳情模態框快取翻譯數量不匹配，重新翻譯');
      translateNodeDetailModal();
    }
  };

  // 翻譯特定模態框內容（支援快取）
  const translateModalContent = async (modalClass) => {
    if (selectedLanguage === 'zh') return;
    
    console.log(`🔍 翻譯模態框內容: ${modalClass}`);
    
    // 建立模態框專用的快取鍵
    const modalCacheKey = `${currentPageKey}_${modalClass}`;
    
    // 先檢查快取
    const cachedModalTranslation = loadTranslationFromCache(modalCacheKey, selectedLanguage);
    if (cachedModalTranslation) {
      console.log(`📦 使用快取的 ${modalClass} 翻譯`);
      // 應用快取的翻譯
      setTimeout(() => {
        applyModalTranslation(modalClass, cachedModalTranslation);
      }, 300);
      return;
    }
    
    const modalElements = document.querySelectorAll(`.${modalClass}`);
    if (modalElements.length === 0) {
      console.log(`❌ 未找到模態框: ${modalClass}`);
      // 延遲重試，因為模態框可能還在渲染
      setTimeout(() => {
        translateModalContent(modalClass);
      }, 800);
      return;
    }
    
    const modalNodes = [];
    const originalTexts = [];
    
    modalElements.forEach(modal => {
      const walker = document.createTreeWalker(
        modal,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: function(textNode) {
            const text = textNode.textContent.trim();
            if (!text || !/[\u4e00-\u9fff]/.test(text)) {
              return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );
      
      let textNode;
      while ((textNode = walker.nextNode())) {
        modalNodes.push(textNode);
        originalTexts.push(textNode.textContent.trim());
      }
    });
    
    if (modalNodes.length > 0) {
      console.log(`🎯 在 ${modalClass} 中找到 ${modalNodes.length} 個中文文字節點`);
      modalNodes.forEach((node, index) => {
        console.log(`   ${index + 1}. "${node.textContent.trim()}"`);
      });
      
      try {
        // 翻譯文字
        const translatedTexts = await translateTexts(originalTexts, selectedLanguage);
        
        if (translatedTexts && translatedTexts.length === modalNodes.length) {
          // 應用翻譯
          modalNodes.forEach((node, index) => {
            if (translatedTexts[index]) {
              const originalText = node.textContent;
              node.textContent = translatedTexts[index];
              console.log(`   ✅ "${originalText}" → "${translatedTexts[index]}"`);
            }
          });
          
          // 保存到快取 - 保存翻譯文字陣列
          saveTranslationToCache(modalCacheKey, selectedLanguage, translatedTexts);
          console.log(`✅ ${modalClass} 翻譯完成並已快取，快取鍵: ${modalCacheKey}`);
        }
      } catch (error) {
        console.error(`❌ ${modalClass} 翻譯失敗:`, error);
      }
    } else {
      console.log(`❌ 在 ${modalClass} 中未找到中文內容`);
    }
  };

  // 應用模態框快取翻譯
  const applyModalTranslation = (modalClass, translatedTexts) => {
    const modalElements = document.querySelectorAll(`.${modalClass}`);
    if (modalElements.length === 0) {
      console.log(`❌ 應用快取時未找到模態框: ${modalClass}`);
      return;
    }
    
    const modalNodes = [];
    modalElements.forEach(modal => {
      const walker = document.createTreeWalker(
        modal,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: function(textNode) {
            const text = textNode.textContent.trim();
            if (!text || !/[\u4e00-\u9fff]/.test(text)) {
              return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );
      
      let textNode;
      while ((textNode = walker.nextNode())) {
        modalNodes.push(textNode);
      }
    });
    
    console.log(`🔍 找到 ${modalNodes.length} 個文字節點，快取有 ${translatedTexts.length} 個翻譯`);
    
    if (modalNodes.length === translatedTexts.length) {
      modalNodes.forEach((node, index) => {
        const originalText = node.textContent;
        if (translatedTexts[index]) {
          node.textContent = translatedTexts[index];
          console.log(`   ✅ 快取應用: "${originalText}" → "${translatedTexts[index]}"`);
        }
      });
      console.log(`✅ 成功應用 ${modalClass} 快取翻譯，共 ${modalNodes.length} 個節點`);
    } else {
      console.log(`⚠️ ${modalClass} 快取翻譯數量不匹配 (節點:${modalNodes.length}, 快取:${translatedTexts.length})，重新翻譯`);
      translateModalContent(modalClass);
    }
  };


  return (
    <header className="header">
      <div className="mainBar">
        <div className="brandSection">
          <Link to="/" className="brandLink">
            <div className="logo">AIversity</div>
          </Link>
          <span className="tagline">智能新聞，深度洞察</span>
        </div>

        <div className="rightSection">
          <div className="searchSection">
            <div className="searchInputWrapper">
              <span className="searchIcon">🔍</span>
              <input
                className="searchInput"
                type="text"
                placeholder="搜尋新聞/關鍵字..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyPress={handleSearchKeyPress}
              />
            </div>
          </div>

          <div className="languageSection">
            <select 
              className="languageSelect"
              value={selectedLanguage}
              onChange={handleLanguageChange}
              disabled={isTranslating}
            >
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {isTranslating && selectedLanguage === lang.code && lang.code !== 'zh' 
                    ? `翻譯中...` 
                    : lang.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="tagBarWrapper">
        <div className="domainTagBar">
          {domains.map((domain) => (
            <Link
              key={domain.id}
              to={domain.path}
              className={`tagLink ${activeDomain === domain.id ? 'is-active' : ''}`}
              onClick={() => setActiveDomain(domain.id)}
            >
              {domain.label}
            </Link>
          ))}
        </div>
      </div>
    </header>
  );
}

export default Header;