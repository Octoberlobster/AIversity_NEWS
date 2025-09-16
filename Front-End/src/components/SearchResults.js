import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import styled from 'styled-components';
import { searchNews } from '../services/searchService';

const SearchContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
`;

const SearchHeader = styled.div`
  margin-bottom: 2rem;
`;

const SearchTitle = styled.h1`
  font-size: 2rem;
  color: #1e3a8a;
  margin-bottom: 0.5rem;
`;

const SearchInfo = styled.p`
  color: #6b7280;
  font-size: 1rem;
`;

const ResultsContainer = styled.div`
  display: grid;
  gap: 1.5rem;
`;

const NewsCard = styled.article`
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  padding: 1.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  }
`;

const NewsTitle = styled.h2`
  font-size: 1.25rem;
  color: #1e3a8a;
  margin-bottom: 0.75rem;
  line-height: 1.5;
`;

const NewsContent = styled.p`
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 1rem;
`;

const NewsMeta = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: #6b7280;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: 1.1rem;
  color: #667eea;
`;

const ErrorMessage = styled.div`
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
`;

function SearchResults() {
  const [searchParams] = useSearchParams();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const query = searchParams.get('q');

  useEffect(() => {
    if (!query) return;

    const performSearch = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const searchResults = await searchNews(query);
        setResults(searchResults);
      } catch (err) {
        setError('搜尋時發生錯誤，請稍後再試');
        console.error('搜尋錯誤:', err);
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [query]);

  if (!query) {
    return (
      <SearchContainer>
        <SearchHeader>
          <SearchTitle>請輸入搜尋關鍵字</SearchTitle>
        </SearchHeader>
      </SearchContainer>
    );
  }

  return (
    <SearchContainer>
      <SearchHeader>
        <SearchTitle>搜尋結果</SearchTitle>
        <SearchInfo>
          關鍵字: "{query}" {!loading && `(找到 ${results.length} 則相關新聞)`}
        </SearchInfo>
      </SearchHeader>

      {loading && <LoadingSpinner>正在搜尋相關新聞...</LoadingSpinner>}
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      
      {!loading && !error && results.length === 0 && (
        <ErrorMessage>沒有找到相關新聞，請嘗試其他關鍵字</ErrorMessage>
      )}

      {!loading && results.length > 0 && (
        <ResultsContainer>
          {results.map((news, index) => (
            <NewsCard key={news.id || index}>
              <NewsTitle>{news.title}</NewsTitle>
              <NewsContent>{news.summary || news.content}</NewsContent>
              <NewsMeta>
                <span>分類: {news.category}</span>
                <span>{news.published_at}</span>
              </NewsMeta>
            </NewsCard>
          ))}
        </ResultsContainer>
      )}
    </SearchContainer>
  );
}

export default SearchResults;