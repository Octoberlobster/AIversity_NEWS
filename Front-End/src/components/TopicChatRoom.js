import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from 'i18next';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { fetchJson } from './api';
import './../css/ChatRoom.css';
import ReactMarkdown from 'react-markdown';

function TopicChatRoom({topic_id, topic_title, onClose}) {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);

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
  const inputRef = useRef(null);
  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

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
      const response = await fetchJson('/hint_prompt/topic', {
        topic_id: topic_id,
        room_id: room_id,
        user_id: user_id,
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
  }, [topic_id, topic_title, room_id, user_id, t]);

  useEffect(() => {
    loadQuickPrompts();
  }, [loadQuickPrompts]); // 現在可以安全地添加 loadQuickPrompts 作為依賴

  const handlePromptSend = (promptText) => {
    if (!promptText.trim()) {
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
    try {
      const response = await fetchJson('/chat/topic', {
        topic_id: topic_id,
        room_id: room_id,
        user_id: user_id,
        prompt: promptText,
      });
      
      console.log(response);
      
      // 處理AI回覆
      setTimeout(() => {
        const reply = {
          id: Date.now() + 1,
          text: response.response[0].chat_response,
          isOwn: false,
          time: getFormattedTime()
        };
        setMessages((prev) => [...prev, reply]);
      }, 1000);
      
      // 更新快速提示
      loadQuickPrompts("user:" + promptText + " assistant:" + response.response[0].chat_response);
    } catch (error) {
      console.error('Error fetching response:', error);
    }
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

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
            <p className="chat__subtitle">{t('topicChat.subtitle', { topicTitle: topic_title })}</p>
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
          <div key={m.id} className={`message ${m.isOwn ? 'message--own' : ''}`}>
            <div className={`bubble ${m.isOwn ? 'bubble--own' : ''}`}>
              <ReactMarkdown>{m.text}</ReactMarkdown>
            </div>
            <span className="time">{m.time}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 快速提示區域 */}
      <div className="prompt">
        {quickPrompts.length > 0 && (
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
          placeholder={t('topicChat.input.placeholder')}
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