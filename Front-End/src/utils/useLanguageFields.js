import { useLocation } from 'react-router-dom';
import { useCallback } from 'react';

const LANGUAGE_SUFFIX_MAP = {
  'zh-TW': '',           // 中文使用原欄位名稱
  'en': '_en_lang',      // 英文欄位後綴
  'jp': '_jp_lang',      // 日文欄位後綴  
  'id': '_id_lang'       // 印尼文欄位後綴
};

export const useLanguageFields = () => {
  const location = useLocation();
  
  const getCurrentLanguage = useCallback(() => {
    const pathSegments = location.pathname.split('/');
    const langCode = pathSegments[1];
    return ['zh-TW', 'en', 'jp', 'id'].includes(langCode) ? langCode : 'zh-TW';
  }, [location.pathname]);
  
  const getFieldName = useCallback((baseFieldName) => {
    const language = getCurrentLanguage();
    const suffix = LANGUAGE_SUFFIX_MAP[language] || '';
    return `${baseFieldName}${suffix}`;
  }, [getCurrentLanguage]);
  
  const getMultiLanguageSelect = useCallback((fields) => {
    const language = getCurrentLanguage();
    const suffix = LANGUAGE_SUFFIX_MAP[language] || '';
    
    return fields.map(field => {
      // 同時選擇原欄位和翻譯欄位，用於 fallback
      if (suffix) {
        return `${field}, ${field}${suffix}`;
      }
      return field;
    }).join(', ');
  }, [getCurrentLanguage]);
  
  return {
    getCurrentLanguage,
    getFieldName,
    getMultiLanguageSelect
  };
};