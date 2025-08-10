import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import styled from 'styled-components';

const PageContainer = styled.div`
  min-height: 100vh;
  background-color: #f8fafc;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
`;

const MainContent = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
`;

const ReportHeader = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 2rem;
  align-items: center;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
    text-align: center;
  }
`;

const HeaderContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const ReportTitle = styled.h1`
  color: #1e3a8a;
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
  line-height: 1.3;
`;

const ReportSummary = styled.p`
  color: #4b5563;
  font-size: 1rem;
  line-height: 1.6;
  margin: 0;
`;

const ReportMeta = styled.div`
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-top: 1rem;
`;

const MetaItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
  font-size: 0.9rem;
`;

const ConnectionImage = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.1rem;
  font-weight: 500;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: "關聯圖";
    z-index: 1;
  }
  
  &::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%), 
                linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%), 
                linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%), 
                linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%);
    background-size: 20px 20px;
    background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  }
`;

// 完全獨立的布局
const ContentLayout = styled.div`
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const MainColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const Sidebar = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  position: sticky;
  top: 2rem;
  height: fit-content;
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
`;

const SidebarCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
`;

const SidebarTitle = styled.h3`
  color: #1e3a8a;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  border-bottom: 2px solid #e0e7ff;
  padding-bottom: 0.5rem;
`;

const NavigationMenu = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const NavItem = styled.div`
  padding: 0.8rem 1rem;
  background: ${props => props.active ? '#e0e7ff' : 'transparent'};
  color: ${props => props.active ? '#1e3a8a' : '#4b5563'};
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.95rem;
  font-weight: ${props => props.active ? '600' : '500'};
  border-left: 3px solid ${props => props.active ? '#667eea' : 'transparent'};
  
  &:hover {
    background: ${props => props.active ? '#e0e7ff' : '#f8fafc'};
    color: #1e3a8a;
  }
`;

const ContentSection = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  scroll-margin-top: 8rem;
`;

const SectionTitle = styled.h2`
  color: #1e3a8a;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &::before {
    content: "📰";
    font-size: 1.2rem;
  }
`;

const SectionSummary = styled.p`
  color: #4b5563;
  font-size: 1rem;
  line-height: 1.6;
  margin: 0 0 1.5rem 0;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 4px solid #667eea;
`;

// 完全按照UnifiedNewsCard的樣式
const NewsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  }
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const CardContainer = styled.div`
  background: white;
  border-radius: 16px;
  padding: 1.2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border-left: 4px solid #667eea;
  position: relative;
  height: fit-content;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    border-left-color: #7c3aed;
  }
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.8rem;
`;

const CardTitle = styled(Link)`
  margin: 0;
  color: #1e3a8a;
  font-size: 1.2rem;
  font-weight: 600;
  line-height: 1.3;
  flex: 1;
  text-decoration: none;
  transition: color 0.3s ease;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  
  &:hover {
    color: #667eea;
  }
`;

const CardMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.8rem;
  flex-wrap: wrap;
`;

const CardInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.8rem;
  flex-wrap: wrap;
  font-size: 0.8rem;
  color: #6b7280;
`;

const CategoryTag = styled.span`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 500;
`;

const DateText = styled.span`
  color: #6b7280;
  font-size: 0.8rem;
`;

const AuthorText = styled.span`
  color: #6b7280;
  font-size: 0.8rem;
`;

const SourceCount = styled.span`
  background: #f3f4f6;
  color: #4b5563;
  padding: 0.2rem 0.6rem;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 500;
`;

const KeywordChip = styled.span`
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 10px;
  padding: 0.15rem 0.7rem;
  font-size: 0.8rem;
  font-weight: 500;
  margin-left: 0.2rem;
`;

const CardContent = styled.div`
  margin-bottom: 0.8rem;
`;

