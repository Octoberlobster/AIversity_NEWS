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
          <button type="button" className="closeButton" onClick={onClose} aria-label="關閉">
            ×
          </button>
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
