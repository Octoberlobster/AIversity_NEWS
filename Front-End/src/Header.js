import React from 'react';
import './css/Header.css';
import translateIcon from './Translate.png';
import { FaSearch } from 'react-icons/fa';
import { Link } from 'react-router-dom';

function Header({ language, setLanguage }) {
  return (
    <>
      <div className="header-bar">
        <div className="platform-name">
          <span></span>
        </div>
        <div className="search-bar-container">
          <form className="search-form" onSubmit={(e) => e.preventDefault()}>
            <input
              type="text"
              className="search-input"
              placeholder="搜尋主題、地點和來源"
            />
            <button type="submit" className="search-button">
              <FaSearch />
            </button>
          </form>
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
        <Link to="#" className="sub-nav-item active">首頁</Link>
        <Link to="#recommend" className="sub-nav-item">為你推薦</Link>
        <Link to="#trending" className="sub-nav-item">追蹤中</Link>
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
