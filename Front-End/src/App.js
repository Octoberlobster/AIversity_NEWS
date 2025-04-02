import React, { useState, useEffect } from 'react';
import './main.css';
import TimelineAnalysis from './TimelineAnalysis';
import ChatRoom from './ChatRoom';
import newsData from './News.json';
import rolesData from './Roles.json';
import roleAnalyzes from './NewsAnalyze.json';
import translateIcon from './Translate.png'

function App() {
  const [selectedRole, setSelectedRole] = useState('');
  const [chatHistories, setChatHistories] = useState({});
  const [language, setLanguage] = useState('zh'); // 預設語言為中文
  const roles = rolesData.Roles.map(role => role.Role);

  // 副作用：應用啟動時清除localStorage中的聊天歷史
  useEffect(() => {
    localStorage.removeItem('all_chat_histories');
    console.log('已清除聊天歷史記錄');
  }, []);

  // 副作用：應用初始化時嘗試從localStorage加載聊天歷史
  useEffect(() => {
    const savedHistories = localStorage.getItem('all_chat_histories');
    if (savedHistories) {
      setChatHistories(JSON.parse(savedHistories));
    }
  }, []);

  // 副作用：當聊天歷史更新時，將其保存到localStorage
  useEffect(() => {
    if (Object.keys(chatHistories).length > 0) {
      localStorage.setItem('all_chat_histories', JSON.stringify(chatHistories));
    }
  }, [chatHistories]);

  const handleRoleChange = (e) => {
    setSelectedRole(e.target.value);
  };

  const updateChatHistory = (role, messages) => {
    setChatHistories(prev => ({
      ...prev,
      [role]: messages
    }));
  };

  const getSelectedRoleAnalyze = () => {
    return selectedRole ? roleAnalyzes[selectedRole]?.Analyze : null;
  };

  // 處理語言變更
  const handleLanguageChange = (e) => {
    setLanguage(e.target.value);
  };

  return (
    <div className="container">
      <div className="header-bar">
        <div className="platform-name">
          <span className="platform-logo">I</span>ntelexis
        </div>
        <div className="language-selector">
          <img src={translateIcon} alt="Translate" className="translate-icon" />
          <select 
            value={language}
            onChange={handleLanguageChange}
            className="language-dropdown"
          >
            <option value="zh">中文</option>
            <option value="tw">台語</option>
            <option value="en">English</option>
            <option value="ja">日本語</option>
            <option value="ko">한국어</option>
            <option value="vi">Tiếng Việt</option>
            <option value="th">ภาษาไทย</option>
            <option value="es">Español</option>
          </select>
        </div>
      </div>

      
      <div className="content">
        <div className="left-panel">
          <h2 className="panel-title">{newsData.Title}</h2>
          <p className="panel-date">發布日期：{newsData.Date}</p>
          <div className="panel-content">
            {newsData.Content.split('\n\n').map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </div>
        </div>
        
        <div className="right-panel">
          <h3 className="right-panel-title">多觀點新聞分析討論室</h3>
          <div className="divider"></div>
          <div className="dropdown-container">
            <select 
              className="role-dropdown"
              value={selectedRole}
              onChange={handleRoleChange}
            >
              <option value="" disabled>選擇角色</option>
              {roles.map((role, index) => (
                <option key={index} value={role}>{role}</option>
              ))}
            </select>
          </div>
          
          {selectedRole && (
            <>
              <ChatRoom 
                selectedRole={selectedRole}
                messages={chatHistories[selectedRole] || []}
                updateMessages={(newMessages) => updateChatHistory(selectedRole, newMessages)}
                roleAnalyze={getSelectedRoleAnalyze()}
              />
            </>
          )}
        </div>
      </div>
      <TimelineAnalysis />
    </div>
  );
}

export default App;
