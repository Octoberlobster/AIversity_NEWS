import React, { useState, useRef, useEffect } from 'react';
import styled, { css } from 'styled-components';

const ChatContainer = styled.div`
  flex: 1;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  height: 700px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
`;

const ChatHeader = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.2rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
`;

const HeaderLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 0.8rem;
`;

const ChatIcon = styled.div`
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
`;

const ChatTitle = styled.h3`
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
`;

const ChatSubtitle = styled.p`
  margin: 0;
  font-size: 0.85rem;
  opacity: 0.9;
`;

const ExpertSelector = styled.div`
  padding: 0.8rem 1.5rem;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
  position: relative;
`;

const DropdownContainer = styled.div`
  position: relative;
  display: inline-block;
`;

const DropdownButton = styled.button`
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  min-width: 200px;
  
  &:hover {
    border-color: #667eea;
    box-shadow: 0 2px 4px rgba(102, 126, 234, 0.1);
  }
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const DropdownIcon = styled.span`
  font-size: 0.8rem;
  transition: transform 0.2s ease;
  transform: ${props => props.isOpen ? 'rotate(180deg)' : 'rotate(0deg)'};
`;

const DropdownMenu = styled.div`
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 0.5rem;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }
`;

const DropdownItem = styled.div`
  padding: 0.8rem 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: background 0.2s ease;
  border-bottom: 1px solid #f3f4f6;
  
  &:hover {
    background: #f8fafc;
  }
  
  &:last-child {
    border-bottom: none;
  }
`;

const Checkbox = styled.div`
  width: 16px;
  height: 16px;
  border: 2px solid ${props => props.checked ? '#667eea' : '#d1d5db'};
  border-radius: 3px;
  background: ${props => props.checked ? '#667eea' : 'transparent'};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  
  &::after {
    content: '✓';
    color: white;
    font-size: 0.7rem;
    font-weight: bold;
    opacity: ${props => props.checked ? 1 : 0};
    transition: opacity 0.2s ease;
  }
`;

const SelectedCount = styled.span`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.5rem;
`;

const MessagesContainer = styled.div`
  flex: 1;
  padding: 1.2rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: #fafafa;
  scroll-behavior: smooth;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }
`;

const Message = styled.div`
  display: flex;
  flex-direction: column;
  align-items: ${props => props.isOwn ? 'flex-end' : 'flex-start'};
`;

const MessageBubble = styled.div`
  background: ${props => props.isOwn ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'white'};
  color: ${props => props.isOwn ? 'white' : '#374151'};
  padding: 0.8rem 1.2rem;
  border-radius: 18px;
  max-width: 85%;
  word-wrap: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  line-height: 1.5;
  font-size: 0.95rem;
`;

const MessageTime = styled.span`
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.3rem;
  font-weight: 500;
`;

const PromptContainer = styled.div`
  padding: 0.8rem 1.5rem;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
  position: relative;
`;

const PromptDropdownContainer = styled.div`
  position: relative;
  display: inline-block;
`;

const PromptDropdownButton = styled.button`
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  min-width: 180px;
  
  &:hover {
    border-color: #667eea;
    box-shadow: 0 2px 4px rgba(102, 126, 234, 0.1);
  }
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const PromptDropdownIcon = styled.span`
  font-size: 0.8rem;
  transition: transform 0.2s ease;
  transform: ${props => props.isOpen ? 'rotate(180deg)' : 'rotate(0deg)'};
`;

const PromptDropdownMenu = styled.div`
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 250px;
  overflow-y: auto;
  margin-bottom: 0.5rem;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }
`;

const PromptDropdownItem = styled.div`
  padding: 0.8rem 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: background 0.2s ease;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.9rem;
  color: #374151;
  
  &:hover {
    background: #f8fafc;
    color: #667eea;
  }
  
  &:last-child {
    border-bottom: none;
  }
`;

const InputContainer = styled.div`
  padding: 1.2rem 1.5rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.8rem;
  background: white;
`;

const MessageInput = styled.input`
  flex: 1;
  padding: 0.8rem 1.2rem;
  border: 2px solid #e5e7eb;
  border-radius: 25px;
  outline: none;
  font-size: 0.95rem;
  transition: all 0.2s ease;
  
  &:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
  
  &::placeholder {
    color: #9ca3af;
  }
`;

