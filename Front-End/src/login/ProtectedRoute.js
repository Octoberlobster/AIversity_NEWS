import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  // 載入中顯示 loading 畫面
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '1.2rem',
        color: '#666'
      }}>
        載入中...
      </div>
    );
  }

  // 未登入則導向登入頁，並記住原本要去的頁面
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 已登入則顯示內容
  return children;
};

export default ProtectedRoute;
