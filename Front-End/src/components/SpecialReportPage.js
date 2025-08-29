import React from 'react';
import { Link } from 'react-router-dom';
import './../css/SpecialReportPage.css';

// 模擬專題報導資料（原樣保留）
const specialReports = [
  {
    id: 1,
    title: "2025罷免案",
    summary: "國民黨與民眾黨自2024年合作以來，因立法改革引發不滿，民間團體於2025年開始發起罷免國民黨立委。7月26日24位國民黨立委及新竹市長高虹安面臨罷免投票，25案全數被否決。第二波7案罷免投票將於8月23日舉行。",
    icon: "🗳️",
    articles: 15,
    views: "25.3k",
    lastUpdate: "2025/7/29 15:48"
  },
  {
    id: 2,
    title: "人工智慧發展專題",
    summary: "深入探討人工智慧技術在各領域的應用與發展，從基礎技術到實際應用案例，全面解析AI對社會的影響。",
    icon: "🤖",
    articles: 12,
    views: "18.7k",
    lastUpdate: "2025/7/28 10:30"
  },
  {
    id: 3,
    title: "氣候變遷與永續發展",
    summary: "分析全球氣候變遷現況，探討各國應對策略及永續發展目標的實現路徑，從科學證據到政策制定。",
    icon: "🌍",
    articles: 8,
    views: "12.4k",
    lastUpdate: "2025/7/27 14:15"
  },
];

function SpecialReportPage() {
  return (
    <div className="srp-page">
      <header className="srp-header">
        <h1 className="srp-title">專題報導</h1>
        <p className="srp-subtitle">深入探討重要議題，提供全面而深度的新聞分析</p>
      </header>

      <section className="srp-grid">
        {specialReports.map(report => (
          <article key={report.id} className="srp-card">
            <div className="srp-cardHeader">
              {/* 如需顯示 icon 或 status，可在這裡插入 */}
              <h3 className="srp-cardTitle">{report.title}</h3>
            </div>

            <div className="srp-cardContent">
              <p className="srp-summary">{report.summary}</p>

              <div className="srp-meta">
                <div className="srp-metaInfo">
                  <span>📄 {report.articles} 篇文章</span>
                  <span>👁️ {report.views}</span>
                  <span>🕒 {report.lastUpdate}</span>
                </div>
                <Link to={`/special-report/${report.id}`} className="srp-readMore">
                  查看專題 →
                </Link>
              </div>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}

export default SpecialReportPage;
