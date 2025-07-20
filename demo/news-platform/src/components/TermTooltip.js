import React, { useEffect } from 'react';
import styled from 'styled-components';

const TooltipOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const TooltipContent = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  max-width: 400px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  position: relative;
  animation: slideIn 0.3s ease;
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const TooltipHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #667eea;
`;

const TermTitle = styled.h3`
  margin: 0;
  color: #667eea;
  font-size: 1.2rem;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
  
  &:hover {
    background: #f1f5f9;
    color: #333;
  }
`;

const Definition = styled.p`
  color: #444;
  line-height: 1.6;
  margin: 0;
  font-size: 1rem;
`;

const Example = styled.div`
  margin-top: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 4px solid #667eea;
`;

const ExampleTitle = styled.h4`
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 0.9rem;
  font-weight: 600;
`;

const ExampleText = styled.p`
  margin: 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.5;
`;

function TermTooltip({ term, definition, position, onClose }) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // 根據術語提供額外的例子
  const getExample = (term) => {
    const examples = {
      "人工智慧": {
        title: "應用例子",
        text: "例如：語音助手（如 Siri、Alexa）、推薦系統、自動駕駛汽車等"
      },
      "機器學習": {
        title: "應用例子", 
        text: "例如：垃圾郵件過濾、產品推薦、股票預測等"
      },
      "影像識別": {
        title: "應用例子",
        text: "例如：人臉識別、物體檢測、醫學影像分析等"
      },
      "倫理考量": {
        title: "相關議題",
        text: "例如：AI 偏見、自動化對就業的影響、決策透明度等"
      },
      "隱私保護": {
        title: "保護措施",
        text: "例如：數據加密、匿名化處理、用戶同意機制等"
      },
      "深度學習": {
        title: "應用例子",
        text: "例如：自然語言處理、圖像生成、語音合成等"
      }
    };
    return examples[term] || null;
  };

  const example = getExample(term);

  return (
    <TooltipOverlay onClick={handleOverlayClick}>
      <TooltipContent>
        <TooltipHeader>
          <TermTitle>{term}</TermTitle>
          <CloseButton onClick={onClose}>×</CloseButton>
        </TooltipHeader>
        
        <Definition>{definition}</Definition>
        
        {example && (
          <Example>
            <ExampleTitle>{example.title}</ExampleTitle>
            <ExampleText>{example.text}</ExampleText>
          </Example>
        )}
      </TooltipContent>
    </TooltipOverlay>
  );
}

export default TermTooltip; 