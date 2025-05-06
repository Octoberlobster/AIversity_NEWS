import React from 'react';
import './css/Header.css';
import translateIcon from './Translate.png';

function Header({ language, setLanguage }) {
  return (
    <div className="header-bar">
      <div className="platform-name">
        <span></span>
      </div>
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
