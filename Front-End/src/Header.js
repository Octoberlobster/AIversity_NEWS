import React from 'react';
import './css/Header.css';
import translateIcon from './Translate.png';
import { FaSearch } from 'react-icons/fa';
import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';

function Header({ language, setLanguage }) {
  // 新增日期狀態
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [keyword, setKeyword] = useState('');
  const navigate = useNavigate();

  // 日期變更處理（可依需求改寫）
  const handleStartDateChange = (e) => setStartDate(e.target.value);
  const handleEndDateChange = (e) => setEndDate(e.target.value);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!keyword.trim()) return;

    // 組合搜尋路由，將日期篩選條件用 query string 傳遞
    const params = new URLSearchParams();
    if (startDate) params.append('startDate', startDate);
    if (endDate) params.append('endDate', endDate);

    const queryString = params.toString();
    const path = `/search/${encodeURIComponent(keyword.trim())}${queryString ? `?${queryString}` : ''}`;

    navigate(path);
  };
  return (
    <>
      <div className="header-bar">
        <div className="platform-name">
          <span></span>
        </div>
        <div className="search-bar-container">
          <form className="search-form" onSubmit={handleSubmit}>
            <input
              type="text"
              className="search-input"
              placeholder="搜尋主題、地點和來源"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
            <button type="submit" className="search-button">
              <FaSearch />
            </button>
          </form>
        </div>

        {/* 日期篩選工具 */}
        <div className="date-filter-container">
          <label>
            起始日期:
            <input
              type="date"
              value={startDate}
              onChange={handleStartDateChange}
              className="date-input"
            />
          </label>
          <label>
            結束日期:
            <input
              type="date"
              value={endDate}
              onChange={handleEndDateChange}
              className="date-input"
            />
          </label>
        </div>

        <div className="language-selector">
          <img src={translateIcon} alt="Translate" className="translate-icon" />
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            className="language-dropdown"
          >
            <option value="zh">中文</option>
            <option value="tw">台語</option>
            <option value="en">English</option>
            <option value="ja">日本語</option>
            <option value="ko">한국어</option>
            <option value="vi">Tiếng Việt</option>
            <option value="th">ภาษาไทย</option>
            <option value="es">Español</option>
          </select>
        </div>
      </div>

      {/* 主題列 */}
      <div className="sub-nav-bar">
        <Link to="/" className="sub-nav-item active">首頁</Link>
        <Link to="/#recommend" className="sub-nav-item">為你推薦</Link>
        <Link to="/#trending" className="sub-nav-item">追蹤中</Link>
        <Link to="/category/Politics" className="sub-nav-item">政治</Link>
        <Link to="/category/Social News" className="sub-nav-item">社會</Link>
        <Link to="/category/Science" className="sub-nav-item">科學</Link>
        <Link to="/category/Technology" className="sub-nav-item">科技</Link>
        <Link to="/category/International News" className="sub-nav-item">國際</Link>
        <Link to="/category/Lifestyle & Consumer News" className="sub-nav-item">生活</Link>
        <Link to="/category/Sports" className="sub-nav-item">運動</Link>
        <div className="sub-nav-dropdown">
          <button className="sub-nav-item">⋯</button>
          <div className="sub-nav-dropdown-content">
            <Link to="/category/Entertainment" className="sub-nav-dropdown-item">娛樂</Link>
            <Link to="/category/Business & Finance" className="sub-nav-dropdown-item">財經</Link>
            <Link to="/category/Health & Wellness" className="sub-nav-dropdown-item">醫療保健</Link>
          </div>
        </div>
      </div>
    </>
  );
}

export default Header;