const SummaryText = styled.p`
  color: #4b5563;
  line-height: 1.5;
  margin: 0;
  font-size: ${props => props.isExpanded ? '0.9rem' : '0.85rem'};
  transition: all 0.3s ease;
  display: -webkit-box;
  -webkit-line-clamp: ${props => props.isExpanded ? 'none' : '3'};
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const ExpandedContent = styled.div`
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
  animation: slideDown 0.3s ease;
  
  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const RelatedNews = styled.div`
  margin-top: 1rem;
`;

const RelatedNewsTitle = styled.h4`
  color: #374151;
  font-size: 1rem;
  margin: 0 0 0.5rem 0;
  font-weight: 600;
`;

const RelatedNewsList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`;

const RelatedNewsItem = styled.li`
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
  
  &:last-child {
    border-bottom: none;
  }
`;

const RelatedNewsLink = styled(Link)`
  color: #4b5563;
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.3s ease;
  
  &:hover {
    color: #667eea;
  }
`;

const CardActions = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
`;

const ActionButton = styled.button`
  background: ${props => props.primary ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#f3f4f6'};
  color: ${props => props.primary ? 'white' : '#4b5563'};
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

const StatsContainer = styled.div`
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #6b7280;
  flex-wrap: wrap;
`;

const StatItem = styled.span`
  display: flex;
  align-items: center;
  gap: 0.3rem;
`;

// 專題聊天室組件 - 整合到邊欄
const TopicChatCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  margin-top: 1.5rem;
`;

const ChatHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 1rem;
  padding-bottom: 0.8rem;
  border-bottom: 2px solid #e0e7ff;
`;

const ChatIcon = styled.div`
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.2rem;
`;

const ChatTitle = styled.h4`
  margin: 0;
  color: #1e3a8a;
  font-size: 1.1rem;
  font-weight: 600;
`;

const ChatDescription = styled.p`
  margin: 0.3rem 0 0 0;
  color: #6b7280;
  font-size: 0.85rem;
  line-height: 1.4;
`;

const ChatMessages = styled.div`
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
`;

const Message = styled.div`
  margin-bottom: 0.8rem;
  padding: 0.8rem;
  border-radius: 8px;
  background: ${props => props.isOwn ? '#667eea' : 'white'};
  color: ${props => props.isOwn ? 'white' : '#374151'};
  font-size: 0.9rem;
  line-height: 1.4;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const QuickPrompts = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
`;

const PromptButton = styled.button`
  background: #f3f4f6;
  color: #4b5563;
  border: 1px solid #d1d5db;
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: #e5e7eb;
    transform: translateY(-1px);
  }
