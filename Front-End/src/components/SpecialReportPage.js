import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './../css/SpecialReportPage.css';
import { useSupabase } from './supabase';

function SpecialReportPage() {
  const [specialReports, setSpecialReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const supabase = useSupabase();

  // 獲取專題新聞對應關係
  const fetchTopicNewsCounts = async () => {
    const { data: topicNewsData, error } = await supabase
      .from('topic_news_map')
      .select('topic_id');

    if (error) {
      throw new Error(`無法獲取專題新聞對應關係: ${error.message}`);
    }

    if (!topicNewsData || topicNewsData.length === 0) {
      return { topicCounts: {}, validTopicIds: [] };
    }

    // 計算每個 topic_id 的新聞數量
    const topicCounts = topicNewsData.reduce((acc, item) => {
      if (item.topic_id) {
        acc[item.topic_id] = (acc[item.topic_id] || 0) + 1;
      }
      return acc;
    }, {});

    // 過濾有效的 topic_id
    const validTopicIds = Object.keys(topicCounts).filter(id => id.trim() !== '');

    return { topicCounts, validTopicIds };
  };

  // 獲取專題基本資訊
  const fetchTopicDetails = async (topicIds) => {
    if (topicIds.length === 0) {
      return [];
    }

    const { data, error } = await supabase
      .from('topic')
      .select('topic_id, topic_title, topic_short, generated_date')
      .in('topic_id', topicIds);

    if (error) {
      throw new Error(`無法獲取專題詳細資訊: ${error.message}`);
    }

    return data || [];
  };

  // 組合最終資料
  const formatReportsData = (topicDetails, topicCounts) => {
    return topicDetails.map(topic => ({
      ...topic,
      articles: topicCounts[topic.topic_id] || 0,
      views: `${(Math.floor(Math.random() * 20) + 1).toFixed(1)}k`,
      lastUpdate: topic.generated_date
    }));
  };

  // 主要資料獲取函數
  const fetchSpecialReports = async () => {
    try {
      setLoading(true);
      setError(null);

      const { topicCounts, validTopicIds } = await fetchTopicNewsCounts();
      const topicDetails = await fetchTopicDetails(validTopicIds);
      const reports = formatReportsData(topicDetails, topicCounts);

      setSpecialReports(reports);
    } catch (err) {
      setError(err.message);
      console.error('獲取專題報導資料失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpecialReports();
  }, [supabase]);

  if (loading) {
    return (
      <div className="srp-page">
        <div className="loading-message">載入中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="srp-page">
        <div className="error-message">
          載入失敗: {error}
          <button onClick={fetchSpecialReports} className="retry-button">
            重新載入
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="srp-page">
      <header className="srp-header">
        <h1 className="srp-title">專題報導</h1>
        <p className="srp-subtitle">深入探討重要議題，提供全面而深度的新聞分析</p>
      </header>

      <section className="srp-grid">
        {specialReports.length === 0 ? (
          <div className="no-data-message">目前沒有專題報導</div>
        ) : (
          specialReports.map(report => (
            <article key={report.topic_id} className="srp-card">
              <div className="srp-cardHeader">
                <h3 className="srp-cardTitle">{report.topic_title}</h3>
              </div>

              <div className="srp-cardContent">
                <p className="srp-summary">{report.topic_short}</p>

                <div className="srp-meta">
                  <div className="srp-metaInfo">
                    <span>📄 {report.articles} 篇文章</span>
                    <span>👁️ {report.views}</span>
                    <span>🕒 {new Date(report.lastUpdate).toLocaleDateString('zh-TW')}</span>
                  </div>
                  <Link to={`/special-report/${report.topic_id}`} className="srp-readMore">
                    查看專題 →
                  </Link>
                </div>
              </div>
            </article>
          ))
        )}
      </section>
    </div>
  );
}

export default SpecialReportPage;
