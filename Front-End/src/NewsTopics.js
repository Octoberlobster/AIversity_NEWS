import React, { useState, useEffect } from 'react';
import { useSupabase } from './supabase';
import NewsTopicSources from './NewsTopicSources';
import './css/TimelineAnalysis.css';

const NewsTopics = ({ timelineItemId, mediaColors }) => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const supabaseClient = useSupabase();
  
  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const { data, error } = await supabaseClient
          .from('news_topics')
          .select('*')
          .eq('timeline_item_id', timelineItemId);
          
        if (error) throw error;
        setTopics(data || []);
      } catch (error) {
        console.error('Error fetching news topics:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTopics();
  }, [timelineItemId, supabaseClient]);
  
  if (loading) return null;
  if (topics.length === 0) return <div className="no-topics">此時間段無媒體焦點分析</div>;
  
  return (
    <div className="media-topics">
      <h4 className="topics-title">媒體焦點分析</h4>
      
      {topics.map((topic, topicIndex) => (
        <div className="topic-item" key={topicIndex}>
          <div className="topic-content">{topic.topic}</div>
          <NewsTopicSources 
            topicId={topic.news_topics_id} 
            mediaColors={mediaColors} 
          />
        </div>
      ))}
    </div>
  );
};

export default NewsTopics;
