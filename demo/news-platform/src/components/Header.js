import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
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

function Header() {
  const [activeDomain, setActiveDomain] = useState(domains[0].id);
  const [search, setSearch] = useState('');
  const location = useLocation();
  const navigate = useNavigate();

  // 處理搜尋功能
  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter' && search.trim() !== '') {
      // 導航到搜尋結果頁面
      navigate(`/search/${encodeURIComponent(search.trim())}`);
    }
  };

  // 依路徑設定目前 active 的類別
  useEffect(() => {
    if (location.pathname === '/') {
      setActiveDomain('/');
    } else if (location.pathname.startsWith('/special-reports')) {
      setActiveDomain('project');
    } else if (location.pathname.startsWith('/category/')) {
      const categoryFromPath = decodeURIComponent(location.pathname.substring(10)); // 移除 '/category/' 前綴
      const domain = domains.find((d) => {
        const categoryFromDomain = d.path.substring(10); // 移除 '/category/' 前綴
        return categoryFromDomain === categoryFromPath;
      });
      if (domain) setActiveDomain(domain.id);
    }
  }, [location.pathname]);

  return (
    <header className="header">
      <div className="mainBar">
        <div className="brandSection">
          <Link to="/" className="brandLink">
            <div className="logo">AIversity</div>
          </Link>
          <span className="tagline">智能新聞，深度洞察</span>
        </div>

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