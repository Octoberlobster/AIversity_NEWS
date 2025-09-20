import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './../css/ChatRoom.css';
import { useLocation } from 'react-router-dom';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { fetchJson } from './api';

function FloatingChat() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [quickPrompts, setQuickPrompts] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const location = useLocation();
  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  const fixedPrompts = React.useMemo(() => [
    "近期有什麼重要的新聞？",
  ], []);

  // 滾動到底
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch quickPrompts 從後端獲取資料
  useEffect(() => {
    let isMounted = true;
    const fetchQuickPrompts = async () => {
      try {
        const response = await fetchJson('/hint_prompt/search', {});
        if (isMounted) {
          const dynamicPrompts = response.Hint_Prompt || [];
          setQuickPrompts([...fixedPrompts, ...dynamicPrompts]);
        }
      } catch (error) {
        if (isMounted) {
          console.error('Error fetching quick prompts:', error);
          setQuickPrompts([...fixedPrompts]);
        }
      }
    };
    fetchQuickPrompts();
    return () => {
      isMounted = false;
    };
  }, [user_id, fixedPrompts]);


  // 詳情頁不顯示
  const isSpecialReportPage = location.pathname.includes('/special-report/');
  const isNewsDetailPage = location.pathname.startsWith('/news/');
  if (isSpecialReportPage || isNewsDetailPage) return null;

  const toggleChat = () => setIsExpanded((v) => !v);

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    // 添加用戶訊息
    const userMsg = {
      id: Date.now(),
      text: newMessage,
      isOwn: true,
      time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);

    const currentMessage = newMessage;
    setNewMessage('');

    try {
      // 調用後端搜尋API
      const response = await fetchJson('/search/single', {
        user_id: user_id,
        room_id: room_id,
        prompt: currentMessage,
      });

      // 處理AI回覆
      if (response.ai_response) {
        const aiMsg = {
          id: Date.now() + 1,
          text: response.ai_response,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, aiMsg]);
      }

      // 處理新聞結果
      if (response.news && response.news.length > 0) {
        response.news.forEach((newsItem, index) => {
          setTimeout(() => {
            const newsMsg = {
              id: Date.now() + 2 + index,
              type: 'news',
              newsId: newsItem.story_id,
              title: newsItem.title,
              ultra_short: newsItem.ultra_short,
              image: newsItem.image,
              time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
            };
            setMessages((prev) => [...prev, newsMsg]);
          }, 500 + index * 300);
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = {
        id: Date.now() + 999,
        text: '抱歉，搜尋時發生錯誤，請稍後再試。',
        isOwn: false,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSendMessage();
  };

  const handlePromptSend = (promptText) => {
    // 直接處理發送，不依賴狀態更新
    if (!promptText.trim()) return;

    // 添加用戶訊息
    const userMsg = {
      id: Date.now(),
      text: promptText,
      isOwn: true,
      time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);

    // 清空輸入框
    setNewMessage('');

    // 直接調用搜尋API
    handleSearchWithPrompt(promptText);
  };

  const handleSearchWithPrompt = async (promptText) => {
    try {
      // 調用後端搜尋API
      const response = await fetchJson('/search/single', {
        user_id: user_id,
        room_id: room_id,
        prompt: promptText,
      });

      // 處理AI回覆
      if (response.ai_response) {
        const aiMsg = {
          id: Date.now() + 1,
          text: response.ai_response,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, aiMsg]);
      }

      // 處理新聞結果
      if (response.news && response.news.length > 0) {
        response.news.forEach((newsItem, index) => {
          setTimeout(() => {
            const newsMsg = {
              id: Date.now() + 2 + index,
              type: 'news',
              newsId: newsItem.story_id,
              title: newsItem.title,
              ultra_short: newsItem.ultra_short,
              image: newsItem.image,
              time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
            };
            setMessages((prev) => [...prev, newsMsg]);
          }, 500 + index * 300);
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = {
        id: Date.now() + 999,
        text: '抱歉，搜尋時發生錯誤，請稍後再試。',
        isOwn: false,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
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
          <div className="chat">
            {/* Header - 統一使用ChatRoom樣式 */}
            <div className="chat__header">
              <div className="chat__headerLeft">
                <div className="chat__icon">🔍</div>
                <div>
                  <h3 className="chat__title">智慧搜尋助手</h3>
                  <p className="chat__subtitle">AI 驅動的新聞搜尋與分析</p>
                </div>
              </div>
              <div className="chat__headerRight">
                <button
                  type="button"
                  className="chat-close-btn"
                  onClick={toggleChat}
                  aria-label="收合"
                  title="收合"
                >
                  ×
                </button>
              </div>
            </div>

            {/* 搜尋說明區 - 採用ChatRoom的expertSelector樣式 */}
            <div className="chat__expertSelector">
              🔍 輸入任何關鍵字、問題或主題，我將為您搜尋相關新聞、提供分析見解，並推薦相關報導
            </div>

            {/* 訊息區 - 完全採用ChatRoom樣式 */}
            <div className="messages">
                {messages.length === 0 && (
                  <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔍</div>
                    <h3>歡迎使用智慧搜尋助手</h3>
                    <p>請輸入您想搜尋的新聞主題或問題</p>
                  </div>
                )}

                {messages.map((m) => {
                  if (m.type === 'news') {
                    return (
                      <div key={m.id} className="message message--news">
                        <div
                          className="bubble bubble--news"
                          onClick={() => window.location.href = `/news/${m.newsId}`}
                        >
                          <img
                            src={`data:image/png;base64,${m.image}`}
                            alt="新聞圖片"
                          />
                          <div>
                            <h4>{m.title}</h4>
                            <p>{m.ultra_short}</p>
                          </div>
                        </div>
                        <span className="message__time">{m.time}</span>
                      </div>
                    );
                  } else {
                    return (
                      <div
                        key={m.id}
                        className={`message ${m.isOwn ? 'message--own' : ''}`}
                      >
                        <div className={`bubble ${m.isOwn ? 'bubble--own' : ''}`}>
                          <ReactMarkdown>{m.text}</ReactMarkdown>
                        </div>
                        <span className="message__time">{m.time}</span>
                      </div>
                    );
                  }
                })}
                <div ref={messagesEndRef} />
              </div>

            {/* 快速提示區 - 水平滾動設計 */}
            {quickPrompts.length > 0 && (
              <div className="prompt">
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
              </div>
            )}

            {/* 底部輸入區 - 完全採用ChatRoom樣式 */}
            <div className="input">
              <input
                ref={inputRef}
                type="text"
                className="input__text"
                placeholder="輸入您想搜尋的新聞主題或問題..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                autoComplete="off"
                spellCheck="false"
              />
              <button
                className="input__send"
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