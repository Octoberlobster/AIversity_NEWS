import React, { useState, useEffect, useCallback } from 'react';
import { useSupabase } from '../supabase';
import AdminTable from './AdminTable';
import AdminModal from './AdminModal';

const SingleNewsManagement = () => {
  const [singleNews, setSingleNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNews, setSelectedNews] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('view');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedRows, setSelectedRows] = useState([]);
  const [batchEditModal, setBatchEditModal] = useState(false);
  const pageSize = 20;

  const supabase = useSupabase();

  // 載入 single_news 資料
  const loadSingleNews = useCallback(async () => {
    try {
      setLoading(true);
      let query = supabase
        .from('single_news')
        .select(`
          *,
          stories(
            story_title,
            story_url,
            crawl_date
          )
        `, { count: 'exact' });

      // 搜尋過濾
      if (searchTerm) {
        query = query.or(`news_title.ilike.%${searchTerm}%,ultra_short.ilike.%${searchTerm}%,short.ilike.%${searchTerm}%`);
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
      query = query.order('generated_date', { ascending: false });

      const { data, error, count } = await query;

      if (error) throw error;

      setSingleNews(data || []);
      setTotalCount(count || 0);
    } catch (error) {
      console.error('載入 single news 失敗:', error);
      alert('載入資料失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  }, [currentPage, searchTerm, filterCategory, supabase]);

  useEffect(() => {
    loadSingleNews();
  }, [loadSingleNews]);

  // 刪除新聞
  const handleDelete = async (storyId) => {
    const confirmDelete = window.confirm('確定要刪除這篇新聞嗎？');
    if (!confirmDelete) return;

    try {
      setLoading(true);
      
      // 先刪除相關的外鍵記錄
      // 1. 刪除 keywords_map 中的記錄
      const { error: keywordsError } = await supabase
        .from('keywords_map')
        .delete()
        .eq('story_id', storyId);
      
      if (keywordsError) {
        console.warn('刪除關鍵詞映射時出現警告:', keywordsError);
        // 不中斷流程，因為可能沒有相關記錄
      }

      // 2. 刪除 term_map 中的記錄
      const { error: termMapError } = await supabase
        .from('term_map')
        .delete()
        .eq('story_id', storyId);
      
      if (termMapError) {
        console.warn('刪除術語映射時出現警告:', termMapError);
      }

      // 3. 刪除其他可能的外鍵記錄
      const { error: relativeNewsError } = await supabase
        .from('relative_news')
        .delete()
        .or(`story_id.eq.${storyId},relative_story_id.eq.${storyId}`);
      
      if (relativeNewsError) {
        console.warn('刪除相關新聞時出現警告:', relativeNewsError);
      }

      const { error: relativeTopicsError } = await supabase
        .from('relative_topics')
        .delete()
        .eq('story_id', storyId);
      
      if (relativeTopicsError) {
        console.warn('刪除相關專題時出現警告:', relativeTopicsError);
      }

      // 4. 最後刪除主記錄
      const { error } = await supabase
        .from('single_news')
        .delete()
        .eq('story_id', storyId);

      if (error) throw error;
      alert('✅ 刪除成功');
      loadSingleNews();
    } catch (error) {
      console.error('刪除失敗:', error);
      alert('❌ 刪除失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 批量刪除
  const handleBatchDelete = async () => {
    if (selectedRows.length === 0) {
      alert('請先選擇要刪除的項目');
      return;
    }

    const confirmDelete = window.confirm(`確定要刪除選中的 ${selectedRows.length} 篇新聞嗎？`);
    if (!confirmDelete) return;

    try {
      setLoading(true);
      
      // 對每個選中的記錄進行逐一刪除，確保正確處理外鍵約束
      for (const storyId of selectedRows) {
        // 1. 刪除 keywords_map 中的記錄
        const { error: keywordsError } = await supabase
          .from('keywords_map')
          .delete()
          .eq('story_id', storyId);
        
        if (keywordsError) {
          console.warn(`刪除 story_id ${storyId} 的關鍵詞映射時出現警告:`, keywordsError);
        }

        // 2. 刪除 term_map 中的記錄
        const { error: termMapError } = await supabase
          .from('term_map')
          .delete()
          .eq('story_id', storyId);
        
        if (termMapError) {
          console.warn(`刪除 story_id ${storyId} 的術語映射時出現警告:`, termMapError);
        }

        // 3. 刪除相關新聞記錄
        const { error: relativeNewsError } = await supabase
          .from('relative_news')
          .delete()
          .or(`story_id.eq.${storyId},relative_story_id.eq.${storyId}`);
        
        if (relativeNewsError) {
          console.warn(`刪除 story_id ${storyId} 的相關新聞時出現警告:`, relativeNewsError);
        }

        // 4. 刪除相關專題記錄
        const { error: relativeTopicsError } = await supabase
          .from('relative_topics')
          .delete()
          .eq('story_id', storyId);
        
        if (relativeTopicsError) {
          console.warn(`刪除 story_id ${storyId} 的相關專題時出現警告:`, relativeTopicsError);
        }
      }

      // 5. 最後批量刪除主記錄
      const { error } = await supabase
        .from('single_news')
        .delete()
        .in('story_id', selectedRows);

      if (error) throw error;
      alert(`✅ 成功刪除 ${selectedRows.length} 篇新聞`);
      setSelectedRows([]);
      loadSingleNews();
    } catch (error) {
      console.error('批量刪除失敗:', error);
      alert('❌ 批量刪除失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 批量修正分類
  const handleBatchFixCategory = async (newCategory) => {
    if (selectedRows.length === 0) {
      alert('請先選擇要修正的項目');
      return;
    }

    try {
      setLoading(true);
      const { error } = await supabase
        .from('single_news')
        .update({ category: newCategory })
        .in('story_id', selectedRows);

      if (error) throw error;
      alert(`✅ 成功修正 ${selectedRows.length} 篇新聞的分類`);
      setSelectedRows([]);
      setBatchEditModal(false);
      loadSingleNews();
    } catch (error) {
      console.error('批量修正失敗:', error);
      alert('❌ 批量修正失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 儲存或更新新聞
  const handleSave = async (formData) => {
    try {
      setLoading(true);
      
      if (modalMode === 'edit') {
        // 過濾掉不屬於 single_news 表的欄位
        const allowedFields = ['news_title', 'category', 'total_articles', 'ultra_short', 'short', 'long', 'generated_date'];
        const updateData = {};
        
        allowedFields.forEach(field => {
          if (formData.hasOwnProperty(field)) {
            updateData[field] = formData[field];
          }
        });
        
        const { error } = await supabase
          .from('single_news')
          .update(updateData)
          .eq('story_id', selectedNews.story_id);
        
        if (error) throw error;
        alert('✅ 更新成功');
      }
      
      setIsModalOpen(false);
      setSelectedNews(null);
      loadSingleNews();
    } catch (error) {
      console.error('儲存失敗:', error);
      alert('❌ 儲存失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { 
      key: 'news_title', 
      label: '新聞標題', 
      sortable: true,
      render: (value) => value || <span className="missing-data">無標題</span>
    },
    { 
      key: 'category', 
      label: '分類', 
      sortable: true,
      render: (value) => value || <span className="missing-data">未分類</span>
    },
    { 
      key: 'total_articles', 
      label: '文章數量', 
      render: (value) => value ? `${value} 篇` : <span className="missing-data">0 篇</span>
    },
    { 
      key: 'stories', 
      label: '來源故事', 
      render: (value) => value ? (
        <div>
          <div className="story-title">{value.story_title}</div>
          <small className="story-date">{value.crawl_date}</small>
        </div>
      ) : <span className="missing-data">無關聯故事</span>
    },
    { 
      key: 'ultra_short', 
      label: '超短摘要', 
      render: (value) => {
        if (!value) return <span className="missing-data">無內容</span>;
        return (
          <div className="content-preview" title={value}>
            {value.substring(0, 80)}...
          </div>
        );
      }
    },
    { 
      key: 'generated_date', 
      label: '生成日期', 
      render: (value) => {
        if (!value) return <span className="missing-data">無日期</span>;
        try {
          // 處理 "2025-08-26 08:51" 格式的字串
          let dateStr = value.toString();
          
          // 如果包含時間部分，保留日期部分
          if (dateStr.includes(' ')) {
            dateStr = dateStr.split(' ')[0];
          }
          
          const date = new Date(dateStr);
          if (isNaN(date.getTime())) {
            // 如果直接解析失敗，嘗試手動解析
            const parts = dateStr.split('-');
            if (parts.length === 3) {
              const [year, month, day] = parts;
              const parsedDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
              if (!isNaN(parsedDate.getTime())) {
                return parsedDate.toLocaleDateString('zh-TW', {
                  year: 'numeric',
                  month: '2-digit',
                  day: '2-digit'
                });
              }
            }
            return <span className="missing-data">無效日期</span>;
          }
          
          return date.toLocaleDateString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
          });
        } catch (error) {
          console.error('日期解析錯誤:', error, '原始值:', value);
          return <span className="missing-data">日期錯誤</span>;
        }
      }
    },
    {
      key: 'actions',
      label: '操作',
      render: (_, item) => (
        <div className="action-buttons">
          <button 
            onClick={() => {
              setSelectedNews(item);
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
              setSelectedNews(item);
              setModalMode('edit');
              setIsModalOpen(true);
            }}
            className="btn-edit"
            title="編輯"
          >
            ✏️
          </button>
          <button 
            onClick={() => handleDelete(item.story_id)}
            className="btn-delete"
            title="刪除"
          >
            🗑️
          </button>
        </div>
      )
    }
  ];

  const formFields = [
    { key: 'news_title', label: '新聞標題', type: 'text', required: true },
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
    { key: 'total_articles', label: '文章數量', type: 'number', min: 1 },
    { 
      key: 'ultra_short', 
      label: '超短摘要', 
      type: 'textarea', 
      rows: 3,
      help: '簡短的新聞摘要（1-2 句話）'
    },
    { 
      key: 'short', 
      label: '短摘要', 
      type: 'textarea', 
      rows: 4,
      help: '中等長度的新聞摘要'
    },
    { 
      key: 'long', 
      label: '長摘要', 
      type: 'textarea', 
      rows: 6,
      help: '詳細的新聞摘要'
    },
    { key: 'generated_date', label: '生成日期', type: 'date' }
  ];

  return (
    <div className="single-news-management">
      <div className="management-header">
        <h2>📰 Single News 內容管理</h2>
        <p className="management-description">
          管理整合後的新聞內容，檢查摘要品質、分類正確性，支援批量修正
        </p>
      </div>

      <div className="management-controls">
        <div className="search-filters">
          <input
            type="text"
            placeholder="搜尋標題或摘要..."
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
        
        <div className="batch-actions">
          {selectedRows.length > 0 && (
            <>
              <span className="selected-count">
                已選擇 {selectedRows.length} 項
              </span>
              <button
                onClick={() => setBatchEditModal(true)}
                className="btn-batch-edit"
              >
                🔧 批量修正
              </button>
              <button
                onClick={handleBatchDelete}
                className="btn-batch-delete"
              >
                🗑️ 批量刪除
              </button>
            </>
          )}
        </div>
      </div>

      <AdminTable
        data={singleNews}
        columns={columns}
        loading={loading}
        currentPage={currentPage}
        totalCount={totalCount}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
        selectable={true}
        selectedRows={selectedRows}
        onRowSelect={setSelectedRows}
      />

      <AdminModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedNews(null);
        }}
        title={modalMode === 'edit' ? '編輯新聞內容' : '檢視新聞內容'}
        mode={modalMode}
        data={selectedNews}
        fields={formFields}
        onSave={handleSave}
      />

      {/* 批量編輯模態框 */}
      {batchEditModal && (
        <div className="modal-overlay" onClick={() => setBatchEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>批量修正分類</h3>
              <button onClick={() => setBatchEditModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <p>將為選中的 {selectedRows.length} 篇新聞修正分類</p>
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    handleBatchFixCategory(e.target.value);
                  }
                }}
                className="form-select"
                defaultValue=""
              >
                <option value="">請選擇新分類...</option>
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
            <div className="modal-footer">
              <button onClick={() => setBatchEditModal(false)} className="btn-cancel">
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SingleNewsManagement;
