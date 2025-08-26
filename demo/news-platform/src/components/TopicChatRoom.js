import React, { useState, useRef, useEffect } from 'react';
import { getOrCreateUserId, createRoomId } from './utils.js';
import { useParams } from 'react-router-dom';
import { fetchJson } from './api';
import './../css/TopicChatRoom.css';

const specialReportData = {
  1: {
    id: 1,
    title: "2025罷免案",
    summary: "國民黨與民眾黨2024年起聯手以人數優勢陸續通過國會職權等修法引發不滿，民團2025年起陸續鎖定國民黨立委發動罷免連署。24位藍委及新竹市長高虹安罷免案7月26日投開票，25案全數遭到否決。第二波共7案罷免投票將在8月23日登場，包括國民黨立委馬文君、游顥、羅明才、江啟臣、楊瓊瓔、顏寬恒、林思銘。",
    icon: "🗳️",
    events: [
      "即時開票",
    ],
    articles: 15,
    views: "25.3k",
    lastUpdate: "2025/7/30 18:10",
    eventDetails: {
      "即時開票": {
        title: "即時開票結果",
        summary: "最新罷免投票開票結果，包含各選區投票率、同意票與不同意票統計。",
        articles: [
          { 
            id: 101, 
            title: "大罷免投票率平均破5成5 傅崐萁案破6成創紀錄", 
            views: "12.5k", 
            date: "2025/7/26 22:55", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 3,
            shortSummary: "2025年7月26日舉行的罷免投票中，整體投票率平均突破55%，其中傅崐萁案的投票率更突破60%，創下歷史新高。各選區的投票情況顯示民眾對罷免案的高度關注。",
            relatedNews: [
              { id: 1011, title: "傅崐萁罷免案詳細分析" },
              { id: 1012, title: "各選區投票率統計" },
              { id: 1013, title: "罷免案投票結果影響" }
            ],
            keywords: ["投票", "罷免", "統計"]
          },
          { 
            id: 102, 
            title: "2025立委罷免案開票結果一覽 7月26日24案全數不通過", 
            views: "8.9k", 
            date: "2025/7/26 16:00", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 4,
            shortSummary: "7月26日舉行的24個立委罷免案全部未通過門檻，顯示選民對罷免制度的態度趨於保守。各案投票結果分析顯示，反對罷免的票數明顯高於支持罷免。",
            relatedNews: [
              { id: 1021, title: "罷免制度檢討聲浪" },
              { id: 1022, title: "選民態度分析報告" },
              { id: 1023, title: "政治影響評估" }
            ],
            keywords: ["罷免", "制度", "分析"]
          },
          { 
            id: 103, 
            title: "高虹安鄭正鈐罷免案即時開票 中央社圖表掌握實況", 
            views: "15.2k", 
            date: "2025/7/26 15:00", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 2,
            shortSummary: "新竹市長高虹安與立委鄭正鈐的罷免案開票過程透過中央社即時圖表呈現，讓民眾能夠第一時間掌握投票進度與結果。",
            relatedNews: [
              { id: 1031, title: "高虹安罷免案背景" },
              { id: 1032, title: "鄭正鈐政治立場" },
              { id: 1033, title: "新竹市政治情勢" }
            ],
            keywords: ["高虹安", "鄭正鈐", "新竹"]
          }
        ]
      },
    }
  }
};


