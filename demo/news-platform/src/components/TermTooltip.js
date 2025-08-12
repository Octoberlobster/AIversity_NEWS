import React, { useEffect, useRef } from 'react';
import './../css/TermTooltip.css';

function TermTooltip({ term, definition, position, onClose }) {
  const contentRef = useRef(null);

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

  // 範例內容
  const examples = {
    "人工智慧": { title: "應用例子", text: "例如：語音助手（如 Siri、Alexa）、推薦系統、自動駕駛汽車等" },
    "機器學習": { title: "應用例子", text: "例如：垃圾郵件過濾、產品推薦、股票預測等" },
    "影像識別": { title: "應用例子", text: "例如：人臉識別、物體檢測、醫學影像分析等" },
    "倫理考量": { title: "相關議題", text: "例如：AI 偏見、自動化對就業的影響、決策透明度等" },
    "隱私保護": { title: "保護措施", text: "例如：數據加密、匿名化處理、用戶同意機制等" },
    "深度學習": { title: "應用例子", text: "例如：自然語言處理、圖像生成、語音合成等" },
    "精準醫療": { title: "你好", text: "你好" },
    "三級三審": { title: "應用例子", text: "這起殺人案因為案情複雜，經過三級三審，歷時多年才最終定讞。\n\n由於證據不足，高等法院發回更審，這個案件可能要走完三級三審的程序。" },
    "IRB": { title: "應用例子", text: "這個研究計畫必須先通過 IRB 審查才能開始執行。\n\n因為 IRB 的要求，我們需要修改受試者同意書。\n\nIRB 委員仔細審閱了研究方案，並提出了一些建議。" }
  };
  const example = examples[term] || null;

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
