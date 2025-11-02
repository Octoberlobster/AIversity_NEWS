import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'; // Added useMemo
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
  { id: 5, name: "生活達人", category: "Lifestyle & Consumer" },
  { id: 6, name: "體育專家", category: "Sports" },
  { id: 7, name: "娛樂專家", category: "Entertainment" },
  { id: 8, name: "財經專家", category: "Business & Finance" },
  { id: 9, name: "健康顧問", category: "Health & Wellness" },
];

// <<< REMOVED: Default prompts constant (will use t()) >>>

// 輔助函數：安全地解析 who_talk
const parseWhoTalk = (whoTalk) => {
  if (!whoTalk) return [];
  if (Array.isArray(whoTalk)) return whoTalk;
  if (typeof whoTalk === 'string') {
    try { const parsed = JSON.parse(whoTalk); return Array.isArray(parsed) ? parsed : []; }
    catch (error) { console.error('Error parsing who_talk JSON:', error); return []; }
  }
  if (typeof whoTalk === 'object' && whoTalk !== null && whoTalk.who_talk && Array.isArray(whoTalk.who_talk)) {
    return whoTalk.who_talk;
  }
  return [];
};

function updateExpertNamesByTopicExperts(topicExperts) {
  if (!Array.isArray(topicExperts)) return;
  topicExperts.forEach(item => {
    if (!item || !item.category) return;
    const expert = experts.find(e => e.category === item.category);
    if (expert && item.analyze?.Role) expert.name = item.analyze.Role;
  });
}

