import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import NewsCarousel from './components/NewsCarousel';
import CategorySection from './components/CategorySection';
import UnifiedNewsCard from './components/UnifiedNewsCard';
import NewsDetail from './components/NewsDetail';
import FloatingChat from './components/FloatingChat';
import KeywordNewsPage from './components/KeywordNewsPage';
import SpecialReportPage from './components/SpecialReportPage';
import SpecialReportDetail from './components/SpecialReportDetail';
import './css/App.css';

const hotKeywords = [
  '女足', '大罷免', '颱風', '疫苗', 'AI', '房價', '能源', '選舉', '地震', '股市', 'ChatGPT',
  '缺水', '升息', '碳中和', '罷工', '通膨', '烏俄戰爭', '台積電', 'AI醫療', '元宇宙'
];

function App() {
  const [showAllNews, setShowAllNews] = useState(false);

  return (
    <Router>
      <div className="app">
        <Header />
        <main className="mainContent">
          <Routes>
            <Route
              path="/"
              element={
                <>
                  <NewsCarousel />
                  <div className="contentGrid">
                    <div className="mainColumn">
                      <h2 className="sectionTitle">最新新聞</h2>
                      <UnifiedNewsCard limit={showAllNews ? undefined : 9} />
                      {(() => {
                        // 取得所有新聞數量
                        const { defaultNewsData } = require('./components/UnifiedNewsCard');
                        const newsData = defaultNewsData || [];
                        if (!showAllNews && newsData.length > 6) {
                          return (
                            <div className="moreButtonWrap">
                              <button className="moreButton" onClick={() => setShowAllNews(true)}>
                                閱讀更多新聞
                              </button>
                            </div>
                          );
                        }
                        return null;
                      })()}
                    </div>

                    <aside className="sidebar">
                      <div className="sidebarCard">
                        <h3 className="sidebarTitle">🔥 熱門專題</h3>
                        <div className="keywordCloud">
                          {hotKeywords.map((kw) => (
                            <span
                              key={kw}
                              className="keyword"
                              style={{ '--size': `${(1 + Math.random() * 0.5).toFixed(2)}rem` }}
                              onClick={() => (window.location.href = `/keyword/${encodeURIComponent(kw)}`)}
                            >
                              {kw}
                            </span>
                          ))}
                        </div>
                      </div>
                    </aside>
                  </div>
                </>
              }
            />
            <Route path="/news/:id" element={<NewsDetail />} />
            <Route path="/keyword/:keyword" element={<KeywordNewsPage />} />
            <Route path="/category/politics" element={<CategorySection category="政治" />} />
            <Route path="/category/taiwan" element={<CategorySection category="台灣" />} />
            <Route path="/category/scienceandtech" element={<CategorySection category="科學與科技" />} />
            <Route path="/category/international" element={<CategorySection category="國際" />} />
            <Route path="/category/life" element={<CategorySection category="生活" />} />
            <Route path="/category/sports" element={<CategorySection category="體育" />} />
            <Route path="/category/entertainment" element={<CategorySection category="娛樂" />} />
            <Route path="/category/finance" element={<CategorySection category="商業財經" />} />
            <Route path="/category/health" element={<CategorySection category="健康" />} />
            <Route path="/special-reports" element={<SpecialReportPage />} />
            <Route path="/special-report/:id" element={<SpecialReportDetail />} />
          </Routes>
        </main>

        <FloatingChat />
      </div>
    </Router>
  );
}

export default App;
