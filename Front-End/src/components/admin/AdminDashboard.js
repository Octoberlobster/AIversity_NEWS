import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import StoriesManagement from './StoriesManagement';
import SingleNewsManagement from './SingleNewsManagement';
import TopicBranchNewsManagement from './TopicBranchNewsManagement';
import TopicNewsManagement from './TopicNewsManagement';
import './../../css/AdminDashboard.css';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('stories');
  const navigate = useNavigate();

  // 檢查管理員權限（可以後續擴展）
  useEffect(() => {
    // 這裡可以添加權限驗證邏輯
    console.log('管理後台已載入');
  }, []);

  const tabs = [
    { id: 'stories', label: 'Stories 管理', icon: '📰' },
    { id: 'single-news', label: 'Single News 管理', icon: '📝' },
    { id: 'topic-branch', label: '專題分支新聞管理', icon: '🌿' },
    { id: 'topic-events', label: '專題事件管理', icon: '🎯' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'stories':
        return <StoriesManagement />;
      case 'single-news':
        return <SingleNewsManagement />;
      case 'topic-branch':
        return <TopicBranchNewsManagement />;
      case 'topic-events':
        return <TopicNewsManagement />;
      default:
        return <StoriesManagement />;
    }
  };

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <div className="admin-header-content">
          <h1 className="admin-title">
            <span className="admin-icon">⚙️</span>
            AIversity News 管理後台
          </h1>
          <div className="admin-header-actions">
            <button 
              className="back-to-site-btn"
              onClick={() => navigate('/')}
            >
              返回前台
            </button>
          </div>
        </div>
      </header>

      <div className="admin-content">
        <nav className="admin-sidebar">
          <div className="admin-nav">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`admin-nav-item ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="nav-icon">{tab.icon}</span>
                <span className="nav-label">{tab.label}</span>
              </button>
            ))}
          </div>
        </nav>

        <main className="admin-main">
          <div className="admin-main-content">
            {renderTabContent()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;
