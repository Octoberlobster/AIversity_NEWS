import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
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
import './i18n'; 
import './css/App.css';

// Layout 組件使用 Outlet 來渲染子路由
function LanguageLayout() {
  return (
    <div className="app">
      <Header />
      <main className="mainContent">
        <Outlet />
      </main>
      
    </div>
  );
}

// 首頁組件
function HomePage() {
  const { t } = useTranslation();
  
  return (
    <>
      <LatestTopics />
      <div className="contentGrid news-section-overlap">
        <div className="mainColumn">
          <h2 className="sectionTitle">
            {t('home.latestNews')}
          </h2>
          <UnifiedNewsCard instanceId="main_news_list" />
        </div>
      </div>
    </>
  );
}

function App() {
  return (
    <SupabaseProvider>
      <Router>
        <Routes>
          {/* 根路由重定向到預設語言 */}
          <Route path="/" element={<Navigate to="/zh-TW/" replace />} />
          
          {/* 管理後台路由 - 獨立介面 */}
          <Route path="/admin/*" element={<AdminDashboard />} />
          
          {/* 多語言路由 */}
          {["zh-TW", "en", "jp", "id"].map(lang => (
            <Route key={`redirect-${lang}`} path={`/${lang}`} element={<Navigate to={`/${lang}/`} replace />} />
          ))}
          
          {["zh-TW", "en", "jp", "id"].map(lang => (
            <Route key={lang} path={`/${lang}`} element={<LanguageLayout />}>
              <Route index element={<HomePage />} />
              <Route path="news/:id" element={<NewsDetail />} />
              <Route path="keyword/:keyword" element={<KeywordNewsPage />} />
              <Route path="search/:query" element={<SearchResultsPage />} />
              <Route path="category/Politics" element={<CategorySection category="政治" />} />
              <Route path="category/Taiwan News" element={<CategorySection category="台灣" />} />
              <Route path="category/International News" element={<CategorySection category="國際" />} />
              <Route path="category/Science & Technology" element={<CategorySection category="科學與科技" />} />
              <Route path="category/Lifestyle & Consumer" element={<CategorySection category="生活" />} />
              <Route path="category/Sports" element={<CategorySection category="體育" />} />
              <Route path="category/Entertainment" element={<CategorySection category="娛樂" />} />
              <Route path="category/Business & Finance" element={<CategorySection category="商業財經" />} />
              <Route path="category/Health & Wellness" element={<CategorySection category="健康" />} />
              <Route path="special-reports" element={<SpecialReportPage />} />
              <Route path="special-report/:id" element={<SpecialReportDetail />} />
              <Route path="abroad" element={<AbroadNewsPage />} />
            </Route>
          ))}
        </Routes>
      </Router>
    </SupabaseProvider>
  );
}

export default App;
