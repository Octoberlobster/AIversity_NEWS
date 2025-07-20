import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';

const ChatContainer = styled.div`
  flex: 1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: 600px;
`;

const ChatHeader = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem;
  border-radius: 12px 12px 0 0;
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const ChatTitle = styled.h3`
  margin: 0;
  font-size: 1.1rem;
`;

const MessagesContainer = styled.div`
  flex: 1 1 0;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
`;

const Message = styled.div`
  display: flex;
  flex-direction: column;
  align-items: ${props => props.isOwn ? 'flex-end' : 'flex-start'};
`;

const MessageBubble = styled.div`
  background: ${props => props.isOwn ? '#667eea' : '#f1f5f9'};
  color: ${props => props.isOwn ? 'white' : '#333'};
  padding: 0.75rem 1rem;
  border-radius: 18px;
  max-width: 80%;
  word-wrap: break-word;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const MessageTime = styled.span`
  font-size: 0.75rem;
  color: #666;
  margin-top: 0.25rem;
`;

const InputContainer = styled.div`
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
`;

const MessageInput = styled.input`
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 25px;
  outline: none;
  font-size: 0.9rem;
  &:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const SendButton = styled.button`
  background: #667eea;
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s ease;
  &:hover {
    background: #764ba2;
  }
  &:disabled {
    background: #d1d5db;
    cursor: not-allowed;
  }
`;

const assistant = { name: "AI 新聞助理", avatar: "🤖" };

function GlobalAssistantChat() {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      const userMsg = {
        id: Date.now(),
        text: newMessage,
        isOwn: true,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
      };
      setMessages([...messages, userMsg]);
      setNewMessage('');
      setTimeout(() => {
        const reply = {
          id: Date.now() + 1,
          text: "您好，我是全域AI新聞助理，能結合各領域專家知識為您解答！有任何新聞、科技、金融、環境、醫療等問題都可以問我。",
          isOwn: false,
          expert: assistant.name,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, reply]);
      }, 1000);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <ChatContainer>
      <ChatHeader>
        <span style={{ fontSize: '1.5rem', marginRight: '0.5rem' }}>{assistant.avatar}</span>
        <ChatTitle>{assistant.name}</ChatTitle>
      </ChatHeader>
      <MessagesContainer>
        {messages.map(message => (
          <Message key={message.id} isOwn={message.isOwn}>
            <MessageBubble isOwn={message.isOwn}>
              {message.isOwn ? message.text : <><b>{assistant.name}：</b>{message.text}</>}
            </MessageBubble>
            <MessageTime>{message.time}</MessageTime>
          </Message>
        ))}
        <div ref={messagesEndRef} />
      </MessagesContainer>
      <InputContainer>
        <MessageInput
          type="text"
          placeholder={"請輸入訊息..."}
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
    </ChatContainer>
  );
}

export default GlobalAssistantChat; 