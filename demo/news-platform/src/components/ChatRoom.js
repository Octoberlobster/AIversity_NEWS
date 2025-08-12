import React, { useState, useRef, useEffect } from 'react';
import './../css/ChatRoom.css';

// 10大類別專家
const experts = [
  { id: 1, name: "科技專家", category: "科技", prompt: "你是科技領域的專家..." },
  { id: 2, name: "金融專家", category: "金融", prompt: "你是金融領域的專家..." },
  { id: 3, name: "環境專家", category: "環境", prompt: "你是環境領域的專家..." },
  { id: 4, name: "醫療專家", category: "醫療", prompt: "你是醫療領域的專家..." },
  { id: 5, name: "教育專家", category: "教育", prompt: "你是教育領域的專家..." },
  { id: 6, name: "體育專家", category: "體育", prompt: "你是體育領域的專家..." },
  { id: 7, name: "政治專家", category: "政治", prompt: "你是政治領域的專家..." },
  { id: 8, name: "國際專家", category: "國際", prompt: "你是國際事務專家..." },
  { id: 9, name: "文化專家", category: "文化", prompt: "你是文化領域的專家..." },
  { id: 10, name: "生活專家", category: "生活", prompt: "你是生活領域的專家..." },
];

// 專家預設回覆
const expertReplies = {
  1: "根據最新科技趨勢，AI 將持續改變我們的生活。",
  2: "金融市場近期波動，建議多元分散投資。",
  3: "環境保護需全民參與，減碳是關鍵。",
  4: "醫療科技進步有助於提升全民健康。",
  5: "教育創新是未來人才培育的核心。",
  6: "體育運動有助於身心健康，建議多參與。",
  7: "政治穩定對國家發展至關重要。",
  8: "國際局勢變化快速，需持續關注。",
  9: "文化多元是社會進步的象徵。",
  10: "生活品質提升需從日常做起。"
};

// 快速提示
const quickPrompts = [
  "這則新聞的重點是什麼？",
  "對社會有什麼影響？",
  "未來發展趨勢如何？",
  "有什麼爭議點？",
  "專家怎麼看？"
];

function ChatRoom() {
  const [selectedExperts, setSelectedExperts] = useState([1, 2, 3]);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isPromptDropdownOpen, setIsPromptDropdownOpen] = useState(false);

  const messagesEndRef = useRef(null);
  const dropdownRef = useRef(null);
  const promptDropdownRef = useRef(null);

  // 自動滾到最底
  useEffect(() => {
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.closest('[data-messages-container]');
      if (container) {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
      }
    }
  }, [messages]);

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

  const toggleExpert = (id) => {
    setSelectedExperts((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
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

  const simulateReplies = () => {
    selectedExperts.forEach((expertId, index) => {
      setTimeout(() => setMessages((prev) => [...prev, makeExpertReply(expertId)]), 1000 + index * 500);
    });
  };

  const handlePromptSend = (promptText) => {
    if (selectedExperts.length === 0) return;
    setMessages((prev) => [...prev, makeUserMsg(promptText)]);
    simulateReplies();
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

  return (
    <div className="chat">
      <div className="chat__header">
        <div className="chat__headerLeft">
          <div className="chat__icon">🤖</div>
          <div>
            <h3 className="chat__title">AI 專家討論室</h3>
            <p className="chat__subtitle">{selectedExperts.length} 位專家在線</p>
          </div>
        </div>
      </div>

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
            <div className={`bubble ${m.isOwn ? 'bubble--own' : ''}`}>{m.text}</div>
            <span className="time">{m.time}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="prompt">
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
      </div>

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
    </div>
  );
}

export default ChatRoom;