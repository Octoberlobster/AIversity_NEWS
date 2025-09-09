import React from 'react';

const AdminTable = ({ 
  data, 
  columns, 
  loading, 
  currentPage, 
  totalCount, 
  pageSize, 
  onPageChange,
  selectedRows = [],
  onRowSelect = null,
  selectable = false 
}) => {
  const totalPages = Math.ceil(totalCount / pageSize);
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalCount);

  if (loading) {
    return (
      <div className="table-loading">
        <div className="loading-spinner"></div>
        <p>載入中...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="table-empty">
        <p>📭 沒有找到資料</p>
      </div>
    );
  }

  const renderCellContent = (column, item) => {
    const value = item[column.key];
    
    if (column.render) {
      return column.render(value, item);
    }
    
    if (typeof value === 'boolean') {
      return value ? '✅' : '❌';
    }
    
    if (value === null || value === undefined) {
      return <span className="null-value">—</span>;
    }
    
    if (typeof value === 'string' && value.length > 100) {
      return (
        <span title={value}>
          {value.substring(0, 100)}...
        </span>
      );
    }
    
    return value;
  };

  return (
    <div className="admin-table-container">
      <div className="table-info">
        <span className="table-count">
          顯示第 {startItem} - {endItem} 項，共 {totalCount} 項
        </span>
      </div>
      
      <div className="table-wrapper">
        <table className="admin-table">
          <thead>
            <tr>
              {selectable && (
                <th className="select-column">
                  <input
                    type="checkbox"
                    onChange={(e) => {
                      if (e.target.checked) {
                        onRowSelect?.(data.map(item => item.id || item.story_id || item.article_id));
                      } else {
                        onRowSelect?.([]);
                      }
                    }}
                    checked={selectedRows.length === data.length && data.length > 0}
                  />
                </th>
              )}
              {columns.map(column => (
                <th key={column.key} className={column.sortable ? 'sortable' : ''}>
                  {column.label}
                  {column.sortable && <span className="sort-icon">↕️</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => {
              const itemId = item.id || item.story_id || item.article_id || index;
              const isSelected = selectedRows.includes(itemId);
              
              return (
                <tr key={itemId} className={isSelected ? 'selected' : ''}>
                  {selectable && (
                    <td className="select-column">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => {
                          if (e.target.checked) {
                            onRowSelect?.([...selectedRows, itemId]);
                          } else {
                            onRowSelect?.(selectedRows.filter(id => id !== itemId));
                          }
                        }}
                      />
                    </td>
                  )}
                  {columns.map(column => (
                    <td key={column.key} className={`column-${column.key}`}>
                      {renderCellContent(column, item)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="table-pagination">
          <button
            onClick={() => onPageChange(1)}
            disabled={currentPage === 1}
            className="pagination-btn"
          >
            ⏮️
          </button>
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="pagination-btn"
          >
            ⬅️
          </button>
          
          <div className="pagination-info">
            <span>第 {currentPage} 頁，共 {totalPages} 頁</span>
          </div>
          
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="pagination-btn"
          >
            ➡️
          </button>
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={currentPage === totalPages}
            className="pagination-btn"
          >
            ⏭️
          </button>
        </div>
      )}
    </div>
  );
};

export default AdminTable;
