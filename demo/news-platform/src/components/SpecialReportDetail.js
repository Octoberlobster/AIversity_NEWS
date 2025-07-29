import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import styled from 'styled-components';
import UnifiedNewsCard from './UnifiedNewsCard';

const PageContainer = styled.div`
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

const ReportIcon = styled.div`
  font-size: 3rem;
  margin-bottom: 0.5rem;
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

const ConnectionSection = styled.div`
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 2rem;
  align-items: center;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const ConnectionText = styled.div`
  color: #4b5563;
  font-size: 1rem;
  line-height: 1.6;
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

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const MainContent = styled.div``;

const Sidebar = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  position: sticky;
  top: 2rem;
  height: fit-content;
`;

const SidebarCard = styled.div`
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
`;

const SidebarTitle = styled.h3`
  color: #1e3a8a;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
`;

const EventGuide = styled.div`
  margin-bottom: 1rem;
`;

const EventItem = styled.div`
  padding: 0.8rem;
  margin-bottom: 0.5rem;
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#f8fafc'};
  color: ${props => props.active ? 'white' : '#4b5563'};
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  font-weight: 500;
  
  &:hover {
    background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#e0e7ff'};
    transform: translateX(4px);
  }
  
  &::before {
    content: "•";
    margin-right: 0.5rem;
    color: ${props => props.active ? 'white' : '#667eea'};
  }
`;

const EventContent = styled.div`
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
`;

const EventTitle = styled.h4`
  color: #1e3a8a;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
`;

const EventSummary = styled.p`
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0 0 1rem 0;
`;

const EventArticles = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const EventArticle = styled.div`
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: #e0e7ff;
    transform: translateX(4px);
  }
`;

const ArticleTitle = styled.div`
  color: #1e3a8a;
  font-weight: 500;
  margin-bottom: 0.2rem;
`;

const ArticleMeta = styled.div`
  color: #6b7280;
  font-size: 0.8rem;
  display: flex;
  gap: 1rem;
`;

const SectionTitle = styled.h2`
  color: #1e3a8a;
  font-size: 1.8rem;
  font-weight: 700;
  margin: 2rem 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &::before {
    content: "📰";
    font-size: 1.5rem;
  }
`;

const RelatedNewsSection = styled.div`
  margin-top: 2rem;
`;

const NewsFilter = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
`;

const FilterButton = styled.button`
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#f3f4f6'};
  color: ${props => props.active ? 'white' : '#4b5563'};
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

const NewsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const NewsCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border-left: 3px solid #667eea;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  }
`;

const NewsTitle = styled.h3`
  color: #1e3a8a;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  line-height: 1.3;
`;

const NewsSummary = styled.p`
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0 0 0.8rem 0;
`;

