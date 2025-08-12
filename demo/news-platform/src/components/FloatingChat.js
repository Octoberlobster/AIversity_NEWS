import React, { useState, useRef, useEffect } from 'react';
import './../css/FloatingChat.css';
import { useLocation } from 'react-router-dom';

const quickPrompts = [
  '搜尋最新科技新聞',
  '分析今日股市趨勢',
  '推薦熱門話題',
  '查找相關報導',
  '總結新聞重點',
];

function FloatingChat() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef(null);
  const location = useLocation();

  // 滾動到底
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 詳情頁不顯示
  const isSpecialReportPage = location.pathname.includes('/special-report/');
  const isNewsDetailPage = location.pathname.startsWith('/news/');
  if (isSpecialReportPage || isNewsDetailPage) return null;

  

  const toggleChat = () => setIsExpanded((v) => !v);

  const handleSendMessage = () => {
    const text = newMessage.trim();
    if (!text) return;

    const now = new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });

    setMessages((prev) => [
      ...prev,
      { id: Date.now(), text, isOwn: true, time: now },
    ]);
    setNewMessage('');

    // 模擬 AI 回覆
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          text:
            `我是您的智慧搜尋助手！我正在為您搜尋相關資訊...\n\n` +
            `根據我的分析，${text} 相關的最新報導包括：\n• 相關新聞1\n• 相關新聞2\n• 相關新聞3\n\n需要我為您深入分析某個特定主題嗎？`,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }, 1000);
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