function TopicChatRoom(){
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isPromptDropdownOpen, setIsPromptDropdownOpen] = useState(false);
  const [quickPrompts, setQuickPrompts] = useState([]);
  const { id } = useParams();
  const report = specialReportData[id];
  const [activeEvent, setActiveEvent] = useState(report?.events[0] || '');
  
  const promptDropdownRef = useRef(null);
  const user_id = getOrCreateUserId();
  const roomIdRef = useRef(createRoomId());
  const room_id = roomIdRef.current;

  // 點擊外部關閉下拉
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (promptDropdownRef.current && !promptDropdownRef.current.contains(e.target)) {
        setIsPromptDropdownOpen(false);
      }
    };
    if (isPromptDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isPromptDropdownOpen]);

  // 載入快速提示
  useEffect(() => {
    const loadQuickPrompts = async () => {
      try {
        const response = await fetchJson('/hint_prompt/single', {
          option: ['Special Report'], // 專題報導類別
          article: report,
        });
        console.log('Fetched quick prompts:', response);
        setQuickPrompts(response.Hint_Prompt || []);
      } catch (error) {
        console.error('Error loading quick prompts:', error);
        // 如果API失敗，使用預設提示
        setQuickPrompts([
          "分析這個專題的主要議題",
          "提供相關背景資訊", 
          "專家如何看待這個議題？",
          "這個專題的未來發展趨勢",
          "有什麼值得關注的重點？"
        ]);
      }
    };

    loadQuickPrompts();
  }, [report]);

  const handlePromptSend = (promptText) => {
    setChatInput(promptText);
    setIsPromptDropdownOpen(false);
    // 自動發送訊息
    setTimeout(() => {
      handleSendMessage();
    }, 100);
  };


  const handleSendMessage = () => {
    if (!chatInput.trim()) return;
    const userMsg = {
      id: Date.now(),
      text: chatInput,
      isOwn: true,
      time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');

    setTimeout(() => {
      const reply = {
        id: Date.now() + 1,
        text: `關於「${report.title}」這個專題，我可以為您提供深入分析。您提到的內容與專題中的「${activeEvent}」部分相關。需要我為您詳細解釋某個特定觀點嗎？`,
        isOwn: false,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages((prev) => [...prev, reply]);
    }, 1000);
  };

  const handleKeyPress = (e) => {
  if (e.key === 'Enter') handleSendMessage();
  };

  return (
    <div className="modern-chat-container">
      {/* 歡迎區域 */}
      <div className="chat-welcome">
        <div className="chat-welcome-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" 
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="chat-welcome-text">
          <h3>專題討論</h3>
          <p>與AI助手討論這個專題的相關議題</p>
        </div>
      </div>

      {/* 聊天訊息區域 */}
      <div className="chat-messages-container">
        <div className="chat-messages">
          {chatMessages.length === 0 ? (
            <div className="welcome-message">
              <div className="welcome-bubble">
                <p>👋 歡迎討論「{report?.title}」這個專題！</p>
                <p>您可以詢問任何相關問題。</p>
              </div>
            </div>
          ) : (
            chatMessages.map((message) => (
              <div key={message.id} className={`message ${message.isOwn ? 'user' : 'ai'}`}>
                <div className="message-bubble">
                  <p>{message.text}</p>
                  <span className="message-time">{message.time}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 快速提示按鈕 - 下拉選單方式 */}
      <div className="chat-quick-actions">
        <div className="prompt-dropdown-wrapper" ref={promptDropdownRef}>
          <button
            type="button"
            className="prompt-dropdown-btn"
            onClick={() => setIsPromptDropdownOpen(!isPromptDropdownOpen)}
          >
            <span>💡 快速提示</span>
            <span className={`dropdown-icon ${isPromptDropdownOpen ? 'is-open' : ''}`}>▼</span>
          </button>

          {isPromptDropdownOpen && (
            <div className="prompt-dropdown-menu">
              {quickPrompts.map((prompt, index) => (
                <div 
                  key={index} 
                  className="prompt-dropdown-item" 
                  onClick={() => handlePromptSend(prompt)}
                >
                  {prompt}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 輸入區域 */}
      <div className="chat-input-container">
        <div className="input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder="輸入您的問題或觀點..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button
            className="send-button"
            onClick={handleSendMessage}
            disabled={!chatInput.trim()}
            title="發送訊息"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}


// quickPrompts
export default TopicChatRoom;