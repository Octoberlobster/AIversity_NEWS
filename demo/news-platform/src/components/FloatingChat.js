import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';

const FloatingChatContainer = styled.div`
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
  transition: all 0.3s ease;
`;

const ChatWindow = styled.div`
  width: ${props => props.isExpanded ? '100vw' : '60px'};
  height: ${props => props.isExpanded ? '100vh' : '60px'};
  background: white;
  border-radius: ${props => props.isExpanded ? '0' : '16px'};
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  transition: all 0.3s ease;
  border: ${props => props.isExpanded ? 'none' : '2px solid #667eea'};
  position: ${props => props.isExpanded ? 'fixed' : 'relative'};
  top: ${props => props.isExpanded ? '0' : 'auto'};
  left: ${props => props.isExpanded ? '0' : 'auto'};
`;

const ChatHeader = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #7c3aed 100%);
  color: white;
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  height: 60px;
`;

const HeaderContent = styled.div`
  display: flex;
  align-items: center;
  gap: 0.8rem;
`;

const ChatIcon = styled.div`
  font-size: 1.5rem;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const ChatTitle = styled.h3`
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
`;

const ChatSubtitle = styled.p`
  margin: 0;
  font-size: 0.8rem;
  opacity: 0.9;
`;

const ToggleButton = styled.button`
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
  }
`;

const NotificationBadge = styled.span`
  position: absolute;
  top: -5px;
  right: -5px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
`;

const ChatBody = styled.div`
  height: calc(100% - 60px);
  display: flex;
  flex-direction: column;
  opacity: ${props => props.isExpanded ? 1 : 0};
  transition: opacity 0.3s ease;
`;

const SearchSection = styled.div`
  padding: 1.5rem;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
`;

const SearchTitle = styled.h4`
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1.1rem;
  font-weight: 600;
`;

const SearchDescription = styled.p`
  margin: 0 0 1rem 0;
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.5;
`;

const MessagesContainer = styled.div`
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  background: #fafafa;
`;

const Message = styled.div`
  display: flex;
  flex-direction: column;
  align-items: ${props => props.isOwn ? 'flex-end' : 'flex-start'};
`;

const MessageBubble = styled.div`
  background: ${props => props.isOwn ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#f1f5f9'};
  color: ${props => props.isOwn ? 'white' : '#333'};
  padding: 0.8rem 1.2rem;
  border-radius: 16px;
  max-width: 80%;
  word-wrap: break-word;
  font-size: 0.9rem;
  line-height: 1.4;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const MessageTime = styled.span`
  font-size: 0.7rem;
  color: #6b7280;
  margin-top: 0.2rem;
`;

const InputContainer = styled.div`
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
  background: white;
`;

const MessageInput = styled.input`
  flex: 1;
  padding: 0.8rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  outline: none;
  font-size: 0.9rem;
  
  &:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const SendButton = styled.button`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  }
  
  &:disabled {
    background: #d1d5db;
    cursor: not-allowed;
    transform: none;
  }
`;

const QuickPrompts = styled.div`
  padding: 1rem;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
  max-height: 80px;
  overflow-y: auto;
`;

const PromptButton = styled.button`
  background: #f3f4f6;
  color: #4b5563;
  border: none;
  border-radius: 12px;
  padding: 0.4rem 0.8rem;
  font-size: 0.8rem;
  margin: 0.2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: #667eea;
    color: white;
  }
`;

// 快速提示
const quickPrompts = [
  "搜尋最新科技新聞",
  "分析今日股市趨勢",
  "推薦熱門話題",
  "查找相關報導",
  "總結新聞重點"
];

function FloatingChat() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [unreadCount, setUnreadCount] = useState(2);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const toggleChat = () => {
    setIsExpanded(!isExpanded);
    if (!isExpanded) {
      setUnreadCount(0);
    }
  };

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      const userMsg = {
        id: Date.now(),
        text: newMessage,
        isOwn: true,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, userMsg]);
      setNewMessage('');
      
      // 模擬AI助手回覆
      setTimeout(() => {
        const reply = {
          id: Date.now() + 1,
          text: `我是您的智慧搜尋助手！我正在為您搜尋相關資訊...\n\n根據我的分析，${newMessage}相關的最新報導包括：\n• 相關新聞1\n• 相關新聞2\n• 相關新聞3\n\n需要我為您深入分析某個特定主題嗎？`,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, reply]);
      }, 1000);
    }
  };

  const handleQuickPrompt = (prompt) => {
    setNewMessage(prompt);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <FloatingChatContainer>
      <ChatWindow isExpanded={isExpanded}>
        <ChatHeader onClick={toggleChat}>
          <HeaderContent>
            <ChatIcon>🔍</ChatIcon>
            {isExpanded && (
              <div>
                <ChatTitle>智慧搜尋助手</ChatTitle>
                <ChatSubtitle>AI 驅動的新聞搜尋與分析</ChatSubtitle>
              </div>
            )}
          </HeaderContent>
          <div style={{ position: 'relative' }}>
            <ToggleButton>
              {isExpanded ? '×' : '+'}
            </ToggleButton>
            {!isExpanded && unreadCount > 0 && (
              <NotificationBadge>{unreadCount}</NotificationBadge>
            )}
          </div>
        </ChatHeader>
        
        {isExpanded && (
          <ChatBody isExpanded={isExpanded}>
            <SearchSection>
              <SearchTitle>🔍 智慧搜尋</SearchTitle>
              <SearchDescription>
                輸入任何關鍵字、問題或主題，我將為您搜尋相關新聞、提供分析見解，並推薦相關報導。
                支援自然語言查詢，讓您快速找到所需資訊。
              </SearchDescription>
            </SearchSection>
            
            <MessagesContainer>
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔍</div>
                  <h3>歡迎使用智慧搜尋助手</h3>
                  <p>請輸入您想搜尋的新聞主題或問題</p>
                </div>
              )}
              {messages.map(message => (
                <Message key={message.id} isOwn={message.isOwn}>
                  <MessageBubble isOwn={message.isOwn}>
                    {message.text}
                  </MessageBubble>
                  <MessageTime>{message.time}</MessageTime>
                </Message>
              ))}
              <div ref={messagesEndRef} />
            </MessagesContainer>
            
            <QuickPrompts>
              {quickPrompts.map((prompt, index) => (
                <PromptButton
                  key={index}
                  onClick={() => handleQuickPrompt(prompt)}
                >
                  {prompt}
                </PromptButton>
              ))}
            </QuickPrompts>
            
            <InputContainer>
              <MessageInput
                type="text"
                placeholder="輸入您想搜尋的新聞主題或問題..."
                value={newMessage}
                onChange={e => setNewMessage(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <SendButton
                onClick={handleSendMessage}
                disabled={!newMessage.trim()}
              >
                ➤
              </SendButton>
            </InputContainer>
          </ChatBody>
        )}
      </ChatWindow>
    </FloatingChatContainer>
  );
}

export default FloatingChat; 