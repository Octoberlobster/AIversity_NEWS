import React, { useState, useEffect, useMemo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useCountry } from './CountryContext';
import { useAuth } from '../login/AuthContext';
import './../css/Header.css';

function Header() {
  const { t, i18n } = useTranslation();
  const { selectedCountry, setSelectedCountry } = useCountry();
  const { user, signOut } = useAuth();
  
  const domains = useMemo(() => [
    { id: '/', label: t('header.menu.home'), path: '/'},
    { id: 'yesterday', label: t('header.menu.yesterdayFocus'), path: '/yesterday-focus'},
    { id: 'project', label: t('header.menu.specialReports'), path: '/special-reports'},
  ], [t]);

  // 定義類別的基本資料（不含路徑）
  const categoryDefinitions = useMemo(() => [
    { id: 'international', label: t('header.menu.international'), name: 'International News' },
    { id: 'politics', label: t('header.menu.politics'), name: 'Politics' },
    { id: 'scienceandtech', label: t('header.menu.scienceAndTech'), name: 'Science & Technology' },
    { id: 'life', label: t('header.menu.life'), name: 'Lifestyle & Consumer' },
    { id: 'sports', label: t('header.menu.sports'), name: 'Sports' },
    { id: 'entertainment', label: t('header.menu.entertainment'), name: 'Entertainment' },
    { id: 'finance', label: t('header.menu.finance'), name: 'Business & Finance' },
    { id: 'health', label: t('header.menu.health'), name: 'Health & Wellness' },
  ], [t]);
  
  // 定義國家及其分類
  const countries = useMemo(() => [
    {
      id: 'taiwan',
      label: t('header.countries.taiwan'),
      dbName: 'Taiwan',
      categories: categoryDefinitions.map(cat => ({
        ...cat,
        path: `/category/Taiwan/${cat.name}`
      }))
    },
    {
      id: 'usa',
      label: t('header.countries.usa'),
      dbName: 'United States of America',
      categories: categoryDefinitions.map(cat => ({
        ...cat,
        path: `/category/United States of America/${cat.name}`
      }))
    },
    {
      id: 'japan',
      label: t('header.countries.japan'),
      dbName: 'Japan',
      categories: categoryDefinitions.map(cat => ({
        ...cat,
        path: `/category/Japan/${cat.name}`
      }))
    },
    {
      id: 'indonesia',
      label: t('header.countries.indonesia'),
      dbName: 'Indonesia',
      categories: categoryDefinitions.map(cat => ({
        ...cat,
        path: `/category/Indonesia/${cat.name}`
      }))
    },
  ], [t, categoryDefinitions]);

  // 定義語言選單陣列，使用 i18n 翻譯
  const languages = [
    { name: "繁體中文", code: 'zh-TW', route: 'zh-TW' },
    { name: "English", code: 'en', route: 'en' },
    { name: "日本語", code: 'jp', route: 'jp' },
    { name: "Bahasa Indonesia", code: 'id', route: 'id' },
  ];

  const [activeDomain, setActiveDomain] = useState(domains[0].id);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

  const [selectedLanguage, setSelectedLanguage] = useState('zh-TW');

  // 處理搜尋功能
  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter' && search.trim() !== '') {
      navigate(`/${selectedLanguage}/search/${encodeURIComponent(search.trim())}`);
    }
  };

  // 處理語言切換功能 (使用 i18n 和路由切換)
  const handleLanguageChange = (e) => {
    const newLanguage = e.target.value;
    console.log('切換語言到:', newLanguage);
    setSelectedLanguage(newLanguage);
    i18n.changeLanguage(newLanguage);
    
    // 更新路由到新語言
    const pathSegments = location.pathname.split('/');
    pathSegments[1] = newLanguage; // 替換語言代碼
    const newPath = pathSegments.join('/');
    navigate(newPath);
  };

  // 處理國家切換功能
  const handleCountryChange = (e) => {
    const newCountryId = e.target.value;
    setSelectedCountry(newCountryId);
    setActiveDomain(null); // 清除主導航的 active 狀態
    
    const newCountry = countries.find(c => c.id === newCountryId);
    if (!newCountry) return;
    
    // 如果目前有選中的類別，導航到新國家的相同類別
    if (activeCategory) {
      const matchingCategory = newCountry.categories.find(cat => cat.id === activeCategory);
      if (matchingCategory) {
        navigate(`/${selectedLanguage}${matchingCategory.path}`);
        return;
      }
    }
    
    // 如果在首頁或其他頁面，只更新國家狀態，不進行導航
    // HomePage 會自動根據國家狀態更新新聞內容
  };

  // 處理登出
  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('登出失敗:', error);
    }
  };

  // 當路由改變時，更新語言和 active domain
  useEffect(() => {
    const pathSegments = location.pathname.split('/');
    const langCode = pathSegments[1];
    let currentLang = 'zh-TW'; // 預設語言
    
    if (['zh-TW', 'en', 'jp', 'id'].includes(langCode)) {
      currentLang = langCode;
    }
    
    // 只在語言真的改變時才更新
    if (currentLang !== selectedLanguage) {
      setSelectedLanguage(currentLang);
      i18n.changeLanguage(currentLang);
    }

    // 移除語言前綴來檢查路徑，使用正確的語言長度
    const pathWithoutLang = location.pathname.replace(/^\/[a-z-]+/, '') || '/';
    
    // 設定當前 active 的類別
    if (pathWithoutLang === '/') {
      setActiveDomain('/');
      setActiveCategory(null);
    } else if (pathWithoutLang.startsWith('/yesterday-focus')) {
      setActiveDomain('yesterday');
      setActiveCategory(null);
    } else if (pathWithoutLang.startsWith('/special-reports')) {
      setActiveDomain('project');
      setActiveCategory(null);
    } else if (pathWithoutLang.startsWith('/abroad')) {
      setActiveDomain('abroad');
      setActiveCategory(null);
    } else if (pathWithoutLang.startsWith('/category/')) {
      const categoryFromPath = decodeURIComponent(pathWithoutLang.substring(10));
      
      // 檢查是否匹配國家
      const matchedCountry = countries.find(country => 
        categoryFromPath.startsWith(country.dbName)
      );
      if (matchedCountry) {
        setSelectedCountry(matchedCountry.id);
        
        // 檢查是否匹配特定類別
        const matchedCategory = matchedCountry.categories.find(cat => 
          categoryFromPath === `${matchedCountry.dbName}/${cat.name}`
        );
        if (matchedCategory) {
          setActiveCategory(matchedCategory.id);
          setActiveDomain(null); // 清除主導航的 active 狀態
        } else {
          setActiveCategory(null);
        }
      }
      
      const domain = domains.find((d) => {
        const categoryFromDomain = d.path.substring(10);
        return categoryFromDomain === categoryFromPath;
      });
      if (domain) setActiveDomain(domain.id);
    }
  }, [location.pathname, domains, countries, selectedLanguage, i18n, setSelectedCountry]);

  return (
    <header className="header">
      <div className="mainBar">
        <div className="brandSection">
          <Link to={`/${selectedLanguage}`} className="brandLink">
            <div className="logo">{t('header.brand')}</div>
          </Link>
          <span className="tagline">{t('header.tagline')}</span>
        </div>

        {/* AI 警語 */}
        <div className="aiWarning">
          {t('header.aiWarning').split('\n').map((line, index) => (
            <React.Fragment key={index}>
              {line}
              {index < t('header.aiWarning').split('\n').length - 1 && <br />}
            </React.Fragment>
          ))}
        </div>

        <div className="rightSection">
          <div className="searchSection">
            <div className="searchInputWrapper">
              <span className="searchIcon">🔍</span>
              <input
                className="searchInput"
                type="text"
                placeholder={t('header.search.placeholder')}
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
            >
              {languages.map((language) => (
                <option key={language.code} value={language.route}>
                  {language.name}
                </option>
              ))}
            </select>
          </div>

          {/* 登出按鈕 */}
          {user && (
            <button 
              className="logoutButton"
              onClick={handleSignOut}
              title="登出"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="tagBarWrapper">   
        <div className="domainTagBar">
          {/* 國家下拉式選單 */}
          <div className="countrySelectWrapper">
            <select 
              className="countrySelect"
              value={selectedCountry}
              onChange={handleCountryChange}
            >
              {countries.map((country) => (
                <option key={country.id} value={country.id}>
                  {country.label}
                </option>
              ))}
            </select>
          </div>

          {domains.map((domain) => (
            <Link
              key={domain.id}
              to={`/${selectedLanguage}${domain.path}`}
              className={`tagLink ${activeDomain === domain.id ? 'is-active' : ''}`}
              onClick={() => {
                setActiveDomain(domain.id);
                setActiveCategory(null);
              }}
            >
              {domain.label}
            </Link>
          ))}
          
          {/* 類別標籤 */}
          {countries
            .find((country) => country.id === selectedCountry)
            ?.categories.map((category) => (
              <Link
                key={category.id}
                to={`/${selectedLanguage}${category.path}`}
                className={`tagLink categoryTag ${activeCategory === category.id ? 'is-active' : ''}`}
                onClick={() => {
                  setActiveCategory(category.id);
                  setActiveDomain(null);
                }}
              >
                {category.label}
              </Link>
            ))}
        </div>
      </div>
    </header>
  );
}

export default Header;