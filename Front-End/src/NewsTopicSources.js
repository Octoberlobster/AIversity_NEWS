import React, { useState, useEffect } from 'react';
import { useSupabase } from './supabase';
import './css/TimelineAnalysis.css';

const NewsTopicSources = ({ topicId, mediaColors }) => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const supabaseClient = useSupabase();
  
  // 獲取新聞來源的顏色
  const getSourceColor = (source) => {
    return mediaColors[source] || mediaColors.default;
  };

  useEffect(() => {
    const fetchTopicSources = async () => {
      try {
        const { data, error } = await supabaseClient
          .from('news_topic_sources')
          .select('*')
          .eq('news_topics_id', topicId);
          
        if (error) throw error;
        setSources(data || []);
      } catch (error) {
        console.error('Error fetching topic sources:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTopicSources();
  }, [topicId, supabaseClient]);
  
  if (loading) return null;
  if (sources.length === 0) return null;
  
  // 移除重複的來源
  const uniqueSources = [...new Set(sources.map(s => s.source))];
  
  return (
    <div className="topic-sources">
      {uniqueSources.map((source, sourceIndex) => (
        <span
          className="media-source-tag"
          key={sourceIndex}
          style={{
            backgroundColor: `${getSourceColor(source)}20`,
            color: getSourceColor(source),
            borderLeft: `3px solid ${getSourceColor(source)}`
          }}
        >
          {source}
        </span>
      ))}
    </div>
  );
};

export default NewsTopicSources;
