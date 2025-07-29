import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const PageContainer = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
`;

const PageHeader = styled.div`
  text-align: center;
  margin-bottom: 3rem;
`;

const PageTitle = styled.h1`
  color: #1e3a8a;
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  
  &::before {
    content: "📰";
    font-size: 2rem;
  }
`;

const PageSubtitle = styled.p`
  color: #6b7280;
  font-size: 1.1rem;
  margin: 0;
  line-height: 1.6;
`;

const ReportsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const ReportCard = styled.div`
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border-left: 4px solid #667eea;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    border-left-color: #7c3aed;
  }
`;

const ReportHeader = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  position: relative;
`;

const ReportIcon = styled.div`
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
`;

const ReportTitle = styled.h3`
  color: white;
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  line-height: 1.3;
`;

const ReportStatus = styled.span`
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 0.2rem 0.8rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
`;

const ReportContent = styled.div`
  padding: 1.5rem;
`;

const ReportSummary = styled.p`
  color: #4b5563;
  line-height: 1.6;
  margin: 0 0 1rem 0;
  font-size: 0.95rem;
`;

const EventBranches = styled.div`
  margin-top: 1rem;
`;

const BranchTitle = styled.h4`
  color: #1e3a8a;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
`;

const BranchList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`;

const BranchItem = styled.li`
  padding: 0.3rem 0;
  color: #6b7280;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &::before {
    content: "•";
    color: #667eea;
    font-weight: bold;
  }
`;

const ReportMeta = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
`;

const MetaInfo = styled.div`
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #6b7280;
`;

const ReadMoreButton = styled(Link)`
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  }
`;

// 模擬專題報導資料
const specialReports = [
  {
    id: 1,
    title: "2025罷免案",
    summary: "國民黨與民眾黨自2024年合作以來，因立法改革引發不滿，民間團體於2025年開始發起罷免國民黨立委。7月26日24位國民黨立委及新竹市長高虹安面臨罷免投票，25案全數被否決。第二波7案罷免投票將於8月23日舉行。",
    status: "進行中",
    icon: "🗳️",
    branches: [
      "即時開票",
      "結果分析", 
      "投票日動態",
      "立委罷免案",
      "高虹安罷免案",
      "罷免案日程",
      "投票須知",
      "其他文章"
    ],
    articles: 15,
    views: "25.3k",
    lastUpdate: "2025/7/29 15:48"
  },
  {
    id: 2,
    title: "人工智慧發展專題",
    summary: "深入探討人工智慧技術在各領域的應用與發展，從基礎技術到實際應用案例，全面解析AI對社會的影響。",
    status: "進行中",
    icon: "🤖",
    branches: [
      "AI技術發展",
      "機器學習應用",
      "深度學習進展",
      "AI倫理議題",
      "產業應用案例",
      "未來趨勢預測",
      "專家觀點",
      "技術解析"
    ],
    articles: 12,
    views: "18.7k",
    lastUpdate: "2025/7/28 10:30"
  },
  {
    id: 3,
    title: "氣候變遷與永續發展",
    summary: "分析全球氣候變遷現況，探討各國應對策略及永續發展目標的實現路徑，從科學證據到政策制定。",
    status: "進行中",
    icon: "🌍",
    branches: [
      "氣候科學數據",
      "全球政策分析",
      "永續發展目標",
      "減碳技術",
      "綠色能源",
      "國際合作",
      "個人行動指南",
      "未來展望"
    ],
    articles: 8,
    views: "12.4k",
    lastUpdate: "2025/7/27 14:15"
  },
  {
    id: 4,
    title: "氣候變遷與永續發展",
    summary: "分析全球氣候變遷現況，探討各國應對策略及永續發展目標的實現路徑，從科學證據到政策制定。",
    status: "進行中",
    icon: "🌍",
    branches: [
      "氣候科學數據",
      "全球政策分析",
      "永續發展目標",
      "減碳技術",
      "綠色能源",
      "國際合作",
      "個人行動指南",
      "未來展望"
    ],
    articles: 8,
    views: "12.4k",
    lastUpdate: "2025/7/27 14:15"
  },
  {
    id: 5,
    title: "氣候變遷與永續發展",
    summary: "分析全球氣候變遷現況，探討各國應對策略及永續發展目標的實現路徑，從科學證據到政策制定。",
    status: "進行中",
    icon: "🌍",
    branches: [
      "氣候科學數據",
      "全球政策分析",
      "永續發展目標",
      "減碳技術",
      "綠色能源",
      "國際合作",
      "個人行動指南",
      "未來展望"
    ],
    articles: 8,
    views: "12.4k",
    lastUpdate: "2025/7/27 14:15"
  },
  {
    id: 6,
    title: "氣候變遷與永續發展",
    summary: "分析全球氣候變遷現況，探討各國應對策略及永續發展目標的實現路徑，從科學證據到政策制定。",
    status: "進行中",
    icon: "🌍",
    branches: [
      "氣候科學數據",
      "全球政策分析",
      "永續發展目標",
      "減碳技術",
      "綠色能源",
      "國際合作",
      "個人行動指南",
      "未來展望"
    ],
    articles: 8,
    views: "12.4k",
    lastUpdate: "2025/7/27 14:15"
  }
];

function SpecialReportPage() {
  return (
    <PageContainer>
      <PageHeader>
        <PageTitle>專題報導</PageTitle>
        <PageSubtitle>
          深入探討重要議題，提供全面而深度的新聞分析
        </PageSubtitle>
      </PageHeader>

      <ReportsGrid>
        {specialReports.map(report => (
          <ReportCard key={report.id}>
            <ReportHeader>
              <ReportIcon>{report.icon}</ReportIcon>
              <ReportTitle>{report.title}</ReportTitle>
            </ReportHeader>
            <ReportContent>
              <ReportSummary>{report.summary}</ReportSummary>
              
              
              
              <ReportMeta>
                <MetaInfo>
                  <span>📄 {report.articles} 篇文章</span>
                  <span>👁️ {report.views}</span>
                  <span>🕒 {report.lastUpdate}</span>
                </MetaInfo>
                <ReadMoreButton to={`/special-report/${report.id}`}>
                  查看專題 →
                </ReadMoreButton>
              </ReportMeta>
            </ReportContent>
          </ReportCard>
        ))}
      </ReportsGrid>
    </PageContainer>
  );
}

export default SpecialReportPage; 