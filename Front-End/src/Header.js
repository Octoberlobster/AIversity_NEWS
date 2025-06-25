import React from 'react';
import './css/Header.css';
import translateIcon from './Translate.png';
import { FaSearch } from 'react-icons/fa';

function Header({ language, setLanguage }) {
  return (
    <div className="header-bar">
      <div className="platform-name">
        <span></span>
      </div>
      <div className="search-bar-container">
        <form className="search-form" onSubmit={(e) => e.preventDefault()}>
          <input
            type="text"
            className="search-input"
            placeholder="搜尋..."
          />
          <button type="submit" className="search-button">
            <FaSearch />
          </button>
        </form>
      </div>

      {/* 語言選擇器 */}
      <div className="language-selector">
        <img src={translateIcon} alt="Translate" className="translate-icon" />
        <select value={language} className="language-dropdown">
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
  );
}

export default Header;
