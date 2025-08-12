import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './../css/Header.css';

const domains = [
  { id: '/', label: '首頁', path: '/'},
  { id: 'politics', label: '政治', path: '/category/politics' },
  { id: 'society', label: '社會', path: '/category/society' },
  { id: 'scienceandtech', label: '科學與科技', path: '/category/scienceandtech' },
  { id: 'international', label: '國際', path: '/category/international' },
  { id: 'life', label: '生活', path: '/category/life' },
  { id: 'sports', label: '運動', path: '/category/sports' },
  { id: 'entertainment', label: '娛樂', path: '/category/entertainment' },
  { id: 'finance', label: '財經', path: '/category/finance' },
  { id: 'health', label: '醫療保健', path: '/category/health' },
  { id: 'project', label: '專題報導', path: '/special-reports'}
];

function Header() {
  const [activeDomain, setActiveDomain] = useState(domains[0].id);
  const [search, setSearch] = useState('');
  const location = useLocation();

  // 依路徑設定目前 active 的類別
  useEffect(() => {
    if (location.pathname === '/') {
      setActiveDomain('/');
    } else if (location.pathname.startsWith('/special-reports')) {
      setActiveDomain('project');
    } else if (location.pathname.startsWith('/category/')) {
      const category = location.pathname.split('/')[2];
      const domain = domains.find((d) => d.path === `/category/${category}`);
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