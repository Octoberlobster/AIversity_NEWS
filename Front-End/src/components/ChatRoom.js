import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import { getOrCreateUserId, createRoomId } from './utils.js';
import ReactMarkdown from 'react-markdown';
import { fetchJson } from './api';
import './../css/ChatRoom.css';

const experts = [
  { id: 1, name: "政治專家", category: "Politics" },
  { id: 2, name: "台灣議題分析師", category: "Taiwan News" },
  { id: 3, name: "國際專家", category: "International News" },
  { id: 4, name: "科技專家", category: "Science & Technology" },
  { id: 5, name: "生活達人", category: "Lifestyle & Consumer News" },
  { id: 6, name: "體育專家", category: "Sports" },
  { id: 7, name: "娛樂專家", category: "Entertainment" },
  { id: 8, name: "財經專家", category: "Business & Finance" },
  { id: 9, name: "健康顧問", category: "Health & Wellness" },
];

const expertReplies = {};

// 快速提示
const quickPrompts = [];

function ChatRoom({newsData}, ref) {
  const [selectedExperts, setSelectedExperts] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isPromptDropdownOpen, setIsPromptDropdownOpen] = useState(false);
  
  // 溯源驗證相關狀態
  const [proofMessages, setProofMessages] = useState([]);
  const [showProofMode, setShowProofMode] = useState(false);

  const messagesEndRef = useRef(null);
  const proofMessagesEndRef = useRef(null);
  const dropdownRef = useRef(null);
  const promptDropdownRef = useRef(null);

  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  // 暴露給父組件的方法
  useImperativeHandle(ref, () => ({
    addFactCheckMessage: (message) => {
      setProofMessages((prev) => [...prev, message]);
      setShowProofMode(true); // 自動切換到溯源驗證模式
    }
  }), []);

  // 自動滾到最底
  useEffect(() => {
    if (messagesEndRef.current && !showProofMode) {
      const container = messagesEndRef.current.closest('[data-messages-container]');
      if (container) {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
      }
    }
    if (proofMessagesEndRef.current && showProofMode) {
      const container = proofMessagesEndRef.current.closest('[data-proof-container]');
      if (container) {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
      }
    }
  }, [messages, proofMessages, showProofMode]);

  // 點擊外部關閉下拉
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setIsDropdownOpen(false);
      if (promptDropdownRef.current && !promptDropdownRef.current.contains(e.target)) setIsPromptDropdownOpen(false);
    };
    if (isDropdownOpen || isPromptDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isDropdownOpen, isPromptDropdownOpen]);

  //讓一開始就有提示字可以用
  useEffect(() => {
    changeQuickPrompt();
  }, [selectedExperts]);

  // 等待 category 傳遞後初始化 selectedExperts
  useEffect(() => {
    if (newsData.category) {
      const filteredExperts = experts
        .filter((expert) => expert.category === newsData.category)
        .map((expert) => expert.id);
      setSelectedExperts(filteredExperts);
    }
  }, [newsData.category]);

  const toggleExpert = (id) => {
    setSelectedExperts((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    changeQuickPrompt();
  };

  const changeQuickPrompt = async (chat_content = '') => {
    try{
      const options = selectedExperts.map(
        (expertId) => experts.find((e) => e.id === expertId).category
      );

      const response = await fetchJson('/hint_prompt/single', {
        option : options,
        user_id: user_id,
        room_id: room_id,
        article: newsData.long,
        chat_content: chat_content,
      });
      quickPrompts.length = 0; // 清空之前的提示
      console.log('Fetched quick prompts:', response);
      response.Hint_Prompt.forEach((prompt) => {
        quickPrompts.push(prompt);
      });      
      console.log('Updated quick prompts:', quickPrompts);
    } catch (error) {
      console.error('Error updating quick prompts:', error);
    }
    
  };

  const makeUserMsg = (text) => ({
    id: Date.now(),
    text,
    isOwn: true,
    time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
  });

  const makeExpertReply = (expertId) => {
    const expert = experts.find((e) => e.id === expertId);
    return {
      id: Date.now() + expertId,
      text: `${expert.name}：${expertReplies[expertId]}`,
      isOwn: false,
      time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
    };
  };

  const simulateReplies = async () => {
    try {
      // 構建請求的資料
      const categories = selectedExperts.map(
        (expertId) => experts.find((e) => e.id === expertId).category
      );
  
      // 呼叫後端 API
      const response = await fetchJson('/chat/single', {
        user_id: user_id,
        room_id: room_id,
        prompt: inputMessage,
        category: categories,
        article: newsData.long,
      });
  
      // 處理後端回傳的回覆
      response.response.forEach((reply, index) => {
        setTimeout(() => {
          const expertId = selectedExperts[index]; // 根據順序匹配專家 ID
          const expertReply = makeExpertReply(expertId); // 使用 makeExpertReply 生成回覆
          expertReply.text = `${experts.find((e) => e.id === expertId).name}：${reply.chat_response}`; // 更新回覆內容

          setMessages((prev) => [...prev, expertReply]);
        }, 1000 + index * 500); // 模擬延遲
      });

      // 格式化專家回覆為 "類別:回答"
      const formattedReplies = response.response.map((reply, index) => {
        const category = categories[index];
        return `${category}: ${reply.chat_response}`;
      });

      // 呼叫 changeQuickPrompt，傳入格式化的回覆
      changeQuickPrompt(`user:${inputMessage} ${formattedReplies.join(" ")}`);
    } catch (error) {
      console.error('Error fetching expert replies:', error);
    }
  };


  const handlePromptSend = (promptText) => {
    setInputMessage(promptText);
    handleSendMessage();
    setIsPromptDropdownOpen(false);
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim() || selectedExperts.length === 0) return;
    setMessages((prev) => [...prev, makeUserMsg(inputMessage)]);
    setInputMessage('');
    simulateReplies();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSendMessage();
  };

  const handleProofButtonClick = async () => {
    try {
      const response = await fetchJson('/proof/single_news', {
        story_id: newsData.story_id,
      });

      // Format the response into a more structured format
      let formattedResponse = "### 📋 新聞內容溯源驗證報告\n\n";
      
      if (response && response.length > 0) {        
        response.forEach((item, index) => {
          formattedResponse += `#### 📖 內容片段 ${index + 1}\n`;
          formattedResponse += `**原文：** ${item.sentence}\n\n`;
          
          if (item.source && item.source.length > 0) {
            formattedResponse += `**📚 相關來源：**\n`;
            item.source.forEach((src, srcIndex) => {
              formattedResponse += `${srcIndex + 1}. **[${src.title}](${src.url})** *來源：${src.media}*\n`;
            });
          } else {
            formattedResponse += `<div class="verification-status warning">⚠️ 此片段暫無找到相關來源</div>\n`;
          }
          
          formattedResponse += "\n---\n\n";
        });
        
        formattedResponse += "**💡 說明：** 以上資料來自系統自動比對，建議進一步查證確認。\n";
      } else {
        formattedResponse += `<div class="verification-status error">❌ 查無相關來源資料</div>\n\n`;
        formattedResponse += "**建議：** 請檢查新聞來源的可信度或嘗試其他查證方式。\n";
      }

      // Add the formatted response to the proof messages container
      setProofMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: formattedResponse,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      
      // Switch to proof mode to show the verification results
      setShowProofMode(true);
    } catch (error) {
      console.error('Error fetching proof data:', error);
      
      const errorMessage = `### ❌ 溯源驗證失敗\n\n<div class="verification-status error">系統錯誤</div>\n\n**錯誤原因：** 無法連接到驗證服務\n\n**建議：** 請稍後再試或聯繫系統管理員`;
      
      setProofMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: errorMessage,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setShowProofMode(true);
    }
  };

  return (
    <div className="chat">
      <div className="chat__header">
        <div className="chat__headerLeft">
          <div className="chat__icon">🤖</div>
          <div>
            <h3 className="chat__title">
              {showProofMode ? "溯源驗證結果" : "AI 專家討論室"}
            </h3>
            <p className="chat__subtitle">
              {showProofMode ? "新聞內容溯源查核" : `${selectedExperts.length} 位專家在線`}
            </p>
          </div>
        </div>
        <div className="chat__headerRight">
          <button
            className={`mode-toggle ${showProofMode ? 'proof-mode' : 'chat-mode'}`}
            onClick={() => setShowProofMode(!showProofMode)}
          >
            {showProofMode ? "📊 專家聊天" : "🔍 溯源驗證"}
          </button>
        </div>
      </div>

      {!showProofMode && (
        <div className="chat__expertSelector">
          <div className="dropdown" ref={dropdownRef}>
            <button
              type="button"
              className="dropdown__btn"
              onClick={() => setIsDropdownOpen((v) => !v)}
            >
              <span>選擇專家</span>
              {selectedExperts.length > 0 && <span className="selectedCount">{selectedExperts.length}</span>}
              <span className={`dropdown__icon ${isDropdownOpen ? 'is-open' : ''}`}>▼</span>
            </button>

            {isDropdownOpen && (
              <div className="dropdown__menu">
                {experts.map((expert) => {
                  const checked = selectedExperts.includes(expert.id);
                  return (
                    <div
                      key={expert.id}
                      className="dropdown__item"
                      onClick={() => toggleExpert(expert.id)}
                    >
                      <span>{expert.name}</span>
                      <span className={`checkbox ${checked ? 'is-checked' : ''}`} />
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {!showProofMode ? (
        // 專家聊天室訊息區域
        <div className="messages" data-messages-container>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💬</div>
              <h3>歡迎來到 AI 專家討論室</h3>
              <p>選擇專家並開始討論吧！</p>
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className={`message ${m.isOwn ? 'message--own' : ''}`}>
              <div className={`bubble ${m.isOwn ? 'bubble--own' : ''}`}>
                <ReactMarkdown>{m.text}</ReactMarkdown>
              </div>
              <span className="time">{m.time}</span>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      ) : (
        // 溯源驗證結果區域
        <div className="messages proof-messages" data-proof-container>
          {proofMessages.length === 0 && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '3rem 2rem',
              color: '#64748b',
              textAlign: 'center',
              height: '100%'
            }}>
              <div style={{ 
                fontSize: '4rem', 
                marginBottom: '1.5rem',
                background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>🔍</div>
              <h3 style={{ 
                color: '#3b82f6', 
                marginBottom: '1rem',
                fontSize: '1.5rem',
                fontWeight: '600'
              }}>溯源驗證查核</h3>
              <p style={{ 
                color: '#64748b',
                fontSize: '1rem',
                lineHeight: '1.6',
                maxWidth: '400px'
              }}>點擊下方「🔍 溯源驗證」按鈕開始查核新聞內容的真實性和來源</p>
              <div style={{
                marginTop: '1.5rem',
                padding: '1rem',
                background: '#f8faff',
                borderRadius: '8px',
                border: '2px solid #e2e8f0',
                fontSize: '0.9rem',
                color: '#475569'
              }}>
                💡 系統將自動比對新聞內容與可信來源
              </div>
            </div>
          )}

          {proofMessages.map((m) => (
            <div key={m.id} className={`message ${m.isOwn ? 'message--own' : ''} proof-message`}>
              <div className={`bubble ${m.isOwn ? 'bubble--own' : 'bubble--proof'}`}>
                <ReactMarkdown>{m.text}</ReactMarkdown>
              </div>
              <span className="time">{m.time}</span>
            </div>
          ))}
          <div ref={proofMessagesEndRef} />
        </div>
      )}

      <div className="prompt">
        {!showProofMode && (
          <div className="prompt__wrap" ref={promptDropdownRef}>
            <button
              type="button"
              className="prompt__btn"
              onClick={() => setIsPromptDropdownOpen((v) => !v)}
              disabled={selectedExperts.length === 0}
            >
              <span>💡 快速提示</span>
              <span className={`prompt__icon ${isPromptDropdownOpen ? 'is-open' : ''}`}>▼</span>
            </button>

            {isPromptDropdownOpen && (
              <div className="prompt__menu">
                {quickPrompts.map((p, i) => (
                  <div key={i} className="prompt__item" onClick={() => handlePromptSend(p)}>
                    {p}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* 溯源驗證按鈕只在溯源驗證模式下顯示 */}
        {showProofMode && (
          <button className="proofButton" onClick={handleProofButtonClick}>
            溯源驗證
          </button>
        )}
      </div>

      {!showProofMode && (
        <div className="input">
          <input
            type="text"
            className="input__text"
            placeholder={selectedExperts.length === 0 ? "請先選擇專家..." : "輸入您的問題..."}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={selectedExperts.length === 0}
          />
          <button
            className="input__send"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || selectedExperts.length === 0}
          >
            ➤
          </button>
        </div>
      )}
    </div>
  );
}


// quickPrompts
export default forwardRef(ChatRoom);