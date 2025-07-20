import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import styled from 'styled-components';
import ChatRoom from './ChatRoom';
import TermTooltip from './TermTooltip';

// --- styled-components ---
const Container = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
`;
const BackButton = styled(Link)`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  margin-bottom: 2rem;
  transition: color 0.3s ease;
  &:hover { color: #764ba2; }
`;
const NewsTypeSelector = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  justify-content: center;
`;
const TypeCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 2px solid ${props => props.active ? '#667eea' : 'transparent'};
  position: relative;
  overflow: hidden;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  }
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: ${props => props.active ? 'linear-gradient(135deg, #667eea, #764ba2)' : '#e0e0e0'};
  }
`;
const TypeTitle = styled.h3`
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.5rem;
`;
const TypeDescription = styled.p`
  color: #666;
  margin: 0;
  line-height: 1.5;
`;
const Tooltip = styled.div`
  position: absolute;
  bottom: -40px;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
  z-index: 10;
  ${TypeCard}:hover & {
    opacity: 1;
    visibility: visible;
  }
  &::before {
    content: '';
    position: absolute;
    top: -5px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 5px solid #333;
  }
`;
const LengthToggle = styled.div`
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin: 2rem 0;
`;
const ToggleButton = styled.button`
  background: ${props => props.active ? '#667eea' : 'white'};
  color: ${props => props.active ? 'white' : '#667eea'};
  border: 2px solid #667eea;
  padding: 0.5rem 1.5rem;
  border-radius: 25px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  &:hover {
    background: ${props => props.active ? '#764ba2' : '#f0f0f0'};
    border-color: ${props => props.active ? '#764ba2' : '#764ba2'};
  }
`;
const ArticleContent = styled.div`
  flex: ${props => props.width};
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: flex 0.3s ease;
`;
const ArticleTitle = styled.h2`
  color: #333;
  margin: 0 0 1.5rem 0;
  font-size: 2rem;
  line-height: 1.3;
