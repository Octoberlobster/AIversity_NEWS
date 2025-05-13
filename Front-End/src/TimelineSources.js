import React, { useState, useEffect } from 'react';
import { useSupabase } from './supabase';
import './css/TimelineAnalysis.css';

function TimelineSources({ timelineItemId }) {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const supabaseClient = useSupabase();
  
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const { data, error } = await supabaseClient
          .from('timeline_sources')
          .select('*')
          .eq('timeline_items_id', timelineItemId);
          
        if (error) throw error;
        setSources(data || []);
      } catch (error) {
        console.error('Error fetching timeline sources:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSources();
  }, [timelineItemId, supabaseClient]);
  
  if (loading) return <div className="loading-sources">載入來源中...</div>;
  if (sources.length === 0) return null;
  
  return (
    <div className="timeline-sources">
      <h4>資料來源：</h4>
      <ul className="sources-list">
        {sources.map(source => (
          <li key={source.timeline_sources_id} className="source-item">
            <a 
              href={source.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="source-link"
            >
              {source.source}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default TimelineSources;
