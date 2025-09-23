import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './../css/ChatRoom.css';
import { useLocation } from 'react-router-dom';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { fetchJson } from './api';
import { supabase } from './supabase.js';

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

  const fixedPrompts = [
    "近期有什麼重要的新聞？",
  ];

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
  }, [user_id]);

  // 詳情頁不顯示
  const isSpecialReportPage = location.pathname.includes('/special-report/');
  const isNewsDetailPage = location.pathname.startsWith('/news/');
  if (isSpecialReportPage || isNewsDetailPage) return null;

  const toggleChat = () => setIsExpanded((v) => !v);

  const handleSendMessage = async (customMessage = null) => {
    const text = (customMessage ?? newMessage).trim();
    if (!text) return;

    const now = new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });

    // 新增使用者訊息
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), text, isOwn: true, time: now, type: 'text' },
    ]);
    setNewMessage('');

    try {
      // 呼叫後端 API（舊版邏輯）
      const response = await fetchJson('/chat/search', {
        user_id: user_id,
        room_id: room_id,
        prompt: text,
        category: ['search'],
      });

      // 處理後端回應
      const reply = response.response || [];
      console.log('後端回應:', reply);

      // 先處理普通訊息
      const textMessages = reply
        .map((item) => ({
          id: Date.now() + Math.random(),
          type: 'text',
          text: item.chat_response,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
        }));

      setMessages((prev) => [...prev, ...textMessages]);

      // 延遲處理新聞訊息
      const newsMessages = await Promise.all(
        reply
          .filter((item) => item.news_id && Array.isArray(item.news_id))
          .map(async (item) => {
            const newsData = await Promise.all(
              item.news_id.map(async (newsId) => {
                const { data, error } = await supabase
                  .from('single_news')
                  .select('news_title, ultra_short,generated_image(image)')
                  .eq('story_id', newsId)
                  .single();

                if (error) {
                  console.error('Error fetching news:', error);
                  return null;
                }

                return {
                  id: Date.now() + Math.random(),
                  type: 'news',
                  title: data.news_title,
                  image: data.generated_image.image,
                  ultra_short: data.ultra_short,
                  newsId,
                  isOwn: false,
                  time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
                };
              })
            );
            return newsData.filter(Boolean);
          })
      );

      // 延遲顯示新聞訊息
      setTimeout(() => {
        setMessages((prev) => [...prev, ...newsMessages.flat()]);
      }, 1000);
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

  // 新版 handlePromptSend：直接送出，而不是塞進 input
  const handlePromptSend = (promptText) => {
    if (!promptText.trim()) return;
    handleSendMessage(promptText);
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

            {/* 搜尋說明區 */}
            <div className="chat__expertSelector">
              🔍 輸入任何關鍵字、問題或主題，我將為您搜尋相關新聞、提供分析見解，並推薦相關報導
            </div>

            {/* 訊息區 */}
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

            {/* 快速提示區 */}
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

            {/* 輸入區 */}
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
                onClick={() => handleSendMessage()}
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