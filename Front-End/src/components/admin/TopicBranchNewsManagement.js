import React, { useState, useEffect, useCallback } from 'react';
import { useSupabase } from '../supabase';
import AdminTable from './AdminTable';

const TopicBranchNewsManagement = () => {
  const [newsData, setNewsData] = useState([]);
  const [topics, setTopics] = useState([]);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState('');
  const [selectedBranch, setSelectedBranch] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferringNews, setTransferringNews] = useState(null);
  const [targetBranch, setTargetBranch] = useState('');
  const [showAddBranchModal, setShowAddBranchModal] = useState(false);
  const [newBranchTitle, setNewBranchTitle] = useState('');
  const [newBranchContent, setNewBranchContent] = useState('');
  const [showEditBranchModal, setShowEditBranchModal] = useState(false);
  const [editingBranch, setEditingBranch] = useState(null);
  const [editBranchTitle, setEditBranchTitle] = useState('');
  const [editBranchContent, setEditBranchContent] = useState('');
  const pageSize = 20;

  const supabase = useSupabase();

  // 載入專題列表
  const loadTopics = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('topic')
        .select('topic_id, topic_title')
        .order('topic_title');

      if (error) throw error;
      setTopics(data || []);
    } catch (error) {
      console.error('載入專題失敗:', error);
    }
  }, [supabase]);

  // 載入專題分支
  const loadBranches = useCallback(async (topicId) => {
    if (!topicId) {
      setBranches([]);
      return;
    }

    try {
      const { data, error } = await supabase
        .from('topic_branch')
        .select('topic_branch_id, topic_branch_title')
        .eq('topic_id', topicId)
        .order('topic_branch_title');

      if (error) throw error;
      setBranches(data || []);
    } catch (error) {
      console.error('載入專題分支失敗:', error);
    }
  }, [supabase]);

  // 載入新聞資料
  const loadNewsData = useCallback(async () => {
    try {
      setLoading(true);
      
      if (!selectedTopic) {
        setNewsData([]);
        setTotalCount(0);
        return;
      }

      let query;
      
      if (selectedBranch) {
        // 選擇了分支：顯示該分支下的所有新聞
        query = supabase
          .from('topic_branch_news_map')
          .select(`
            story_id,
            topic_branch_id,
            single_news:story_id(
              story_id,
              news_title,
              category,
              ultra_short
            ),
            topic_branch:topic_branch_id(
              topic_branch_title
            )
          `, { count: 'exact' })
          .eq('topic_branch_id', selectedBranch);
      } else {
        // 只選擇了專題：顯示該專題下的所有新聞
        query = supabase
          .from('topic_news_map')
          .select(`
            story_id,
            single_news:story_id(
              story_id,
              news_title,
              category,
              ultra_short
            )
          `, { count: 'exact' })
          .eq('topic_id', selectedTopic);
      }

      // 搜尋過濾
      if (searchTerm) {
        query = query.ilike('single_news.news_title', `%${searchTerm}%`);
      }

      // 分頁
      const from = (currentPage - 1) * pageSize;
      const to = from + pageSize - 1;
      query = query.range(from, to);

      const { data, error, count } = await query;

      if (error) throw error;

      // 處理資料格式
      let processedData = [];
      
      if (selectedBranch) {
        // 分支模式：直接從 topic_branch_news_map 來的資料
        processedData = data?.map(item => ({
          story_id: item.story_id,
          news_title: item.single_news?.news_title,
          category: item.single_news?.category,
          ultra_short: item.single_news?.ultra_short,
          current_branch_id: item.topic_branch_id,
          current_branch_title: item.topic_branch?.topic_branch_title
        })) || [];
      } else {
        // 專題模式：需要額外查詢分支資訊
        const storyIds = data?.map(item => item.story_id) || [];
        
        if (storyIds.length > 0) {
          // 查詢這些新聞的分支映射
          const { data: branchMappings } = await supabase
            .from('topic_branch_news_map')
            .select(`
              story_id,
              topic_branch_id,
              topic_branch:topic_branch_id(
                topic_branch_title
              )
            `)
            .in('story_id', storyIds);
          
          // 建立 story_id 到分支資訊的映射
          const branchMap = {};
          branchMappings?.forEach(mapping => {
            branchMap[mapping.story_id] = {
              branch_id: mapping.topic_branch_id,
              branch_title: mapping.topic_branch?.topic_branch_title
            };
          });
          
          processedData = data?.map(item => ({
            story_id: item.story_id,
            news_title: item.single_news?.news_title,
            category: item.single_news?.category,
            ultra_short: item.single_news?.ultra_short,
            current_branch_id: branchMap[item.story_id]?.branch_id || null,
            current_branch_title: branchMap[item.story_id]?.branch_title || '無分支'
          })) || [];
        }
      }

      setNewsData(processedData);
      setTotalCount(count || 0);
    } catch (error) {
      console.error('載入新聞資料失敗:', error);
      alert('載入資料失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  }, [currentPage, selectedTopic, selectedBranch, searchTerm, supabase]);

  // 轉移新聞到其他分支
  const handleTransferNews = async () => {
    if (!transferringNews || !targetBranch) {
      alert('請選擇目標分支');
      return;
    }

    try {
      setLoading(true);

      // 如果新聞目前有分支分配，先刪除舊的映射
      if (transferringNews.current_branch_id) {
        const { error: deleteError } = await supabase
          .from('topic_branch_news_map')
          .delete()
          .eq('topic_branch_id', transferringNews.current_branch_id)
          .eq('story_id', transferringNews.story_id);

        if (deleteError) throw deleteError;
      }

      // 添加新的映射
      // 檢查是否已存在相同的映射
      const { data: existing } = await supabase
        .from('topic_branch_news_map')
        .select('*')
        .eq('topic_branch_id', targetBranch)
        .eq('story_id', transferringNews.story_id);

      if (existing && existing.length > 0) {
        alert('⚠️ 該新聞已在目標分支中');
        return;
      }

      const { error: insertError } = await supabase
        .from('topic_branch_news_map')
        .insert([{
          topic_branch_id: targetBranch,
          story_id: transferringNews.story_id
        }]);

      if (insertError) throw insertError;

      alert('✅ 轉移成功');
      setShowTransferModal(false);
      setTransferringNews(null);
      setTargetBranch('');
      loadNewsData();
    } catch (error) {
      console.error('轉移失敗:', error);
      alert('❌ 轉移失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 新增分支
  const handleAddBranch = async () => {
    if (!selectedTopic) {
      alert('請先選擇專題');
      return;
    }

    if (!newBranchTitle.trim()) {
      alert('請輸入分支標題');
      return;
    }

    try {
      setLoading(true);

      const { error } = await supabase
        .from('topic_branch')
        .insert([{
          topic_id: selectedTopic,
          topic_branch_title: newBranchTitle.trim(),
          topic_branch_content: newBranchContent.trim() || null
        }]);

      if (error) throw error;

      alert('✅ 分支新增成功');
      setShowAddBranchModal(false);
      setNewBranchTitle('');
      setNewBranchContent('');
      loadBranches(selectedTopic); // 重新載入分支列表
    } catch (error) {
      console.error('新增分支失敗:', error);
      alert('❌ 新增分支失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 刪除分支
  const handleDeleteBranch = async (branchId, branchTitle) => {
    if (!branchId) return;

    try {
      // 先檢查該分支下是否還有新聞
      const { data: newsInBranch, error: checkError } = await supabase
        .from('topic_branch_news_map')
        .select('story_id')
        .eq('topic_branch_id', branchId);

      if (checkError) throw checkError;

      if (newsInBranch && newsInBranch.length > 0) {
        alert(`❌ 無法刪除分支「${branchTitle}」\n該分支下還有 ${newsInBranch.length} 篇新聞，請先移除或轉移這些新聞。`);
        return;
      }

      // 確認刪除
      const confirmDelete = window.confirm(`確定要刪除分支「${branchTitle}」嗎？\n此操作無法復原。`);
      if (!confirmDelete) return;

      setLoading(true);

      // 執行刪除
      const { error } = await supabase
        .from('topic_branch')
        .delete()
        .eq('topic_branch_id', branchId);

      if (error) throw error;

      alert('✅ 分支刪除成功');
      
      // 如果刪除的是當前選中的分支，清空選擇
      if (selectedBranch === branchId) {
        setSelectedBranch('');
      }
      
      // 重新載入分支列表和新聞資料
      loadBranches(selectedTopic);
      loadNewsData();
    } catch (error) {
      console.error('刪除分支失敗:', error);
      alert('❌ 刪除分支失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 開始編輯分支
  const handleEditBranch = async (branchId) => {
    try {
      // 獲取分支詳細資料
      const { data, error } = await supabase
        .from('topic_branch')
        .select('*')
        .eq('topic_branch_id', branchId)
        .single();

      if (error) throw error;

      if (data) {
        setEditingBranch(data);
        setEditBranchTitle(data.topic_branch_title || '');
        setEditBranchContent(data.topic_branch_content || '');
        setShowEditBranchModal(true);
      }
    } catch (error) {
      console.error('載入分支資料失敗:', error);
      alert('❌ 載入分支資料失敗: ' + error.message);
    }
  };

  // 儲存編輯的分支
  const handleSaveEditBranch = async () => {
    if (!editBranchTitle.trim()) {
      alert('請輸入分支標題');
      return;
    }

    try {
      setLoading(true);

      const { error } = await supabase
        .from('topic_branch')
        .update({
          topic_branch_title: editBranchTitle.trim(),
          topic_branch_content: editBranchContent.trim() || null
        })
        .eq('topic_branch_id', editingBranch.topic_branch_id);

      if (error) throw error;

      alert('✅ 分支更新成功');
      setShowEditBranchModal(false);
      setEditingBranch(null);
      setEditBranchTitle('');
      setEditBranchContent('');
      loadBranches(selectedTopic); // 重新載入分支列表
    } catch (error) {
      console.error('更新分支失敗:', error);
      alert('❌ 更新分支失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTopics();
  }, [loadTopics]);

  useEffect(() => {
    if (selectedTopic) {
      loadBranches(selectedTopic);
    }
  }, [selectedTopic, loadBranches]);

  useEffect(() => {
    // 當選擇專題改變時，清空分支選擇並重置頁面
    setSelectedBranch('');
    setCurrentPage(1);
  }, [selectedTopic]);

  useEffect(() => {
    // 當分支選擇改變時，重置頁面
    setCurrentPage(1);
  }, [selectedBranch]);

  useEffect(() => {
    loadNewsData();
  }, [loadNewsData]);

  // 表格欄位定義
  const columns = [
    {
      key: 'news_title',
      label: '新聞標題',
      render: (title, item) => (
        <div>
          <div className="news-title" title={title}>
            {title || '無標題'}
          </div>
          <small className="news-category">
            分類: {item.category || '未分類'}
          </small>
          {item.ultra_short && (
            <div className="news-summary">
              {item.ultra_short.substring(0, 100)}...
            </div>
          )}
        </div>
      )
    },
    {
      key: 'current_branch_title',
      label: '當前分支',
      render: (branchTitle) => (
        <div className="branch-tag">
          📂 {branchTitle}
        </div>
      )
    },
    {
      key: 'story_id',
      label: '新聞ID',
      render: (storyId) => (
        <span className="story-id">#{storyId}</span>
      )
    },
    {
      key: 'actions',
      label: '操作',
      render: (_, item) => (
        <div className="action-buttons">
          <button 
            onClick={() => {
              setTransferringNews(item);
              setTargetBranch('');
              setShowTransferModal(true);
            }}
            className="btn-transfer"
            title="轉移分支"
          >
            🔄 轉移分支
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="topic-branch-news-management">
      <div className="management-header">
        <h2>🌿 專題分支新聞管理</h2>
        <p className="management-description">
          {selectedTopic && !selectedBranch && '顯示專題下的所有新聞，可以調整新聞的分支歸屬'}
          {selectedTopic && selectedBranch && '顯示特定分支下的所有新聞，可以轉移到其他分支'}
          {!selectedTopic && '請選擇專題以查看新聞'}
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

          <select
            value={selectedBranch}
            onChange={(e) => setSelectedBranch(e.target.value)}
            className="filter-select"
            disabled={!selectedTopic}
          >
            <option value="">顯示所有分支</option>
            {branches.map(branch => (
              <option key={branch.topic_branch_id} value={branch.topic_branch_id}>
                {branch.topic_branch_title}
              </option>
            ))}
          </select>

          <input
            type="text"
            placeholder="搜尋新聞標題..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />

          <button
            onClick={() => setShowAddBranchModal(true)}
            className="btn-add-branch"
            disabled={!selectedTopic}
            title="新增分支"
          >
            ➕ 新增分支
          </button>

          <button
            onClick={() => {
              if (selectedBranch) {
                handleEditBranch(selectedBranch);
              }
            }}
            className="btn-edit-branch"
            disabled={!selectedBranch}
            title="編輯選中的分支"
          >
            ✏️ 編輯分支
          </button>

          <button
            onClick={() => {
              const selectedBranchData = branches.find(b => b.topic_branch_id === selectedBranch);
              if (selectedBranchData) {
                handleDeleteBranch(selectedBranch, selectedBranchData.topic_branch_title);
              }
            }}
            className="btn-delete-branch"
            disabled={!selectedBranch}
            title="刪除選中的分支"
          >
            🗑️ 刪除分支
          </button>
        </div>
      </div>

      <AdminTable
        data={newsData}
        columns={columns}
        loading={loading}
        currentPage={currentPage}
        totalCount={totalCount}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
      />

      {/* 轉移分支的模態框 */}
      {showTransferModal && transferringNews && (
        <div className="modal-overlay" onClick={() => setShowTransferModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>轉移新聞分支</h3>
              <button onClick={() => setShowTransferModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="news-info">
                <h4>新聞資訊</h4>
                <p><strong>標題:</strong> {transferringNews.news_title}</p>
                <p><strong>當前分支:</strong> {transferringNews.current_branch_title}</p>
              </div>
              <div className="form-group">
                <label>選擇目標分支:</label>
                <select
                  value={targetBranch}
                  onChange={(e) => setTargetBranch(e.target.value)}
                  className="form-select"
                >
                  <option value="">請選擇分支...</option>
                  {branches
                    .filter(branch => branch.topic_branch_id !== transferringNews.current_branch_id)
                    .map(branch => (
                      <option key={branch.topic_branch_id} value={branch.topic_branch_id}>
                        {branch.topic_branch_title}
                      </option>
                    ))}
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowTransferModal(false)} className="btn-cancel">
                取消
              </button>
              <button 
                onClick={handleTransferNews} 
                className="btn-save"
                disabled={!targetBranch}
              >
                轉移
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 新增分支的模態框 */}
      {showAddBranchModal && (
        <div className="modal-overlay" onClick={() => setShowAddBranchModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>新增專題分支</h3>
              <button onClick={() => setShowAddBranchModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>分支標題: <span className="required">*</span></label>
                <input
                  type="text"
                  value={newBranchTitle}
                  onChange={(e) => setNewBranchTitle(e.target.value)}
                  placeholder="輸入分支標題..."
                  className="form-input"
                  maxLength={100}
                />
              </div>
              <div className="form-group">
                <label>分支描述: <span className="optional">(選填)</span></label>
                <textarea
                  value={newBranchContent}
                  onChange={(e) => setNewBranchContent(e.target.value)}
                  placeholder="輸入分支描述或說明..."
                  className="form-textarea"
                  rows={4}
                  maxLength={500}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowAddBranchModal(false)} className="btn-cancel">
                取消
              </button>
              <button 
                onClick={handleAddBranch} 
                className="btn-save"
                disabled={!newBranchTitle.trim()}
              >
                新增分支
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 編輯分支的模態框 */}
      {showEditBranchModal && editingBranch && (
        <div className="modal-overlay" onClick={() => setShowEditBranchModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>編輯專題分支</h3>
              <button onClick={() => setShowEditBranchModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>分支標題: <span className="required">*</span></label>
                <input
                  type="text"
                  value={editBranchTitle}
                  onChange={(e) => setEditBranchTitle(e.target.value)}
                  placeholder="輸入分支標題..."
                  className="form-input"
                  maxLength={100}
                />
              </div>
              <div className="form-group">
                <label>分支描述: <span className="optional">(選填)</span></label>
                <textarea
                  value={editBranchContent}
                  onChange={(e) => setEditBranchContent(e.target.value)}
                  placeholder="輸入分支描述或說明..."
                  className="form-textarea"
                  rows={4}
                  maxLength={500}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button 
                onClick={() => {
                  setShowEditBranchModal(false);
                  setEditingBranch(null);
                  setEditBranchTitle('');
                  setEditBranchContent('');
                }} 
                className="btn-cancel"
              >
                取消
              </button>
              <button 
                onClick={handleSaveEditBranch} 
                className="btn-save"
                disabled={!editBranchTitle.trim()}
              >
                儲存變更
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TopicBranchNewsManagement;