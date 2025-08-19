import React, { useState, useRef, useEffect } from 'react';
import './../css/FloatingChat.css';
import { useLocation } from 'react-router-dom';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { fetchJson } from './api';

function FloatingChat() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [quickPrompts, setQuickPrompts] = useState([]);
  const messagesEndRef = useRef(null);
  const location = useLocation();
  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  // 滾動到底
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

    // Fetch quickPrompts 從後端獲取資料
  useEffect(() => {
    const fetchQuickPrompts = async () => {
      try {
        const response = await fetchJson('/hint_prompt/search', {});
        setQuickPrompts(response.Hint_Prompt || []);
      } catch (error) {
        console.error('Error fetching quick prompts:', error);
      }
    };

    fetchQuickPrompts();
  }, []);

  // 詳情頁不顯示
  const isSpecialReportPage = location.pathname.includes('/special-report/');
  const isNewsDetailPage = location.pathname.startsWith('/news/');
  if (isSpecialReportPage || isNewsDetailPage) return null;

  const toggleChat = () => setIsExpanded((v) => !v);

  const handleSendMessage = async () => {
    const text = newMessage.trim();
    if (!text) return;

    const now = new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });

    // 新增使用者訊息
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), text, isOwn: true, time: now },
    ]);
    setNewMessage('');

    try {
      // 呼叫後端 API
      const response = await fetchJson('/chat/search', {
        user_id: user_id,
        room_id: room_id,
        prompt: text,
        category: ['search'], // 假設這裡的分類是固定的
      });

      // 處理後端回應
      const reply = response.response || '抱歉，我無法處理您的請求。';
      console.log('後端回應:', reply);
      setMessages((prev) => [
        ...prev,
        ...reply.map((item) => ({
          id: Date.now() + Math.random(), // 確保唯一 ID
          text: item.chat_response, // 提取 chat_response
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
        })),
      ]);
    } catch (error) {
      console.error('Error fetching chat response:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          text: '抱歉，伺服器發生錯誤，請稍後再試。',
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSendMessage();
  };

  return (
    <div className="fchat">
      <div className={`fchat__window ${isExpanded ? 'is-expanded' : ''}`}>
        {!isExpanded ? (
          <button
            type="button"
            className="fchat__collapsed"
            onClick={toggleChat}
            aria-label="展開智慧搜尋助手"
            title="展開智慧搜尋助手"
          >
            <span className="fchat__icon">🔍</span>
          </button>
        ) : (
          <div
            className="fchat__header"
            onClick={toggleChat}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && toggleChat()}
            aria-label="收合智慧搜尋助手"
          >
            <div className="fchat__headerContent">
              <span className="fchat__icon">🔍</span>
              <div>
                <h3 className="fchat__title">智慧搜尋助手</h3>
                <p className="fchat__subtitle">AI 驅動的新聞搜尋與分析</p>
              </div>
            </div>
            <button
              type="button"
              className="fchat__toggle"
              aria-label="收合"
              title="收合"
            >
              ×
            </button>
          </div>
        )}

        {isExpanded && (
          <div className="fchat__body">
            <div className="fchat__intro">
              輸入任何關鍵字、問題或主題，我將為您搜尋相關新聞、提供分析見解，並推薦相關報導。
              支援自然語言查詢，讓您快速找到所需資訊。
            </div>

            <div className="fchat__messages">
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔍</div>
                  <h3>歡迎使用智慧搜尋助手</h3>
                  <p>請輸入您想搜尋的新聞主題或問題</p>
                </div>
              )}

              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`fchat__message ${m.isOwn ? 'fchat__message--own' : ''}`}
                >
                  <div className={`fchat__bubble ${m.isOwn ? 'fchat__bubble--own' : ''}`}>
                    {m.text}
                  </div>
                  <span className="fchat__time">{m.time}</span>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <div className="fchat__quick">
              {quickPrompts.map((p, i) => (
                <button
                  key={i}
                  type="button"
                  className="fchat__quickBtn"
                  onClick={() => setNewMessage(p)}
                >
                  {p}
                </button>
              ))}
            </div>

            <div className="fchat__input">
              <input
                type="text"
                className="fchat__inputText"
                placeholder="輸入您想搜尋的新聞主題或問題..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={handleKeyPress}
              />
              <button
                type="button"
                className="fchat__send"
                onClick={handleSendMessage}
                disabled={!newMessage.trim()}
              >
                ➤
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default FloatingChat;