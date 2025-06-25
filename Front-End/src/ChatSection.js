import React, { useState, useEffect } from 'react';
import ChatRoom from './ChatRoom';
import ScenarioSetup from './ScenarioSetup';
import ScenarioChatRoom from './ScenarioChatRoom';
import './css/ChatRoom.css';
import { useSupabase } from './supabase';

function ChatSection({eventId}) {
    const [selectedRole, setSelectedRole] = useState('');
    const [chatHistories, setChatHistories] = useState({});
    const [mode, setMode] = useState('interactive');
    const [scenarioCfg, setScenarioCfg] = useState(null);
    const [eventData, setEventData] = useState(null);
    const [roleData, setRoleData] = useState(null);
    const [newsText, setNewsText] = useState('');
    const [viewpoints, setViewpoints] = useState({});
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(true);

    const supabaseClient = useSupabase();
    localStorage.removeItem('all_chat_histories')

    // 加載事件數據
    useEffect(() => {
        const fetchEventData = async () => {
            try {
                setLoading(true);
                const { data, error } = await supabaseClient
                    .from('generated_news')
                    .select('*')
                    .eq('event_id', eventId)
                    .order('date', { ascending: false })
                    .limit(1);
                    
                if (error) throw error;
                
                if (data && data.length > 0) {
                    setEventData(data[0]);
                    setNewsText(data[0].content);
                    console.log("資料庫抓到新聞數據:", data[0]);
                } else {
                    console.log("找不到相關事件的新聞數據");
                }
            } catch (error) {
                console.error('Error fetching news data:', error);
            } finally {
                setLoading(false);
            }
        };
        
        if (eventId) {
            fetchEventData();
        }
    }, [eventId, supabaseClient]);

    // 加載角色數據，只有在 eventData 存在且有 generated_id 時執行
    useEffect(() => {
        const fetchRoleData = async () => {
            if (!eventData || !eventData.generated_id) return;
            
            try {
                setLoading(true);
                const { data, error } = await supabaseClient
                    .from('role_causal_analysis')
                    .select('*')
                    .eq('generated_id', eventData.generated_id);
                    
                if (error) throw error;
                
                if (data && data.length > 0) {
                    setRoleData(data);
                    const roleNames = data.map(item => item.role);
                    setRoles(roleNames);
                    const vp = {};
                    data.forEach(item => (vp[item.role] = item.analysis));
                    setViewpoints(vp);

                    console.log("資料庫抓到角色數據:", data);
                    console.log("角色名稱:", roleNames);
                } else {
                    console.log("找不到相關事件的角色分析數據");
                }
            } catch (error) {
                console.error('Error fetching role data:', error);
            } finally {
                setLoading(false);
            }
        };
        
        fetchRoleData();
    }, [eventData, supabaseClient]);

    // 載入聊天歷史
    useEffect(() => {
        const savedHistories = localStorage.getItem('all_chat_histories');
        if (savedHistories) {
            setChatHistories(JSON.parse(savedHistories));
        }
    }, []);

    // 初始化選擇角色的聊天
    useEffect(() => {
         if (!roleData) return;
         
         if (selectedRole && chatHistories[selectedRole] === undefined) {
            /* ① 取得分析文字 ------------------------------------ */
            let analysis = '（暫無分析文字）';

            const roleInfo = roleData.find(item => item.role === selectedRole);
            if (roleInfo) {
                analysis = roleInfo.analysis || analysis;
            }

            /* ② 準備「問候」與「分析」兩條訊息 ------------------ */
            const greetMsg = {
                sender: selectedRole,
                text: `你好，我是 ${selectedRole}，請問有什麼我可以幫助你的？`
            };

            // 把陣列分析轉成換行文字
            const anaText = Array.isArray(analysis) ? analysis.join('\n') : analysis;
            const anaMsg  = { sender: selectedRole, text: anaText };

            /* ③ 按固定順序寫入父層歷史 ------------------------- */
            updateChatHistory(selectedRole, [
                { sender: 'system', text: `您已選擇與「${selectedRole}」對話。` },
                greetMsg,
                anaMsg
            ]);
        }
    }, [selectedRole, chatHistories, roleData]);

    // 更新聊天歷史
    const updateChatHistory = (role, messages) => {
        setChatHistories(prev => ({
            ...prev,
            [role]: messages
        }));
    };

    // 保存聊天歷史到 localStorage
    useEffect(() => {
        if (Object.keys(chatHistories).length > 0) {
            localStorage.setItem(
                'all_chat_histories',
                JSON.stringify(chatHistories)
            );
        }
    }, [chatHistories]);

    // 獲取選定角色的分析文本
    const getSelectedRoleAnalyze = () => {
        if (!roleData || !selectedRole) return null;
        
        // 根據實際數據結構調整
        const roleInfo = roleData.find(item => item.role === selectedRole);
        return roleInfo ? roleInfo.analysis : null;
    };

    // 渲染加載狀態或錯誤信息
    if (loading) return <div className="loading">載入中...</div>;
    if (!eventData) return <div className="error">未找到新聞數據</div>;
    if (!roleData) return <div className="error">未找到角色數據</div>;

    return (
        <div className="right-panel">
            <h3 className="right-panel-title">角色聊天室</h3>
            <div className="divider"></div>
            <div className="dropdown-container">
                <select
                    value={mode}
                    onChange={e => {
                        setMode(e.target.value);
                        setScenarioCfg(null);
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
                selectedRole ? (
                    <ChatRoom
                        selectedRole={selectedRole}
                        messages={chatHistories[selectedRole] || []}
                        updateMessages={(messages) => updateChatHistory(selectedRole, messages)}
                        roleAnalyze={getSelectedRoleAnalyze()}
                        news={newsText}
                        viewpoints={viewpoints}
                    />
                ) : (
                    <p style={{ textAlign: 'center', marginTop: '1rem', color: '#666' }}>
                        請先從上方下拉選擇一位角色…
                    </p>
                )
            ) : (
                scenarioCfg ? (
                    <ScenarioChatRoom
                        scenario={scenarioCfg.scenario}
                        roles={scenarioCfg.roles}
                        onReset={() => setScenarioCfg(null)}
                        news={newsText}
                        viewpoints={viewpoints}
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