function TopicChatRoom({topic_id, topic_title, topic_who_talk, topicExperts, onClose}) {
  const { t } = useTranslation();
  const [selectedExperts, setSelectedExperts] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [quickPrompts, setQuickPrompts] = useState([]);

  // <<< MODIFIED: Use t() for default prompts >>>
  const DEFAULT_QUICK_PROMPTS_TOPIC = useMemo(() => [
      t('topicChat.prompts.default1', { topicTitle: topic_title || t('topicChat.defaultTopicTitle') }),
      t('topicChat.prompts.default2', { topicTitle: topic_title || t('topicChat.defaultTopicTitle') }),
      t('topicChat.prompts.default3', { topicTitle: topic_title || t('topicChat.defaultTopicTitle') })
  ], [t, topic_title]);

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

  useEffect(() => {
    const whoTalkArray = parseWhoTalk(topic_who_talk);
    const availableTopicExperts = experts.filter(expert =>
        whoTalkArray.length === 0 || whoTalkArray.includes(expert.category)
    );
    if (availableTopicExperts.length > 0) {
        setSelectedExperts(prevSelected => {
            const validSelected = prevSelected.filter(expertId => availableTopicExperts.some(e => e.id === expertId));
            if (validSelected.length === 0) return [availableTopicExperts[0].id];
            return validSelected;
        });
    } else {
        setSelectedExperts([]);
    }
  }, [topic_who_talk]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setIsDropdownOpen(false);
    };
    if (isDropdownOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isDropdownOpen]);

  useEffect(() => {
    updateExpertNamesByTopicExperts(topicExperts);
  }, [topicExperts]);

  useEffect(() => {
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.closest('[data-messages-container]');
      if (container) container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
      setMessages([{ id: Date.now() + Math.random(), text: t('exportChat.welcome.chat.greeting'), isOwn: false, time: getFormattedTime() }]);
  }, [t, getFormattedTime]);


  const loadQuickPrompts = useCallback(async (chat_content = '') => {
    setQuickPrompts(DEFAULT_QUICK_PROMPTS_TOPIC); // Set defaults initially

    if (selectedExperts.length === 0) {
        setQuickPrompts(DEFAULT_QUICK_PROMPTS_TOPIC); // Keep defaults if no expert
        return;
    }

    try {
      const options = selectedExperts.map(expertId => experts.find(e => e.id === expertId)?.category).filter(Boolean);
      if (options.length === 0) {
           setQuickPrompts(DEFAULT_QUICK_PROMPTS_TOPIC);
           return;
      }
      const response = await fetchJson('/api/hint_prompt/topic', {
        topic_id, room_id, user_id, option: options, chat_content, language: getCurrentLocale()
      });
      console.log('Fetched topic quick prompts:', response);
      const dynamicPrompts = (response && Array.isArray(response.Hint_Prompt)) ? response.Hint_Prompt.filter(p => p && p.trim()) : [];
      setQuickPrompts([...dynamicPrompts, ...DEFAULT_QUICK_PROMPTS_TOPIC]); // Combine dynamic with defaults
    } catch (error) {
      console.error('Error loading topic quick prompts:', error);
      setQuickPrompts(DEFAULT_QUICK_PROMPTS_TOPIC); // Fallback on error
    }
  }, [topic_id, topic_title, room_id, user_id, selectedExperts, t, getCurrentLocale, DEFAULT_QUICK_PROMPTS_TOPIC]); // Added DEFAULT to deps

  useEffect(() => {
    setQuickPrompts(DEFAULT_QUICK_PROMPTS_TOPIC); // Set defaults on mount/selection change
    if (selectedExperts.length > 0) {
      loadQuickPrompts();
    } else {
        setQuickPrompts(DEFAULT_QUICK_PROMPTS_TOPIC); // Ensure defaults if selection becomes empty
    }
  }, [selectedExperts, loadQuickPrompts, DEFAULT_QUICK_PROMPTS_TOPIC]); // Added DEFAULT to deps

  const toggleExpert = (id) => {
    setSelectedExperts((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  const makeUserMsg = (text) => ({ id: Date.now(), text, isOwn: true, time: getFormattedTime() });

  const makeExpertReply = (expertId, replyText) => {
      const expert = experts.find((e) => e.id === expertId);
      const expertName = expert ? expert.name : t('topicChat.defaultExpertName');
      return { id: Date.now() + expertId + Math.random(), text: replyText || t('topicChat.noReply'), isOwn: false, time: getFormattedTime() };
  };

   const simulateRepliesWithPrompt = async (promptText) => {
     setIsLoading(true);
     const loadingMsg = { id: 'loading-' + Date.now(), isLoading: true, isOwn: false, time: getFormattedTime() };
     setMessages((prev) => [...prev, loadingMsg]);
     try {
       const expertsData = selectedExperts.map(expertId => {
         const expertInfo = experts.find(e => e.id === expertId);
         const topicExpertData = Array.isArray(topicExperts) ? topicExperts.find(te => te?.category === expertInfo?.category) : null;
         return {
           category: expertInfo?.category,
           role: topicExpertData?.analyze?.Role || expertInfo?.name || t('topicChat.defaultExpertName'),
           analyze: topicExpertData?.analyze?.Analyze || ''
         };
       }).filter(e => e.category);

        if (expertsData.length === 0) throw new Error(t('exportChat.error.noExpertSelected'));

       const results = await fetchJson('/api/chat/topic', {
         topic_id, room_id, user_id, prompt: promptText, categories_data: expertsData, language: getCurrentLocale(),
       });

        setMessages((prev) => prev.filter(m => !m.isLoading));
        setIsLoading(false);

        const newReplies = (results.response || []).map((res, index) => {
             const expertId = selectedExperts[index];
             return makeExpertReply(expertId, res.chat_response);
        });

       newReplies.forEach((replyMsg, index) => {
         setTimeout(() => { setMessages((prev) => [...prev, replyMsg]); }, 500 + index * 300);
       });

       const chatHistoryForPrompt = `user:${promptText} ${newReplies.map(r => r.text).join(' ')}`;
       loadQuickPrompts(chatHistoryForPrompt);

     } catch (error) {
       console.error('Error fetching topic expert replies:', error);
       setMessages((prev) => prev.filter(m => !m.isLoading));
       setIsLoading(false);
       setMessages((prev) => [...prev, { id: Date.now() + 1, text: error.message || t('topicChat.error.serverError'), isOwn: false, time: getFormattedTime() }]);
     }
   };

  const handlePromptSend = (promptText) => {
    if (!promptText || !promptText.trim() || isLoading) return;
    if (selectedExperts.length === 0) { alert(t('exportChat.placeholders.selectFirst')); return; }
    setMessages((prev) => [...prev, makeUserMsg(promptText)]);
    setInputMessage('');
    simulateRepliesWithPrompt(promptText);
  };

  const handleSendMessage = () => {
    const currentInput = inputMessage.trim();
    if (!currentInput || isLoading) return;
    if (selectedExperts.length === 0) { alert(t('exportChat.placeholders.selectFirst')); return; }
    setMessages((prev) => [...prev, makeUserMsg(currentInput)]);
    setInputMessage('');
    simulateRepliesWithPrompt(currentInput);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) handleSendMessage();
  };

  const availableExperts = useMemo(() => {
      const whoTalkArray = parseWhoTalk(topic_who_talk);
      if (whoTalkArray.length === 0) return experts;
      return experts.filter(expert => whoTalkArray.includes(expert.category));
  }, [topic_who_talk]);

  return (
    <div className="chat">
      <div className="chat__header">
        <div className="chat__headerLeft">
          <div className="chat__icon">💬</div>
          <div>
            <h3 className="chat__title">{topic_title || t('topicChat.defaultTopicTitle')}</h3>
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

export default TopicChatRoom;