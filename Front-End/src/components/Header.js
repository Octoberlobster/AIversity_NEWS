import React, { useState, useEffect, useMemo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './../css/Header.css';
function Header() {
  const { t, i18n } = useTranslation();
  
  // 定義導航選單陣列，使用 i18n 翻譯 (使用 useMemo 優化性能)
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
    { name: t('header.language.chinese'), code: 'zh-TW' },
    { name: t('header.language.english'), code: 'en' },
  ];

  const [activeDomain, setActiveDomain] = useState(domains[0].id);
  const [search, setSearch] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState(i18n.language || 'zh-TW');
  const location = useLocation();
  const navigate = useNavigate();

  // 處理搜尋功能
  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter' && search.trim() !== '') {
      navigate(`/search/${encodeURIComponent(search.trim())}`);
    }
  };

  // 處理語言切換功能 (使用 i18n)
  const handleLanguageChange = (e) => {
    const newLanguage = e.target.value;
    console.log('切換語言到:', newLanguage);
    setSelectedLanguage(newLanguage);
    i18n.changeLanguage(newLanguage);
  };

  // 當路由改變時，設定 active domain
  useEffect(() => {
    // 設定當前 active 的類別
    if (location.pathname === '/') {
      setActiveDomain('/');
    } else if (location.pathname.startsWith('/special-reports')) {
      setActiveDomain('project');
    } else if (location.pathname.startsWith('/abroad')) {
      setActiveDomain('abroad');
    } else if (location.pathname.startsWith('/category/')) {
      const categoryFromPath = decodeURIComponent(location.pathname.substring(10));
      const domain = domains.find((d) => {
        const categoryFromDomain = d.path.substring(10);
        return categoryFromDomain === categoryFromPath;
      });
      if (domain) setActiveDomain(domain.id);
    }
  }, [location.pathname, domains]);

  return (
    <header className="header">
      <div className="mainBar">
        <div className="brandSection">
          <Link to="/" className="brandLink">
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
                <option key={language.code} value={language.code}>
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