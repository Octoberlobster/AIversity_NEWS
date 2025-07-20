import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';

const HeaderContainer = styled.header`
  background: #f8fafc;
  color: #1e3a8a;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  position: sticky;
  top: 0;
  z-index: 1000;
`;

const MainBar = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem 0.5rem 2rem;
  background: #f8fafc;
  @media (max-width: 700px) {
    flex-direction: column;
    gap: 0.7rem;
    padding: 1rem 1rem 0.5rem 1rem;
  }
`;

const BrandSection = styled.div`
  display: flex;
  align-items: center;
  gap: 1.1rem;
  @media (max-width: 700px) {
    justify-content: center;
    width: 100%;
  }
`;

const Logo = styled.div`
  font-size: 2.1rem;
  font-weight: 800;
  background: linear-gradient(45deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 1px;
`;

const Tagline = styled.span`
  font-size: 1.05rem;
  opacity: 0.95;
  font-weight: 400;
  letter-spacing: 1px;
  color: #1e3a8a;
  @media (max-width: 700px) {
    display: none;
  }
`;

const SearchSection = styled.div`
  display: flex;
  align-items: center;
  gap: 0.7rem;
  @media (max-width: 700px) {
    width: 100%;
    justify-content: center;
  }
`;

const SearchInputWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const SearchIcon = styled.span`
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #667eea;
  font-size: 1.1rem;
  pointer-events: none;
`;

const SearchInput = styled.input`
  padding: 0.5rem 1.2rem 0.5rem 2.5rem;
  border-radius: 25px;
  border: none;
  font-size: 1rem;
  outline: none;
  min-width: 220px;
  background: white;
  box-shadow: 0 2px 8px rgba(102,126,234,0.06);
  transition: box-shadow 0.2s, border 0.2s;
  color: #1e3a8a;
  border: 2px solid transparent;
  &:focus {
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.12);
    border: 2px solid #667eea;
  }
`;

const TagBarWrapper = styled.div`
  width: 100%;
  background: white;
  box-shadow: 0 2px 12px rgba(30,58,138,0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.2rem 0.5rem 0.2rem 0.5rem;
  border-radius: 0 0 18px 18px;
  @media (max-width: 700px) {
    border-radius: 0;
    padding: 0.2rem 0.2rem;
  }
`;

const DomainTagBar = styled.div`
  display: flex;
  align-items: center;
  gap: 0.7rem;
  overflow-x: auto;
  @media (max-width: 700px) {
    gap: 0.5rem;
  }
`;

const Tag = styled.button`
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#f3f4f6'};
  color: ${props => props.active ? 'white' : '#4b5563'};
  border: none;
  border-radius: 20px;
  padding: 0.45rem 1.3rem;
  font-size: 1.05rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s;
  box-shadow: 0 1px 2px rgba(102,126,234,0.04);
  white-space: nowrap;
  letter-spacing: 0.5px;
  &:hover {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    transform: translateY(-2px) scale(1.04);
  }
`;

const HotTag = styled(Tag)`
  background: ${props => props.active ? 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)' : '#f3f4f6'};
  color: ${props => props.active ? '#1e3a8a' : '#fbbf24'};
  font-weight: 700;
  border: 2px solid #fbbf24;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  svg, span {
    color: #fbbf24;
  }
  &:hover {
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    color: #1e3a8a;
  }
`;

const MoreButton = styled.button`
  background: #f3f4f6;
  color: #4b5563;
  border: none;
  border-radius: 20px;
  padding: 0.45rem 1.3rem;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s;
  margin-left: 0.2rem;
  &:hover {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
`;

const Dropdown = styled.div`
  position: absolute;
  top: 110%;
  right: 0;
  min-width: 170px;
  background: white;
  color: #1e3a8a;
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  z-index: 2000;
  padding: 0.5rem 0;
  display: flex;
  flex-direction: column;
  width: 100vw;
  left: 0;
  right: 0;
  margin: 0 auto;
  @media (max-width: 700px) {
    min-width: 100vw;
    border-radius: 0 0 14px 14px;
  }
`;

const DropdownTag = styled.button`
  background: none;
  border: none;
  color: #1e3a8a;
  font-size: 1.05rem;
  padding: 0.7rem 1.5rem;
  text-align: left;
  cursor: pointer;
  border-radius: 8px;
  font-weight: 500;
  transition: background 0.18s;
  &:hover, &.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
`;

const hotEvents = [
  { id: 'event1', label: '女足', icon: '🔥' },
  { id: 'event2', label: '大罷免', icon: '⚡' }
];
const domains = [
  { id: 'politics', label: '政治' },
  { id: 'society', label: '社會' },
  { id: 'science', label: '科學' },
  { id: 'tech', label: '科技' },
  { id: 'international', label: '國際' },
  { id: 'life', label: '生活' },
  { id: 'sports', label: '運動' },
  { id: 'entertainment', label: '娛樂' },
  { id: 'finance', label: '財經' },
  { id: 'health', label: '醫療保健' }
];
const MAX_VISIBLE = 6;

function Header() {
  const [activeDomain, setActiveDomain] = useState(domains[0].id);
  const [search, setSearch] = useState('');

  return (
    <HeaderContainer>
      <MainBar>
        <BrandSection>
          <Logo>AIversity</Logo>
          <Tagline>智能新聞，深度洞察</Tagline>
        </BrandSection>
        <SearchSection>
          <SearchInputWrapper>
            <SearchIcon>🔍</SearchIcon>
            <SearchInput
              type="text"
              placeholder="搜尋新聞/關鍵字..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </SearchInputWrapper>
        </SearchSection>
      </MainBar>
      <TagBarWrapper>
        <DomainTagBar>
          {domains.map(domain => (
            <Tag
              key={domain.id}
              active={activeDomain === domain.id}
              onClick={() => setActiveDomain(domain.id)}
            >
              {domain.label}
            </Tag>
          ))}
        </DomainTagBar>
      </TagBarWrapper>
    </HeaderContainer>
  );
}

export default Header; 