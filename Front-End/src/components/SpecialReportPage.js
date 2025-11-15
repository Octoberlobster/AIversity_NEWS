import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './../css/SpecialReportPage.css';
import { useLanguageFields } from '../utils/useLanguageFields';
import { useSpecialReportsList } from '../hooks/useSpecialReports';
import { useCountry } from './CountryContext';

function SpecialReportPage() {
  const { t } = useTranslation();
  const { getCurrentLanguage, getFieldName } = useLanguageFields();
  const { selectedCountry } = useCountry();
  
  const getLanguageRoute = (path) => {
    return `/${getCurrentLanguage()}${path}`;
  };

  // 🚀 使用 React Query Hook 載入資料
  const { topicCounts, topicDetails, isLoading, error, refetch } = useSpecialReportsList();

  // 🚀 組合最終資料 (使用 useMemo 優化)
  const specialReports = useMemo(() => {
    if (!topicDetails || topicDetails.length === 0) return [];

    return topicDetails.map(topic => ({
      ...topic,
      topic_title: topic[getFieldName('topic_title')] || topic.topic_title,
      topic_short: topic[getFieldName('topic_short')] || topic.topic_short,
      articles: topicCounts[topic.topic_id] || 0,
      lastUpdate: topic.generated_date
    }));
  }, [topicDetails, topicCounts, getFieldName]);

  if (isLoading) {
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
          {t('specialReportPage.error.loadFailed', { error: error.message })}
          <button onClick={refetch} className="retry-button">
            {t('specialReportPage.retry')}
          </button>
        </div>
      </div>
    );
  }

  // 如果不是選擇臺灣，就顯示沒有專題
  if (selectedCountry !== 'taiwan') {
    return (
      <div className="srp-page">
        <header className="srp-header">
          <h1 className="srp-title">{t('specialReportPage.title')}</h1>
          <p className="srp-subtitle">{t('specialReportPage.subtitle')}</p>
        </header>
        <section className="srp-grid">
          <div className="no-data-message">{t('specialReportPage.empty.noTopics')}</div>
        </section>
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
                <Link to={getLanguageRoute(`/special-report/${report.topic_id}`)} target="_blank" rel="noopener noreferrer" className="srp-cardTitle-link">
                  <h3 className="srp-cardTitle">{report.topic_title}</h3>
                </Link>
              </div>

              <div className="srp-cardContent">
                <p className="srp-summary">{report.topic_short}</p>

                <div className="srp-meta">
                  <div className="srp-metaInfo">
                    <span>📄 {report.articles} {t('specialReportPage.meta.articles')}</span>
                    <span>🕒 {new Date(report.lastUpdate).toLocaleDateString('zh-TW')}</span>
                  </div>
                  <Link to={getLanguageRoute(`/special-report/${report.topic_id}`)} target="_blank" rel="noopener noreferrer" className="srp-readMore">
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
