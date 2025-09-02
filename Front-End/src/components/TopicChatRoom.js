import { useState, useRef, useEffect,useCallback } from 'react';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { fetchJson } from './api';
import './../css/TopicChatRoom.css';
import ReactMarkdown from 'react-markdown';


function TopicChatRoom({topic_id,topic_title}){
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isPromptDropdownOpen, setIsPromptDropdownOpen] = useState(false);
  const [quickPrompts, setQuickPrompts] = useState([]);
  
  const promptDropdownRef = useRef(null);
  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  // 點擊外部關閉下拉
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (promptDropdownRef.current && !promptDropdownRef.current.contains(e.target)) {
        setIsPromptDropdownOpen(false);
      }
    };
    if (isPromptDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isPromptDropdownOpen]);

  const loadQuickPrompts = useCallback(async (chat_content = '') => {
    const fixedPrompts = [
      "「" + topic_title + "」近期有什麼更新",
      "「" + topic_title + "」提供甚麼內容？",
      "你對於「" + topic_title + "」有什麼看法？"
    ]; // 固定的 prompt

    try {
      const response = await fetchJson('/hint_prompt/topic', {
        topic_id: topic_id,
        room_id: room_id,
        user_id: user_id,
        chat_content: chat_content
      });
      console.log('Fetched quick prompts:', response);

      // 合併固定 prompt 和後端返回的 prompt
      setQuickPrompts([...(response.Hint_Prompt || []), ...fixedPrompts]);
    } catch (error) {
      console.error('Error loading quick prompts:', error);

      // 如果發生錯誤，僅保留固定的 prompt
      setQuickPrompts([
        "專家如何看待這個議題？",
        "這個專題的未來發展趨勢",
        ...fixedPrompts,
      ]);
    }
  }, [topic_id, topic_title]);

  useEffect(() => {
    loadQuickPrompts();
  }, [loadQuickPrompts]); // 現在可以安全地添加 loadQuickPrompts 作為依賴

  const handlePromptSend = (promptText) => {
    setChatInput(promptText);
    setIsPromptDropdownOpen(false);
    // 自動發送訊息
    setTimeout(() => {
      handleSendMessage();
    }, 100);
  };

  const fetchResponse = async () => {
    try {
      const response = await fetchJson('/chat/topic', {
        topic_id: topic_id,
        room_id: room_id,
        user_id: user_id,
        prompt: chatInput,
      });
      console.log(response);
      return response;
    } catch (error) {
      console.error('Error fetching response:', error);
    }
  };

  const handleSendMessage = () => {
    if (!chatInput.trim()) return;

    const userMsg = {
      id: Date.now(),
      text: chatInput,
      isOwn: true,
      time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');

    fetchResponse().then((response) => {
      setTimeout(() => {
        const reply = {
          id: Date.now() + 1,
          text: response.response[0].chat_response,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
        };
        setChatMessages((prev) => [...prev, reply]);
      }, 1000);
      loadQuickPrompts("user:" + chatInput + " assistant:" + response.response[0].chat_response);
    });
  };


  const handleKeyPress = (e) => {
  if (e.key === 'Enter') handleSendMessage();
  };

  return (
    <div className="modern-chat-container">
      {/* 歡迎區域 */}
      <div className="chat-welcome">
        <div className="chat-welcome-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" 
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="chat-welcome-text">
          <h3>專題討論</h3>
          <p>與AI助手討論這個專題的相關議題</p>
        </div>
      </div>

      {/* 聊天訊息區域 */}
      <div className="chat-messages-container">
        <div className="chat-messages">
          {chatMessages.length === 0 ? (
            <div className="welcome-message">
              <div className="welcome-bubble">
                <p>👋 歡迎討論「{topic_title}」這個專題！</p>
                <p>您可以詢問任何相關問題。</p>
              </div>
            </div>
          ) : (
            chatMessages.map((message) => (
              <div key={message.id} className={`message ${message.isOwn ? 'user' : 'ai'}`}>
                <div className="message-bubble">
                  <ReactMarkdown>{message.text}</ReactMarkdown>
                  <span className="message-time">{message.time}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 快速提示按鈕 - 下拉選單方式 */}
      <div className="chat-quick-actions">
        <div className="prompt-dropdown-wrapper" ref={promptDropdownRef}>
          <button
            type="button"
            className="prompt-dropdown-btn"
            onClick={() => setIsPromptDropdownOpen(!isPromptDropdownOpen)}
          >
            <span>💡 快速提示</span>
            <span className={`dropdown-icon ${isPromptDropdownOpen ? 'is-open' : ''}`}>▼</span>
          </button>

          {isPromptDropdownOpen && (
            <div className="prompt-dropdown-menu">
              {quickPrompts.map((prompt, index) => (
                <div 
                  key={index} 
                  className="prompt-dropdown-item" 
                  onClick={() => handlePromptSend(prompt)}
                >
                  {prompt}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 輸入區域 */}
      <div className="chat-input-container">
        <div className="input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder="輸入您的問題或觀點..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button
            className="send-button"
            onClick={handleSendMessage}
            disabled={!chatInput.trim()}
            title="發送訊息"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}


export default TopicChatRoom;