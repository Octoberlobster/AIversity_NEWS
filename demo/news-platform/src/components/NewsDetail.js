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
const ArticleContent = styled.div`
  flex: ${props => props.width};
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: ${props => props.isResizing ? 'none' : 'flex 0.1s ease'};
  min-width: 300px;
`;
const ArticleTitle = styled.h2`
  color: #333;
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  line-height: 1.3;
`;

const ArticleInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
  color: #6b7280;
  flex-wrap: wrap;
`;

const ArticleDate = styled.span`
  color: #6b7280;
  font-size: 0.9rem;
`;

const ArticleAuthor = styled.span`
  color: #6b7280;
  font-size: 0.9rem;
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

const ArticleImage = styled.div`
  margin: 2rem 0;
  text-align: center;
  
  img {
    max-width: 100%;
    height: auto;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  }
  
  .image-caption {
    margin-top: 0.5rem;
    color: #666;
    font-size: 0.9rem;
    font-style: italic;
  }
`;
const ResizeHandle = styled.div`
  width: 1px;
  background: ${props => props.isResizing ? '#667eea' : '#e5e7eb'};
  cursor: col-resize;
  position: relative;
  transition: all 0.2s ease;
  height: 100%;
  min-height: 400px;
  
  /* 懸停區域 */
  &::before {
    content: '';
    position: absolute;
    left: -6px;
    right: -6px;
    top: 0;
    bottom: 0;
    background: transparent;
    cursor: col-resize;
  }
  
  /* 懸停時的視覺效果 */
  &:hover {
    background: #667eea;
    width: 2px;
    
    &::after {
      opacity: 1;
    }
  }
  
  /* 拖動指示器 - 三個點 */
  &::after {
    content: '⋮';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    color: ${props => props.isResizing ? 'white' : '#6b7280'};
    font-size: 14px;
    font-weight: bold;
    opacity: ${props => props.isResizing ? 1 : 0.4};
    transition: all 0.2s ease;
    background: ${props => props.isResizing ? '#667eea' : '#f3f4f6'};
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
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
  padding: 1.5rem;
  border-top: 2px solid #e5e7eb;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
`;

const SectionTitle = styled.h4`
  margin-bottom: 1.5rem;
  color: #1e293b;
  font-size: 1.2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &::before {
    content: '📰';
    font-size: 1.1rem;
  }
`;

const RelatedItem = styled.div`
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 0 2px 2px 0;
  }
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    border-color: #667eea;
  }
  
  a {
    color: #1e293b;
    font-weight: 600;
    text-decoration: none;
    font-size: 1rem;
    line-height: 1.4;
    display: block;
    margin-bottom: 0.5rem;
    
    &:hover {
      color: #667eea;
    }
  }
`;

const RelevanceText = styled.div`
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.5;
  padding-left: 0.5rem;
  border-left: 2px solid #e2e8f0;
  margin-left: 0.5rem;
  font-style: italic;
`;

const RelatedBadge = styled.span`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.5rem;
  display: inline-block;
`;

