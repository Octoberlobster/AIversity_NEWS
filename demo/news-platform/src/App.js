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
import { SupabaseProvider } from './components/supabase';
import './css/App.css';

const hotKeywords = [
  'AI', '房價', '疫苗', '選舉', '颱風', '股市', '升息', '地震', '烏俄', '通膨',
  '台積電', '碳中和', '缺水', '罷工', 'ChatGPT', '元宇宙', '女足', '大罷免',
  '能源', 'AI醫療', '5G', '電動車', '半導體', '新冠', '核電', '綠能'
];

function App() {
  const [showAllNews, setShowAllNews] = useState(false);
  const [totalNewsCount, setTotalNewsCount] = useState(0);

  return (
    <SupabaseProvider>
      <Router>
        <div className="app">
          <Header />
          <main className="mainContent">
            <Routes>
              <Route
                path="/"
                element={
                  <>
                    <div className="carousel-title-section">
                      <div className="carousel-title-content">
                        <span className="fire-icon">🔥</span>
                        熱門新聞
                      </div>
                      <div></div> {/* 空 div 用於對應 sidebar 空間 */}
                    </div>
                    <NewsCarousel />
                    <div className="contentGrid">
                      <div className="mainColumn">
                        <h2 className="sectionTitle">
                          最新新聞 
                        </h2>
                        <UnifiedNewsCard 
                          limit={showAllNews ? undefined : 15} 
                          onNewsCountUpdate={setTotalNewsCount}
                          instanceId="main_news_list"
                        />
                        {!showAllNews && totalNewsCount > 15 && (
                          <div className="moreButtonWrap">
                            <button className="moreButton" onClick={() => setShowAllNews(true)}>
                              閱讀更多新聞 ({totalNewsCount - 15} 篇)
                            </button>
                          </div>
                        )}
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
              <Route path="/category/Politics" element={<CategorySection category="政治" />} />
              <Route path="/category/Taiwan News" element={<CategorySection category="台灣" />} />
              <Route path="/category/International News" element={<CategorySection category="國際" />} />
              <Route path="/category/Science & Technology" element={<CategorySection category="科學與科技" />} />
              <Route path="/category/Lifestyle & Consumer" element={<CategorySection category="生活" />} />
              <Route path="/category/Sports" element={<CategorySection category="體育" />} />
              <Route path="/category/Entertainment" element={<CategorySection category="娛樂" />} />
              <Route path="/category/Business & Finance" element={<CategorySection category="商業財經" />} />
              <Route path="/category/Health & Wellness" element={<CategorySection category="健康" />} />
              <Route path="/special-reports" element={<SpecialReportPage />} />
              <Route path="/special-report/:id" element={<SpecialReportDetail />} />
            </Routes>
          </main>

          <FloatingChat />
        </div>
      </Router>
    </SupabaseProvider>
  );
}

export default App;
