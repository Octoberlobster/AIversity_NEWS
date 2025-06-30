import React, { useState } from 'react';
import Header from './Header';
// 引入更新後的組件
// import NewsCategory from './News_category';
import NewsProject from './NewsProject'; 
import NonNewsProject from './NonNewsProject';
import './css/EventList.css'; // 確保引入了樣式文件

function App() {
  const [activeView, setActiveView] = useState('news');

  return (
    <div className="app-container">
      <Header />

      <nav className="view-switcher">
        <button
          className={activeView === 'news' ? 'active' : ''}
          onClick={() => setActiveView('news')}
        >
          新聞專題
        </button>
        <button
          className={activeView === 'other' ? 'active' : ''}
          onClick={() => setActiveView('other')}
        >
          非新聞專題
        </button>
      </nav>

      <main className="main-content">
        {/* 使用更新後的組件名稱進行條件渲染 */}
        {activeView === 'news' ? <NewsProject /> : <NonNewsProject />}
      </main>
    </div>
  );
}

export default App;
