import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef, useCallback } from 'react';
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

// 輔助函數：安全地解析 who_talk
const parseWhoTalk = (whoTalk) => {
  if (!whoTalk) return [];
  
  if (Array.isArray(whoTalk)) {
    return whoTalk;
  }
  
  if (typeof whoTalk === 'string') {
    try {
      const parsed = JSON.parse(whoTalk);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.error('Error parsing who_talk JSON:', error);
      return [];
    }
  }
  
  // 如果是物件，可能有嵌套的結構
  if (typeof whoTalk === 'object' && whoTalk !== null) {
    // 如果是 {who_talk: [...]} 的格式
    if (whoTalk.who_talk && Array.isArray(whoTalk.who_talk)) {
      return whoTalk.who_talk;
    }
  }
  
  return [];
};

function ChatRoom({newsData, onClose}, ref) {
  const [selectedExperts, setSelectedExperts] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  
  // 溯源驗證相關狀態
  const [proofMessages, setProofMessages] = useState([]);
  const [showProofMode, setShowProofMode] = useState(false);

  const messagesEndRef = useRef(null);
  const proofMessagesEndRef = useRef(null);
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);

  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  // 暴露給父組件的方法
  useImperativeHandle(ref, () => ({
    addFactCheckMessage: (message) => {
      setProofMessages((prev) => [...prev, message]);
      setShowProofMode(true); // 自動切換到溯源驗證模式
    },
    resetToChat: () => {
      setShowProofMode(false);
    }
  }), []);

  // 當切換回專家聊天模式時的處理
  useEffect(() => {
    // 目前只是監聽模式切換，不做額外處理
  }, [showProofMode]);

  // 當 newsData 改變時，清理不在 who_talk 範圍內的已選專家
  useEffect(() => {
    const whoTalkArray = parseWhoTalk(newsData?.who_talk);

    if (whoTalkArray.length > 0) {
      setSelectedExperts(prevSelected => {
        const validExperts = prevSelected.filter(expertId => {
          const expert = experts.find(e => e.id === expertId);
          return expert && whoTalkArray.includes(expert.category);
        });
        return validExperts;
      });
    }
  }, [newsData?.who_talk]);

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

  const changeQuickPrompt = useCallback(async (chat_content = '') => {
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
    
  }, [selectedExperts, user_id, room_id, newsData.long]);

  // 點擊外部關閉下拉
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setIsDropdownOpen(false);
    };
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isDropdownOpen]);

  //讓一開始就有提示字可以用
  useEffect(() => {
    if (selectedExperts.length > 0) {
      changeQuickPrompt();
    }
  }, [selectedExperts, changeQuickPrompt]);

  // 等待 category 傳遞後初始化 selectedExperts
  useEffect(() => {
    if (newsData.category) {
      const filteredExperts = experts
        .filter((expert) => expert.category === newsData.category)
        .map((expert) => expert.id);
      setSelectedExperts(filteredExperts);
      setMessages(["歡迎使用新聞小幫手，在這你可以同時詢問多位不同領域的專家，利用快速提示幫助你展開第一個話題，運用溯源驗證來證實新聞內容並非虛言。"].map(text => ({
        id: Date.now() + Math.random(),
        text,
        isOwn: false,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
      }))); 
    }
  }, [newsData.category]);

  const toggleExpert = (id) => {
    setSelectedExperts((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    changeQuickPrompt();
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
    // 直接處理發送，不依賴狀態更新
    if (!promptText.trim()) return;
    
    // 如果沒有選擇專家，提醒用戶
    if (selectedExperts.length === 0) {
      alert('請先選擇至少一位專家來回答您的問題');
      return;
    }
    
    // 添加用戶訊息
    setMessages((prev) => [...prev, makeUserMsg(promptText)]);
    
    // 設置輸入框內容（顯示用）
    setInputMessage('');
    
    // 模擬專家回覆
    simulateRepliesWithPrompt(promptText);
  };

  const simulateRepliesWithPrompt = async (promptText) => {
    try {
      // 構建請求的資料
      const categories = selectedExperts.map(
        (expertId) => experts.find((e) => e.id === expertId).category
      );
  
      // 呼叫後端 API
      const response = await fetchJson('/chat/single', {
        user_id: user_id,
        room_id: room_id,
        prompt: promptText,
        category: categories,
        article: newsData.long,
      });
  
      // 處理後端回傳的回覆
      response.response.forEach((reply, index) => {
        setTimeout(() => {
          const expertId = selectedExperts[index];
          const expertReply = makeExpertReply(expertId);
          expertReply.text = `${experts.find((e) => e.id === expertId).name}：${reply.chat_response}`;

          setMessages((prev) => [...prev, expertReply]);
        }, 1000 + index * 500);
      });

      // 格式化專家回覆為 "類別:回答"
      const formattedReplies = response.response.map((reply, index) => {
        const category = categories[index];
        return `${category}: ${reply.chat_response}`;
      });

      // 呼叫 changeQuickPrompt，傳入格式化的回覆
      changeQuickPrompt(`user:${promptText} ${formattedReplies.join(" ")}`);
    } catch (error) {
      console.error('Error fetching expert replies:', error);
    }
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;
    
    // 如果沒有選擇專家，提醒用戶
    if (selectedExperts.length === 0) {
      alert('請先選擇至少一位專家來回答您的問題');
      return;
    }
    
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
          {/* 關閉聊天室按鈕 - 採用FloatingChat樣式 */}
          {onClose && (
            <button 
              className="chat-close-btn"
              onClick={onClose}
              title="關閉聊天室"
            >
              ✕
            </button>
          )}
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
                {experts
                  .filter(expert => {
                    const whoTalkArray = parseWhoTalk(newsData?.who_talk);
                    
                    // 如果沒有有效的 who_talk 資料，顯示所有專家
                    if (whoTalkArray.length === 0) {
                      return true;
                    }
                    
                    return whoTalkArray.includes(expert.category);
                  })
                  .map((expert) => {
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
          
          <button className="proofButton proofButton--inline" onClick={handleProofButtonClick}>
            🔍 溯源驗證
          </button>
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
        {!showProofMode && quickPrompts.length > 0 && selectedExperts.length > 0 && (
          <div className="prompt__container">
            {quickPrompts.map((p, i) => (
              <button
                key={i}
                type="button"
                className="prompt__item"
                onClick={() => handlePromptSend(p)}
              >
                {p}
              </button>
            ))}
          </div>
        )}
        
        
      </div>

      {!showProofMode && (
        <div className="input">
          <input
            ref={inputRef}
            type="text"
            className="input__text"
            placeholder={selectedExperts.length === 0 ? "請先選擇專家..." : "輸入您的問題..."}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            onKeyDown={(e) => {
              // 手動處理輸入，因為 onChange 在某些情況下不工作
              if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
                e.preventDefault();
                const currentValue = e.target.value;
                const newValue = currentValue + e.key;
                setInputMessage(newValue);
              } else if (e.key === 'Backspace') {
                e.preventDefault();
                const currentValue = e.target.value;
                const newValue = currentValue.slice(0, -1);
                setInputMessage(newValue);
              }
            }}
            autoComplete="off"
            spellCheck="false"
          />
          <button
            className="input__send"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim()}
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