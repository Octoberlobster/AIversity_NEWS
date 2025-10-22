import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import './../css/TermTooltip.css';

function TermTooltip({ term, definition, example: exampleFromDB, position, onClose }) {
  const contentRef = useRef(null);
  const { t } = useTranslation();

  // Esc 關閉 + 初始聚焦到對話框
  useEffect(() => {
    const handleEscape = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleEscape);
    // 聚焦到對話框本體（方便鍵盤使用者）
    contentRef.current?.focus();
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  // Google 搜尋功能
  const handleGoogleSearch = () => {
    const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(term)}`;
    window.open(searchUrl, '_blank', 'noopener,noreferrer');
  };
  
  // 優先使用資料庫的範例，如果沒有則使用預設範例
  const getFinalExample = () => {
    // 首先檢查是否有資料庫提供的範例
    if (exampleFromDB) {
      return { title: t("term.example"), text: exampleFromDB };
    }
    
    // 使用預設範例
    return null;
  };

  const example = getFinalExample();

  return (
    <div className="tooltipOverlay" onClick={handleOverlayClick}>
      <div
        className="tooltipContent"
        role="dialog"
        aria-modal="true"
        aria-labelledby="term-tooltip-title"
        aria-describedby="term-tooltip-definition"
        tabIndex={-1}
        ref={contentRef}
      >
        <div className="tooltipHeader">
          <h3 className="termTitle" id="term-tooltip-title">{term}</h3>
          <div className="headerButtons">
            <button 
              type="button" 
              className="googleSearchButton" 
              onClick={handleGoogleSearch}
              aria-label="在 Google 搜尋"
              title="在 Google 搜尋"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="M21 21l-4.35-4.35"></path>
              </svg>
              <span>Google搜尋</span>
            </button>
            <button type="button" className="closeButton" onClick={onClose} aria-label="關閉">
              ×
            </button>
          </div>
        </div>

        <p className="definition" id="term-tooltip-definition">{definition}</p>

        {example && (
          <div className="example">
            <h4 className="exampleTitle">{example.title}</h4>
            <p className="exampleText" style={{ whiteSpace: 'pre-line' }}>{example.text}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default TermTooltip;
