import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// 建立 QueryClient 實例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 快取時間設定
      staleTime: 5 * 60 * 1000, // 5分鐘內資料視為新鮮,不會重新請求
      cacheTime: 30 * 60 * 1000, // 30分鐘後清除未使用的快取
      
      // 重試設定
      retry: 2, // 失敗時重試2次
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      
      // 效能優化
      refetchOnWindowFocus: false, // 視窗重新聚焦時不自動重新請求
      refetchOnMount: false, // 元件掛載時不自動重新請求(使用快取)
      refetchOnReconnect: true, // 網路重新連線時重新請求
    },
  },
});

export function QueryProvider({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

export { queryClient };