const RelatedGrid = styled.div`
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;
  
  @media (min-width: 768px) {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }
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
    date: "2024-01-15 14:30",
    author: "張明華",
    image: "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800&h=500&fit=crop",
    imageCaption: "AI 技術在醫療影像識別中的應用示意圖",
    short: `最新研究顯示，**人工智慧**技術在疾病診斷和治療方案制定方面取得了重大突破。研究團隊利用**機器學習**算法分析了數千個病例，成功提高了診斷準確率達95%以上。\n\n這項技術特別在**影像識別**方面表現出色，能夠快速識別X光片、CT掃描等醫學影像中的異常情況。專家表示，這將大大減輕醫護人員的工作負擔，並提高醫療效率。\n\n然而，這項技術的應用也面臨著**倫理考量**和**隱私保護**等挑戰。如何在提高醫療效率的同時保護患者隱私，成為業界關注的焦點。`,
    long: `最新研究顯示，**人工智慧**技術在疾病診斷和治療方案制定方面取得了重大突破。這項由國際頂尖醫療機構聯合進行的研究，歷時三年，投入資金超過數千萬美元，最終在**機器學習**和**深度學習**技術的結合下，成功開發出了新一代醫療AI系統。\n\n研究團隊利用**機器學習**算法分析了數千個病例，涵蓋了從常見疾病到罕見病症的各種情況。通過對大量數據的深度學習，AI系統能夠識別出人類醫生可能忽略的細微症狀，成功提高了診斷準確率達95%以上，遠超傳統診斷方法的準確率。\n\n這項技術特別在**影像識別**方面表現出色，能夠快速識別X光片、CT掃描、核磁共振等各種醫學影像中的異常情況。AI系統不僅能夠識別腫瘤、骨折等明顯病變，還能夠發現早期癌症的微小徵兆，為早期治療提供了寶貴的時間窗口。\n\n專家表示，這將大大減輕醫護人員的工作負擔，並提高醫療效率。在資源緊張的醫療環境中，AI助手可以幫助醫生快速篩選病例，讓醫生能夠將更多時間投入到需要專業判斷的複雜病例中。\n\n然而，這項技術的應用也面臨著**倫理考量**和**隱私保護**等挑戰。如何在提高醫療效率的同時保護患者隱私，成為業界關注的焦點。此外，AI診斷結果的責任歸屬問題也需要法律和倫理框架的完善。\n\n未來，這項技術有望在全球範圍內推廣應用，為更多患者提供更準確、更快速的醫療服務。同時，研究團隊也正在開發針對不同地區和人群的個性化AI模型，以確保技術的普適性和有效性。`,
    keywords: ["AI", "醫療", "影像識別"], // 領域關鍵字
    terms: ["人工智慧", "機器學習", "影像識別", "倫理考量", "隱私保護", "深度學習"], // 專有名詞
    related: [
      { id: 2, title: "AI助力癌症早期診斷", relevance: "本篇新聞介紹的 AI 技術在醫療領域的應用，與延伸閱讀中 AI 協助癌症早期診斷的主題密切相關，皆強調 AI 如何提升診斷準確率。" },
      { id: 3, title: "醫療影像新技術", relevance: "本篇強調 AI 在影像識別的突破，延伸閱讀則深入介紹醫療影像技術的最新發展，兩者皆聚焦於醫療影像的創新。" }
    ],
    source: "https://www.healthai-news.com/article/ai-medical-breakthrough"
  },
  2: {
    title: "AI助力癌症早期診斷",
    date: "2024-01-14 16:45",
    author: "李曉雯",
    image: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=800&h=500&fit=crop",
    imageCaption: "AI 協助醫生進行癌症早期診斷的場景",
    short: `AI 技術協助醫生更早發現癌症徵兆，通過分析大量醫療數據和影像資料，AI系統能夠識別出人類醫生可能忽略的細微症狀。這項技術特別在**影像識別**方面表現出色，能夠快速分析X光片、CT掃描等醫學影像。\n\n研究顯示，AI輔助診斷系統能夠將癌症早期發現率提升30%以上，為患者爭取寶貴的治療時間。專家表示，這項技術將成為未來醫療診斷的重要工具。\n\n然而，AI診斷技術的推廣仍面臨**技術標準化**和**醫生培訓**等挑戰。如何讓更多醫療機構採用這項技術，成為業界關注的焦點。`,
    long: `AI 技術協助醫生更早發現癌症徵兆，通過分析大量醫療數據和影像資料，AI系統能夠識別出人類醫生可能忽略的細微症狀。這項技術特別在**影像識別**方面表現出色，能夠快速分析X光片、CT掃描等醫學影像。\n\n研究顯示，AI輔助診斷系統能夠將癌症早期發現率提升30%以上，為患者爭取寶貴的治療時間。專家表示，這項技術將成為未來醫療診斷的重要工具。\n\n然而，AI診斷技術的推廣仍面臨**技術標準化**和**醫生培訓**等挑戰。如何讓更多醫療機構採用這項技術，成為業界關注的焦點。\n\n未來，這項技術有望在全球範圍內推廣應用，為更多患者提供更準確、更快速的醫療服務。`,
    keywords: ["AI", "醫療", "癌症"], // 領域關鍵字
    terms: ["影像識別", "技術標準化", "醫生培訓"], // 專有名詞
    related: [
      { id: 1, title: "人工智慧在醫療領域的突破性進展", relevance: "延伸閱讀介紹 AI 在醫療領域的多元應用，與本篇聚焦於癌症診斷的內容相輔相成，皆展現 AI 對醫療的正面影響。" },
      { id: 3, title: "醫療影像新技術", relevance: "本篇提及 AI 協助癌症診斷，延伸閱讀則說明醫療影像技術的進步，兩者共同強調影像技術在癌症診斷的重要性。" }
    ],
    source: "https://www.cancernews.com/ai-early-diagnosis"
  },
  3: {
    title: "醫療影像新技術",
    date: "2024-01-13 11:20",
    author: "王建國",
    image: "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&h=500&fit=crop",
    imageCaption: "新一代醫療影像技術設備展示",
    short: `新一代醫療影像技術提升診斷效率，通過高解析度成像和智能分析，能夠更準確地識別病變。這項技術結合了**影像識別**和**機器學習**，大幅降低了誤判率。\n\n新技術在X光、CT、核磁共振等各種影像檢查中都有出色表現，為醫生提供更清晰的診斷依據。專家表示，這將大大提高醫療診斷的準確性和效率。\n\n然而，新技術的推廣需要**設備更新**和**人員培訓**，如何在成本控制的前提下推廣應用，成為醫療機構面臨的挑戰。`,
    long: `新一代醫療影像技術提升診斷效率，通過高解析度成像和智能分析，能夠更準確地識別病變。這項技術結合了**影像識別**和**機器學習**，大幅降低了誤判率。\n\n新技術在X光、CT、核磁共振等各種影像檢查中都有出色表現，為醫生提供更清晰的診斷依據。專家表示，這將大大提高醫療診斷的準確性和效率。\n\n然而，新技術的推廣需要**設備更新**和**人員培訓**，如何在成本控制的前提下推廣應用，成為醫療機構面臨的挑戰。\n\n未來，這項技術有望在全球範圍內推廣應用，為更多患者提供更準確、更快速的醫療服務。`,
    keywords: ["醫療", "影像識別"], // 領域關鍵字
    terms: ["影像識別", "機器學習", "設備更新", "人員培訓"], // 專有名詞
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
  "深度學習": "深度學習是機器學習的一個子集，使用多層神經網絡來模擬人腦的學習過程。",
  "技術標準化": "技術標準化是指建立統一的技術規範和標準，確保技術在不同環境下的一致性和互操作性。",
  "醫生培訓": "醫生培訓是指對醫療人員進行新技術、新方法的專業教育和技能提升。",
  "設備更新": "設備更新是指醫療機構引進新的醫療設備和技術，以提升診斷和治療能力。",
  "人員培訓": "人員培訓是指對醫療工作人員進行專業技能和知識的培訓，以適應新技術的應用。"
};

// --- NewsDetail 元件 ---
function NewsDetail() {
  const { id } = useParams();
  const [showLongContent, setShowLongContent] = useState(false);
  const [articleWidth, setArticleWidth] = useState('2');
  const [isResizing, setIsResizing] = useState(false);
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [dragStartX, setDragStartX] = useState(0);
  const [dragStartWidth, setDragStartWidth] = useState(0);

  const newsData = mockNewsData[id];

  // 添加拖動事件監聽器
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isResizing]);

  // 拖曳寬度
  const handleMouseDown = (e) => {
    e.preventDefault(); // 防止文字選擇
    
    // 記錄拖動開始的位置和當前寬度
    const container = document.querySelector('.article-container');
    if (container) {
      const containerRect = container.getBoundingClientRect();
      setDragStartX(e.clientX - containerRect.left);
      setDragStartWidth(parseFloat(articleWidth));
    }
    
    setIsResizing(true);
    document.body.style.cursor = 'col-resize'; // 改變整個頁面的游標
    document.body.style.userSelect = 'none'; // 防止文字選擇
  };
  
  const handleMouseMove = (e) => {
    if (!isResizing) return;
    e.preventDefault();
    
    const container = document.querySelector('.article-container');
    if (!container) return;
    const containerRect = container.getBoundingClientRect();
    const currentMouseX = e.clientX - containerRect.left;
    
    // 計算滑鼠移動的距離
    const deltaX = currentMouseX - dragStartX;
    
    // 將滑鼠移動距離轉換為寬度變化
    // 假設滑鼠移動 100px 對應 flex 值變化 1
    const widthChange = deltaX / 100;
    const newWidth = Math.max(1, Math.min(4, dragStartWidth + widthChange));
    
    // 平滑更新，避免抖動
    setArticleWidth(newWidth.toFixed(1));
  };
  
  const handleMouseUp = () => {
    setIsResizing(false);
    document.body.style.cursor = ''; // 恢復游標
    document.body.style.userSelect = ''; // 恢復文字選擇
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
        // 只有在新聞的 terms 列表中的詞才可點擊
        const isClickable = newsData.terms && newsData.terms.includes(term);
        return (
          <strong
            key={index}
            onClick={isClickable ? (e) => handleTermClick(term, e) : undefined}
            style={{ 
              position: 'relative',
              cursor: isClickable ? 'pointer' : 'default',
              color: isClickable ? '#667eea' : 'inherit',
              textDecoration: isClickable ? 'underline' : 'none'
            }}
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
      {/* chips 標籤 */}
      {newsData.keywords && (
        <ChipsRow>
          {newsData.keywords.map(kw => (
            <KeywordChip key={kw}>{kw}</KeywordChip>
          ))}
        </ChipsRow>
      )}
      
      <div className="article-container" style={{ display: 'flex', gap: '2rem', alignItems: 'flex-start' }}>
        <ArticleContent width={articleWidth} isResizing={isResizing}>
          <ArticleTitle>{newsData.title}</ArticleTitle>
          <ArticleInfo>
            <ArticleDate>{newsData.date}</ArticleDate>
            <ArticleAuthor>記者 {newsData.author}</ArticleAuthor>
          </ArticleInfo>
          
          {newsData.image && (
            <ArticleImage>
              <img src={newsData.image} alt={newsData.imageCaption} />
              {newsData.imageCaption && (
                <div className="image-caption">{newsData.imageCaption}</div>
              )}
            </ArticleImage>
          )}
          
          <ArticleText>
            {renderArticleText(newsData.short)}
          </ArticleText>
          
          {!showLongContent && (
            <ReadMoreButton onClick={() => setShowLongContent(true)}>
              閱讀更多 →
            </ReadMoreButton>
          )}
          
          {showLongContent && (
            <>
              <LongContent>
                <ArticleText>
                  {renderArticleText(newsData.long)}
                </ArticleText>
              </LongContent>
              <ReadMoreButton onClick={() => setShowLongContent(false)}>
                閱讀較少 ←
              </ReadMoreButton>
            </>
          )}
        </ArticleContent>
        
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          gap: '0.5rem',
          position: 'relative',
          height: '100%'
        }}>
          <ResizeHandle onMouseDown={handleMouseDown} isResizing={isResizing} />
          <div 
            style={{ 
              fontSize: '0.75rem', 
              color: '#6b7280', 
              writingMode: 'vertical-rl',
              textOrientation: 'mixed',
              opacity: 0.7,
              cursor: 'col-resize',
              marginTop: '1rem',
              userSelect: 'none',
              padding: '0.5rem',
              borderRadius: '4px',
              transition: 'all 0.2s ease'
            }}
            onMouseDown={handleMouseDown}
            onMouseEnter={(e) => {
              e.target.style.opacity = '1';
              e.target.style.color = '#667eea';
              e.target.style.background = 'rgba(102, 126, 234, 0.1)';
            }}
            onMouseLeave={(e) => {
              e.target.style.opacity = '0.7';
              e.target.style.color = '#6b7280';
              e.target.style.background = 'transparent';
            }}
          >
            拖動調整
          </div>
        </div>
        
        <ChatRoom />
      </div>
      
      {/* 延伸閱讀區塊 */}
      {newsData.related && newsData.related.length > 0 && (
        <RelatedSection>
          <SectionTitle>相關報導</SectionTitle>
          <RelatedGrid>
            {newsData.related.map(item => (
              <RelatedItem key={item.id}>
                <Link to={`/news/${item.id}`}>
                  {item.title}
                  <RelatedBadge>相關</RelatedBadge>
                </Link>
                <RelevanceText>{item.relevance}</RelevanceText>
              </RelatedItem>
            ))}
          </RelatedGrid>
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