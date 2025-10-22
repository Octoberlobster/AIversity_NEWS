import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from 'i18next';
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

function updateExpertNamesByChatExperts(chatExperts) {
  if (!Array.isArray(chatExperts)) return;

  chatExperts.forEach(item => {
    if (!item || !item.category) return; // 避免 item 為 null 或沒有 category

    const expert = experts.find(e => e.category === item.category);
    if (expert && item.analyze?.Role) {
      expert.name = item.analyze.Role;
    }
  });
}

function ChatRoom({newsData, onClose, chatExperts}, ref) {
  const { t } = useTranslation();
  const [selectedExperts, setSelectedExperts] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

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

  const messagesEndRef = useRef(null);
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);

  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  // 暴露給父組件的方法
  useImperativeHandle(ref, () => ({
  }), []);



  // 當 newsData 改變時,清理不在 who_talk 範圍內的已選專家
  useEffect(() => {
    const whoTalkArray = parseWhoTalk(newsData?.who_talk);

    if (whoTalkArray.length > 0) {
      setSelectedExperts(prevSelected => {
        const validExperts = prevSelected.filter(expertId => {
          const expert = experts.find(e => e.id === expertId);
          return expert && whoTalkArray.includes(expert.category);
        });
        
        // 自動選擇第一個符合條件的專家(如果目前沒有選中任何專家)
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
    }
  }, [newsData?.who_talk]);

    // 自動滾動到底部
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      });
    }
  }, [messages]);

  const changeQuickPrompt = useCallback(async (chat_content = '') => {
    try{
      const options = selectedExperts.map(
        (expertId) => experts.find((e) => e.id === expertId).category
      );

      const response = await fetchJson('/api/hint_prompt/single', {
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

  useEffect(() => {
    // chatExperts 變動時自動更新 experts 的 name
    updateExpertNamesByChatExperts(chatExperts);
  }, [chatExperts]);

  // 等待 category 傳遞後初始化 selectedExperts
  useEffect(() => {
    if (newsData.category) {
      const filteredExperts = experts
        .filter((expert) => expert.category === newsData.category)
        .map((expert) => expert.id);
      
      // 自動選擇第一個符合條件的專家
      if (filteredExperts.length > 0) {
        setSelectedExperts([filteredExperts[0]]);
      }
      
      setMessages([t('exportChat.welcome.chat.greeting')].map(text => ({
        id: Date.now() + Math.random(),
        text,
        isOwn: false,
        time: getFormattedTime(),
      }))); 
    }
  }, [newsData.category, t, getFormattedTime]);

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
    time: getFormattedTime(),
  });

  const makeExpertReply = (expertId) => {
    const expert = experts.find((e) => e.id === expertId);
    return {
      id: Date.now() + expertId,
      text: `**${expert.name}：**\n\n${expertReplies[expertId]}`,
      isOwn: false,
      time: getFormattedTime(),
    };
  };

  const simulateReplies = async () => {
    setIsLoading(true);

    // 加入「載入中」訊息
    const loadingMsg = {
      id: 'loading-' + Date.now(),
      isLoading: true,
      isOwn: false,
      time: getFormattedTime(),
    };
    setMessages((prev) => [...prev, loadingMsg]);

    try {
      // 取得分類（categories）
      const categories = selectedExperts.map(
        (expertId) => experts.find((e) => e.id === expertId).category
      );

      // 🧠 1️⃣ 依每個 category 建立單獨請求
      const fetchCategory = async (category) => {
        return fetchJson('/api/chat/single', {
          story_id: newsData.story_id,
          user_id,
          room_id,
          prompt: inputMessage,
          category: [category], // ✅ 每次只送一個分類
          article: newsData.long,
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

      // 🧠 2️⃣ 平行送出所有請求
      const allPromises = categories.map(fetchCategory);
      const results = await Promise.all(allPromises);

      // 移除「載入中」訊息
      setMessages((prev) => prev.filter((m) => !m.isLoading));
      setIsLoading(false);

      // 🧠 3️⃣ 顯示每個分類的回覆
      results.forEach(({ category, reply }, index) => {
        const expertId = selectedExperts[index];
        const expertName = experts.find((e) => e.id === expertId).name;

        // 將字串中的 \n 轉換成真正的換行符
        const formattedReply = reply.replace(/\\n/g, '\n');

        const expertReply = makeExpertReply(expertId);
        expertReply.text = `${expertName}：${formattedReply}`;
        expertReply.time = getFormattedTime();

        // 模擬回覆延遲
        setTimeout(() => {
          setMessages((prev) => [...prev, expertReply]);
        }, 1000 + index * 500);
      });

      // 🧠 4️⃣ 整理成 quick prompt 格式
      const formattedReplies = results.map(
        ({ category, reply }) => `${category}: ${reply}`
      );
      changeQuickPrompt(`user:${inputMessage} ${formattedReplies.join(' ')}`);

    } catch (error) {
      console.error('Error fetching expert replies:', error);

      // 移除載入中
      setMessages((prev) => prev.filter((m) => !m.isLoading));
      setIsLoading(false);

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: t('exportChat.error.serverError'),
          isOwn: false,
          time: getFormattedTime(),
        },
      ]);
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
    setIsLoading(true);

    // 加入載入中訊息
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
        return fetchJson('/api/chat/single', {
          story_id: newsData.story_id,
          user_id,
          room_id,
          prompt: promptText,
          category: [category], // ✅ 每次只傳單一分類
          article: newsData.long,
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

      // 移除載入中訊息
      setMessages((prev) => prev.filter((m) => !m.isLoading));
      setIsLoading(false);

      // 🧠 顯示每個分類的回覆
      results.forEach(({ category, reply }, index) => {
        const expertId = selectedExperts[index];
        const expertName = experts.find((e) => e.id === expertId).name;

        // 將字串中的 \n 轉換成真正的換行符
        const formattedReply = reply.replace(/\\n/g, '\n');

        const expertReply = makeExpertReply(expertId);
        expertReply.text = `${expertName}：${formattedReply}`;
        expertReply.time = getFormattedTime();

        // 模擬輸出延遲，讓畫面看起來自然
        setTimeout(() => {
          setMessages((prev) => [...prev, expertReply]);
        }, 1000 + index * 500);
      });

      // 🧠 整合成 quick prompt 格式
      const formattedReplies = results.map(
        ({ category, reply }) => `${category}: ${reply}`
      );
      changeQuickPrompt(`user:${promptText} ${formattedReplies.join(' ')}`);

    } catch (error) {
      console.error('Error fetching expert replies:', error);

      // 移除載入訊息
      setMessages((prev) => prev.filter((m) => !m.isLoading));
      setIsLoading(false);

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: t('exportChat.error.serverError'),
          isOwn: false,
          time: getFormattedTime(),
        },
      ]);
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



  return (
    <div className="chat">
      <div className="chat__header">
        <div className="chat__headerLeft">
          <div className="chat__icon">🤖</div>
          <div>
            <h3 className="chat__title">
              {t('exportChat.titles.chat')}
            </h3>
            <p className="chat__subtitle">
              {t('exportChat.subtitles.chat', { count: selectedExperts.length })}
            </p>
          </div>      
        </div>
        <div className="chat__headerRight">
          {/* 關閉聊天室按鈕 - 採用FloatingChat樣式 */}
          {onClose && (
            <button 
              className="chat-close-btn"
              onClick={onClose}
              title={t('exportChat.tooltips.closeChat')}
            >
              ✕
            </button>
          )}
        </div>
      </div>

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
        </div>

      {/* 專家聊天室訊息區域 */}
        <div className="messages" data-messages-container>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💬</div>
              <h3>{t('exportChat.welcome.chat.title')}</h3>
              <p>{t('exportChat.welcome.chat.description')}</p>
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


        <div className="input">
          <input
            ref={inputRef}
            type="text"
            className="input__text"
            placeholder={selectedExperts.length === 0 ? t('exportChat.placeholders.selectFirst') : t('exportChat.placeholders.enterQuestion')}
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
    </div>
  );
}


// quickPrompts
export default forwardRef(ChatRoom);