`;
const ArticleText = styled.div`
  line-height: 1.8;
  color: #444;
  font-size: 1.1rem;
  strong {
    color: #667eea;
    cursor: pointer;
    position: relative;
    &:hover { color: #764ba2; }
  }
`;
const ResizeHandle = styled.div`
  width: 8px;
  background: #e0e0e0;
  cursor: col-resize;
  border-radius: 4px;
  transition: background 0.3s ease;
  &:hover { background: #667eea; }
`;
// --- chips/延伸閱讀 ---
const ChipsRow = styled.div`
  display: flex;
  gap: 0.5rem;
  margin: 1rem 0 1.5rem 0;
`;
const KeywordChip = styled.span`
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 12px;
  padding: 0.2rem 0.9rem;
  font-size: 0.95rem;
  font-weight: 500;
`;
const RelatedSection = styled.div`
  margin-top: 2rem;
  padding: 1rem 0;
  border-top: 1px solid #e5e7eb;
`;
const SectionTitle = styled.h4`
  margin-bottom: 1rem;
  color: #667eea;
  font-size: 1.1rem;
`;
const RelatedItem = styled.div`
  margin-bottom: 0.7rem;
  a {
    color: #3b82f6;
    font-weight: 600;
    text-decoration: none;
    &:hover { text-decoration: underline; }
  }
`;
const RelevanceText = styled.div`
  color: #6b7280;
  font-size: 0.92rem;
  margin-left: 0.2rem;
`;

const ReadMoreButton = styled.button`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.8rem 2rem;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 1.5rem;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }
`;

const LongContent = styled.div`
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #e5e7eb;
  animation: slideDown 0.5s ease;
  
  @keyframes slideDown {
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

// --- mock data ---
const mockNewsData = {
  1: {
    title: "人工智慧在醫療領域的突破性進展",
    short: `最新研究顯示，**人工智慧**技術在疾病診斷和治療方案制定方面取得了重大突破。研究團隊利用**機器學習**算法分析了數千個病例，成功提高了診斷準確率達95%以上。\n\n這項技術特別在**影像識別**方面表現出色，能夠快速識別X光片、CT掃描等醫學影像中的異常情況。專家表示，這將大大減輕醫護人員的工作負擔，並提高醫療效率。\n\n然而，這項技術的應用也面臨著**倫理考量**和**隱私保護**等挑戰。如何在提高醫療效率的同時保護患者隱私，成為業界關注的焦點。`,
    long: `最新研究顯示，**人工智慧**技術在疾病診斷和治療方案制定方面取得了重大突破。這項由國際頂尖醫療機構聯合進行的研究，歷時三年，投入資金超過數千萬美元，最終在**機器學習**和**深度學習**技術的結合下，成功開發出了新一代醫療AI系統。\n\n研究團隊利用**機器學習**算法分析了數千個病例，涵蓋了從常見疾病到罕見病症的各種情況。通過對大量數據的深度學習，AI系統能夠識別出人類醫生可能忽略的細微症狀，成功提高了診斷準確率達95%以上，遠超傳統診斷方法的準確率。\n\n這項技術特別在**影像識別**方面表現出色，能夠快速識別X光片、CT掃描、核磁共振等各種醫學影像中的異常情況。AI系統不僅能夠識別腫瘤、骨折等明顯病變，還能夠發現早期癌症的微小徵兆，為早期治療提供了寶貴的時間窗口。\n\n專家表示，這將大大減輕醫護人員的工作負擔，並提高醫療效率。在資源緊張的醫療環境中，AI助手可以幫助醫生快速篩選病例，讓醫生能夠將更多時間投入到需要專業判斷的複雜病例中。\n\n然而，這項技術的應用也面臨著**倫理考量**和**隱私保護**等挑戰。如何在提高醫療效率的同時保護患者隱私，成為業界關注的焦點。此外，AI診斷結果的責任歸屬問題也需要法律和倫理框架的完善。\n\n未來，這項技術有望在全球範圍內推廣應用，為更多患者提供更準確、更快速的醫療服務。同時，研究團隊也正在開發針對不同地區和人群的個性化AI模型，以確保技術的普適性和有效性。`,
    keywords: ["AI", "醫療", "影像識別"],
    related: [
      { id: 2, title: "AI助力癌症早期診斷", relevance: "本篇新聞介紹的 AI 技術在醫療領域的應用，與延伸閱讀中 AI 協助癌症早期診斷的主題密切相關，皆強調 AI 如何提升診斷準確率。" },
      { id: 3, title: "醫療影像新技術", relevance: "本篇強調 AI 在影像識別的突破，延伸閱讀則深入介紹醫療影像技術的最新發展，兩者皆聚焦於醫療影像的創新。" }
    ],
    source: "https://www.healthai-news.com/article/ai-medical-breakthrough"
  },
  2: {
    title: "AI助力癌症早期診斷",
    short: `AI 技術協助醫生更早發現癌症徵兆...`,
    long: `AI 技術協助醫生更早發現癌症徵兆，提升治療成功率...`,
    keywords: ["AI", "醫療", "癌症"],
    related: [
      { id: 1, title: "人工智慧在醫療領域的突破性進展", relevance: "延伸閱讀介紹 AI 在醫療領域的多元應用，與本篇聚焦於癌症診斷的內容相輔相成，皆展現 AI 對醫療的正面影響。" },
      { id: 3, title: "醫療影像新技術", relevance: "本篇提及 AI 協助癌症診斷，延伸閱讀則說明醫療影像技術的進步，兩者共同強調影像技術在癌症診斷的重要性。" }
    ],
    source: "https://www.cancernews.com/ai-early-diagnosis"
  },
  3: {
    title: "醫療影像新技術",
    short: `新一代醫療影像技術提升診斷效率...`,
    long: `新一代醫療影像技術提升診斷效率，降低誤判率...`,
    keywords: ["醫療", "影像識別"],
    related: [
      { id: 1, title: "人工智慧在醫療領域的突破性進展", relevance: "本篇介紹醫療影像技術的創新，延伸閱讀則說明 AI 如何應用於影像識別，兩者皆關注醫療診斷的技術提升。" },
      { id: 2, title: "AI助力癌症早期診斷", relevance: "本篇聚焦於影像技術，延伸閱讀則強調 AI 在癌症診斷的角色，兩者共同展現醫療科技的進步。" }
    ],
    source: "https://www.medtechnews.com/medical-imaging-innovation"
  }
};

const termDefinitions = {
  "人工智慧": "人工智慧（Artificial Intelligence, AI）是指由機器展現的智能，與人類和其他動物的自然智能相對。",
  "機器學習": "機器學習是人工智慧的一個分支，使計算機能夠在沒有明確編程的情況下學習和改進。",
  "影像識別": "影像識別是指計算機視覺技術，能夠自動識別和分析圖像中的內容和特徵。",
  "倫理考量": "倫理考量是指在技術發展和應用過程中需要考慮的道德和價值觀問題。",
  "隱私保護": "隱私保護是指保護個人信息不被未經授權的訪問、使用或披露的措施。",
  "深度學習": "深度學習是機器學習的一個子集，使用多層神經網絡來模擬人腦的學習過程。"
};

// --- NewsDetail 元件 ---
function NewsDetail() {
  const { id } = useParams();
  const [showLongContent, setShowLongContent] = useState(false);
  const [articleWidth, setArticleWidth] = useState('2');
  const [isResizing, setIsResizing] = useState(false);
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const newsData = mockNewsData[id];

  // 拖曳寬度
  const handleMouseDown = (e) => {
    setIsResizing(true);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };
  const handleMouseMove = (e) => {
    if (!isResizing) return;
    const container = document.querySelector('.article-container');
    if (!container) return;
    const containerRect = container.getBoundingClientRect();
    const mouseX = e.clientX - containerRect.left;
    const containerWidth = containerRect.width;
    const newArticleWidth = Math.max(1, Math.min(4, (mouseX / containerWidth) * 3));
    setArticleWidth(newArticleWidth.toString());
  };
  const handleMouseUp = () => {
    setIsResizing(false);
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };

  // 名詞解釋
  const handleTermClick = (term, e) => {
    const rect = e.target.getBoundingClientRect();
    setTooltipTerm(term);
    setTooltipPosition({ x: rect.left + rect.width / 2, y: rect.top - 10 });
  };
  const renderArticleText = (text) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const term = part.slice(2, -2);
        return (
          <strong
            key={index}
            onClick={(e) => handleTermClick(term, e)}
            style={{ position: 'relative' }}
          >
            {term}
          </strong>
        );
      }
      return part;
    });
  };

  if (!newsData) {
    return (
      <Container>
        <BackButton to="/">← 返回首頁</BackButton>
        <p>找不到該新聞</p>
      </Container>
    );
  }

  return (
    <Container>
      <BackButton to="/">← 返回首頁</BackButton>
      {/* chips 標籤 */}
      {newsData.keywords && (
        <ChipsRow>
          {newsData.keywords.map(kw => (
            <KeywordChip key={kw}>{kw}</KeywordChip>
          ))}
        </ChipsRow>
      )}
      
      <div className="article-container" style={{ display: 'flex', gap: '2rem' }}>
        <ArticleContent width={articleWidth}>
          <ArticleTitle>{newsData.title}</ArticleTitle>
          <ArticleText>
            {renderArticleText(newsData.short)}
          </ArticleText>
          
          {!showLongContent && (
            <ReadMoreButton onClick={() => setShowLongContent(true)}>
              閱讀更多 →
            </ReadMoreButton>
          )}
          
          {showLongContent && (
            <LongContent>
              <ArticleText>
                {renderArticleText(newsData.long)}
              </ArticleText>
            </LongContent>
          )}
        </ArticleContent>
        <ResizeHandle onMouseDown={handleMouseDown} />
        <ChatRoom />
      </div>
      
      {/* 延伸閱讀區塊 */}
      {newsData.related && newsData.related.length > 0 && (
        <RelatedSection>
          <SectionTitle>相關報導</SectionTitle>
          {newsData.related.map(item => (
            <RelatedItem key={item.id}>
              <Link to={`/news/${item.id}`}>{item.title}</Link>
              <RelevanceText>{item.relevance}</RelevanceText>
            </RelatedItem>
          ))}
        </RelatedSection>
      )}
      {tooltipTerm && (
        <TermTooltip
          term={tooltipTerm}
          definition={termDefinitions[tooltipTerm]}
          position={tooltipPosition}
          onClose={() => setTooltipTerm(null)}
        />
      )}
      {/* 新增資料來源顯示 */}
      {newsData.source && (
        <div style={{ marginTop: '2.5rem', borderTop: '1px solid #e5e7eb', paddingTop: '1rem', color: '#888', fontSize: '0.98rem' }}>
          資料來源：<a href={newsData.source} target="_blank" rel="noopener noreferrer" style={{ color: '#3b82f6' }}>{newsData.source}</a>
        </div>
      )}
    </Container>
  );
}

export default NewsDetail; 