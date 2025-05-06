// 引入React核心庫和必要的鉤子函數
import React, { useState, useEffect, useRef } from 'react';
// 引入聊天室樣式
import './css/ChatRoom.css';

/**
 * 聊天室組件
 * @param {string} selectedRole - 當前選擇的角色
 * @param {Array} initialMessages - 初始聊天消息
 * @param {Function} updateMessages - 更新父組件中聊天歷史的函數
 * @param {string} roleAnalyze - 角色的分析文本
 */
function ChatRoom({ selectedRole, messages: initialMessages, updateMessages, roleAnalyze }) {
  const [messages, setMessages] = useState(initialMessages);  // 聊天消息狀態
  const [newMessage, setNewMessage] = useState('');  // 新消息輸入框狀態
  const [isLoading, setIsLoading] = useState(false);  // 加載狀態，用於顯示發送消息時的加載指示器
  const messagesEndRef = useRef(null);  // 引用消息列表底部的元素，用於自動滾動

  // 當選擇的角色改變或初始消息改變時更新消息
  useEffect(() => {
    // 如果沒有初始消息（首次選擇角色）
    if (initialMessages.length === 0) {
      // 創建角色的初始問候和分析文本
      const initialGreeting = `你好，我是${selectedRole}。\n對於烏俄戰爭，我的分析是：\n${roleAnalyze}`;
      // 設置初始消息：系統提示和角色問候
      const initialMsgs = [
        { sender: 'system', text: `您已選擇與${selectedRole}對話` },
        { sender: selectedRole, text: initialGreeting }
      ];
      setMessages(initialMsgs);      // 更新本地狀態
      updateMessages(initialMsgs);      // 同時更新父組件中的聊天歷史
    } else {
      setMessages(initialMessages);      // 如果有初始消息，直接使用它們
    }
  }, [selectedRole, initialMessages, roleAnalyze, updateMessages]); // 依賴項：當這些值變化時重新執行

  /**
   * 處理發送消息
   * @param {Event} e - 表單提交事件
   */
  const handleSendMessage = async (e) => {

    e.preventDefault();    // 阻止表單默認提交行為
    // 檢查消息是否為空且有選擇角色
    if (newMessage.trim() && selectedRole) {

      const userMessage = { sender: '使用者', text: newMessage };      // 創建用戶消息對象
      const updatedMessages = [...messages, userMessage];      // 將用戶消息添加到消息列表

      setMessages(updatedMessages);      // 更新本地狀態
      updateMessages(updatedMessages);      // 更新父組件中的聊天歷史
      setNewMessage('');      // 清空輸入框
      setIsLoading(true);      // 設置加載狀態為true
      
      try {
        // 調用後端API獲取角色回覆
        const response = await fetch('http://localhost:5000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            role: selectedRole,  // 發送選定的角色
            message: newMessage  // 發送用戶輸入的消息
          }),
        });
        
        // 檢查API響應是否成功
        if (!response.ok) {
          throw new Error('API request failed');
        }
        
        // 解析API返回的JSON數據
        const data = await response.json();
        
        // 創建AI回覆消息對象
        const aiMessage = { 
          sender: selectedRole,  // 發送者是選定的角色
          text: data.response    // 回覆內容來自API
        };
        // 將AI回覆添加到消息列表
        const newUpdatedMessages = [...updatedMessages, aiMessage];

        setMessages(newUpdatedMessages);        // 更新本地狀態
        updateMessages(newUpdatedMessages);        // 更新父組件中的聊天歷史
      } catch (error) {

        console.error("Error getting response:", error);        // 捕獲並記錄錯誤
        // 創建錯誤消息對象
        const errorMessage = { 
          sender: 'system', 
          text: '發生錯誤，請稍後再試。' 
        };

        const newUpdatedMessages = [...updatedMessages, errorMessage];        // 將錯誤消息添加到消息列表

        setMessages(newUpdatedMessages);        // 更新本地狀態
        updateMessages(newUpdatedMessages);        // 更新父組件中的聊天歷史
      } finally {
        setIsLoading(false);        // 無論成功或失敗，最終都將加載狀態設為false
      }
    }
  };

  // 渲染聊天室UI
  return (
    <div className="chat-container">
      {/* 聊天消息區域 */}
      <div className="chat-messages">
        {/* 遍歷並渲染所有消息 */}
        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`message ${
              // 根據發送者設置不同的CSS類
              msg.sender === 'system' ? 'system-message' : 
              msg.sender === '使用者' ? 'user-message' : 'role-message'
            }`}
          >
            {/* 非系統消息顯示發送者名稱 */}
            {msg.sender !== 'system' && <strong>{msg.sender}:</strong>} {msg.text}
          </div>
        ))}
        {/* 加載指示器，僅在isLoading為true時顯示 */}
        {isLoading && (
          <div className="message system-message loading-message">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        {/* 用於自動滾動的空div元素 */}
        <div ref={messagesEndRef} />
      </div>
      {/* 消息輸入表單 */}
      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="輸入您的問題或觀點..."
          className="chat-input"
          disabled={isLoading}  // 加載時禁用輸入
        />
        <button 
          type="submit" 
          className="send-button" 
          disabled={isLoading}  // 加載時禁用按鈕
        >
          {isLoading ? '發送中...' : '發送'}
        </button>
      </form>
    </div>
  );
}

export default ChatRoom;
