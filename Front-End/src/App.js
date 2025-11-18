import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Header from './components/Header';
import FocusNews from './components/FocusNews';
import CategorySection from './components/CategorySection';
import UnifiedNewsCard from './components/UnifiedNewsCard';
import NewsDetail from './components/NewsDetail';
import FloatingChat from './components/FloatingChat';
import KeywordNewsPage from './components/KeywordNewsPage';
import SearchResultsPage from './components/SearchResultsPage';
import SpecialReportPage from './components/SpecialReportPage';
import SpecialReportDetail from './components/SpecialReportDetail';
//import AdminDashboard from './components/admin/AdminDashboard';
import AbroadNewsPage from './components/AbroadNewsPage';
import YesterdayFocus from './components/YesterdayFocus';
import { SupabaseProvider } from './components/supabase';
import { CountryProvider, useCountry } from './components/CountryContext';
import { QueryProvider } from './providers/QueryProvider';
import { AuthProvider } from './login/AuthContext';
import ProtectedRoute from './login/ProtectedRoute';
import LoginPage from './login/LoginPage';
import './i18n'; 
import './css/App.css';

// 專題報導路由保護元件 (只有台灣可以訪問)
function TaiwanOnlyRoute({ children }) {
  const { selectedCountry, setSelectedCountry } = useCountry();
  const location = useLocation();
  const hasCheckedRef = React.useRef(false);
  
  // 從當前路徑提取語言前綴
  const pathParts = location.pathname.split('/').filter(p => p);
  const currentLang = pathParts[0] || 'zh-TW';
  
  // 只在第一次進入時檢查,避免干擾頁面內的國家切換導航
  React.useEffect(() => {
    if (!hasCheckedRef.current && selectedCountry !== 'taiwan') {
      hasCheckedRef.current = true;
      // 路由爆破保護:非台灣模式直接訪問專題頁面,切換到台灣並導航到首頁
      localStorage.setItem('selectedCountry', 'taiwan');
      setSelectedCountry('taiwan');
      window.location.href = window.location.origin + `/${currentLang}/`;
    }
  }, []); // 空依賴,只執行一次
  
  // 如果是第一次進入且不是台灣,不渲染內容
  if (!hasCheckedRef.current && selectedCountry !== 'taiwan') {
    hasCheckedRef.current = true;
    return null;
  }
  
  return children;
}

// Layout 組件使用 Outlet 來渲染子路由
function LanguageLayout() {
  const location = useLocation();
  
  // 檢查當前路由是否應該隱藏 FloatingChat
  // 在 NewsDetail 和 SpecialReportDetail 頁面隱藏 FloatingChat，因為這些頁面有自己的聊天室
  const shouldHideFloatingChat = location.pathname.includes('/news/') || 
                                location.pathname.match(/\/special-report\/[^/]+$/); // 只匹配 /special-report/id 不匹配 /special-reports
  
  return (
    <div className="app">
      <Header />
      <main className="mainContent">
        <Outlet />
      </main>
      {!shouldHideFloatingChat && <FloatingChat />}
    </div>
  );
}

// 首頁組件
function HomePage() {
  const { t } = useTranslation();
  const { selectedCountry } = useCountry();
  
  // 國家 ID 對應到 dbName
  const countryMap = {
    'taiwan': 'Taiwan',
    'usa': 'United States of America',
    'japan': 'Japan',
    'indonesia': 'Indonesia'
  };
  
  const currentCountryDbName = countryMap[selectedCountry] || 'Taiwan';
  
  return (
    <>
      <FocusNews />
      <div className="contentGrid news-section-overlap">
        <div className="mainColumn">
          <h2 className="sectionTitle">
            {t('home.latestNews')}
          </h2>
          <UnifiedNewsCard instanceId="main_news_list" country={currentCountryDbName} showLoadMore={true} />
        </div>
      </div>
    </>
  );
}

function App() {
  return (
    <QueryProvider>
      <SupabaseProvider>
        <AuthProvider>
          <CountryProvider>
            <Router>
              <Routes>
                {/* 登入頁面 - 不需要保護 */}
                <Route path="/login" element={<LoginPage />} />
                
                {/* 根路由重定向到預設語言 */}
                <Route path="/" element={<Navigate to="/zh-TW/" replace />} />
                
                {/* 管理後台路由 - 獨立介面 */}
                {/*<Route path="/admin/*" element={<AdminDashboard />} />*/}
                
                {/* 多語言路由 */}
                {["zh-TW", "en", "jp", "id"].map(lang => (
                  <Route key={`redirect-${lang}`} path={`/${lang}`} element={<Navigate to={`/${lang}/`} replace />} />
                ))}
                
                {/* 所有內容頁面都需要登入保護 */}
                {["zh-TW", "en", "jp", "id"].map(lang => (
                  <Route 
                    key={lang} 
                    path={`/${lang}`} 
                    element={
                      <ProtectedRoute>
                        <LanguageLayout />
                      </ProtectedRoute>
                    }
                  >
                    <Route index element={<HomePage />} />
                    <Route path="news/:id" element={<NewsDetail />} />
                    <Route path="keyword/:keyword" element={<KeywordNewsPage />} />
                    <Route path="search/:query" element={<SearchResultsPage />} />
                    
                    {/* 國家路由 - 顯示該國所有新聞 */}
                    <Route path="category/Taiwan" element={<CategorySection country="Taiwan" />} />
                    <Route path="category/United States of America" element={<CategorySection country="USA" />} />
                    <Route path="category/Japan" element={<CategorySection country="Japan" />} />
                    <Route path="category/Indonesia" element={<CategorySection country="Indonesia" />} />
                    
                    {/* 國家+類別路由 - 顯示該國特定類別的新聞 */}
                    <Route path="category/Taiwan/:categoryName" element={<CategorySection country="Taiwan" />} />
                    <Route path="category/United States of America/:categoryName" element={<CategorySection country="USA" />} />
                    <Route path="category/Japan/:categoryName" element={<CategorySection country="Japan" />} />
                    <Route path="category/Indonesia/:categoryName" element={<CategorySection country="Indonesia" />} />
                    
                    <Route path="special-reports" element={<TaiwanOnlyRoute><SpecialReportPage /></TaiwanOnlyRoute>} />
                    <Route path="special-report/:id" element={<TaiwanOnlyRoute><SpecialReportDetail /></TaiwanOnlyRoute>} />
                    <Route path="focus-news" element={<YesterdayFocus />} />
                    <Route path="abroad" element={<AbroadNewsPage />} />
                  </Route>
                ))}
              </Routes>
            </Router>
          </CountryProvider>
        </AuthProvider>
      </SupabaseProvider>
    </QueryProvider>
  );
}

export default App;
