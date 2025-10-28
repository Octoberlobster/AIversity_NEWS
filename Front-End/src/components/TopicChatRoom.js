import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from 'i18next';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { fetchJson } from './api';
import './../css/ChatRoom.css'; // 使用相同的 CSS
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

  // 當 topic_who_talk 改變時，清理不在 who_talk 範圍內的已選專家，並預選第一個專家
  useEffect(() => {
    const whoTalkArray = parseWhoTalk(topic_who_talk);

    if (whoTalkArray.length > 0) {
      setSelectedExperts(prevSelected => {
        // 過濾出有效的專家
        const validExperts = prevSelected.filter(expertId => {
          const expert = experts.find(e => e.id === expertId);
          return expert && whoTalkArray.includes(expert.category);
        });

        // 如果沒有已選專家，自動選擇第一個可用的專家
        if (validExperts.length === 0) {
          const firstAvailableExpert = experts.find(expert =>
            whoTalkArray.includes(expert.category)
          );
          if (firstAvailableExpert) {
            return [firstAvailableExpert.id];
          }
        }

        return validExperts;
      });
    } else {
        // 如果 who_talk 為空或無效，則預設選擇第一個專家
        if (experts.length > 0) {
            setSelectedExperts([experts[0].id]);
        }
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

  // 初始化歡迎訊息
  useEffect(() => {
      setMessages([{
          id: Date.now() + Math.random(),
          text: t('exportChat.welcome.chat.greeting'), // 使用 ChatRoom 的歡迎語
          isOwn: false,
          time: getFormattedTime(),
      }]);
  }, [t, getFormattedTime]);


  const loadQuickPrompts = useCallback(async (chat_content = '') => {
    // 專題討論的 Quick Prompts 邏輯保持不變
    const fixedPrompts = [
      t('topicChat.prompts.fixed.updates', { topicTitle: topic_title }),
      t('topicChat.prompts.fixed.content', { topicTitle: topic_title }),
      t('topicChat.prompts.fixed.opinion', { topicTitle: topic_title })
    ];

    try {
      const options = selectedExperts.map(
        (expertId) => experts.find((e) => e.id === expertId).category
      );

      const response = await fetchJson('/api/hint_prompt/topic', {
        topic_id: topic_id,
        room_id: room_id,
        user_id: user_id,
        option: options,
        chat_content: chat_content
      });
      console.log('Fetched topic quick prompts:', response);

      setQuickPrompts([...(response.Hint_Prompt || []), ...fixedPrompts]);
    } catch (error) {
      console.error('Error loading topic quick prompts:', error);
      setQuickPrompts([
        ...t('topicChat.prompts.default', { returnObjects: true }),
        ...fixedPrompts,
      ]);
    }
  }, [topic_id, topic_title, room_id, user_id, selectedExperts, t]);

  useEffect(() => {
    if (selectedExperts.length > 0) {
      loadQuickPrompts();
    } else {
      setQuickPrompts([]); // 沒有選擇專家時清空提示
    }
  }, [selectedExperts, loadQuickPrompts]);

  const toggleExpert = (id) => {
    setSelectedExperts((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const makeUserMsg = (text) => ({
      id: Date.now(),
      text,
      isOwn: true,
      time: getFormattedTime(),
  });

  const makeExpertReply = (expertId, reply) => {
      const expert = experts.find((e) => e.id === expertId);
      const expertName = expert ? expert.name : '專家'; // Fallback name
      // 將字串中的 \n 轉換成真正的換行符
      const formattedReply = reply.replace(/\\n/g, '\n');
      return {
          id: Date.now() + expertId + Math.random(), // Add random to avoid key collision
          text: `**${expertName}：**\n\n${formattedReply}`,
          isOwn: false,
          time: getFormattedTime(),
      };
  };

  const handlePromptSend = (promptText) => {
    if (!promptText.trim()) return;
    if (selectedExperts.length === 0) {
      alert(t('exportChat.placeholders.selectFirst')); // 提示選擇專家
      return;
    }
    setMessages((prev) => [...prev, makeUserMsg(promptText)]);
    setInputMessage('');
    simulateRepliesWithPrompt(promptText);
  };

  const simulateRepliesWithPrompt = async (promptText) => {
    setIsLoading(true);
    const loadingMsg = {
      id: 'loading-' + Date.now(),
      isLoading: true,
      isOwn: false,
      time: getFormattedTime(),
    };
    setMessages((prev) => [...prev, loadingMsg]);

    try {
      const categories = selectedExperts.map(
        (expertId) => experts.find((e) => e.id === expertId)?.category
      ).filter(Boolean); // Filter out undefined categories

      if (categories.length === 0) {
          throw new Error("No valid categories selected");
      }

      const fetchCategory = async (category, expertId) => {
        return fetchJson('/api/chat/topic', { // 保持呼叫 topic API
          topic_id: topic_id,
          room_id: room_id,
          user_id: user_id,
          prompt: promptText,
          category: [category],
        })
          .then((res) => ({
            expertId,
            category,
            reply: res.response?.[0]?.chat_response || '(無回覆)',
          }))
          .catch((err) => ({
            expertId,
            category,
            reply: `(錯誤) ${err.message}`,
          }));
      };

      // 創建 Promise 列表時包含 expertId
      const allPromises = selectedExperts.map(expertId => {
          const expert = experts.find(e => e.id === expertId);
          if (expert) {
              return fetchCategory(expert.category, expertId);
          }
          return Promise.resolve({ expertId, category: null, reply: '(無效專家)'}); // Handle invalid expertId
      });

      const results = await Promise.all(allPromises);

      setMessages((prev) => prev.filter(m => !m.isLoading));
      setIsLoading(false);

      const newReplies = [];
      results.forEach(({ expertId, reply }, index) => {
          if (reply !== '(無效專家)') {
            newReplies.push(makeExpertReply(expertId, reply));
          }
      });

      // 延遲顯示回覆
      newReplies.forEach((replyMsg, index) => {
        setTimeout(() => {
          setMessages((prev) => [...prev, replyMsg]);
        }, 500 + index * 300); // 稍微調整延遲
      });

      // 更新 Quick Prompts (使用 topic 的邏輯)
      const formattedReplies = results
        .filter(r => r.category)
        .map(({ category, reply }) => `${category}: ${reply}`);
      loadQuickPrompts(`user:${promptText} ${formattedReplies.join(' ')}`);

    } catch (error) {
      console.error('Error fetching response:', error);
      setMessages((prev) => prev.filter(m => !m.isLoading));
      setIsLoading(false);
      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        text: t('topicChat.error.serverError'),
        isOwn: false,
        time: getFormattedTime(),
      }]);
    }
  };


  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;
    if (selectedExperts.length === 0) {
      alert(t('exportChat.placeholders.selectFirst'));
      return;
    }
    const currentInput = inputMessage;
    setMessages((prev) => [...prev, makeUserMsg(currentInput)]);
    setInputMessage('');
    simulateRepliesWithPrompt(currentInput); // 使用包含 prompt 的函數
  };


  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) handleSendMessage();
  };

  // 過濾有效的專家列表 (基於 who_talk)
  const availableExperts = experts.filter(expert => {
      const whoTalkArray = parseWhoTalk(topic_who_talk);
      if (whoTalkArray.length === 0) return true; // 如果沒限制，全顯示
      return whoTalkArray.includes(expert.category);
  });

  return (
    // 使用 .chat 作為根 class
    <div className="chat">
      {/* Header: 使用 ChatRoom 的樣式和文字 */}
      <div className="chat__header">
        <div className="chat__headerLeft">
          <div className="chat__icon">🤖</div> {/* 修改圖示 */}
          <div>
            <h3 className="chat__title">
              {t('exportChat.titles.chat')} {/* 修改標題 */}
            </h3>
            <p className="chat__subtitle">
              {t('exportChat.subtitles.chat', { count: selectedExperts.length })} {/* 修改副標題 */}
            </p>
          </div>
        </div>
        <div className="chat__headerRight">
          {onClose && (
            <button
              className="chat-close-btn"
              onClick={onClose}
              title={t('exportChat.tooltips.closeChat')} // 使用 ChatRoom 的 tooltip 文字
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
            disabled={availableExperts.length === 0} // 如果沒有可用專家則禁用
          >
            <span>{t('exportChat.buttons.selectExperts')}</span>
            {selectedExperts.length > 0 && <span className="selectedCount">{selectedExperts.length}</span>}
            <span className={`dropdown__icon ${isDropdownOpen ? 'is-open' : ''}`}>▼</span>
          </button>

          {isDropdownOpen && availableExperts.length > 0 && (
            <div className="dropdown__menu">
              {availableExperts.map((expert) => {
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
        {/* 初始歡迎訊息: 使用 ChatRoom 的樣式和文字 */}
        {messages.length === 1 && messages[0].text === t('exportChat.welcome.chat.greeting') && (
            <div className="message">
                <div className="bubble">
                    <ReactMarkdown>{messages[0].text}</ReactMarkdown>
                </div>
                <span className="time">{messages[0].time}</span>
            </div>
        )}
        {/* 後續訊息 */}
        {messages.slice(messages.length === 1 && messages[0].text === t('exportChat.welcome.chat.greeting') ? 1: 0).map((m) => (
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
        {quickPrompts.length > 0 && selectedExperts.length > 0 && !isLoading && (
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
          // 修改 placeholder 文字邏輯
          placeholder={selectedExperts.length === 0 ? t('exportChat.placeholders.selectFirst') : t('exportChat.placeholders.enterQuestion')}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          autoComplete="off"
          spellCheck="false"
          disabled={isLoading} // 載入中禁用輸入
        />
        <button
          className="input__send"
          onClick={handleSendMessage}
          disabled={!inputMessage.trim() || isLoading || selectedExperts.length === 0} // 添加禁用條件
        >
          {isLoading ? '...' : '➤'} {/* 載入中顯示不同圖示 */}
        </button>
      </div>
    </div>
  );
}


export default TopicChatRoom;