const SendButton = styled.button`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 50%;
  width: 44px;
  height: 44px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.2);
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }
  
  &:disabled {
    background: #d1d5db;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

// 10大類別專家
const experts = [
  { id: 1, name: "科技專家", category: "科技", prompt: "你是科技領域的專家..." },
  { id: 2, name: "金融專家", category: "金融", prompt: "你是金融領域的專家..." },
  { id: 3, name: "環境專家", category: "環境", prompt: "你是環境領域的專家..." },
  { id: 4, name: "醫療專家", category: "醫療", prompt: "你是醫療領域的專家..." },
  { id: 5, name: "教育專家", category: "教育", prompt: "你是教育領域的專家..." },
  { id: 6, name: "體育專家", category: "體育", prompt: "你是體育領域的專家..." },
  { id: 7, name: "政治專家", category: "政治", prompt: "你是政治領域的專家..." },
  { id: 8, name: "國際專家", category: "國際", prompt: "你是國際事務專家..." },
  { id: 9, name: "文化專家", category: "文化", prompt: "你是文化領域的專家..." },
  { id: 10, name: "生活專家", category: "生活", prompt: "你是生活領域的專家..." },
];

// 專家預設回覆
const expertReplies = {
  1: "根據最新科技趨勢，AI 將持續改變我們的生活。",
  2: "金融市場近期波動，建議多元分散投資。",
  3: "環境保護需全民參與，減碳是關鍵。",
  4: "醫療科技進步有助於提升全民健康。",
  5: "教育創新是未來人才培育的核心。",
  6: "體育運動有助於身心健康，建議多參與。",
  7: "政治穩定對國家發展至關重要。",
  8: "國際局勢變化快速，需持續關注。",
  9: "文化多元是社會進步的象徵。",
  10: "生活品質提升需從日常做起。"
};

// 快速提示
const quickPrompts = [
  "這則新聞的重點是什麼？",
  "對社會有什麼影響？",
  "未來發展趨勢如何？",
  "有什麼爭議點？",
  "專家怎麼看？"
];

function ChatRoom() {
  const [selectedExperts, setSelectedExperts] = useState([1, 2, 3]);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isPromptDropdownOpen, setIsPromptDropdownOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const dropdownRef = useRef(null);
  const promptDropdownRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      const messagesContainer = messagesEndRef.current.closest('[data-messages-container]');
      if (messagesContainer) {
        messagesContainer.scrollTo({
          top: messagesContainer.scrollHeight,
          behavior: 'smooth'
        });
      }
    }
  }, [messages]);

  // 點擊外部關閉下拉選單
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
      if (promptDropdownRef.current && !promptDropdownRef.current.contains(event.target)) {
        setIsPromptDropdownOpen(false);
      }
    };

    if (isDropdownOpen || isPromptDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen, isPromptDropdownOpen]);

  const toggleExpert = (id) => {
    setSelectedExperts(prev =>
      prev.includes(id) ? prev.filter(expertId => expertId !== id) : [...prev, id]
    );
  };

  const handlePromptSend = (promptText) => {
    if (selectedExperts.length === 0) return;

    const userMsg = {
      id: Date.now(),
      text: promptText,
      isOwn: true,
      time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);

    // 模擬專家回覆
    selectedExperts.forEach((expertId, index) => {
      setTimeout(() => {
        const expert = experts.find(e => e.id === expertId);
        const reply = {
          id: Date.now() + expertId,
          text: `${expert.name}：${expertReplies[expertId]}`,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, reply]);
      }, 1000 + index * 500);
    });
    
    // 關閉提示下拉選單
    setIsPromptDropdownOpen(false);
  };

  const handleSendMessage = () => {
    if (inputMessage.trim() && selectedExperts.length > 0) {
      const userMsg = {
        id: Date.now(),
        text: inputMessage,
        isOwn: true,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, userMsg]);
      setInputMessage('');

      // 模擬專家回覆
      selectedExperts.forEach((expertId, index) => {
        setTimeout(() => {
          const expert = experts.find(e => e.id === expertId);
          const reply = {
            id: Date.now() + expertId,
            text: `${expert.name}：${expertReplies[expertId]}`,
            isOwn: false,
            time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
          };
          setMessages(prev => [...prev, reply]);
        }, 1000 + index * 500);
      });
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
        <HeaderLeft>
          <ChatIcon>🤖</ChatIcon>
          <div>
            <ChatTitle>AI 專家討論室</ChatTitle>
            <ChatSubtitle>{selectedExperts.length} 位專家在線</ChatSubtitle>
          </div>
        </HeaderLeft>
      </ChatHeader>

      <ExpertSelector>
        <DropdownContainer ref={dropdownRef}>
          <DropdownButton 
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            type="button"
          >
            <span>選擇專家</span>
            {selectedExperts.length > 0 && (
              <SelectedCount>{selectedExperts.length}</SelectedCount>
            )}
            <DropdownIcon isOpen={isDropdownOpen}>▼</DropdownIcon>
          </DropdownButton>
          
          {isDropdownOpen && (
            <DropdownMenu>
              {experts.map(expert => (
                <DropdownItem
                  key={expert.id}
                  onClick={() => toggleExpert(expert.id)}
                >
                  <span>{expert.name}</span>
                  <Checkbox checked={selectedExperts.includes(expert.id)} />
                </DropdownItem>
              ))}
            </DropdownMenu>
          )}
        </DropdownContainer>
      </ExpertSelector>

      <MessagesContainer data-messages-container>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💬</div>
            <h3>歡迎來到 AI 專家討論室</h3>
            <p>選擇專家並開始討論吧！</p>
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

      <PromptContainer>
        <PromptDropdownContainer ref={promptDropdownRef}>
          <PromptDropdownButton 
            onClick={() => setIsPromptDropdownOpen(!isPromptDropdownOpen)}
            type="button"
            disabled={selectedExperts.length === 0}
          >
            <span>💡 快速提示</span>
            <PromptDropdownIcon isOpen={isPromptDropdownOpen}>▼</PromptDropdownIcon>
          </PromptDropdownButton>
          
          {isPromptDropdownOpen && (
            <PromptDropdownMenu>
              {quickPrompts.map((prompt, index) => (
                <PromptDropdownItem
                  key={index}
                  onClick={() => handlePromptSend(prompt)}
                >
                  {prompt}
                </PromptDropdownItem>
              ))}
            </PromptDropdownMenu>
          )}
        </PromptDropdownContainer>
      </PromptContainer>

      <InputContainer>
        <MessageInput
          type="text"
          placeholder={selectedExperts.length === 0 ? "請先選擇專家..." : "輸入您的問題..."}
          value={inputMessage}
          onChange={e => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={selectedExperts.length === 0}
        />
        <SendButton
          onClick={handleSendMessage}
          disabled={!inputMessage.trim() || selectedExperts.length === 0}
        >
          ➤
        </SendButton>
      </InputContainer>
    </ChatContainer>
  );
}

export default ChatRoom; 