import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { createClient} from '@supabase/supabase-js';
import './main.css';
import TimelineAnalysis from './TimelineAnalysis';
import ChatRoom from './ChatRoom';
import ScenarioSetup from './ScenarioSetup';
import ScenarioChatRoom from './ScenarioChatRoom';
import newsData from './News.json';
import rolesData from './Roles.json';
import roleAnalyzes from './NewsAnalyze.json';
import translateIcon from './Translate.png'

function App() {
  const [selectedRole, setSelectedRole] = useState(''); // 預設選擇第一個角色
  const [chatHistories, setChatHistories] = useState({});
  const [language, setLanguage] = useState('zh');
  const [mode, setMode] = useState('interactive');      // 'interactive' | 'scenario'
  const [scenarioCfg, setScenarioCfg] = useState(null); // {scenario, roles}
  
  const roles = rolesData.Roles.map(role => role.Role);
  const navigate = useNavigate();

  // --- 2. 初始化 Supabase client
  /*
  const supabaseUrl   = process.env.REACT_APP_SUPABASE_URL;
  const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
  console.log('supabaseUrl=', supabaseUrl);
  console.log('supabaseAnonKey=', supabaseAnonKey);
  const supabase = createClient(supabaseUrl, supabaseAnonKey);
  */

  useEffect(() => {
    const savedHistories = localStorage.getItem('all_chat_histories');
    if (savedHistories) {
      setChatHistories(JSON.parse(savedHistories));
    }
  }, []);

  useEffect(() => {
    if (
      selectedRole &&
      chatHistories[selectedRole] === undefined
    ) {
      const analysis =
        roleAnalyzes[selectedRole]?.Analyze || '（暫無分析文字）';
  
      updateChatHistory(selectedRole, [
        { sender: 'SYSTEM', text: `你正在與【${selectedRole}】對話。` },
        { sender: selectedRole, text: analysis }
      ]);
    }
  }, [selectedRole, chatHistories]);   // chatHistories 也要放依賴，才抓得到最新狀態

  const updateChatHistory = (role, messages) => {
    setChatHistories(prev => ({
      ...prev,
      [role]: messages
    }));
  };

  useEffect(() => {
    if (Object.keys(chatHistories).length > 0) {
      localStorage.setItem(
        'all_chat_histories',
        JSON.stringify(chatHistories)
      );
    }
  }, [chatHistories]);

  const getSelectedRoleAnalyze = () => {
    return selectedRole ? roleAnalyzes[selectedRole]?.Analyze : null;
  };

  const handleLanguageChange = (e) => {
    const selectedLanguage = e.target.value;
    setLanguage(selectedLanguage);
    
    if (selectedLanguage === 'tw') {
      navigate('/tw');
    } else if (selectedLanguage === 'zh') {
      navigate('/');
    }
  };

  return (
    <div className="container">
      <div className="header-bar">
        <div className="platform-name">
          <span></span>
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
          <h3 className="right-panel-title">角色聊天室</h3>
          <div className="divider"></div>
          <div className="dropdown-container">
          <select
            value={mode}
            onChange={e => {
              setMode(e.target.value);
              setScenarioCfg(null);      // 切模式就重置
            }}
            >
              <option value="interactive">互動模式</option>
              <option value="scenario">情境模擬模式</option>
            </select>
            {mode === 'interactive' && (
              <div className="dropdown-container">
                <select
                  value={selectedRole}
                  onChange={e => setSelectedRole(e.target.value)}
                >
                  <option value="" disabled>選擇角色</option>
                  {roles.map((role, index) => (
                    <option key={index} value={role}>{role}</option>
                  ))}
                </select>
              </div>
            )}
          </div>    
          {mode === 'interactive' ? (
            /* ------- 互動模式 ------- */
            selectedRole ? (
              /* 已選角色 → 顯示聊天室 */
              <ChatRoom
                selectedRole={selectedRole}
                messages={chatHistories[selectedRole] || []}
                updateMessages={updateChatHistory}
                roleAnalyze={getSelectedRoleAnalyze()}
              />
            ) : (
              /* 尚未選角色 → 顯示提示文字 */
              <p style={{ textAlign: 'center', marginTop: '1rem', color: '#666' }}>
                請先從上方下拉選擇一位角色…
              </p>
            )
          ) : (
            /* ------- 情境模擬模式 ------- */
            scenarioCfg ? (
              <ScenarioChatRoom
                scenario={scenarioCfg.scenario}
                roles={scenarioCfg.roles}
                onReset={() => setScenarioCfg(null)}
              />
            ) : (
              <ScenarioSetup
                allRoles={roles}
                onStart={cfg => setScenarioCfg(cfg)}
              />
            )
          )}
        </div>
      </div>
      <TimelineAnalysis />
    </div>
  );
}

export default App;
