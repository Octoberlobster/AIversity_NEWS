import React, { useState, useEffect, useRef } from 'react';
import { fetchJson } from './api';
import './css/ChatRoom.css';

function ChatRoom({
  selectedRole,
  messages: initialMessages,
  updateMessages,
  roleAnalyze,          // 仍保留，但此版不再用來補訊息
  news
}) {
  const [messages, setMessages] = useState(initialMessages);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const endRef = useRef(null);

  /* 只要父層歷史有更新，就直接顯示 ------------------------ */
  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  /* 發送訊息 ------------------------------------------------ */
  const handleSendMessage = async e => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const userMsg   = { sender: '使用者', text: newMessage };
    const afterUser = [...messages, userMsg];
    setMessages(afterUser);
    updateMessages(afterUser);      // 寫回父層
    setNewMessage('');
    setIsLoading(true);

    try {
      const data = await fetchJson({
        mode: 'interactive',
        news,
        role: selectedRole,
        message: newMessage
      });

      const aiMsg  = { sender: selectedRole, text: data.response };
      const afterAI = [...afterUser, aiMsg];
      setMessages(afterAI);
      updateMessages(afterAI);
    } catch {
      const errMsg = { sender: 'system', text: '發生錯誤，請稍後再試。' };
      const afterErr = [...afterUser, errMsg];
      setMessages(afterErr);
      updateMessages(afterErr);
    } finally {
      setIsLoading(false);
    }
  };

  /* UI ---------------------------------------------------- */
  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`message ${
              m.sender === 'system'
                ? 'system-message'
                : m.sender === '使用者'
                  ? 'user-message'
                  : 'role-message'
            }`}
          >
            {m.sender !== 'system' && <strong>{m.sender}：</strong>}
            {m.text.split('\n').map((line, idx, arr) => (
              <span key={idx}>
                {line}
                {idx < arr.length - 1 && <br />}
              </span>
            ))}
          </div>
        ))}

        {isLoading && (
          <div className="message system-message loading-message">
            <div className="typing-indicator"><span/><span/><span/></div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          className="chat-input"
          placeholder="輸入您的問題或觀點..."
          value={newMessage}
          disabled={isLoading}
          onChange={e => setNewMessage(e.target.value)}
        />
        <button className="send-button" disabled={isLoading}>
          {isLoading ? '發送中…' : '發送'}
        </button>
      </form>
    </div>
  );
}

export default ChatRoom;
