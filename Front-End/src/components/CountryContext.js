import React, { createContext, useContext, useState, useEffect } from 'react';

const CountryContext = createContext();

export function CountryProvider({ children }) {
  // 從 localStorage 讀取上次選擇的國家,如果沒有則預設為 'taiwan'
  const [selectedCountry, setSelectedCountry] = useState(() => {
    const saved = localStorage.getItem('selectedCountry');
    return saved || 'taiwan';
  });

  // 當國家改變時,儲存到 localStorage
  useEffect(() => {
    localStorage.setItem('selectedCountry', selectedCountry);
  }, [selectedCountry]);

  return (
    <CountryContext.Provider value={{ selectedCountry, setSelectedCountry }}>
      {children}
    </CountryContext.Provider>
  );
}

export function useCountry() {
  const context = useContext(CountryContext);
  if (!context) {
    throw new Error('useCountry must be used within a CountryProvider');
  }
  return context;
}
