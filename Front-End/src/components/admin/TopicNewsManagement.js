import React, { useState, useEffect, useCallback } from 'react';
import { useSupabase } from '../supabase';
import AdminTable from './AdminTable';

const TopicNewsManagement = () => {
  const [mappings, setMappings] = useState([]);
  const [topics, setTopics] = useState([]);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedNews, setSelectedNews] = useState('');
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferringNews, setTransferringNews] = useState(null);
  const [targetTopic, setTargetTopic] = useState('');
  const pageSize = 20;

  const supabase = useSupabase();

  // 載入專題列表
  const loadTopics = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('topic')
        .select('topic_id, topic_title, topic_short')
        .order('topic_title');

      if (error) throw error;
      setTopics(data || []);
    } catch (error) {
      console.error('載入專題失敗:', error);
    }
  }, [supabase]);

  // 載入可用的新聞列表
  const loadAvailableNews = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('single_news')
        .select('story_id, news_title, category, ultra_short')
        .order('news_title');

      if (error) throw error;
      setNews(data || []);
    } catch (error) {
      console.error('載入新聞列表失敗:', error);
    }
  }, [supabase]);

  // 載入專題新聞映射
  const loadMappings = useCallback(async () => {
    try {
      setLoading(true);
      let query = supabase
        .from('topic_news_map')
        .select(`
          topic_id,
          story_id,
          topic:topic_id(
            topic_title,
            topic_short,
            ref_num
          ),
          single_news:story_id(
            news_title,
            category,
            ultra_short,
            generated_date
          )
        `, { count: 'exact' });

      // 專題過濾
      if (selectedTopic) {
        query = query.eq('topic_id', selectedTopic);
      }

      // 搜尋過濾
      if (searchTerm) {
        query = query.or(`single_news.news_title.ilike.%${searchTerm}%,topic.topic_title.ilike.%${searchTerm}%`);
      }

      // 分頁
      const from = (currentPage - 1) * pageSize;
      const to = from + pageSize - 1;
      query = query.range(from, to);

      const { data, error, count } = await query;

      if (error) throw error;

      setMappings(data || []);
      setTotalCount(count || 0);
    } catch (error) {
      console.error('載入映射關係失敗:', error);
      alert('載入資料失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  }, [currentPage, selectedTopic, searchTerm, supabase]);

  useEffect(() => {
    loadTopics();
    loadAvailableNews();
  }, [loadTopics, loadAvailableNews]);

  useEffect(() => {
    loadMappings();
  }, [loadMappings]);

  // 刪除映射關係
  const handleDeleteMapping = async (topicId, storyId) => {
    const confirmDelete = window.confirm('確定要移除這個新聞與專題的關聯嗎？\n\n⚠️ 這將同時移除該新聞在此專題所有分支中的關聯');
    if (!confirmDelete) return;

    try {
      setLoading(true);
      
      // 1. 先刪除專題分支中的關聯
      // 獲取該專題下的所有分支
      const { data: branches } = await supabase
        .from('topic_branch')
        .select('topic_branch_id')
        .eq('topic_id', topicId);

      if (branches && branches.length > 0) {
        const branchIds = branches.map(b => b.topic_branch_id);
        
        // 刪除該新聞在這些分支中的所有關聯
        const { error: branchDeleteError } = await supabase
          .from('topic_branch_news_map')
          .delete()
          .in('topic_branch_id', branchIds)
          .eq('story_id', storyId);

        if (branchDeleteError) throw branchDeleteError;
      }

      // 2. 再刪除專題關聯
      const { error } = await supabase
        .from('topic_news_map')
        .delete()
        .eq('topic_id', topicId)
        .eq('story_id', storyId);

      if (error) throw error;
      alert('✅ 移除關聯成功（包含所有分支關聯）');
      loadMappings();
    } catch (error) {
      console.error('移除關聯失敗:', error);
      alert('❌ 移除關聯失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 添加新的映射關係
  const handleAddMapping = async (topicId = selectedTopic, storyId = selectedNews) => {
    if (!topicId || !storyId) {
      alert('請選擇專題和新聞');
      return;
    }

    try {
      setLoading(true);
      
      // 檢查是否已存在相同的映射
      const { data: existing } = await supabase
        .from('topic_news_map')
        .select('*')
        .eq('topic_id', topicId)
        .eq('story_id', storyId);

      if (existing && existing.length > 0) {
        alert('⚠️ 該映射關係已存在');
        return;
      }

      const { error } = await supabase
        .from('topic_news_map')
        .insert([{
          topic_id: topicId,
          story_id: storyId
        }]);

      if (error) throw error;
      
      alert('✅ 添加映射關係成功');
      if (topicId === selectedTopic && storyId === selectedNews) {
        setShowAddModal(false);
        setSelectedNews('');
      }
      loadMappings();
    } catch (error) {
      console.error('添加映射關係失敗:', error);
      alert('❌ 添加映射關係失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 轉移新聞到其他專題或移除專題關聯
  const handleTransferNews = async () => {
    if (!transferringNews) {
      alert('沒有選擇要轉移的新聞');
      return;
    }

    try {
      setLoading(true);

      // 1. 先刪除舊專題分支中的關聯
      const { data: oldBranches } = await supabase
        .from('topic_branch')
        .select('topic_branch_id')
        .eq('topic_id', transferringNews.topic_id);

      if (oldBranches && oldBranches.length > 0) {
        const oldBranchIds = oldBranches.map(b => b.topic_branch_id);
        
        // 刪除該新聞在舊專題所有分支中的關聯
        const { error: branchDeleteError } = await supabase
          .from('topic_branch_news_map')
          .delete()
          .in('topic_branch_id', oldBranchIds)
          .eq('story_id', transferringNews.story_id);

        if (branchDeleteError) throw branchDeleteError;
      }

      // 2. 刪除舊的專題映射
      const { error: deleteError } = await supabase
        .from('topic_news_map')
        .delete()
        .eq('topic_id', transferringNews.topic_id)
        .eq('story_id', transferringNews.story_id);

      if (deleteError) throw deleteError;

      // 3. 如果選擇了新專題，創建新的映射
      if (targetTopic && targetTopic !== 'unassigned') {
        // 檢查是否已存在相同的映射
        const { data: existing } = await supabase
          .from('topic_news_map')
          .select('*')
          .eq('topic_id', targetTopic)
          .eq('story_id', transferringNews.story_id);

        if (existing && existing.length > 0) {
          alert('⚠️ 該新聞已在目標專題中');
          return;
        }

        const { error: insertError } = await supabase
          .from('topic_news_map')
          .insert([{
            topic_id: targetTopic,
            story_id: transferringNews.story_id
          }]);

        if (insertError) throw insertError;
      }

      const action = targetTopic === 'unassigned' ? '移除專題關聯' : '轉移';
      alert(`✅ ${action}成功（包含清理所有分支關聯）`);
      
      setShowTransferModal(false);
      setTransferringNews(null);
      setTargetTopic('');
      loadMappings();
    } catch (error) {
      console.error('轉移失敗:', error);
      alert('❌ 轉移失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { 
      key: 'topic', 
      label: '專題', 
      render: (topic) => (
        <div>
          <div className="topic-title">
            📋 {topic?.topic_title}
          </div>
          {topic?.topic_short && (
            <div className="topic-description">
              {topic.topic_short.substring(0, 100)}...
            </div>
          )}
          <small className="topic-stats">
            引用數: {topic?.ref_num || 0}
          </small>
        </div>
      )
    },
    { 
      key: 'single_news', 
      label: '新聞', 
      render: (news) => (
        <div>
          <div className="news-title">
            {news?.news_title || '無標題'}
          </div>
          <small className="news-category">
            分類: {news?.category || '未分類'}
          </small>
          <small className="news-date">
            發布: {news?.generated_date || '未知'}
          </small>
          {news?.ultra_short && (
            <div className="news-summary">
              {news.ultra_short.substring(0, 150)}...
            </div>
          )}
        </div>
      )
    },
    {
      key: 'actions',
      label: '操作',
      render: (_, item) => (
        <div className="action-buttons">
          <button 
            onClick={() => handleDeleteMapping(item.topic_id, item.story_id)}
            className="btn-delete"
            title="移除關聯"
          >
            🗑️ 移除
          </button>
          <button 
            onClick={() => {
              setTransferringNews(item);
              setTargetTopic('');
              setShowTransferModal(true);
            }}
            className="btn-transfer"
            title="轉移到其他專題"
          >
            🔄 轉移
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="topic-news-management">
      <div className="management-header">
        <h2>🎯 專題事件管理</h2>
        <p className="management-description">
          管理新聞與專題的關聯關係，手動調整自動分類結果
        </p>
      </div>

      <div className="management-controls">
        <div className="filter-row">
          <select
            value={selectedTopic}
            onChange={(e) => setSelectedTopic(e.target.value)}
            className="filter-select"
          >
            <option value="">選擇專題...</option>
            {topics.map(topic => (
              <option key={topic.topic_id} value={topic.topic_id}>
                {topic.topic_title}
              </option>
            ))}
          </select>

          <input
            type="text"
            placeholder="搜尋新聞標題或專題名稱..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="action-buttons">
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-create"
            disabled={!selectedTopic}
          >
            ➕ 手動添加新聞
          </button>
        </div>
      </div>

      <AdminTable
        data={mappings}
        columns={columns}
        loading={loading}
        currentPage={currentPage}
        totalCount={totalCount}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
      />

      {/* 手動添加新聞的模態框 */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>添加新聞到專題</h3>
              <button onClick={() => setShowAddModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>選擇新聞:</label>
                <select
                  value={selectedNews}
                  onChange={(e) => setSelectedNews(e.target.value)}
                  className="form-select"
                >
                  <option value="">請選擇新聞...</option>
                  {news.map(newsItem => (
                    <option key={newsItem.story_id} value={newsItem.story_id}>
                      [{newsItem.category}] {newsItem.news_title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="current-selection">
                <p>目標專題: {topics.find(t => t.topic_id === selectedTopic)?.topic_title}</p>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowAddModal(false)} className="btn-cancel">
                取消
              </button>
              <button onClick={() => handleAddMapping()} className="btn-save">
                添加
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 轉移專題的模態框 */}
      {showTransferModal && transferringNews && (
        <div className="modal-overlay" onClick={() => setShowTransferModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>轉移新聞專題</h3>
              <button onClick={() => setShowTransferModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="news-info">
                <h4>新聞資訊</h4>
                <p><strong>標題:</strong> {transferringNews.single_news?.news_title}</p>
                <p><strong>當前專題:</strong> {transferringNews.topic?.topic_title}</p>
                <p><strong>分類:</strong> {transferringNews.single_news?.category}</p>
              </div>
              <div className="form-group">
                <label>選擇目標專題:</label>
                <select
                  value={targetTopic}
                  onChange={(e) => setTargetTopic(e.target.value)}
                  className="form-select"
                >
                  <option value="">請選擇專題...</option>
                  <option value="unassigned">🚫 移除專題關聯</option>
                  {topics
                    .filter(topic => topic.topic_id !== transferringNews.topic_id)
                    .map(topic => (
                      <option key={topic.topic_id} value={topic.topic_id}>
                        📋 {topic.topic_title}
                      </option>
                    ))}
                </select>
              </div>
              {targetTopic === 'unassigned' && (
                <div className="warning-message">
                  ⚠️ 選擇此選項將移除該新聞與專題及所有分支的關聯
                </div>
              )}
              {targetTopic && targetTopic !== 'unassigned' && (
                <div className="info-message">
                  ℹ️ 轉移將清除該新聞在原專題所有分支中的關聯，並移動到新專題
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowTransferModal(false)} className="btn-cancel">
                取消
              </button>
              <button 
                onClick={handleTransferNews} 
                className="btn-save"
                disabled={!targetTopic}
              >
                {targetTopic === 'unassigned' ? '移除關聯' : '轉移'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TopicNewsManagement;
