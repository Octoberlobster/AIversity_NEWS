import React, { useState, useEffect } from 'react';
import ChatRoom from './ChatRoom';
import ScenarioSetup from './ScenarioSetup';
import ScenarioChatRoom from './ScenarioChatRoom';
import './css/ChatRoom.css';
import rolesData from './Roles.json';
import roleAnalyzes from './NewsAnalyze.json';

function ChatSection({eventId}) {

    const [selectedRole, setSelectedRole] = useState(''); // 預設選擇第一個角色
    const [chatHistories, setChatHistories] = useState({});
    const [mode, setMode] = useState('interactive');      // 'interactive' | 'scenario'
    const [scenarioCfg, setScenarioCfg] = useState(null); // {scenario, roles}
    const roles = rolesData.Roles.map(role => role.Role);

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

    return (
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
    );
}

export default ChatSection;