import React from 'react';
import './css/Header.css';
import translateIcon from './Translate.png';
import { FaSearch } from 'react-icons/fa';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';

function Header({ language, setLanguage }) {
  // 新增日期狀態
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [keyword, setKeyword] = useState('');
  
  // 搜尋建議相關狀態
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  
  const navigate = useNavigate();
  const location = useLocation();
  const searchInputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // 模擬搜尋建議數據（實際應用中應該從 API 獲取）
  const mockSuggestions = [
    '台灣選舉', '疫情最新消息', '經濟政策', '氣候變遷', '人工智能',
    '房價趨勢', '教育改革', '健康飲食', '運動賽事', '娛樂新聞',
    '科技創新', '交通建設', '環保政策', '國際關係', '文化活動'
  ];

  // 從 URL 參數中讀取日期設定
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const urlStartDate = searchParams.get('startDate');
    const urlEndDate = searchParams.get('endDate');
    
    if (urlStartDate) setStartDate(urlStartDate);
    if (urlEndDate) setEndDate(urlEndDate);
  }, [location.search]);

  // 處理搜尋建議
  useEffect(() => {
    if (keyword.trim() && keyword.length > 0) {
      const filteredSuggestions = mockSuggestions.filter(suggestion =>
        suggestion.toLowerCase().includes(keyword.toLowerCase())
      );
      setSearchSuggestions(filteredSuggestions.slice(0, 8)); // 限制顯示 8 個建議
      setShowSuggestions(filteredSuggestions.length > 0);
    } else {
      setSearchSuggestions([]);
      setShowSuggestions(false);
    }
    setSelectedSuggestionIndex(-1);
  }, [keyword]);

  // 處理點擊外部關閉建議
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        searchInputRef.current &&
        !searchInputRef.current.contains(event.target) &&
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // 當日期改變時，更新當前頁面的 URL
  const handleDateChange = (newStartDate, newEndDate) => {
    const searchParams = new URLSearchParams(location.search);
    
    // 更新或刪除日期參數
    if (newStartDate) {
      searchParams.set('startDate', newStartDate);
    } else {
      searchParams.delete('startDate');
    }
    
    if (newEndDate) {
      searchParams.set('endDate', newEndDate);
    } else {
      searchParams.delete('endDate');
    }
    
    // 構建新的 URL
    const newSearch = searchParams.toString();
    const newPath = `${location.pathname}${newSearch ? `?${newSearch}` : ''}`;
    
    // 更新 URL（不會觸發頁面重新載入）
    navigate(newPath, { replace: true });
  };

  const handleStartDateChange = (e) => {
    const newStartDate = e.target.value;
    setStartDate(newStartDate);
    handleDateChange(newStartDate, endDate);
  };

  const handleEndDateChange = (e) => {
    const newEndDate = e.target.value;
    setEndDate(newEndDate);
    handleDateChange(startDate, newEndDate);
  };

  const handleSearch = (searchKeyword) => {
    if (!searchKeyword.trim()) return;

    // 組合搜尋路由，將日期篩選條件用 query string 傳遞
    const params = new URLSearchParams();
    if (startDate) params.append('startDate', startDate);
    if (endDate) params.append('endDate', endDate);

    const queryString = params.toString();
    const path = `/search/${encodeURIComponent(searchKeyword.trim())}${queryString ? `?${queryString}` : ''}`;

    navigate(path);
    setShowSuggestions(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSearch(keyword);
  };

  const handleInputChange = (e) => {
    setKeyword(e.target.value);
  };

  const handleInputFocus = () => {
    if (keyword.trim() && searchSuggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setKeyword(suggestion);
    handleSearch(suggestion);
  };

  const handleKeyDown = (e) => {
    if (!showSuggestions) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => 
          prev < searchSuggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => 
          prev > 0 ? prev - 1 : searchSuggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0) {
          handleSuggestionClick(searchSuggestions[selectedSuggestionIndex]);
        } else {
          handleSubmit(e);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  };

  return (
    <>
      <div className="header-bar">
        <div className="platform-name">
          <span></span>
        </div>
        <div className="search-bar-container">
          <form className="search-form" onSubmit={handleSubmit}>
            <div className="search-input-wrapper">
              <input
                ref={searchInputRef}
                type="text"
                className="search-input"
                placeholder="搜尋主題、地點和來源"
                value={keyword}
                onChange={handleInputChange}
                onFocus={handleInputFocus}
                onKeyDown={handleKeyDown}
                autoComplete="off"
              />
              <button type="submit" className="search-button">
                <FaSearch />
              </button>
              
              {/* 搜尋建議列表 */}
              {showSuggestions && (
                <div ref={suggestionsRef} className="search-suggestions">
                  {searchSuggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      className={`suggestion-item ${
                        index === selectedSuggestionIndex ? 'selected' : ''
                      }`}
                      onClick={() => handleSuggestionClick(suggestion)}
                      onMouseEnter={() => setSelectedSuggestionIndex(index)}
                    >
                      <FaSearch className="suggestion-icon" />
                      <span className="suggestion-text">{suggestion}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </form>
        </div>

        {/* 日期篩選工具 */}
        <div className="date-filter-container">
          <label>
            起始日期:
            <input
              type="date"
              value={startDate}
              onChange={handleStartDateChange}
              className="date-input"
            />
          </label>
          <label>
            結束日期:
            <input
              type="date"
              value={endDate}
              onChange={handleEndDateChange}
              className="date-input"
            />
          </label>
        </div>

        <div className="language-selector">
          <img src={translateIcon} alt="Translate" className="translate-icon" />
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            className="language-dropdown"
          >
            <option value="zh">中文</option>
            <option value="tw">台語</option>
            <option value="en">English</option>
            <option value="ja">日本語</option>
            <option value="ko">한국어</option>
            <option value="vi">Tiếng Việt</option>
            <option value="th">ภาษาไทย</option>
            <option value="es">Español</option>
          </select>
        </div>
      </div>

      {/* 主題列 */}
      <div className="sub-nav-bar">
        <Link to="/" className="sub-nav-item active">首頁</Link>
        <Link to="/#recommend" className="sub-nav-item">為你推薦</Link>
        <Link to="/#trending" className="sub-nav-item">追蹤中</Link>
        <Link to="/category/Politics" className="sub-nav-item">政治</Link>
        <Link to="/category/Social News" className="sub-nav-item">社會</Link>
        <Link to="/category/Science" className="sub-nav-item">科學</Link>
        <Link to="/category/Technology" className="sub-nav-item">科技</Link>
        <Link to="/category/International News" className="sub-nav-item">國際</Link>
        <Link to="/category/Lifestyle & Consumer News" className="sub-nav-item">生活</Link>
        <Link to="/category/Sports" className="sub-nav-item">運動</Link>
        <div className="sub-nav-dropdown">
          <button className="sub-nav-item">⋯</button>
          <div className="sub-nav-dropdown-content">
            <Link to="/category/Entertainment" className="sub-nav-dropdown-item">娛樂</Link>
            <Link to="/category/Business & Finance" className="sub-nav-dropdown-item">財經</Link>
            <Link to="/category/Health & Wellness" className="sub-nav-dropdown-item">醫療保健</Link>
          </div>
        </div>
      </div>
    </>
  );
}

export default Header;