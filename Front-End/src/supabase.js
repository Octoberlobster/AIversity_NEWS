import { createClient } from '@supabase/supabase-js';
import { createContext, useContext, useMemo } from 'react';

// 創建 Supabase 客戶端實例
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

// 導出原始客戶端實例以便在非 React 環境中使用
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// 創建 React Context
const SupabaseContext = createContext(null);

// Supabase Provider 組件
export function SupabaseProvider({ children }) {
  // 使用 useMemo 確保客戶端只創建一次
  const supabaseClient = useMemo(() => 
    createClient(supabaseUrl, supabaseAnonKey), 
  []);

  return (
    <SupabaseContext.Provider value={supabaseClient}>
      {children}
    </SupabaseContext.Provider>
  );
}

// 自定義 Hook 用於在組件中訪問 Supabase
export function useSupabase() {
  const context = useContext(SupabaseContext);
  if (!context) {
    throw new Error('useSupabase 必須在 SupabaseProvider 內使用');
  }
  return context;
}
