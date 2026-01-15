import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { useTranslation } from 'react-i18next';
import i18n from 'i18next';
import './../css/ChatRoom.css';
import { useLocation } from 'react-router-dom';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { fetchJson } from './api';
import { supabase } from './supabase.js';

// <<< REMOVED: Default prompts constant >>>

function FloatingChat() {
  const { t } = useTranslation(); // Get t function
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [quickPrompts, setQuickPrompts] = useState([]); // Initialize as empty
  const [isLoading, setIsLoading] = useState(false);

  // <<< MODIFIED: Use t() for default prompts >>>
  const DEFAULT_QUICK_PROMPTS = useMemo(() => [
    t('floatingChat.prompts.default1'),
    t('floatingChat.prompts.default2'),
  ], [t]);


  // 根據當前語言獲取對應的區域代碼
  const getCurrentLocale = useCallback(() => {
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
  }, [i18n.language]);

  // 獲取格式化的時間字符串
  const getFormattedTime = useCallback(() => {
    return new Date().toLocaleTimeString(getCurrentLocale(), {
      hour: '2-digit',
      minute: '2-digit'
    });
  }, [getCurrentLocale]);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const location = useLocation();
  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  // 根據當前路徑獲取語言並生成路由
  const getLanguageRoute = useCallback((path) => {
    const pathSegments = location.pathname.split('/');
    const langCode = pathSegments[1];
    const currentLang = ['zh-TW', 'en', 'jp', 'id'].includes(langCode) ? langCode : 'zh-TW';
    return `/${currentLang}${path}`;
  }, [location.pathname]);

  const fixedPrompts = useMemo(() => [
    t('floatingChat.prompts.recentNews'),
  ], [t]);

  // 滾動到底
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch quickPrompts 從後端獲取資料
  useEffect(() => {
    let isMounted = true;
    const fetchQuickPrompts = async () => {
      try {
        const response = await fetchJson('/api/hint_prompt/search', {
          language: getCurrentLocale()
        });
        if (isMounted) {
          const dynamicPrompts = response.Hint_Prompt || [];
          // <<< MODIFIED: Combine fetched with fixed >>>
          setQuickPrompts([...fixedPrompts, ...dynamicPrompts].filter(p => p && p.trim())); // Filter empty prompts
        }
      } catch (error) {
        if (isMounted) {
          console.error('Error fetching quick prompts:', error);
          // <<< MODIFIED: Use fixed + default prompts on error >>>
          setQuickPrompts([...fixedPrompts, ...DEFAULT_QUICK_PROMPTS].filter(p => p && p.trim())); // Filter empty prompts
        }
      }
    };
    // <<< MODIFIED: Add default prompts immediately >>>
    setQuickPrompts([...fixedPrompts, ...DEFAULT_QUICK_PROMPTS].filter(p => p && p.trim())); // Show defaults initially and filter
    fetchQuickPrompts();

    return () => {
      isMounted = false;
    };
     // <<< MODIFIED: Run only when fixedPrompts or language changes >>>
  }, [fixedPrompts, getCurrentLocale, DEFAULT_QUICK_PROMPTS]); // Added DEFAULT_QUICK_PROMPTS to dependencies

  // 詳情頁不顯示
  const isSpecialReportPage = location.pathname.includes('/special-report/');
  const isNewsDetailPage = location.pathname.includes('/news/'); // Use includes for broader matching
  if (isSpecialReportPage || isNewsDetailPage) return null;


  const toggleChat = () => setIsExpanded((v) => !v);

  // 語言後綴映射
  const LANGUAGE_SUFFIX_MAP = {
    'zh-TW': '',
    'en': '_en_lang',
    'jp': '_jp_lang',
    'id': '_id_lang'
  };

  const handleSendMessage = async (customMessage = null) => {
    const text = (customMessage ?? newMessage).trim();
    if (!text) return;

    const now = getFormattedTime();

    // 新增使用者訊息
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), text, isOwn: true, time: now, type: 'text' },
    ]);
    setNewMessage('');

    setIsLoading(true);

    // 添加載入訊息
    const loadingMsg = {
      id: 'loading-' + Date.now(),
      type: 'text',
      isLoading: true,
      isOwn: false,
      time: getFormattedTime(),
    };
    setMessages((prev) => [...prev, loadingMsg]);

    try {
      // 呼叫後端 API
      const response = await fetchJson('/api/chat/search', {
        user_id: user_id,
        room_id: room_id,
        prompt: text,
        category: ['search'], // Always 'search' for FloatingChat
        language: getCurrentLocale(),
      });

      // 處理後端回應
      const reply = response.response || [];
      console.log('後端回應:', reply);

      // 移除載入訊息
      setMessages((prev) => prev.filter(m => !m.isLoading));
      setIsLoading(false);

      // 先處理普通訊息
      const textMessages = reply
        .map((item) => ({
          id: Date.now() + Math.random(),
          type: 'text',
          text: item.chat_response,
          isOwn: false,
          time: getFormattedTime(),
        }));

      setMessages((prev) => [...prev, ...textMessages]);

      // 根據 i18n 狀態手動建構查詢
      const currentLangCode = i18n.language || 'zh-TW';
      const suffix = LANGUAGE_SUFFIX_MAP[currentLangCode] || '';
      const titleField = 'news_title' + suffix;
      const shortField = 'ultra_short' + suffix;

      // 構建 select 查詢字串 (總是包含預設欄位作為 fallback, 加上圖片)
      // ===== TASK 1 MODIFICATION (1/3): Add generated_date =====
      const selectFields = `story_id, news_title, ultra_short, generated_date, generated_image(image)${suffix ? `, ${titleField}, ${shortField}` : ''}`;

      // 延遲處理新聞訊息
      const newsMessagesPromises = reply
        .filter((item) => item.news_id && Array.isArray(item.news_id))
        .flatMap(item => // Use flatMap to handle potential nested arrays if backend changes
            item.news_id.map(async (newsId) => {
                try {
                    const { data, error } = await supabase
                      .from('single_news')
                      .select(selectFields)
                      .eq('story_id', newsId)
                      .maybeSingle(); // Use maybeSingle to handle null data gracefully

                    if (error) {
                      console.error('Error fetching news:', error);
                      return null;
                    }

                     if (!data) {
                         console.warn(`News data not found for story_id: ${newsId}`);
                         return null;
                     }

                    // Extract image safely
                    const imageBase64 = data.generated_image && Array.isArray(data.generated_image) && data.generated_image.length > 0
                                        ? data.generated_image[0]?.image
                                        : (data.generated_image && typeof data.generated_image === 'object' ? data.generated_image.image : null);

                    if (!imageBase64) {
                        console.warn(`Image data not found for story_id: ${newsId}`);
                        // Optionally return a placeholder or skip
                    }

                    // ===== TASK 1 MODIFICATION (2/3): Add generated_date to object =====
                    return {
                      id: newsId + Math.random(), // Use newsId + random for key
                      type: 'news',
                      // 優先使用語言欄位，若無則 fallback 至預設欄位
                      title: data[titleField] || data.news_title || t('floatingChat.newsImage.noTitle'), // Add fallback title
                      image: imageBase64, // Store base64 string
                      ultra_short: data[shortField] || data.ultra_short || '', // Add fallback short description
                      generated_date: data.generated_date, // <-- Added this
                      newsId,
                      isOwn: false,
                      time: getFormattedTime(),
                    };
                } catch (fetchError) {
                    console.error(`Error processing news ID ${newsId}:`, fetchError);
                    return null;
                }
          })
        );

        const resolvedNewsMessages = (await Promise.all(newsMessagesPromises)).filter(Boolean);


      // 延遲顯示新聞訊息
      setTimeout(() => {
        setMessages((prev) => [...prev, ...resolvedNewsMessages]);
      }, 500); // Shorter delay

    } catch (error) {
      console.error('Error fetching chat response:', error);
      // 移除載入訊息
      setMessages((prev) => prev.filter(m => !m.isLoading));
      setIsLoading(false);

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          text: t('floatingChat.error.serverError'),
          isOwn: false,
          time: getFormattedTime(),
        },
      ]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) handleSendMessage(); // Prevent sending while loading
  };

  // 新版 handlePromptSend：直接送出，而不是塞進 input
  const handlePromptSend = (promptText) => {
    if (!promptText || !promptText.trim() || isLoading) return; // Prevent sending empty/while loading
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
            aria-label={t('floatingChat.aria.expand')}
            title={t('floatingChat.aria.expand')}
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
                  <h3 className="chat__title">{t('floatingChat.title')}</h3>
                  <p className="chat__subtitle">{t('floatingChat.subtitle')}</p>
                </div>
              </div>
              <div className="chat__headerRight">
                <button
                  type="button"
                  className="chat-close-btn"
                  onClick={toggleChat}
                  aria-label={t('floatingChat.aria.collapse')}
                  title={t('floatingChat.aria.collapse')}
                >
                  ×
                </button>
              </div>
            </div>

            {/* 搜尋說明區 */}
            <div className="chat__expertSelector">
              {t('floatingChat.description')}
            </div>

            {/* 訊息區 */}
            <div className="messages" data-messages-container> {/* Added data attribute */}
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔍</div>
                  <h3>{t('floatingChat.welcome.title')}</h3>
                  <p>{t('floatingChat.welcome.message')}</p>
                </div>
              )}

              {messages.map((m) => {
                if (m.type === 'news') {
                   // Skip rendering if image is missing or invalid
                   if (!m.image) return null;
                  return (
                    <div key={m.id} className="message message--news">
                      <div
                        className="bubble bubble--news"
                        onClick={() => window.open(getLanguageRoute(`/news/${m.newsId}`), '_blank')}
                        style={{ cursor: 'pointer' }}
                      >
                         {/* <<< MODIFIED: Construct data URL for image >>> */}
                        <img
                           src={`data:image/png;base64,${m.image.replace(/\s/g, '')}`}
                           alt={t('floatingChat.newsImage.alt')}
                           onError={(e) => { e.target.style.display = 'none'; }} // Hide broken images
                        />
                        <div>
                          <h4>{m.title}</h4>
                          {/* ===== TASK 1 MODIFICATION (3/3): Display the date ===== */}
                          {m.generated_date && (
                            <span className="news-card-date" style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '0.5rem', display: 'block' }}>
                              {/* 使用 getCurrentLocale() 來確保日期格式正確 */}
                              {new Date(m.generated_date).toLocaleDateString(getCurrentLocale(), { year: 'numeric', month: '2-digit', day: '2-digit' })}
                            </span>
                          )}
                          <p>{m.ultra_short}</p>
                        </div>
                      </div>
                      <span className="time">{m.time}</span> {/* Changed class name */}
                    </div>
                  );
                } else {
                  return (
                    <div
                      key={m.id}
                      className={`message ${m.isOwn ? 'message--own' : ''} ${m.isLoading ? 'message--loading' : ''}`}
                    >
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
                      <span className="time">{m.time}</span> {/* Changed class name */}
                    </div>
                  );
                }
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* 快速提示區 */}
            {/* <<< MODIFIED: Check quickPrompts length >>> */}
            {Array.isArray(quickPrompts) && quickPrompts.length > 0 && !isLoading && (
              <div className="prompt">
                <div className="prompt__container">
                  {quickPrompts.map((p, i) => (
                    <button
                      key={i}
                      type="button"
                      className="prompt__item"
                      onClick={() => handlePromptSend(p)}
                      // <<< ADDED: Prevent sending empty prompts >>>
                      disabled={!p || !p.trim()}
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
                placeholder={t('floatingChat.placeholders.input')}
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                autoComplete="off"
                spellCheck="false"
                disabled={isLoading} // Disable input while loading
              />
              <button
                className="input__send"
                onClick={() => handleSendMessage()}
                disabled={!newMessage.trim() || isLoading} // Disable button while loading or if input is empty
              >
                {isLoading ? '...' : '➤'} {/* Show loading indicator */}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default FloatingChat;