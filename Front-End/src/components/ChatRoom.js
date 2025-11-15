import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef, useCallback,useMemo } from 'react';
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
  { id: 5, name: "生活達人", category: "Lifestyle & Consumer" },
  { id: 6, name: "體育專家", category: "Sports" },
  { id: 7, name: "娛樂專家", category: "Entertainment" },
  { id: 8, name: "財經專家", category: "Business & Finance" },
  { id: 9, name: "健康顧問", category: "Health & Wellness" },
];

// 輔助函數：安全地解析 who_talk
const parseWhoTalk = (whoTalk) => {
  if (!whoTalk) return [];
  if (Array.isArray(whoTalk)) return whoTalk;
  if (typeof whoTalk === 'string') {
    try {
      const parsed = JSON.parse(whoTalk);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.error('Error parsing who_talk JSON:', error);
      return [];
    }
  }
  if (typeof whoTalk === 'object' && whoTalk !== null && whoTalk.who_talk && Array.isArray(whoTalk.who_talk)) {
    return whoTalk.who_talk;
  }
  return [];
};

function updateExpertNamesByChatExperts(chatExperts) {
  if (!Array.isArray(chatExperts)) return;
  chatExperts.forEach(item => {
    if (!item || !item.category) return;
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
  const [quickPrompts, setQuickPrompts] = useState([]);

  const DEFAULT_QUICK_PROMPTS_SINGLE = useMemo(() => [
      t('chatRoom.prompts.default1'),
      t('chatRoom.prompts.default2'),
      t('chatRoom.prompts.default3'),
  ], [t]);


  const getCurrentLocale = useCallback(() => {
    const currentLang = i18n.language;
    switch (currentLang) {
      case 'zh-TW': return 'zh-TW';
      case 'en': return 'en-US';
      case 'jp': return 'ja-JP';
      case 'id': return 'id-ID';
      default: return 'zh-TW';
    }
  }, [i18n.language]);

  const getFormattedTime = useCallback(() => {
    return new Date().toLocaleTimeString(getCurrentLocale(), { hour: '2-digit', minute: '2-digit' });
  }, [getCurrentLocale]);

  const messagesEndRef = useRef(null);
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);
  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  useImperativeHandle(ref, () => ({}), []);

  // 🔴 (舊) 移除這個會導致競爭條件的 useEffect
  // useEffect(() => {
  //   const whoTalkArray = parseWhoTalk(newsData?.who_talk);
  //   ... (舊的選取邏輯)
  // }, [newsData?.who_talk, newsData?.category]);

  useEffect(() => {
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.closest('[data-messages-container]');
      if (container) container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);

  const changeQuickPrompt = useCallback(async (chat_content = '') => {
    // 🔴 (修復閃爍 1/2) 移除這一行： setQuickPrompts(DEFAULT_QUICK_PROMPTS_SINGLE);
    try{
      const options = selectedExperts.map(expertId => experts.find(e => e.id === expertId)?.category).filter(Boolean);
       if (options.length === 0) {
           setQuickPrompts(DEFAULT_QUICK_PROMPTS_SINGLE); // Keep defaults if no expert
           return;
       }
      const response = await fetchJson('/api/hint_prompt/single', {
        option : options, user_id, room_id, article: newsData?.long || "", chat_content, language: getCurrentLocale(),
      });
      console.log('Fetched quick prompts:', response);
       if (response && Array.isArray(response.Hint_Prompt)) {
            // 🟢 (修復閃爍 2/2) 改為合併提示，而不是完全替換
            const dynamicPrompts = response.Hint_Prompt.filter(p => p && p.trim());
            setQuickPrompts([...dynamicPrompts, ...DEFAULT_QUICK_PROMPTS_SINGLE]);
       } else {
            console.warn("Received invalid hint prompts response:", response);
             setQuickPrompts(DEFAULT_QUICK_PROMPTS_SINGLE);
       }
    } catch (error) {
      console.error('Error updating quick prompts:', error);
       setQuickPrompts(DEFAULT_QUICK_PROMPTS_SINGLE);
    }
  }, [selectedExperts, user_id, room_id, newsData?.long, getCurrentLocale, DEFAULT_QUICK_PROMPTS_SINGLE]);


  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setIsDropdownOpen(false);
    };
    if (isDropdownOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isDropdownOpen]);

  useEffect(() => {
    // 🔴 (修復閃爍) 移除這行： setQuickPrompts(DEFAULT_QUICK_PROMPTS_SINGLE);
    if (selectedExperts.length > 0) {
      changeQuickPrompt();
    } else {
       setQuickPrompts(DEFAULT_QUICK_PROMPTS_SINGLE); // Ensure defaults if selection becomes empty
    }
  }, [selectedExperts, changeQuickPrompt, DEFAULT_QUICK_PROMPTS_SINGLE]);

  useEffect(() => {
    updateExpertNamesByChatExperts(chatExperts);
  }, [chatExperts]);

  useEffect(() => {
    setMessages([ { id: Date.now() + Math.random(), text: t('exportChat.welcome.chat.greeting'), isOwn: false, time: getFormattedTime() } ]);
    // 初始專家選擇邏輯移至下面新的 useEffect
  }, [newsData?.category, t, getFormattedTime]);


  const toggleExpert = (id) => {
    setSelectedExperts((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  const makeUserMsg = (text) => ({ id: Date.now(), text, isOwn: true, time: getFormattedTime() });

  const makeExpertReply = (expertId, replyText) => {
    const expert = experts.find((e) => e.id === expertId);
    const expertName = expert ? expert.name : t('exportChat.defaultExpertName');
    return { id: Date.now() + expertId + Math.random(), text: replyText || t('exportChat.noReply'), isOwn: false, time: getFormattedTime() };
  };

   const simulateReplies = async (currentInputMessage) => {
     setIsLoading(true);
     const loadingMsg = { id: 'loading-' + Date.now(), isLoading: true, isOwn: false, time: getFormattedTime() };
     setMessages((prev) => [...prev, loadingMsg]);
     try {
       const expertsData = selectedExperts.map(expertId => {
         const expertInfo = experts.find(e => e.id === expertId);
         const chatExpertData = Array.isArray(chatExperts) ? chatExperts.find(ce => ce?.category === expertInfo?.category) : null;
         return {
           category: expertInfo?.category,
           role: chatExpertData?.analyze?.Role || expertInfo?.name || t('exportChat.defaultExpertName'),
           analyze: chatExpertData?.analyze?.Analyze || ''
         };
       }).filter(e => e.category);

        if (expertsData.length === 0) throw new Error(t('exportChat.error.noExpertSelected'));

       const results = await fetchJson('/api/chat/single', {
           story_id: newsData.story_id, user_id, room_id, prompt: currentInputMessage, categories_data: expertsData, language: getCurrentLocale(),
       });

       setMessages((prev) => prev.filter((m) => !m.isLoading));
       setIsLoading(false);

        const newReplies = (results.response || []).map((res, index) => {
             const expertId = selectedExperts[index];
             return makeExpertReply(expertId, res.chat_response);
         });

       newReplies.forEach((replyMsg, index) => {
         setTimeout(() => { setMessages((prev) => [...prev, replyMsg]); }, 500 + index * 300);
       });

       const chatHistoryForPrompt = `user:${currentInputMessage} ${newReplies.map(r => r.text).join(' ')}`;
       changeQuickPrompt(chatHistoryForPrompt);

     } catch (error) {
       console.error('Error fetching expert replies:', error);
       setMessages((prev) => prev.filter((m) => !m.isLoading));
       setIsLoading(false);
       setMessages((prev) => [
         ...prev, { id: Date.now() + 1, text: error.message || t('exportChat.error.serverError'), isOwn: false, time: getFormattedTime() },
       ]);
     }
   };

  const handlePromptSend = (promptText) => {
    if (!promptText || !promptText.trim() || isLoading) return;
    if (selectedExperts.length === 0) { alert(t('exportChat.placeholders.selectFirst')); return; }
    setMessages((prev) => [...prev, makeUserMsg(promptText)]);
    setInputMessage('');
    simulateReplies(promptText);
  };

  const handleSendMessage = () => {
    const messageToSend = inputMessage.trim();
    if (!messageToSend || isLoading) return;
    if (selectedExperts.length === 0) { alert(t('exportChat.placeholders.selectFirst')); return; }
    setMessages((prev) => [...prev, makeUserMsg(messageToSend)]);
    setInputMessage('');
    simulateReplies(messageToSend);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) handleSendMessage();
  };

  const availableExperts = useMemo(() => {
      // 優先使用 chatExperts 來決定可用的專家
      if (Array.isArray(chatExperts) && chatExperts.length > 0 && chatExperts[0] !== null) {
          const chatExpertCategories = chatExperts.map(ce => ce?.category).filter(Boolean);
          if (chatExpertCategories.length > 0) {
              return experts.filter(expert => chatExpertCategories.includes(expert.category));
          }
      }
      
      // 如果沒有 chatExperts，則使用 who_talk
      const whoTalkArray = parseWhoTalk(newsData?.who_talk);
      if (whoTalkArray.length === 0) {
          return newsData?.category ? experts.filter(expert => expert.category === newsData.category) : experts;
      }
      return experts.filter(expert => whoTalkArray.includes(expert.category));
  }, [chatExperts, newsData?.who_talk, newsData?.category]);

  // 🟢 (修復計數問題) 新增此 useEffect 來同步 selectedExperts 和 availableExperts
  useEffect(() => {
    const availableIds = new Set(availableExperts.map(e => e.id));
    
    setSelectedExperts(prevSelected => {
      const validSelected = prevSelected.filter(id => availableIds.has(id));
      
      // 如果所有選中的專家都失效了 (例如從無到有載入了新的專家列表)
      // 並且新的可用專家列表不為空，則預選第一位
      if (validSelected.length === 0 && availableExperts.length > 0) {
        return [availableExperts[0].id];
      }
      return validSelected;
    });
  }, [availableExperts]); // 當 availableExperts 列表變化時觸發

  return (
    <div className="chat">
      <div className="chat__header">
        <div className="chat__headerLeft">
          <div className="chat__icon">🤖</div>
          <div>
            <h3 className="chat__title">{t('exportChat.titles.chat')}</h3>
            <p className="chat__subtitle">{t('exportChat.subtitles.chat', { count: selectedExperts.length })}</p>
          </div>
        </div>
        <div className="chat__headerRight">
          {onClose && ( <button className="chat-close-btn" onClick={onClose} title={t('exportChat.tooltips.closeChat')}>✕</button> )}
        </div>
      </div>

      <div className="chat__expertSelector">
          <div className="dropdown" ref={dropdownRef}>
            <button type="button" className="dropdown__btn" onClick={() => setIsDropdownOpen((v) => !v)} disabled={availableExperts.length === 0}>
              <span>{t('exportChat.buttons.selectExperts')}</span>
              {selectedExperts.length > 0 && <span className="selectedCount">{selectedExperts.length}</span>}
              <span className={`dropdown__icon ${isDropdownOpen ? 'is-open' : ''}`}>▼</span>
            </button>
            {isDropdownOpen && availableExperts.length > 0 && (
              <div className="dropdown__menu">
                {availableExperts.map((expert) => {
                    const checked = selectedExperts.includes(expert.id);
                    return ( <div key={expert.id} className="dropdown__item" onClick={() => toggleExpert(expert.id)}>
                        <span>{expert.name}</span>
                        <span className={`checkbox ${checked ? 'is-checked' : ''}`} />
                      </div> );
                  })}
              </div>
            )}
          </div>
        </div>

        <div className="messages" data-messages-container>
          {messages.map((m) => (
            <div key={m.id} className={`message ${m.isOwn ? 'message--own' : ''} ${m.isLoading ? 'message--loading' : ''}`}>
              <div className={`bubble ${m.isOwn ? 'bubble--own' : ''} ${m.isLoading ? 'bubble--loading' : ''}`}>
                {m.isLoading ? ( <div className="loading-dots"><span/><span/><span/></div> ) : ( <ReactMarkdown>{m.text}</ReactMarkdown> )}
              </div>
              <span className="time">{m.time}</span>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

       {/* 快速提示區 */}
       <div className="prompt">
         {Array.isArray(quickPrompts) && quickPrompts.length > 0 && selectedExperts.length > 0 && !isLoading && (
           <div className="prompt__container">
             {quickPrompts.map((p, i) => ( <button key={i} type="button" className="prompt__item" onClick={() => handlePromptSend(p)} disabled={!p || !p.trim()}> {p} </button> ))}
           </div>
         )}
       </div>

        <div className="input">
          <input ref={inputRef} type="text" className="input__text"
            placeholder={selectedExperts.length === 0 ? t('exportChat.placeholders.selectFirst') : t('exportChat.placeholders.enterQuestion')}
            value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} onKeyPress={handleKeyPress}
            autoComplete="off" spellCheck="false" disabled={isLoading || selectedExperts.length === 0} />
          <button className="input__send" onClick={handleSendMessage} disabled={!inputMessage.trim() || isLoading || selectedExperts.length === 0}>
            {isLoading ? '...' : '➤'}
          </button>
        </div>
    </div>
  );
}

export default forwardRef(ChatRoom);