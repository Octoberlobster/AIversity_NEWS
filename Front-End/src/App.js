import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Header from './components/Header';
import LatestTopics from './components/LatestTopics';
import CategorySection from './components/CategorySection';
import UnifiedNewsCard from './components/UnifiedNewsCard';
import NewsDetail from './components/NewsDetail';
import FloatingChat from './components/FloatingChat';
import KeywordNewsPage from './components/KeywordNewsPage';
import SearchResultsPage from './components/SearchResultsPage';
import SpecialReportPage from './components/SpecialReportPage';
import SpecialReportDetail from './components/SpecialReportDetail';
import AdminDashboard from './components/admin/AdminDashboard';
import AbroadNewsPage from './components/AbroadNewsPage';
import { SupabaseProvider } from './components/supabase';
import './i18n'; // 初始化 i18n
import './css/App.css';

function App() {

  const { t, i18n } = useTranslation();

  return (
    <SupabaseProvider>
      <Router>
        <Routes>
          {/* 管理後台路由 - 獨立介面 */}
          <Route path="/admin/*" element={<AdminDashboard />} />
          
          {/* 前台路由 - 包含 Header 和 FloatingChat */}
          <Route path="/*" element={
            <div className="app">
              <Header />
              <main className="mainContent">
                <Routes>
                  <Route
                    path="/"
                    element={
                      <>
                        <LatestTopics />
                        <div className="contentGrid news-section-overlap">
                          <div className="mainColumn">
                            <h2 className="sectionTitle">
                              {t('home.latestNews')} 
                            </h2>
                            <UnifiedNewsCard 
                              instanceId="main_news_list"
                            />
                          </div>
                        </div>
                      </>
                    }
                  />
                  <Route path="/news/:id" element={<NewsDetail />} />
                  <Route path="/keyword/:keyword" element={<KeywordNewsPage />} />
                  <Route path="/search/:query" element={<SearchResultsPage />} />
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
                  <Route path="/abroad" element={<AbroadNewsPage />} />
                </Routes>
              </main>
              <FloatingChat />
            </div>
          } />
        </Routes>
      </Router>
    </SupabaseProvider>
  );
}

export default App;
