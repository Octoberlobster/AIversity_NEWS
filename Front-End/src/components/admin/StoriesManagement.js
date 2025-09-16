import React, { useState, useEffect, useCallback } from 'react';
import { useSupabase } from '../supabase';
import AdminTable from './AdminTable';
import AdminModal from './AdminModal';

const StoriesManagement = () => {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStory, setSelectedStory] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('view'); // 'view', 'edit', 'create'
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  const supabase = useSupabase();

  // 載入 stories 資料
  const loadStories = useCallback(async () => {
    try {
      setLoading(true);
      let query = supabase
        .from('stories')
        .select('*', { count: 'exact' });

      // 搜尋過濾
      if (searchTerm) {
        query = query.or(`story_title.ilike.%${searchTerm}%,story_url.ilike.%${searchTerm}%`);
      }

      // 分類過濾
      if (filterCategory) {
        query = query.eq('category', filterCategory);
      }

      // 分頁
      const from = (currentPage - 1) * pageSize;
      const to = from + pageSize - 1;
      query = query.range(from, to);

      // 排序
      query = query.order('crawl_date', { ascending: false });

      const { data, error, count } = await query;

      if (error) throw error;

      setStories(data || []);
      setTotalCount(count || 0);
    } catch (error) {
      console.error('載入 stories 失敗:', error);
      alert('載入資料失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  }, [currentPage, searchTerm, filterCategory, supabase]);

  useEffect(() => {
    loadStories();
  }, [loadStories]);

  // 刪除 story 及其關聯資料（一條鏈刪除）
  const handleCascadeDelete = async (storyId) => {
    const confirmDelete = window.confirm(
      '⚠️ 警告：這將刪除此 Story 及其所有關聯資料，包括：\n' +
      '• Single News\n' +
      '• Cleaned News\n' +
      '• Keywords Map\n' +
      '• Term Map\n' +
      '• Topic News Map\n' +
      '• Topic Branch News Map\n' +
      '• Relative News\n' +
      '• Generated Image\n\n' +
      '此操作無法復原，確定要繼續嗎？'
    );

    if (!confirmDelete) return;

    try {
      setLoading(true);

      // 使用 Supabase RPC 函數來執行一條鏈刪除
      // 如果沒有 RPC 函數，我們需要手動刪除每個關聯表
      
      // 1. 刪除 topic_branch_news_map
      await supabase
        .from('topic_branch_news_map')
        .delete()
        .eq('story_id', storyId);

      // 2. 刪除 topic_news_map
      await supabase
        .from('topic_news_map')
        .delete()
        .eq('story_id', storyId);

      // 3. 刪除 keywords_map
      await supabase
        .from('keywords_map')
        .delete()
        .eq('story_id', storyId);

      // 4. 刪除 term_map
      await supabase
        .from('term_map')
        .delete()
        .eq('story_id', storyId);

      // 5. 刪除 relative_news (src 和 dst)
      await supabase
        .from('relative_news')
        .delete()
        .or(`src_story_id.eq.${storyId},dst_story_id.eq.${storyId}`);

      // 6. 刪除 relative_topics
      await supabase
        .from('relative_topics')
        .delete()
        .eq('src_story_id', storyId);

      // 7. 刪除 generated_image
      await supabase
        .from('generated_image')
        .delete()
        .eq('story_id', storyId);

      // 8. 刪除 cleaned_news
      await supabase
        .from('cleaned_news')
        .delete()
        .eq('story_id', storyId);

      // 9. 刪除 single_news
      await supabase
        .from('single_news')
        .delete()
        .eq('story_id', storyId);

      // 10. 最後刪除 stories
      const { error } = await supabase
        .from('stories')
        .delete()
        .eq('story_id', storyId);

      if (error) throw error;

      alert('✅ 成功刪除 Story 及所有關聯資料');
      loadStories(); // 重新載入資料
    } catch (error) {
      console.error('刪除失敗:', error);
      alert('❌ 刪除失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 儲存或更新 story
  const handleSave = async (formData) => {
    try {
      setLoading(true);
      
      if (modalMode === 'create') {
        // 新增時需要生成 UUID
        const storyId = crypto.randomUUID();
        const insertData = {
          ...formData,
          story_id: storyId
        };
        
        const { error } = await supabase
          .from('stories')
          .insert([insertData]);
        
        if (error) throw error;
        alert('✅ 新增成功');
      } else if (modalMode === 'edit') {
        // 編輯時過濾掉 story_id，因為它不應該被更新
        const { story_id, ...updateData } = formData;
        
        const { error } = await supabase
          .from('stories')
          .update(updateData)
          .eq('story_id', selectedStory.story_id);
        
        if (error) throw error;
        alert('✅ 更新成功');
      }
      
      setIsModalOpen(false);
      setSelectedStory(null);
      loadStories();
    } catch (error) {
      console.error('儲存失敗:', error);
      alert('❌ 儲存失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { key: 'story_title', label: '標題', sortable: true },
    { key: 'category', label: '分類', sortable: true },
    { key: 'crawl_date', label: '爬取日期', sortable: true },
    { key: 'story_url', label: 'URL', render: (value) => (
      <a href={value} target="_blank" rel="noopener noreferrer" className="url-link">
        {value?.substring(0, 50)}...
      </a>
    )},
    { key: 'crawl_date', label: '爬取日期', render: (value) => {
      if (!value) return <span className="missing-data">無日期</span>;
      return new Date(value).toLocaleDateString('zh-TW');
    }},
    {
      key: 'actions',
      label: '操作',
      render: (_, item) => (
        <div className="action-buttons">
          <button 
            onClick={() => {
              setSelectedStory(item);
              setModalMode('view');
              setIsModalOpen(true);
            }}
            className="btn-view"
            title="檢視"
          >
            👁️
          </button>
          <button 
            onClick={() => {
              setSelectedStory(item);
              setModalMode('edit');
              setIsModalOpen(true);
            }}
            className="btn-edit"
            title="編輯"
          >
            ✏️
          </button>
          <button 
            onClick={() => handleCascadeDelete(item.story_id)}
            className="btn-delete"
            title="一條鏈刪除"
          >
            🗑️
          </button>
        </div>
      )
    }
  ];

  const formFields = [
    { key: 'story_title', label: '標題', type: 'text', required: true },
    { key: 'story_url', label: 'URL', type: 'url', required: true },
    { 
      key: 'category', 
      label: '分類', 
      type: 'select',
      options: [
        'Politics', 'Taiwan News', 'International News', 'Science & Technology', 'Lifestyle & Consumer', 
        'Sports', 'Entertainment', 'Business & Finance', 'Health & Wellness'
      ],
      required: true 
    },
    { key: 'crawl_date', label: '爬取日期', type: 'date' }
  ];

  return (
    <div className="stories-management">
      <div className="management-header">
        <h2>📰 Stories 資料管理</h2>
        <p className="management-description">
          管理新聞故事的基本資料，支援一條鏈刪除功能（會同時刪除所有關聯資料）
        </p>
      </div>

      <div className="management-controls">
        <div className="search-filters">
          <input
            type="text"
            placeholder="搜尋標題或 URL..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="filter-select"
          >
            <option value="">所有分類</option>
            <option value="Politics">Politics</option>
            <option value="Taiwan News">Taiwan News</option>
            <option value="International News">International News</option>
            <option value="Science & Technology">Science & Technology</option>
            <option value="Lifestyle & Consumer">Lifestyle & Consumer</option>
            <option value="Sports">Sports</option>
            <option value="Entertainment">Entertainment</option>
            <option value="Business & Finance">Business & Finance</option>
            <option value="Health & Wellness">Health & Wellness</option>
          </select>
        </div>
        
        <button
          onClick={() => {
            setSelectedStory(null);
            setModalMode('create');
            setIsModalOpen(true);
          }}
          className="btn-create"
        >
          ➕ 新增 Story
        </button>
      </div>

      <AdminTable
        data={stories}
        columns={columns}
        loading={loading}
        currentPage={currentPage}
        totalCount={totalCount}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
      />

      <AdminModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedStory(null);
        }}
        title={modalMode === 'create' ? '新增 Story' : modalMode === 'edit' ? '編輯 Story' : '檢視 Story'}
        mode={modalMode}
        data={selectedStory}
        fields={formFields}
        onSave={handleSave}
      />
    </div>
  );
};

export default StoriesManagement;
