import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import zhTW from './locales/zh-TW.json';
import en from './locales/en.json';
import jp from './locales/jp.json';
import id from './locales/id.json';

const resources = {
  'zh-TW': {
    translation: zhTW
  },
  'en': {
    translation: en
  },
  'jp': {
    translation: jp
  },
  'id': {
    translation: id
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'zh-TW',
    lng: 'zh-TW', // 預設語言
    debug: true, // 開啟除錯模式
    
    keySeparator: '.', // 使用點號作為鍵分隔符

    interpolation: {
      escapeValue: false // React 已經對 XSS 進行防護
    },

    detection: {
      // 偵測語言的順序
      order: ['localStorage', 'navigator', 'htmlTag'],
      
      // 快取設定
      caches: ['localStorage'],
      
      // localStorage 的鍵名
      lookupLocalStorage: 'i18nextLng',
    }
  });

export default i18n;