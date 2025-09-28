import React, { useState, useEffect } from 'react';
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
  const [currentPageKey, setCurrentPageKey] = useState('');
  
  const location = useLocation();
  const navigate = useNavigate();



  // 提取文字節點的函數  
  const extractTextNodes = () => {
    const textNodes = [];
    const carouselTexts = [];
    const headerTexts = [];
    const contentTexts = [];
    
    console.log('🔍 開始提取頁面文字節點...');
    
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
      const categories = ['跑馬燈', 'Header', '主要內容', '其他'];
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
    setTranslationCache(prev => ({
      ...prev,
      [pageKey]: {
        ...prev[pageKey],
        [languageCode]: translatedTexts
      }
    }));
    console.log(`已快取 ${languageCode} 翻譯，共 ${translatedTexts.length} 個文字片段`);
  };

  // 從快取載入翻譯結果
  const loadTranslationFromCache = (pageKey, languageCode) => {
    const cached = translationCache[pageKey]?.[languageCode];
    if (cached) {
      console.log(`從快取載入 ${languageCode} 翻譯，共 ${cached.length} 個文字片段`);
      return cached;
    }
    return null;
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
    
    // 如果選擇中文，恢復原始內容
    if (targetLanguage === 'zh') {
      console.log('選擇中文，恢復原始內容');
      restoreOriginalContent();
      return;
    }
    
    const pageKey = currentPageKey;
    
    // 先檢查快取
    const cachedTranslation = loadTranslationFromCache(pageKey, targetLanguage);
    if (cachedTranslation) {
      console.log(`使用快取的 ${targetLanguage} 翻譯`);
      replaceTextNodes(cachedTranslation);
      return;
    }
    
    // 沒有快取，進行翻譯
    setIsTranslating(true);
    
    try {
      // 等待一下確保動態內容（如跑馬燈）完全載入
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // 備份原始內容（如果尚未備份）
      if (!isOriginalContentBackedUp) {
        backupOriginalContent();
      }
      
      console.log(`開始翻譯到 ${languages.find(lang => lang.code === targetLanguage)?.name}...`);
      
      if (originalTextNodes.length === 0) {
        throw new Error('沒有找到可翻譯的內容');
      }
      
      // 提取原始中文文字陣列並提供詳細統計
      const textsToTranslate = originalTextNodes.map(item => item.originalText);
      const totalChars = textsToTranslate.join('').length;
      
      console.log(`🔄 開始翻譯到 ${languages.find(lang => lang.code === targetLanguage)?.name}`);
      console.log(`📊 翻譯統計資訊:`);
      console.log(`   • 文字片段數: ${textsToTranslate.length}個`);
      console.log(`   • 總字元數: ${totalChars}字元`);
      
      // 按分類統計翻譯內容
      const categories = ['跑馬燈', 'Header', '主要內容', '其他'];
      categories.forEach(category => {
        const categoryTexts = originalTextNodes
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
        replaceTextNodes(translationResult);

        // 保存到快取
        saveTranslationToCache(pageKey, targetLanguage, translationResult);

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

  // 當路由改變時，重置翻譯狀態並更新頁面識別符
  useEffect(() => {
    const newPageKey = location.pathname + location.search;
    setCurrentPageKey(newPageKey);
    
    // 重置當前頁面的翻譯狀態
    setIsOriginalContentBackedUp(false);
    setOriginalTextNodes([]);
    setSelectedLanguage('zh');
    
    console.log(`頁面變更: ${newPageKey}`);
    
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
  }, [location.pathname, location.search]);



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