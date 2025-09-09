import React, { useState, useEffect } from 'react';

const AdminModal = ({ isOpen, onClose, title, mode, data, fields, onSave }) => {
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});

  // 當 modal 開啟或 data 改變時，初始化表單資料
  useEffect(() => {
    if (isOpen) {
      if (data && mode !== 'create') {
        setFormData({ ...data });
      } else {
        // 創建模式時初始化空值
        const initialData = {};
        fields.forEach(field => {
          initialData[field.key] = field.defaultValue || '';
        });
        setFormData(initialData);
      }
      setErrors({});
    }
  }, [isOpen, data, mode, fields]);

  const validateForm = () => {
    const newErrors = {};
    
    fields.forEach(field => {
      if (field.required && !formData[field.key]) {
        newErrors[field.key] = `${field.label}為必填欄位`;
      }
      
      if (field.type === 'email' && formData[field.key]) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData[field.key])) {
          newErrors[field.key] = '請輸入有效的 Email 格式';
        }
      }
      
      if (field.type === 'url' && formData[field.key]) {
        try {
          new URL(formData[field.key]);
        } catch {
          newErrors[field.key] = '請輸入有效的 URL 格式';
        }
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    onSave(formData);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field.key]: value
    }));
    
    // 清除該欄位的錯誤訊息
    if (errors[field.key]) {
      setErrors(prev => ({
        ...prev,
        [field.key]: ''
      }));
    }
  };

  const renderField = (field) => {
    const value = formData[field.key] || '';
    const hasError = !!errors[field.key];
    const isReadOnly = mode === 'view';

    switch (field.type) {
      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={(e) => handleInputChange(field, e.target.value)}
            readOnly={isReadOnly}
            className={`form-textarea ${hasError ? 'error' : ''}`}
            rows={field.rows || 4}
            placeholder={field.placeholder}
          />
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleInputChange(field, e.target.value)}
            disabled={isReadOnly}
            className={`form-select ${hasError ? 'error' : ''}`}
          >
            <option value="">請選擇...</option>
            {field.options?.map(option => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      case 'checkbox':
        return (
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={!!value}
              onChange={(e) => handleInputChange(field, e.target.checked)}
              disabled={isReadOnly}
              className="form-checkbox"
            />
            <span className="checkbox-text">{field.checkboxLabel || field.label}</span>
          </label>
        );

      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleInputChange(field, e.target.value)}
            readOnly={isReadOnly}
            className={`form-input ${hasError ? 'error' : ''}`}
            placeholder={field.placeholder}
            min={field.min}
            max={field.max}
            step={field.step}
          />
        );

      case 'date':
        // 處理日期格式轉換：從 "2025-09-05 12:32" 轉換為 "2025-09-05"
        const formatDateForInput = (dateValue) => {
          if (!dateValue) return '';
          try {
            let dateStr = dateValue.toString();
            // 如果包含時間部分，只取日期部分
            if (dateStr.includes(' ')) {
              dateStr = dateStr.split(' ')[0];
            }
            // 確保格式正確 (YYYY-MM-DD)
            const date = new Date(dateStr);
            if (!isNaN(date.getTime())) {
              return date.toISOString().split('T')[0];
            }
            return dateStr;
          } catch (error) {
            console.error('日期格式轉換錯誤:', error);
            return '';
          }
        };

        return (
          <input
            type="date"
            value={formatDateForInput(value)}
            onChange={(e) => handleInputChange(field, e.target.value)}
            readOnly={isReadOnly}
            className={`form-input ${hasError ? 'error' : ''}`}
          />
        );

      case 'datetime-local':
        return (
          <input
            type="datetime-local"
            value={value}
            onChange={(e) => handleInputChange(field, e.target.value)}
            readOnly={isReadOnly}
            className={`form-input ${hasError ? 'error' : ''}`}
          />
        );

      default:
        return (
          <input
            type={field.type || 'text'}
            value={value}
            onChange={(e) => handleInputChange(field, e.target.value)}
            readOnly={isReadOnly}
            className={`form-input ${hasError ? 'error' : ''}`}
            placeholder={field.placeholder}
          />
        );
    }
  };

  if (!isOpen) return null;

  // 判斷是否需要使用大型模態框
  const needsLargeModal = mode === 'view' || mode === 'edit' || 
                         fields.some(field => field.type === 'textarea');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div 
        className={`modal-content ${needsLargeModal ? 'large-modal' : ''}`} 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h3 className="modal-title">{title}</h3>
          <button className="modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="modal-body">
            {fields.map(field => (
              <div key={field.key} className="form-group">
                <label className="form-label">
                  {field.label}
                  {field.required && mode !== 'view' && <span className="required">*</span>}
                </label>
                
                {renderField(field)}
                
                {errors[field.key] && (
                  <span className="error-message">{errors[field.key]}</span>
                )}
                
                {field.help && (
                  <small className="help-text">{field.help}</small>
                )}
              </div>
            ))}
          </div>

          <div className="modal-footer">
            {mode !== 'view' && (
              <>
                <button type="button" onClick={onClose} className="btn-cancel">
                  取消
                </button>
                <button type="submit" className="btn-save">
                  {mode === 'create' ? '新增' : '儲存'}
                </button>
              </>
            )}
            {mode === 'view' && (
              <button type="button" onClick={onClose} className="btn-save">
                關閉
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default AdminModal;
