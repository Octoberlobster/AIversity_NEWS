import React, { useState, useEffect, useMemo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './../css/Header.css';

function Header() {
  const { t, i18n } = useTranslation();
  
  const domains = useMemo(() => [
    { id: '/', label: t('header.menu.home'), path: '/'},
    { id: 'project', label: t('header.menu.specialReports'), path: '/special-reports'},
    { id: 'abroad', label: t('header.menu.abroad'), path: '/abroad'},
    { id: 'politics', label: t('header.menu.politics'), path: '/category/Politics' },
    { id: 'taiwan', label: t('header.menu.taiwan'), path: '/category/Taiwan News' },
    { id: 'international', label: t('header.menu.international'), path: '/category/International News' },
    { id: 'scienceandtech', label: t('header.menu.scienceAndTech'), path: '/category/Science & Technology' },
    { id: 'life', label: t('header.menu.life'), path: '/category/Lifestyle & Consumer' },
    { id: 'sports', label: t('header.menu.sports'), path: '/category/Sports' },
    { id: 'entertainment', label: t('header.menu.entertainment'), path: '/category/Entertainment' },
    { id: 'finance', label: t('header.menu.finance'), path: '/category/Business & Finance' },
    { id: 'health', label: t('header.menu.health'), path: '/category/Health & Wellness' },
  ], [t]);

  // 定義語言選單陣列，使用 i18n 翻譯
  const languages = [
    { name: t('header.language.chinese'), code: 'zh-TW', route: 'zh-TW' },
    { name: t('header.language.english'), code: 'en', route: 'en' },
    { name: t('header.language.japanese'), code: 'jp', route: 'jp' },
    { name: t('header.language.indonesian'), code: 'id', route: 'id' },
  ];

  const [activeDomain, setActiveDomain] = useState(domains[0].id);
  const [search, setSearch] = useState('');
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
    } else if (pathWithoutLang.startsWith('/special-reports')) {
      setActiveDomain('project');
    } else if (pathWithoutLang.startsWith('/abroad')) {
      setActiveDomain('abroad');
    } else if (pathWithoutLang.startsWith('/category/')) {
      const categoryFromPath = decodeURIComponent(pathWithoutLang.substring(10));
      const domain = domains.find((d) => {
        const categoryFromDomain = d.path.substring(10);
        return categoryFromDomain === categoryFromPath;
      });
      if (domain) setActiveDomain(domain.id);
    }
  }, [location.pathname, domains, selectedLanguage, i18n]);

  return (
    <header className="header">
      <div className="mainBar">
        <div className="brandSection">
          <Link to={`/${selectedLanguage}`} className="brandLink">
            <div className="logo">{t('header.brand')}</div>
          </Link>
          <span className="tagline">{t('header.tagline')}</span>
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
        </div>
      </div>

      <div className="tagBarWrapper">
        <div className="domainTagBar">
          {domains.map((domain) => (
            <Link
              key={domain.id}
              to={`/${selectedLanguage}${domain.path}`}
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