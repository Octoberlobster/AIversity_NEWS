import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './../css/SpecialReportPage.css';
import { useSupabase } from './supabase';
import { useLanguageFields } from '../utils/useLanguageFields';

function SpecialReportPage() {
  const { t } = useTranslation();
  const { getCurrentLanguage, getFieldName, getMultiLanguageSelect } = useLanguageFields();
  
  const getLanguageRoute = (path) => {
    return `/${getCurrentLanguage()}${path}`;
  };
  const [specialReports, setSpecialReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const supabase = useSupabase();
  const currentLanguage = getCurrentLanguage();

  // 獲取專題新聞對應關係
  const fetchTopicNewsCounts = useCallback(async () => {
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
  }, [supabase]);

  // 獲取專題基本資訊
  const fetchTopicDetails = useCallback(async (topicIds) => {
    if (topicIds.length === 0) {
      return [];
    }

    // 準備多語言欄位查詢
    const multiLangFields = ['topic_title', 'topic_short'];
    const selectFields = getMultiLanguageSelect(multiLangFields);

    const { data, error } = await supabase
      .from('topic')
      .select(`topic_id, ${selectFields}, generated_date`)
      .in('topic_id', topicIds);

    if (error) {
      throw new Error(`無法獲取專題詳細資訊: ${error.message}`);
    }

    return data || [];
  }, [supabase, getMultiLanguageSelect]);

  // 組合最終資料
  const formatReportsData = useCallback((topicDetails, topicCounts) => {
    return topicDetails.map(topic => ({
      ...topic,
      // 使用多語言欄位，如果不存在則使用原欄位作為 fallback
      topic_title: topic[getFieldName('topic_title')] || topic.topic_title,
      topic_short: topic[getFieldName('topic_short')] || topic.topic_short,
      articles: topicCounts[topic.topic_id] || 0,
      lastUpdate: topic.generated_date
    }));
  }, [getFieldName]);

  // 主要資料獲取函數
  const fetchSpecialReports = useCallback(async () => {
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
  }, [fetchTopicNewsCounts, fetchTopicDetails, formatReportsData]);

  useEffect(() => {
    fetchSpecialReports();
  }, [fetchSpecialReports, currentLanguage]);

  if (loading) {
    return (
      <div className="srp-page">
        <div className="loading-message">{t('specialReportPage.loading')}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="srp-page">
        <div className="error-message">
          {t('specialReportPage.error.loadFailed', { error })}
          <button onClick={fetchSpecialReports} className="retry-button">
            {t('specialReportPage.retry')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="srp-page">
      <header className="srp-header">
        <h1 className="srp-title">{t('specialReportPage.title')}</h1>
        <p className="srp-subtitle">{t('specialReportPage.subtitle')}</p>
      </header>

      <section className="srp-grid">
        {specialReports.length === 0 ? (
          <div className="no-data-message">{t('specialReportPage.empty.noReports')}</div>
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
                    <span>📄 {report.articles} {t('specialReportPage.meta.articles')}</span>
                    <span>🕒 {new Date(report.lastUpdate).toLocaleDateString('zh-TW')}</span>
                  </div>
                  <Link to={getLanguageRoute(`/special-report/${report.topic_id}`)} className="srp-readMore">
                    {t('specialReportPage.meta.viewMore')}
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
