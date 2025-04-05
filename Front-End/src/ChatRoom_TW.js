// 引入 React 核心庫和必要的 Hooks
import React, { useState, useEffect, useRef } from 'react';
// 引入聊天室樣式
import './ChatRoom.css';

/**
 * 聊天室元件
 * @param {string} selectedRole - 目前所揀選欲對話的角色
 * @param {Array} initialMessages - 初始的聊天訊息
 * @param {Function} updateMessages - 用來更新親元組件內聊天紀錄的函式
 * @param {string} roleAnalyze - 角色的分析文本
 */
function ChatRoom({ selectedRole, messages: initialMessages, updateMessages, roleAnalyze }) {
  const [messages, setMessages] = useState(initialMessages);  // 聊天訊息的狀態
  const [newMessage, setNewMessage] = useState('');  // 新訊息輸入框狀態
  const [isLoading, setIsLoading] = useState(false);  // 加載狀態，用來顯示送出訊息時的加載指示
  const messagesEndRef = useRef(null);  // 引用訊息列表底部的元素，用於自動卷動

  // 當角色改變或初始訊息改變時，更新訊息
  useEffect(() => {
    // 若無初始訊息（第一次揀選角色）
    if (initialMessages.length === 0) {
      // 建立角色的初始招呼和分析文本
      const initialGreeting = `你好，我是${selectedRole}。\n對烏俄戰爭，我的分析是：\n${roleAnalyze}`;
      // 設定初始訊息：系統提示和角色招呼
      const initialMsgs = [
        { sender: 'system', text: `你已經揀著跟「${selectedRole}」對話` },
        { sender: selectedRole, text: initialGreeting }
      ];
      setMessages(initialMsgs);      // 更新本地狀態
      updateMessages(initialMsgs);   // 同步更新親元組件內的聊天紀錄
    } else {
      setMessages(initialMessages);  // 若有初始訊息，就直接採用
    }
  }, [selectedRole, initialMessages, roleAnalyze, updateMessages]);

  /**
   * 處理送出訊息
   * @param {Event} e - 表單送出事件
   */
  const handleSendMessage = async (e) => {
    e.preventDefault();    // 避免表單預設送出
    // 檢查訊息有內容且有揀角色
    if (newMessage.trim() && selectedRole) {
      const userMessage = { sender: '使用者', text: newMessage };  // 使用者的訊息物件
      const updatedMessages = [...messages, userMessage];          // 把使用者訊息加入列表

      setMessages(updatedMessages);      // 更新本地狀態
      updateMessages(updatedMessages);   // 更新親元組件的聊天紀錄
      setNewMessage('');                 // 清空輸入框
      setIsLoading(true);                // 顯示加載指示

      try {
        // 呼叫後端 API 拿角色回覆
        const response = await fetch('http://localhost:5000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            role: selectedRole,  // 送出所揀選的角色
            message: newMessage  // 送出使用者輸入的訊息
          }),
        });

        // 檢查 API 回傳是否成功
        if (!response.ok) {
          throw new Error('API request failed');
        }

        // 解析 API 的 JSON
        const data = await response.json();

        // 建立 AI 回覆訊息物件
        const aiMessage = { 
          sender: selectedRole,  // 發訊者是所揀選的角色
          text: data.response    // 回覆內容來自 API
        };
        // 把 AI 回覆加到訊息列表
        const newUpdatedMessages = [...updatedMessages, aiMessage];

        setMessages(newUpdatedMessages);      
        updateMessages(newUpdatedMessages);   
      } catch (error) {
        console.error("取得回覆發生錯誤：", error);  
        // 建立錯誤提示訊息
        const errorMessage = { 
          sender: 'system', 
          text: '發生錯誤，請等一下閣試看覓。' 
        };

        const newUpdatedMessages = [...updatedMessages, errorMessage];

        setMessages(newUpdatedMessages);
        updateMessages(newUpdatedMessages);
      } finally {
        setIsLoading(false);  // 不管成功失敗都把加載狀態關掉
      }
    }
  };

  // 渲染聊天室 UI
  return (
    <div className="chat-container">
      {/* 聊天訊息區塊 */}
      <div className="chat-messages">
        {/* 迴圈渲染所有訊息 */}
        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`message ${
              msg.sender === 'system' ? 'system-message'
              : msg.sender === '使用者' ? 'user-message'
              : 'role-message'
            }`}
          >
            {/* 若不是系統訊息就顯示發訊者 */}
            {msg.sender !== 'system' && <strong>{msg.sender}：</strong>} {msg.text}
          </div>
        ))}
        {/* 加載指示器，isLoading 時才顯示 */}
        {isLoading && (
          <div className="message system-message loading-message">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        {/* 用來自動滾動到底部的引用元素 */}
        <div ref={messagesEndRef} />
      </div>
      {/* 訊息輸入表單 */}
      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="輸入你的問題或看法..."
          className="chat-input"
          disabled={isLoading}
        />
        <button 
          type="submit" 
          className="send-button" 
          disabled={isLoading}
        >
          {isLoading ? '送出中...' : '送出'}
        </button>
      </form>
    </div>
  );
}

export default ChatRoom;
