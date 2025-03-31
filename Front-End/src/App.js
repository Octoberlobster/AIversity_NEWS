import React, { useState, useEffect } from 'react'; // 引入React核心庫和鉤子函數
import './main.css';  // 引入主要CSS樣式
import TimelineAnalysis from './TimelineAnalysis';  // 引入時間軸分析組件
import ChatRoom from './ChatRoom';  // 引入聊天室組件
import newsData from './News.json'; // 引入新聞數據JSON文件
import rolesData from './Roles.json'; // 引入角色數據JSON文件
import roleAnalyzes from './NewsAnalyze.json';  // 引入角色分析數據JSON文件

function App() {
  
  const [selectedRole, setSelectedRole] = useState(''); // 狀態管理：當前選擇的角色
  const [chatHistories, setChatHistories] = useState({}); // 狀態管理：所有角色的聊天歷史記錄
  const roles = rolesData.Roles.map(role => role.Role); // 從角色數據中提取所有角色名稱

  // 副作用：應用啟動時清除localStorage中的聊天歷史
  useEffect(() => {
    localStorage.removeItem('all_chat_histories');
    console.log('已清除聊天歷史記錄');
  }, []); // 空依賴數組確保只在首次渲染時執行一次

  // 副作用：應用初始化時嘗試從localStorage加載聊天歷史
  useEffect(() => {
    const savedHistories = localStorage.getItem('all_chat_histories');
    if (savedHistories) {
      // 如果找到保存的聊天歷史，則解析JSON並更新狀態
      setChatHistories(JSON.parse(savedHistories));
    }
  }, []); // 空依賴數組確保只在首次渲染時執行一次

  // 副作用：當聊天歷史更新時，將其保存到localStorage
  useEffect(() => {
    if (Object.keys(chatHistories).length > 0) {
      // 只有當有聊天歷史時才保存
      localStorage.setItem('all_chat_histories', JSON.stringify(chatHistories));
    }
  }, [chatHistories]); // 依賴於chatHistories，當它變化時執行

  // 處理角色選擇變更的函數
  const handleRoleChange = (e) => {
    setSelectedRole(e.target.value);
  };

  // 更新特定角色聊天歷史的函數
  const updateChatHistory = (role, messages) => {
    setChatHistories(prev => ({
      ...prev, // 保留其他角色的聊天歷史
      [role]: messages // 更新指定角色的聊天歷史
    }));
  };

  // 獲取選定角色的分析文本
  const getSelectedRoleAnalyze = () => {
    // 如果有選定角色且該角色在分析數據中存在，則返回其分析文本
    return selectedRole ? roleAnalyzes[selectedRole]?.Analyze : null;
  };

  return (
    <div className="container">
      <div className="header-bar"></div>         {/* 頁面頂部的藍色條 */}
      <div className="content">
        <div className="left-panel">        {/* 左側面板：顯示新聞內容 */}
          <h2 className="panel-title">{newsData.Title}</h2>          {/* 新聞標題 */}
          <p className="panel-date">發布日期：{newsData.Date}</p>          {/* 新聞發布日期 */}
          <div className="panel-content">          {/* 新聞內容，按段落分割並渲染 */}
            {newsData.Content.split('\n\n').map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </div>
        </div>
        

        <div className="right-panel">        {/* 右側面板：角色選擇和聊天室 */}
          <h3 className="right-panel-title">多觀點新聞分析討論室</h3>          {/* 面板標題 */}
          <div className="divider"></div>          {/* 分隔線 */}
          <div className="dropdown-container">          {/* 角色選擇下拉選單 */}
            <select 
              className="role-dropdown"
              value={selectedRole}
              onChange={handleRoleChange}
            >
              <option value="" disabled>選擇角色</option>
              {/* 動態生成角色選項 */}
              {roles.map((role, index) => (
                <option key={index} value={role}>{role}</option>
              ))}
            </select>
          </div>
          
          {/* 只有當選擇了角色時才顯示聊天室 */}
          {selectedRole && (
            <>
              {/* 聊天室組件 */}
              <ChatRoom 
                selectedRole={selectedRole} // 傳遞選定的角色
                messages={chatHistories[selectedRole] || []} // 傳遞該角色的聊天歷史，如果沒有則傳空數組
                updateMessages={(newMessages) => updateChatHistory(selectedRole, newMessages)} // 傳遞更新聊天歷史的函數
                roleAnalyze={getSelectedRoleAnalyze()} // 傳遞角色分析文本
              />
            </>
          )}
        </div>
      </div>
      {/* 時間軸分析組件 */}
      <TimelineAnalysis />
    </div>
  );
}

export default App;
