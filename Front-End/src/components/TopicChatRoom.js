import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from 'i18next';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { fetchJson } from './api';
import './../css/ChatRoom.css';
import ReactMarkdown from 'react-markdown';

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

function updateExpertNamesByTopicExperts(topicExperts) {
  if (!Array.isArray(topicExperts)) return;

  topicExperts.forEach(item => {
    if (!item || !item.category) return;

    const expert = experts.find(e => e.category === item.category);
    if (expert && item.analyze?.Role) {
      expert.name = item.analyze.Role;
    }
  });
}

function TopicChatRoom({topic_id, topic_title, topic_who_talk, topicExperts, onClose}) {
  const { t } = useTranslation();
  const [selectedExperts, setSelectedExperts] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // 根據當前語言獲取對應的區域代碼
  const getCurrentLocale = () => {
    const currentLang = i18n.language;
    switch (currentLang) {
      case 'zh-TW':
        return 'zh-TW';
      case 'en':
        return 'en-US';
      case 'jp':
        return 'ja-JP';
      case 'id':
        return 'id-ID';
      default:
        return 'zh-TW';
    }
  };

  // 獲取格式化的時間字符串
  const getFormattedTime = useCallback(() => {
    return new Date().toLocaleTimeString(getCurrentLocale(), { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }, []);
  const [inputMessage, setInputMessage] = useState('');
  const [quickPrompts, setQuickPrompts] = useState([]);
  
  const messagesEndRef = useRef(null);
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);
  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  // 當 topic_who_talk 改變時，清理不在 who_talk 範圍內的已選專家
  useEffect(() => {
    const whoTalkArray = parseWhoTalk(topic_who_talk);

    if (whoTalkArray.length > 0) {
      setSelectedExperts(prevSelected => {
        const validExperts = prevSelected.filter(expertId => {
          const expert = experts.find(e => e.id === expertId);
          return expert && whoTalkArray.includes(expert.category);
        });
        return validExperts;
      });
    }
  }, [topic_who_talk]);

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

  // 更新專家名稱
  useEffect(() => {
    updateExpertNamesByTopicExperts(topicExperts);
  }, [topicExperts]);

  // 自動滾到最底
  useEffect(() => {
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.closest('[data-messages-container]');
      if (container) {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
      }
    }
  }, [messages]);

  const loadQuickPrompts = useCallback(async (chat_content = '') => {
    const fixedPrompts = [
      t('topicChat.prompts.fixed.updates', { topicTitle: topic_title }),
      t('topicChat.prompts.fixed.content', { topicTitle: topic_title }),
      t('topicChat.prompts.fixed.opinion', { topicTitle: topic_title })
    ]; // 固定的 prompt

    try {
      const options = selectedExperts.map(
        (expertId) => experts.find((e) => e.id === expertId).category
      );

      const response = await fetchJson('/hint_prompt/topic', {
        topic_id: topic_id,
        room_id: room_id,
        user_id: user_id,
        option: options,
        chat_content: chat_content
      });
      console.log('Fetched quick prompts:', response);

      // 合併固定 prompt 和後端返回的 prompt
      setQuickPrompts([...(response.Hint_Prompt || []), ...fixedPrompts]);
    } catch (error) {
      console.error('Error loading quick prompts:', error);

      // 如果發生錯誤，僅保留固定的 prompt
      setQuickPrompts([
        ...t('topicChat.prompts.default', { returnObjects: true }),
        ...fixedPrompts,
      ]);
    }
  }, [topic_id, topic_title, room_id, user_id, selectedExperts, t]);

  useEffect(() => {
    if (selectedExperts.length > 0) {
      loadQuickPrompts();
    }
  }, [selectedExperts, loadQuickPrompts]);

  const toggleExpert = (id) => {
    setSelectedExperts((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handlePromptSend = (promptText) => {
    if (!promptText.trim()) {
      return;
    }
    
    // 如果沒有選擇專家，提醒用戶
    if (selectedExperts.length === 0) {
      alert('請先選擇至少一位專家來回答您的問題');
      return;
    }
    
    // 直接處理發送，不依賴狀態更新
    const userMsg = {
      id: Date.now(),
      text: promptText,
      isOwn: true,
      time: getFormattedTime(),
    };
    setMessages((prev) => [...prev, userMsg]);
    
    // 清空輸入框
    setInputMessage('');
    
    // 直接調用API
    simulateRepliesWithPrompt(promptText);
  };

  const simulateRepliesWithPrompt = async (promptText) => {
    setIsLoading(true);
    
    // 添加載入訊息
    const loadingMsg = {
      id: 'loading-' + Date.now(),
      isLoading: true,
      isOwn: false,
      time: getFormattedTime(),
    };
    setMessages((prev) => [...prev, loadingMsg]);
    
    try {
      // 取得選中專家的分類
      const categories = selectedExperts.map(
        (expertId) => experts.find((e) => e.id === expertId).category
      );

      // 🧠 每個 category 各自請求
      const fetchCategory = async (category) => {
        return fetchJson('/chat/topic', {
          topic_id: topic_id,
          room_id: room_id,
          user_id: user_id,
          prompt: promptText,
          category: [category], // ✅ 每次只傳單一分類
        })
          .then((res) => ({
            category,
            reply: res.response?.[0]?.chat_response || '(無回覆)',
          }))
          .catch((err) => ({
            category,
            reply: `(錯誤) ${err.message}`,
          }));
      };

      // 🧠 平行發送所有請求
      const allPromises = categories.map(fetchCategory);
      const results = await Promise.all(allPromises);
      
      // 移除載入訊息
      setMessages((prev) => prev.filter(m => !m.isLoading));
      setIsLoading(false);
      
      // 🧠 顯示每個分類的回覆
      results.forEach(({ category, reply }, index) => {
        const expertId = selectedExperts[index];
        const expertName = experts.find((e) => e.id === expertId).name;

        const expertReply = {
          id: Date.now() + expertId,
          text: `${expertName}：${reply}`,
          isOwn: false,
          time: getFormattedTime()
        };

        // 模擬輸出延遲
        setTimeout(() => {
          setMessages((prev) => [...prev, expertReply]);
        }, 1000 + index * 500);
      });

      // 🧠 整合成 quick prompt 格式
      const formattedReplies = results.map(
        ({ category, reply }) => `${category}: ${reply}`
      );
      loadQuickPrompts(`user:${promptText} ${formattedReplies.join(' ')}`);
    } catch (error) {
      console.error('Error fetching response:', error);
      // 移除載入訊息
      setMessages((prev) => prev.filter(m => !m.isLoading));
      setIsLoading(false);
      
      setMessages((prev) => [...prev, {
        id: Date.now(),
        text: t('topicChat.error.serverError'),
        isOwn: false,
        time: getFormattedTime(),
      }]);
    }
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    // 如果沒有選擇專家，提醒用戶
    if (selectedExperts.length === 0) {
      alert('請先選擇至少一位專家來回答您的問題');
      return;
    }

    const userMsg = {
      id: Date.now(),
      text: inputMessage,
      isOwn: true,
      time: getFormattedTime()
    };
    setMessages((prev) => [...prev, userMsg]);
    const currentInput = inputMessage;
    setInputMessage('');

    simulateRepliesWithPrompt(currentInput);
  };


  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSendMessage();
  };

  return (
    <div className="chat">
      <div className="chat__header">
        <div className="chat__headerLeft">
          <div className="chat__icon">💬</div>
          <div>
            <h3 className="chat__title">{t('topicChat.title')}</h3>
            <p className="chat__subtitle">
              {selectedExperts.length > 0 
                ? t('exportChat.subtitles.chat', { count: selectedExperts.length })
                : t('topicChat.subtitle', { topicTitle: topic_title })
              }
            </p>
          </div>      
        </div>
        <div className="chat__headerRight">
          {/* 關閉聊天室按鈕 */}
          {onClose && (
            <button 
              className="chat-close-btn"
              onClick={onClose}
              title={t('topicChat.close')}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* 專家選擇器 */}
      <div className="chat__expertSelector">
        <div className="dropdown" ref={dropdownRef}>
          <button
            type="button"
            className="dropdown__btn"
            onClick={() => setIsDropdownOpen((v) => !v)}
          >
            <span>{t('exportChat.buttons.selectExperts')}</span>
            {selectedExperts.length > 0 && <span className="selectedCount">{selectedExperts.length}</span>}
            <span className={`dropdown__icon ${isDropdownOpen ? 'is-open' : ''}`}>▼</span>
          </button>

          {isDropdownOpen && (
            <div className="dropdown__menu">
              {experts
                .filter(expert => {
                  const whoTalkArray = parseWhoTalk(topic_who_talk);
                  
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
      </div>

      {/* 聊天訊息區域 */}
      <div className="messages" data-messages-container>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💬</div>
            <h3>{t('topicChat.welcome.title')}</h3>
            <p>{t('topicChat.welcome.description', { topicTitle: topic_title })}</p>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={`message ${m.isOwn ? 'message--own' : ''} ${m.isLoading ? 'message--loading' : ''}`}>
            <div className={`bubble ${m.isOwn ? 'bubble--own' : ''} ${m.isLoading ? 'bubble--loading' : ''}`}>
              {m.isLoading ? (
                <div className="loading-dots">
                  <span className="loading-dot"></span>
                  <span className="loading-dot"></span>
                  <span className="loading-dot"></span>
                </div>
              ) : (
                <ReactMarkdown>{m.text}</ReactMarkdown>
              )}
            </div>
            <span className="time">{m.time}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 快速提示區域 */}
      <div className="prompt">
        {quickPrompts.length > 0 && selectedExperts.length > 0 && (
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

      {/* 輸入區域 */}
      <div className="input">
        <input
          ref={inputRef}
          type="text"
          className="input__text"
          placeholder={selectedExperts.length === 0 ? t('exportChat.placeholders.selectFirst') : t('topicChat.input.placeholder')}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
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
    </div>
  );
}


export default TopicChatRoom;