const NewsMeta = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: #9ca3af;
`;

const NewsCategory = styled.span`
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.2rem 0.6rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 500;
`;

// 模擬專題報導詳細資料
const specialReportData = {
  1: {
    id: 1,
    title: "2025罷免案",
    summary: "國民黨與民眾黨自2024年合作以來，因立法改革引發不滿，民間團體於2025年開始發起罷免國民黨立委。7月26日24位國民黨立委及新竹市長高虹安面臨罷免投票，25案全數被否決。第二波7案罷免投票將於8月23日舉行，包括馬文君、游顥、羅明才、江啟臣、楊瓊瓔、顏寬恒、林思銘等立委。",
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
    lastUpdate: "2025/7/29 15:48",
    eventDetails: {
      "即時開票": {
        title: "即時開票結果",
        summary: "最新罷免投票開票結果，包含各選區投票率、同意票與不同意票統計。",
        articles: [
          { id: 101, title: "7月26日罷免投票開票結果出爐", views: "12.5k", date: "2025/7/26" },
          { id: 102, title: "高虹安罷免案投票率達45%", views: "8.9k", date: "2025/7/26" },
          { id: 103, title: "24位立委罷免案全數被否決", views: "15.2k", date: "2025/7/26" }
        ]
      },
      "結果分析": {
        title: "投票結果深度分析",
        summary: "分析罷免投票結果的背後原因、政治影響及未來發展趨勢。",
        articles: [
          { id: 201, title: "罷免案失敗原因分析：選民結構與動員能力", views: "9.7k", date: "2025/7/27" },
          { id: 202, title: "國民黨基層組織力挽狂瀾，成功守住席次", views: "7.3k", date: "2025/7/27" },
          { id: 203, title: "罷免案對2026年選舉的影響評估", views: "11.8k", date: "2025/7/28" }
        ]
      },
      "投票日動態": {
        title: "投票日現場直擊",
        summary: "投票日當天的現場情況、選民反應及重要事件。",
        articles: [
          { id: 301, title: "投票日現場：選民踴躍參與，秩序良好", views: "6.4k", date: "2025/7/26" },
          { id: 302, title: "各黨派動員情況：國民黨全力催票", views: "5.2k", date: "2025/7/26" },
          { id: 303, title: "投票過程中的爭議事件整理", views: "4.8k", date: "2025/7/26" }
        ]
      },
      "立委罷免案": {
        title: "立委罷免案詳情",
        summary: "針對24位國民黨立委的罷免案詳細資訊及背景。",
        articles: [
          { id: 401, title: "24位國民黨立委罷免案完整名單", views: "13.1k", date: "2025/7/25" },
          { id: 402, title: "各立委罷免案連署人數統計", views: "8.6k", date: "2025/7/25" },
          { id: 403, title: "立委回應罷免案：強調服務選民決心", views: "7.9k", date: "2025/7/25" }
        ]
      },
      "高虹安罷免案": {
        title: "高虹安罷免案專題",
        summary: "新竹市長高虹安罷免案的詳細過程及結果。",
        articles: [
          { id: 501, title: "高虹安罷免案投票率創新高", views: "16.3k", date: "2025/7/26" },
          { id: 502, title: "新竹市民對高虹安施政滿意度調查", views: "9.4k", date: "2025/7/25" },
          { id: 503, title: "高虹安回應罷免案：繼續為市民服務", views: "6.7k", date: "2025/7/26" }
        ]
      },
      "罷免案日程": {
        title: "罷免案重要時程",
        summary: "罷免案的重要時間節點及後續發展。",
        articles: [
          { id: 601, title: "第二波罷免案8月23日舉行", views: "10.2k", date: "2025/7/28" },
          { id: 602, title: "罷免案法律程序及時間表", views: "5.8k", date: "2025/7/24" },
          { id: 603, title: "未來罷免案可能發展趨勢", views: "7.5k", date: "2025/7/29" }
        ]
      },
      "投票須知": {
        title: "投票相關資訊",
        summary: "罷免投票的相關規定、注意事項及投票指南。",
        articles: [
          { id: 701, title: "罷免投票資格及注意事項", views: "12.7k", date: "2025/7/24" },
          { id: 702, title: "投票地點查詢及交通資訊", views: "8.1k", date: "2025/7/24" },
          { id: 703, title: "投票日天氣預報及建議", views: "4.3k", date: "2025/7/25" }
        ]
      },
      "其他文章": {
        title: "相關新聞報導",
        summary: "與罷免案相關的其他新聞及評論文章。",
        articles: [
          { id: 801, title: "學者分析：罷免案對台灣民主的影響", views: "9.8k", date: "2025/7/27" },
          { id: 802, title: "國際媒體關注台灣罷免案發展", views: "6.2k", date: "2025/7/28" },
          { id: 803, title: "民眾對罷免制度的看法調查", views: "7.9k", date: "2025/7/29" }
        ]
      }
    }
  },
  2: {
    id: 2,
    title: "人工智慧發展專題",
    summary: "深入探討人工智慧技術在各領域的應用與發展，從基礎技術到實際應用案例，全面解析AI對社會的影響。涵蓋機器學習、深度學習、自然語言處理等核心技術，以及AI在醫療、金融、教育等領域的應用。",
    status: "進行中",
    icon: "🤖",
    events: [
      "AI技術發展",
      "機器學習應用",
      "深度學習進展",
      "AI倫理議題",
      "產業應用案例",
      "未來趨勢預測",
      "專家觀點",
      "技術解析"
    ],
    connectionMap: "AI技術發展涵蓋機器學習、深度學習、自然語言處理等核心領域。各技術相互關聯，共同推動AI產業發展。應用領域包括醫療診斷、金融風控、教育輔助等。",
    articles: 12,
    views: "18.7k",
    lastUpdate: "2025/7/28 10:30",
    eventDetails: {
      "AI技術發展": {
        title: "AI技術發展歷程",
        summary: "人工智慧技術的發展歷程、重要里程碑及技術突破。",
        articles: [
          { id: 901, title: "AI發展史：從圖靈測試到ChatGPT", views: "14.2k", date: "2025/7/28" },
          { id: 902, title: "2024年AI技術重大突破回顧", views: "11.5k", date: "2025/7/27" },
          { id: 903, title: "AI技術發展趨勢預測", views: "9.8k", date: "2025/7/26" }
        ]
      },
      "機器學習應用": {
        title: "機器學習實際應用",
        summary: "機器學習技術在各行業的實際應用案例及效果。",
        articles: [
          { id: 904, title: "機器學習在醫療診斷中的應用", views: "12.3k", date: "2025/7/28" },
          { id: 905, title: "金融業如何運用機器學習降低風險", views: "8.7k", date: "2025/7/27" },
          { id: 906, title: "機器學習在教育領域的創新應用", views: "7.4k", date: "2025/7/26" }
        ]
      },
      "深度學習進展": {
        title: "深度學習技術進展",
        summary: "深度學習技術的最新發展、算法改進及應用突破。",
        articles: [
          { id: 907, title: "深度學習在自然語言處理的突破", views: "13.1k", date: "2025/7/28" },
          { id: 908, title: "計算機視覺技術的最新進展", views: "10.2k", date: "2025/7/27" },
          { id: 909, title: "深度學習模型效率優化技術", views: "8.9k", date: "2025/7/26" }
        ]
      },
      "AI倫理議題": {
        title: "AI倫理與社會影響",
        summary: "人工智慧發展中的倫理問題、社會影響及監管議題。",
        articles: [
          { id: 910, title: "AI偏見問題：如何確保公平性", views: "11.8k", date: "2025/7/28" },
          { id: 911, title: "AI對就業市場的影響分析", views: "9.6k", date: "2025/7/27" },
          { id: 912, title: "AI監管政策國際比較", views: "7.3k", date: "2025/7/26" }
        ]
      },
      "產業應用案例": {
        title: "AI產業應用案例",
        summary: "各產業中AI技術的實際應用案例及成功經驗。",
        articles: [
          { id: 913, title: "製造業AI轉型成功案例", views: "10.5k", date: "2025/7/28" },
          { id: 914, title: "零售業AI應用提升顧客體驗", views: "8.2k", date: "2025/7/27" },
          { id: 915, title: "農業AI技術應用現況", views: "6.7k", date: "2025/7/26" }
        ]
      },
      "未來趨勢預測": {
        title: "AI未來發展趨勢",
        summary: "人工智慧技術的未來發展方向及趨勢預測。",
        articles: [
          { id: 916, title: "2025年AI技術發展趨勢預測", views: "12.7k", date: "2025/7/28" },
          { id: 917, title: "量子計算與AI結合的前景", views: "9.4k", date: "2025/7/27" },
          { id: 918, title: "AI在太空探索中的應用前景", views: "7.8k", date: "2025/7/26" }
        ]
      },
      "專家觀點": {
        title: "AI專家觀點分享",
        summary: "AI領域專家的觀點、見解及對未來發展的看法。",
        articles: [
          { id: 919, title: "AI專家談技術發展與社會責任", views: "11.2k", date: "2025/7/28" },
          { id: 920, title: "企業AI轉型專家的實戰經驗", views: "8.9k", date: "2025/7/27" },
          { id: 921, title: "學術界對AI發展的擔憂與建議", views: "6.5k", date: "2025/7/26" }
        ]
      },
      "技術解析": {
        title: "AI技術深度解析",
        summary: "人工智慧技術的深度技術解析及原理說明。",
        articles: [
          { id: 922, title: "神經網絡原理深度解析", views: "13.8k", date: "2025/7/28" },
          { id: 923, title: "自然語言處理技術詳解", views: "10.1k", date: "2025/7/27" },
          { id: 924, title: "AI算法優化技術分析", views: "8.3k", date: "2025/7/26" }
        ]
      }
    }
  },
  3: {
    id: 3,
    title: "氣候變遷與永續發展",
    summary: "分析全球氣候變遷現況，探討各國應對策略及永續發展目標的實現路徑，從科學證據到政策制定。涵蓋氣候科學、政策分析、技術創新等多個面向，為讀者提供全面的氣候議題解析。",
    status: "進行中",
    icon: "🌍",
    events: [
      "氣候科學數據",
      "全球政策分析",
      "永續發展目標",
      "減碳技術",
      "綠色能源",
      "國際合作",
      "個人行動指南",
      "未來展望"
    ],
    connectionMap: "氣候變遷影響全球各國，需要國際合作共同應對。各國制定減碳政策，發展綠色能源技術，推動永續發展目標。個人行動與政策制定相輔相成。",
    articles: 8,
    views: "12.4k",
    lastUpdate: "2025/7/27 14:15",
    eventDetails: {
      "氣候科學數據": {
        title: "氣候科學數據分析",
        summary: "最新的氣候科學數據、研究發現及趨勢分析。",
        articles: [
          { id: 1001, title: "2024年全球氣溫創歷史新高", views: "15.3k", date: "2025/7/27" },
          { id: 1002, title: "北極冰層融化速度加快", views: "11.7k", date: "2025/7/26" },
          { id: 1003, title: "極端氣候事件頻率增加", views: "9.2k", date: "2025/7/25" }
        ]
      },
      "全球政策分析": {
        title: "全球氣候政策分析",
        summary: "各國氣候政策的比較分析及效果評估。",
        articles: [
          { id: 1004, title: "歐盟氣候政策最新進展", views: "12.8k", date: "2025/7/27" },
          { id: 1005, title: "美國氣候政策轉變分析", views: "10.4k", date: "2025/7/26" },
          { id: 1006, title: "亞洲國家氣候政策比較", views: "8.6k", date: "2025/7/25" }
        ]
      },
      "永續發展目標": {
        title: "永續發展目標進展",
        summary: "聯合國永續發展目標的實現進度及挑戰。",
        articles: [
          { id: 1007, title: "SDGs目標實現進度報告", views: "13.5k", date: "2025/7/27" },
          { id: 1008, title: "企業永續發展實踐案例", views: "9.8k", date: "2025/7/26" },
          { id: 1009, title: "永續發展目標面臨的挑戰", views: "7.3k", date: "2025/7/25" }
        ]
      },
      "減碳技術": {
        title: "減碳技術創新",
        summary: "最新的減碳技術發展及應用案例。",
        articles: [
          { id: 1010, title: "碳捕獲技術最新突破", views: "14.2k", date: "2025/7/27" },
          { id: 1011, title: "工業減碳技術應用案例", views: "10.7k", date: "2025/7/26" },
          { id: 1012, title: "建築節能技術發展", views: "8.9k", date: "2025/7/25" }
        ]
      },
      "綠色能源": {
        title: "綠色能源發展",
        summary: "可再生能源技術發展及應用現況。",
        articles: [
          { id: 1013, title: "太陽能技術效率提升", views: "12.1k", date: "2025/7/27" },
          { id: 1014, title: "風力發電成本持續下降", views: "9.5k", date: "2025/7/26" },
          { id: 1015, title: "氫能源技術發展前景", views: "7.8k", date: "2025/7/25" }
        ]
      },
      "國際合作": {
        title: "國際氣候合作",
        summary: "國際氣候合作的進展及挑戰。",
        articles: [
          { id: 1016, title: "巴黎協定執行進度評估", views: "13.9k", date: "2025/7/27" },
          { id: 1017, title: "國際氣候基金運作現況", views: "10.2k", date: "2025/7/26" },
          { id: 1018, title: "氣候談判最新進展", views: "8.4k", date: "2025/7/25" }
        ]
      },
      "個人行動指南": {
        title: "個人減碳行動",
        summary: "個人可以採取的減碳行動及生活建議。",
        articles: [
          { id: 1019, title: "日常生活減碳小技巧", views: "11.6k", date: "2025/7/27" },
          { id: 1020, title: "綠色消費指南", views: "9.1k", date: "2025/7/26" },
          { id: 1021, title: "環保生活實踐案例", views: "7.2k", date: "2025/7/25" }
        ]
      },
      "未來展望": {
        title: "氣候變遷未來展望",
        summary: "氣候變遷的未來發展趨勢及應對策略。",
        articles: [
          { id: 1022, title: "2050年氣候變遷預測", views: "14.7k", date: "2025/7/27" },
          { id: 1023, title: "氣候適應策略發展", views: "10.8k", date: "2025/7/26" },
          { id: 1024, title: "氣候正義議題探討", views: "8.5k", date: "2025/7/25" }
        ]
      }
    }
  }
};

// 模擬專題相關新聞資料
const getRelatedNews = (reportId) => {
  const newsData = {
    1: { // 2025罷免案
      "即時開票": [
        { id: 101, title: "7月26日罷免投票開票結果出爐", summary: "最新罷免投票開票結果，包含各選區投票率、同意票與不同意票統計。", category: "政治", views: "12.5k", date: "2025/7/26" },
        { id: 102, title: "高虹安罷免案投票率達45%", summary: "新竹市長高虹安罷免案投票率創下新高，顯示選民對罷免案的高度關注。", category: "政治", views: "8.9k", date: "2025/7/26" },
        { id: 103, title: "24位立委罷免案全數被否決", summary: "國民黨24位立委罷免案投票結果出爐，所有罷免案均未通過門檻。", category: "政治", views: "15.2k", date: "2025/7/26" }
      ],
      "結果分析": [
        { id: 201, title: "罷免案失敗原因分析：選民結構與動員能力", summary: "深入分析罷免案失敗的背後原因，探討選民結構與政黨動員能力的影響。", category: "分析", views: "9.7k", date: "2025/7/27" },
        { id: 202, title: "國民黨基層組織力挽狂瀾，成功守住席次", summary: "國民黨基層組織展現強大動員能力，成功守住所有面臨罷免的立委席次。", category: "政治", views: "7.3k", date: "2025/7/27" },
        { id: 203, title: "罷免案對2026年選舉的影響評估", summary: "專家分析罷免案結果對2026年選舉的潛在影響及政治效應。", category: "分析", views: "11.8k", date: "2025/7/28" }
      ],
      "投票日動態": [
        { id: 301, title: "投票日現場：選民踴躍參與，秩序良好", summary: "罷免投票日現場直擊，選民踴躍參與投票，整體秩序良好。", category: "現場", views: "6.4k", date: "2025/7/26" },
        { id: 302, title: "各黨派動員情況：國民黨全力催票", summary: "各黨派在罷免投票日的動員情況，國民黨展現強大的基層組織力。", category: "政治", views: "5.2k", date: "2025/7/26" },
        { id: 303, title: "投票過程中的爭議事件整理", summary: "罷免投票過程中發生的爭議事件整理及相關處理情況。", category: "政治", views: "4.8k", date: "2025/7/26" }
      ],
      "立委罷免案": [
        { id: 401, title: "24位國民黨立委罷免案完整名單", summary: "完整列出24位面臨罷免的國民黨立委名單及相關背景資訊。", category: "政治", views: "13.1k", date: "2025/7/25" },
        { id: 402, title: "各立委罷免案連署人數統計", summary: "各立委罷免案的連署人數統計及達標情況分析。", category: "統計", views: "8.6k", date: "2025/7/25" },
        { id: 403, title: "立委回應罷免案：強調服務選民決心", summary: "面臨罷免的立委們回應罷免案，強調繼續服務選民的決心。", category: "政治", views: "7.9k", date: "2025/7/25" }
      ],
      "高虹安罷免案": [
        { id: 501, title: "高虹安罷免案投票率創新高", summary: "新竹市長高虹安罷免案投票率創下新高，顯示選民高度關注。", category: "政治", views: "16.3k", date: "2025/7/26" },
        { id: 502, title: "新竹市民對高虹安施政滿意度調查", summary: "最新民調顯示新竹市民對高虹安施政的滿意度調查結果。", category: "民調", views: "9.4k", date: "2025/7/25" },
        { id: 503, title: "高虹安回應罷免案：繼續為市民服務", summary: "高虹安針對罷免案發表回應，強調將繼續為新竹市民服務。", category: "政治", views: "6.7k", date: "2025/7/26" }
      ],
      "罷免案日程": [
        { id: 601, title: "第二波罷免案8月23日舉行", summary: "第二波7案罷免投票將於8月23日舉行，包含多位國民黨立委。", category: "政治", views: "10.2k", date: "2025/7/28" },
        { id: 602, title: "罷免案法律程序及時間表", summary: "詳細說明罷免案的法律程序、時間表及相關規定。", category: "法律", views: "5.8k", date: "2025/7/24" },
        { id: 603, title: "未來罷免案可能發展趨勢", summary: "分析未來罷免案可能的發展趨勢及對政治生態的影響。", category: "分析", views: "7.5k", date: "2025/7/29" }
      ],
      "投票須知": [
        { id: 701, title: "罷免投票資格及注意事項", summary: "詳細說明罷免投票的資格條件及投票時需要注意的事項。", category: "指南", views: "12.7k", date: "2025/7/24" },
        { id: 702, title: "投票地點查詢及交通資訊", summary: "提供罷免投票地點查詢服務及相關交通資訊。", category: "指南", views: "8.1k", date: "2025/7/24" },
        { id: 703, title: "投票日天氣預報及建議", summary: "罷免投票日的天氣預報及相關投票建議。", category: "指南", views: "4.3k", date: "2025/7/25" }
      ],
      "其他文章": [
        { id: 801, title: "學者分析：罷免案對台灣民主的影響", summary: "學者專家分析罷免案對台灣民主發展的深遠影響。", category: "分析", views: "9.8k", date: "2025/7/27" },
        { id: 802, title: "國際媒體關注台灣罷免案發展", summary: "國際媒體對台灣罷免案發展的關注及相關報導。", category: "國際", views: "6.2k", date: "2025/7/28" },
        { id: 803, title: "民眾對罷免制度的看法調查", summary: "最新民調顯示民眾對罷免制度的看法及支持度調查。", category: "民調", views: "7.9k", date: "2025/7/29" }
      ]
    },
    2: { // 人工智慧發展專題
      "AI技術發展": [
        { id: 901, title: "AI發展史：從圖靈測試到ChatGPT", summary: "回顧人工智慧發展的重要里程碑，從圖靈測試到現代AI技術的演進。", category: "科技", views: "14.2k", date: "2025/7/28" },
        { id: 902, title: "2024年AI技術重大突破回顧", summary: "2024年人工智慧技術的重大突破及對產業的影響分析。", category: "科技", views: "11.5k", date: "2025/7/27" },
        { id: 903, title: "AI技術發展趨勢預測", summary: "專家預測未來AI技術的發展趨勢及可能的技術突破。", category: "科技", views: "9.8k", date: "2025/7/26" }
      ],
      "機器學習應用": [
        { id: 904, title: "機器學習在醫療診斷中的應用", summary: "機器學習技術在醫療診斷領域的實際應用案例及效果評估。", category: "醫療", views: "12.3k", date: "2025/7/28" },
        { id: 905, title: "金融業如何運用機器學習降低風險", summary: "金融業運用機器學習技術降低風險的實際案例及效果分析。", category: "金融", views: "8.7k", date: "2025/7/27" },
        { id: 906, title: "機器學習在教育領域的創新應用", summary: "機器學習技術在教育領域的創新應用案例及未來發展前景。", category: "教育", views: "7.4k", date: "2025/7/26" }
      ],
      "深度學習進展": [
        { id: 907, title: "深度學習在自然語言處理的突破", summary: "深度學習技術在自然語言處理領域的最新突破及應用。", category: "科技", views: "13.1k", date: "2025/7/28" },
        { id: 908, title: "計算機視覺技術的最新進展", summary: "計算機視覺技術的最新發展及在各領域的應用突破。", category: "科技", views: "10.2k", date: "2025/7/27" },
        { id: 909, title: "深度學習模型效率優化技術", summary: "深度學習模型效率優化的最新技術及實際應用效果。", category: "科技", views: "8.9k", date: "2025/7/26" }
      ],
      "AI倫理議題": [
        { id: 910, title: "AI偏見問題：如何確保公平性", summary: "探討AI系統中的偏見問題及如何確保AI決策的公平性。", category: "倫理", views: "11.8k", date: "2025/7/28" },
        { id: 911, title: "AI對就業市場的影響分析", summary: "深入分析AI技術對就業市場的影響及未來就業趨勢。", category: "社會", views: "9.6k", date: "2025/7/27" },
        { id: 912, title: "AI監管政策國際比較", summary: "各國AI監管政策的比較分析及對產業發展的影響。", category: "政策", views: "7.3k", date: "2025/7/26" }
      ],
      "產業應用案例": [
        { id: 913, title: "製造業AI轉型成功案例", summary: "製造業運用AI技術進行數位轉型的成功案例分享。", category: "產業", views: "10.5k", date: "2025/7/28" },
        { id: 914, title: "零售業AI應用提升顧客體驗", summary: "零售業運用AI技術提升顧客體驗的實際應用案例。", category: "產業", views: "8.2k", date: "2025/7/27" },
        { id: 915, title: "農業AI技術應用現況", summary: "AI技術在農業領域的應用現況及未來發展前景。", category: "農業", views: "6.7k", date: "2025/7/26" }
      ],
      "未來趨勢預測": [
        { id: 916, title: "2025年AI技術發展趨勢預測", summary: "專家預測2025年AI技術的發展趨勢及可能的技術突破。", category: "預測", views: "12.7k", date: "2025/7/28" },
        { id: 917, title: "量子計算與AI結合的前景", summary: "量子計算與AI技術結合的發展前景及潛在應用。", category: "科技", views: "9.4k", date: "2025/7/27" },
        { id: 918, title: "AI在太空探索中的應用前景", summary: "AI技術在太空探索領域的應用前景及發展潛力。", category: "太空", views: "7.8k", date: "2025/7/26" }
      ],
      "專家觀點": [
        { id: 919, title: "AI專家談技術發展與社會責任", summary: "AI領域專家分享對技術發展與社會責任的看法。", category: "觀點", views: "11.2k", date: "2025/7/28" },
        { id: 920, title: "企業AI轉型專家的實戰經驗", summary: "企業AI轉型專家分享實戰經驗及成功關鍵因素。", category: "經驗", views: "8.9k", date: "2025/7/27" },
        { id: 921, title: "學術界對AI發展的擔憂與建議", summary: "學術界對AI發展的擔憂及相關政策建議。", category: "學術", views: "6.5k", date: "2025/7/26" }
      ],
      "技術解析": [
        { id: 922, title: "神經網絡原理深度解析", summary: "深入解析神經網絡的基本原理及運作機制。", category: "技術", views: "13.8k", date: "2025/7/28" },
        { id: 923, title: "自然語言處理技術詳解", summary: "詳細介紹自然語言處理技術的原理及應用。", category: "技術", views: "10.1k", date: "2025/7/27" },
        { id: 924, title: "AI算法優化技術分析", summary: "分析AI算法優化的最新技術及實際應用效果。", category: "技術", views: "8.3k", date: "2025/7/26" }
      ]
    },
    3: { // 氣候變遷與永續發展
      "氣候科學數據": [
        { id: 1001, title: "2024年全球氣溫創歷史新高", summary: "最新氣候數據顯示2024年全球氣溫創下歷史新高，氣候變遷加劇。", category: "科學", views: "15.3k", date: "2025/7/27" },
        { id: 1002, title: "北極冰層融化速度加快", summary: "科學家發現北極冰層融化速度正在加快，對全球氣候造成影響。", category: "科學", views: "11.7k", date: "2025/7/26" },
        { id: 1003, title: "極端氣候事件頻率增加", summary: "最新研究顯示極端氣候事件的頻率正在增加，影響全球各地。", category: "科學", views: "9.2k", date: "2025/7/25" }
      ],
      "全球政策分析": [
        { id: 1004, title: "歐盟氣候政策最新進展", summary: "歐盟最新氣候政策的進展及對全球氣候行動的影響。", category: "政策", views: "12.8k", date: "2025/7/27" },
        { id: 1005, title: "美國氣候政策轉變分析", summary: "分析美國氣候政策的轉變及對國際氣候合作的影響。", category: "政策", views: "10.4k", date: "2025/7/26" },
        { id: 1006, title: "亞洲國家氣候政策比較", summary: "比較亞洲各國的氣候政策及實施效果。", category: "政策", views: "8.6k", date: "2025/7/25" }
      ],
      "永續發展目標": [
        { id: 1007, title: "SDGs目標實現進度報告", summary: "聯合國永續發展目標的實現進度報告及挑戰分析。", category: "永續", views: "13.5k", date: "2025/7/27" },
        { id: 1008, title: "企業永續發展實踐案例", summary: "企業實踐永續發展目標的成功案例分享。", category: "企業", views: "9.8k", date: "2025/7/26" },
        { id: 1009, title: "永續發展目標面臨的挑戰", summary: "分析永續發展目標實現過程中面臨的挑戰及解決方案。", category: "永續", views: "7.3k", date: "2025/7/25" }
      ],
      "減碳技術": [
        { id: 1010, title: "碳捕獲技術最新突破", summary: "碳捕獲技術的最新突破及在減碳中的應用前景。", category: "技術", views: "14.2k", date: "2025/7/27" },
        { id: 1011, title: "工業減碳技術應用案例", summary: "工業減碳技術的實際應用案例及效果評估。", category: "技術", views: "10.7k", date: "2025/7/26" },
        { id: 1012, title: "建築節能技術發展", summary: "建築節能技術的最新發展及在永續建築中的應用。", category: "技術", views: "8.9k", date: "2025/7/25" }
      ],
      "綠色能源": [
        { id: 1013, title: "太陽能技術效率提升", summary: "太陽能技術效率的最新提升及成本下降趨勢。", category: "能源", views: "12.1k", date: "2025/7/27" },
        { id: 1014, title: "風力發電成本持續下降", summary: "風力發電技術成本持續下降，競爭力不斷提升。", category: "能源", views: "9.5k", date: "2025/7/26" },
        { id: 1015, title: "氫能源技術發展前景", summary: "氫能源技術的發展前景及在能源轉型中的角色。", category: "能源", views: "7.8k", date: "2025/7/25" }
      ],
      "國際合作": [
        { id: 1016, title: "巴黎協定執行進度評估", summary: "巴黎協定的執行進度評估及各國承諾的實現情況。", category: "國際", views: "13.9k", date: "2025/7/27" },
        { id: 1017, title: "國際氣候基金運作現況", summary: "國際氣候基金的運作現況及對發展中國家的支持。", category: "國際", views: "10.2k", date: "2025/7/26" },
        { id: 1018, title: "氣候談判最新進展", summary: "國際氣候談判的最新進展及未來發展方向。", category: "國際", views: "8.4k", date: "2025/7/25" }
      ],
      "個人行動指南": [
        { id: 1019, title: "日常生活減碳小技巧", summary: "提供日常生活中可以採取的減碳小技巧及建議。", category: "生活", views: "11.6k", date: "2025/7/27" },
        { id: 1020, title: "綠色消費指南", summary: "綠色消費的完整指南及環保產品選擇建議。", category: "生活", views: "9.1k", date: "2025/7/26" },
        { id: 1021, title: "環保生活實踐案例", summary: "環保生活的實際實踐案例分享及經驗交流。", category: "生活", views: "7.2k", date: "2025/7/25" }
      ],
      "未來展望": [
        { id: 1022, title: "2050年氣候變遷預測", summary: "科學家對2050年氣候變遷的預測及應對策略。", category: "預測", views: "14.7k", date: "2025/7/27" },
        { id: 1023, title: "氣候適應策略發展", summary: "氣候適應策略的發展及在極端氣候中的應用。", category: "策略", views: "10.8k", date: "2025/7/26" },
        { id: 1024, title: "氣候正義議題探討", summary: "探討氣候正義議題及對發展中國家的影響。", category: "正義", views: "8.5k", date: "2025/7/25" }
      ]
    }
  };
  
  return newsData[reportId] || {};
};

function SpecialReportDetail() {
  const { id } = useParams();
  const report = specialReportData[id];
  const [activeEvent, setActiveEvent] = useState(report?.events[0] || '');
  const [selectedCategory, setSelectedCategory] = useState('全部');

  if (!report) {
    return (
      <PageContainer>
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <h2>專題報導不存在</h2>
          <p>請返回專題報導列表</p>
          <Link to="/special-reports" style={{ color: '#667eea' }}>返回專題報導</Link>
        </div>
      </PageContainer>
    );
  }

  const relatedNews = getRelatedNews(report.id);
  const allNews = Object.values(relatedNews).flat();
  const categories = ['全部', ...new Set(allNews.map(news => news.category))];
  
  const filteredNews = selectedCategory === '全部' 
    ? allNews 
    : allNews.filter(news => news.category === selectedCategory);

  return (
    <PageContainer>
      <ReportHeader>
        <HeaderContent>
          <ReportIcon>{report.icon}</ReportIcon>
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

      <ContentGrid>
        <MainContent>
          <SectionTitle>相關報導</SectionTitle>
          
          <NewsFilter>
            {categories.map(category => (
              <FilterButton
                key={category}
                active={selectedCategory === category}
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </FilterButton>
            ))}
          </NewsFilter>
          
          <NewsGrid>
            {filteredNews.map(news => (
              <NewsCard key={news.id}>
                <NewsTitle>{news.title}</NewsTitle>
                <NewsSummary>{news.summary}</NewsSummary>
                <NewsMeta>
                  <div>
                    <NewsCategory>{news.category}</NewsCategory>
                  </div>
                  <div>
                    <span>👁️ {news.views}</span>
                    <span style={{ marginLeft: '0.5rem' }}>📅 {news.date}</span>
                  </div>
                </NewsMeta>
              </NewsCard>
            ))}
          </NewsGrid>
        </MainContent>
        
        <Sidebar>
          <SidebarCard>
            <SidebarTitle>事件導引</SidebarTitle>
            <EventGuide>
              {report.events.map((event, index) => (
                <EventItem
                  key={index}
                  active={activeEvent === event}
                  onClick={() => setActiveEvent(event)}
                >
                  {event}
                </EventItem>
              ))}
            </EventGuide>
          </SidebarCard>
        </Sidebar>
      </ContentGrid>
    </PageContainer>
  );
}

export default SpecialReportDetail; 