`;

const ChatInput = styled.input`
  width: 100%;
  padding: 0.8rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.9rem;
  margin-bottom: 0.8rem;
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const SendButton = styled.button`
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// 模擬專題報導詳細資料
const specialReportData = {
  1: {
    id: 1,
    title: "2025罷免案",
    summary: "國民黨與民眾黨2024年起聯手以人數優勢陸續通過國會職權等修法引發不滿，民團2025年起陸續鎖定國民黨立委發動罷免連署。24位藍委及新竹市長高虹安罷免案7月26日投開票，25案全數遭到否決。第二波共7案罷免投票將在8月23日登場，包括國民黨立委馬文君、游顥、羅明才、江啟臣、楊瓊瓔、顏寬恒、林思銘。",
    status: "進行中",
    icon: "🗳️",
    events: [
      "即時開票",
      "結果分析", 
      "投票日動態",
      "立委罷免案",
      "高虹安罷免案",
      "罷免案日程",
      "投票須知",
      "其他文章"
    ],
    connectionMap: "罷免案涉及國民黨24位立委及新竹市長高虹安，共25案。第一波投票於7月26日舉行，全數被否決。第二波7案將於8月23日舉行，主要針對特定立委的罷免投票。",
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
      "結果分析": {
        title: "投票結果深度分析",
        summary: "分析罷免投票結果的背後原因、政治影響及未來發展趨勢。",
        articles: [
          { 
            id: 201, 
            title: "美學者：大罷免未過不影響台美互動 須持續深化互信", 
            views: "9.7k", 
            date: "2025/7/29 10:45", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 5,
            shortSummary: "美國學者分析指出，台灣的罷免案結果不會影響台美關係發展，但雙方需要持續深化互信關係，在國防、經濟等領域加強合作。",
            relatedNews: [
              { id: 2011, title: "台美關係發展趨勢" },
              { id: 2012, title: "國際學者觀點" },
              { id: 2013, title: "外交政策影響" }
            ],
            keywords: ["台美", "外交", "學者"]
          },
          { 
            id: 202, 
            title: "大罷免結果對台美影響 智庫學者：取決在野國防路線", 
            views: "7.3k", 
            date: "2025/7/29 07:14", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 3,
            shortSummary: "智庫學者認為，罷免案結果對台美關係的影響主要取決於在野黨在國防政策上的立場，以及是否願意與美方保持良好溝通。",
            relatedNews: [
              { id: 2021, title: "國防政策分析" },
              { id: 2022, title: "智庫研究報告" },
              { id: 2023, title: "政策影響評估" }
            ],
            keywords: ["國防", "政策", "智庫"]
          }
        ]
      },
      "投票日動態": {
        title: "投票日現場直擊",
        summary: "投票日當天的現場情況、選民反應及重要事件。",
        articles: [
          { 
            id: 301, 
            title: "大罷免失敗 罷團開票晚會感傷提前結束", 
            views: "6.4k", 
            date: "2025/7/26 19:54", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 2,
            shortSummary: "罷免團體在開票晚會上看到結果不如預期，現場氣氛感傷，活動提前結束。許多支持者表示失望但仍會繼續關注相關議題。",
            relatedNews: [
              { id: 3011, title: "罷免團體反應" },
              { id: 3012, title: "支持者心聲" },
              { id: 3013, title: "後續行動計劃" }
            ],
            keywords: ["罷免", "團體", "反應"]
          }
        ]
      },
      "立委罷免案": {
        title: "立委罷免案詳情",
        summary: "針對24位國民黨立委的罷免案詳細資訊及背景。",
        articles: [
          { 
            id: 401, 
            title: "24位國民黨立委罷免案完整名單", 
            views: "13.1k", 
            date: "2025/7/25", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 6,
            shortSummary: "完整列出24位國民黨立委的罷免案詳細資訊，包括各立委的基本資料、罷免理由、連署人數等相關資訊。",
            relatedNews: [
              { id: 4011, title: "各立委背景資料" },
              { id: 4012, title: "罷免理由分析" },
              { id: 4013, title: "連署情況統計" }
            ],
            keywords: ["立委", "國民黨", "名單"]
          }
        ]
      },
      "高虹安罷免案": {
        title: "高虹安罷免案專題",
        summary: "新竹市長高虹安罷免案的詳細過程及結果。",
        articles: [
          { 
            id: 501, 
            title: "高虹安罷免案投票率創新高", 
            views: "16.3k", 
            date: "2025/7/26", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 4,
            shortSummary: "新竹市長高虹安的罷免案投票率創下歷史新高，顯示新竹市民對此次罷免案的高度關注和參與。",
            relatedNews: [
              { id: 5011, title: "新竹市民反應" },
              { id: 5012, title: "高虹安回應" },
              { id: 5013, title: "政治影響分析" }
            ],
            keywords: ["高虹安", "新竹", "投票率"]
          }
        ]
      },
      "罷免案日程": {
        title: "罷免案重要時程",
        summary: "罷免案的重要時間節點及後續發展。",
        articles: [
          { 
            id: 601, 
            title: "第二波罷免案8月23日舉行", 
            views: "10.2k", 
            date: "2025/7/28", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 3,
            shortSummary: "第二波共7個罷免案將於8月23日舉行投票，包括國民黨立委馬文君、游顥、羅明才、江啟臣、楊瓊瓔、顏寬恒、林思銘。",
            relatedNews: [
              { id: 6011, title: "第二波罷免名單" },
              { id: 6012, title: "投票準備工作" },
              { id: 6013, title: "時程安排" }
            ],
            keywords: ["第二波", "罷免", "時程"]
          }
        ]
      },
      "投票須知": {
        title: "投票相關資訊",
        summary: "罷免投票的相關規定、注意事項及投票指南。",
        articles: [
          { 
            id: 701, 
            title: "罷免投票資格及注意事項", 
            views: "12.7k", 
            date: "2025/7/24", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 5,
            shortSummary: "詳細說明罷免投票的資格條件、投票程序、注意事項等相關規定，幫助選民了解如何正確參與投票。",
            relatedNews: [
              { id: 7011, title: "投票資格查詢" },
              { id: 7012, title: "投票程序說明" },
              { id: 7013, title: "注意事項提醒" }
            ],
            keywords: ["投票", "資格", "程序"]
          }
        ]
      },
      "其他文章": {
        title: "相關新聞報導",
        summary: "與罷免案相關的其他新聞及評論文章。",
        articles: [
          { 
            id: 801, 
            title: "學者分析：罷免案對台灣民主的影響", 
            views: "9.8k", 
            date: "2025/7/27", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 4,
            shortSummary: "政治學者分析罷免案對台灣民主發展的影響，探討罷免制度在民主政治中的角色和意義。",
            relatedNews: [
              { id: 8011, title: "民主制度檢討" },
              { id: 8012, title: "學者觀點彙整" },
              { id: 8013, title: "制度影響評估" }
            ],
            keywords: ["學者", "民主", "制度"]
          }
        ]
      }
    }
  }
};

function SpecialReportDetail() {
  const { id } = useParams();
  const report = specialReportData[id];
  const [activeEvent, setActiveEvent] = useState(report?.events[0] || '');
  const [expandedCards, setExpandedCards] = useState({});
  const sectionRefs = useRef({});
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');

  if (!report) {
    return (
      <PageContainer>
        <MainContent>
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>專題報導不存在</h2>
            <p>請返回專題報導列表</p>
            <Link to="/special-reports" style={{ color: '#667eea' }}>返回專題報導</Link>
          </div>
        </MainContent>
      </PageContainer>
    );
  }

  const handleNavClick = (event) => {
    setActiveEvent(event);
    const targetRef = sectionRefs.current[event];
    if (targetRef) {
      targetRef.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      });
    }
  };

  const toggleExpanded = (cardId) => {
    setExpandedCards(prev => ({
      ...prev,
      [cardId]: !prev[cardId]
    }));
  };

  const handleSendMessage = () => {
    if (chatInput.trim()) {
      const userMsg = {
        id: Date.now(),
        text: chatInput,
        isOwn: true,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, userMsg]);
      setChatInput('');
      
      // 模擬AI助手回覆
      setTimeout(() => {
        const reply = {
          id: Date.now() + 1,
          text: `關於「${report.title}」這個專題，我可以為您提供深入分析。您提到的內容與專題中的「${activeEvent}」部分相關。需要我為您詳細解釋某個特定觀點嗎？`,
          isOwn: false,
          time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
        };
        setChatMessages(prev => [...prev, reply]);
      }, 1000);
    }
  };

  const handleQuickPrompt = (prompt) => {
    setChatInput(prompt);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const quickPrompts = [
    "分析這個專題",
    "相關背景資訊",
    "專家觀點",
    "未來發展趨勢"
  ];

  return (
    <PageContainer>
      <MainContent>
        <ReportHeader>
          <HeaderContent>
            <ReportTitle>{report.title}</ReportTitle>
            <ReportSummary>{report.summary}</ReportSummary>
            <ReportMeta>
              <MetaItem>
                <span>📅</span>
                <span>{report.lastUpdate}</span>
              </MetaItem>
              <MetaItem>
                <span>📄</span>
                <span>{report.articles} 篇文章</span>
              </MetaItem>
              <MetaItem>
                <span>👁️</span>
                <span>{report.views}</span>
              </MetaItem>
            </ReportMeta>
          </HeaderContent>
          
          <ConnectionImage />
        </ReportHeader>

        <ContentLayout>
          <MainColumn>
            {report.events.map((event, index) => {
              const eventDetail = report.eventDetails[event];
              return (
                <ContentSection 
                  key={index}
                  ref={(el) => {
                    sectionRefs.current[event] = el;
                  }}
                >
                  <SectionTitle>{event}</SectionTitle>
                  <SectionSummary>{eventDetail?.summary}</SectionSummary>
                  
                  <NewsGrid>
                    {eventDetail?.articles.map(news => {
                      const isExpanded = expandedCards[news.id] || false;
                      return (
                        <CardContainer key={news.id}>
                          <CardHeader>
                            <CardTitle to={`/news/${news.id}`}>{news.title}</CardTitle>
                          </CardHeader>
                          <CardInfo>
                            <DateText>{news.date}</DateText>
                            <AuthorText>記者 {news.author}</AuthorText>
                          </CardInfo>
                          <CardMeta>
                            <CategoryTag>{news.category}</CategoryTag>
                            <SourceCount>{news.sourceCount} 個來源</SourceCount>
                            {news.keywords && news.keywords.map(kw => (
                              <KeywordChip key={kw}>{kw}</KeywordChip>
                            ))}
                          </CardMeta>
                          <CardContent>
                            <SummaryText isExpanded={isExpanded}>
                              {isExpanded ? news.shortSummary : news.shortSummary.substring(0, 150)}
                            </SummaryText>
                            {isExpanded && (
                              <ExpandedContent>
                                <RelatedNews>
                                  <RelatedNewsTitle>相關報導</RelatedNewsTitle>
                                  <RelatedNewsList>
                                    {news.relatedNews.map(relatedNews => (
                                      <RelatedNewsItem key={relatedNews.id}>
                                        <RelatedNewsLink to={`/news/${relatedNews.id}`}>
                                          {relatedNews.title}
                                        </RelatedNewsLink>
                                      </RelatedNewsItem>
                                    ))}
                                  </RelatedNewsList>
                                </RelatedNews>
                              </ExpandedContent>
                            )}
                          </CardContent>
                          <CardActions>
                            <ActionButtons>
                              <ActionButton onClick={() => toggleExpanded(news.id)}>
                                {isExpanded ? '收起' : '展開'}
                              </ActionButton>
                            </ActionButtons>
                            <StatsContainer>
                              <StatItem>👁️ {news.views}</StatItem>
                            </StatsContainer>
                          </CardActions>
                        </CardContainer>
                      );
                    })}
                  </NewsGrid>
                </ContentSection>
              );
            })}
          </MainColumn>
          
          <Sidebar>
            <SidebarCard>
              <SidebarTitle>專題導覽</SidebarTitle>
              <NavigationMenu>
                {report.events.map((event, index) => (
                  <NavItem
                    key={index}
                    active={activeEvent === event}
                    onClick={() => handleNavClick(event)}
                  >
                    {event}
                  </NavItem>
                ))}
              </NavigationMenu>
            </SidebarCard>

            <TopicChatCard>
              <ChatHeader>
                <ChatIcon>💬</ChatIcon>
                <div>
                  <ChatTitle>專題討論</ChatTitle>
                  <ChatDescription>與AI助手討論這個專題的相關議題</ChatDescription>
                </div>
              </ChatHeader>

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

              <ChatMessages>
                {chatMessages.length === 0 && (
                  <Message isOwn={false}>
                    歡迎討論「{report.title}」這個專題！您可以詢問任何相關問題。
                  </Message>
                )}
                {chatMessages.map(message => (
                  <Message key={message.id} isOwn={message.isOwn}>
                    {message.text}
                  </Message>
                ))}
              </ChatMessages>

              <ChatInput
                type="text"
                placeholder="輸入您的問題或觀點..."
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <SendButton
                onClick={handleSendMessage}
                disabled={!chatInput.trim()}
              >
                發送訊息
              </SendButton>
            </TopicChatCard>
          </Sidebar>
        </ContentLayout>
      </MainContent>
    </PageContainer>
  );
}

export default SpecialReportDetail; 