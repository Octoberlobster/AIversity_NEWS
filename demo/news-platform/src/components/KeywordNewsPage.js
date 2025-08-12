import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import UnifiedNewsCard from './UnifiedNewsCard';
import FloatingChat from './FloatingChat';
import './../css/KeywordNewsPage.css';

const hotKeywords = [
  '女足', '大罷免', '颱風', '疫苗', 'AI', '房價', '能源', '選舉', '地震', '股市', 'ChatGPT',
  '缺水', '升息', '碳中和', '罷工', '通膨', '烏俄戰爭', '台積電', 'AI醫療', '元宇宙'
];

function KeywordNewsPage() {
  const { keyword } = useParams();
  const [showAllNews, setShowAllNews] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="keywordPage">
      <main className="keywordPage__main">
        <div className="keywordPage__grid">
          <div className="keywordPage__mainCol">
            <h2 className="keywordPage__sectionTitle">{keyword}</h2>

            <UnifiedNewsCard limit={showAllNews ? undefined : 6} keyword={keyword} />

            {(() => {
              // 取得該關鍵字新聞數量（沿用你原本的 require 寫法）
              const { defaultNewsData } = require('./UnifiedNewsCard');
              const filtered = (defaultNewsData || []).filter(news =>
                (news.keywords && news.keywords.some(kw => kw === keyword)) ||
                (news.title && news.title.includes(keyword)) ||
                (news.shortSummary && news.shortSummary.includes(keyword))
              );

              if (!showAllNews && filtered.length >= 4) {
                return (
                  <div className="keywordPage__moreWrap">
                    <button
                      className="keywordPage__moreBtn"
                      onClick={() => setShowAllNews(true)}
                    >
                      閱讀更多新聞
                    </button>
                  </div>
                );
              }
              return null;
            })()}
          </div>

          <aside className="keywordPage__sidebar">
            <div className="keywordPage__card">
              <h3 className="keywordPage__cardTitle">🔥 熱門搜尋關鍵字</h3>
              <div className="keywordPage__cloud">
                {hotKeywords.map((kw) => (
                  <span
                    key={kw}
                    className="keywordPage__kw"
                    style={{ '--size': `${(1 + Math.random() * 0.5).toFixed(2)}rem` }}
                    onClick={() => navigate(`/keyword/${encodeURIComponent(kw)}`)}
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </main>
      <FloatingChat />
    </div>
  );
}

export default KeywordNewsPage;
