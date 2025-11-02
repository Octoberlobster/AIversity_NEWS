import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import './LoginPage.css';

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // 登入成功後要導向的頁面（如果有記住原本要去的頁面）
  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // 基本驗證
    if (!email || !password) {
      setError('請輸入電子郵件和密碼');
      setLoading(false);
      return;
    }

    try {
      const { data, error } = await signIn(email, password);

      if (error) {
        // 根據錯誤類型顯示不同訊息
        if (error.message.includes('Invalid login credentials')) {
          setError('電子郵件或密碼錯誤');
        } else if (error.message.includes('Email not confirmed')) {
          setError('請先確認您的電子郵件');
        } else {
          setError(error.message || '登入失敗，請稍後再試');
        }
        setLoading(false);
        return;
      }

      if (data?.user) {
        // 登入成功，導向原本要去的頁面
        navigate(from, { replace: true });
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('登入時發生錯誤，請稍後再試');
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h1 className="login-title">AIversity</h1>
            <p className="login-subtitle">以大語言模型建構多視角與深度分析</p>
            <p className="login-subtitle">之新一代新聞媒體</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                電子郵件
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="form-input"
                placeholder="請輸入電子郵件"
                disabled={loading}
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">
                密碼
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-input"
                placeholder="請輸入密碼"
                disabled={loading}
                autoComplete="current-password"
              />
            </div>

            {error && (
              <div className="error-message">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              className="login-button"
              disabled={loading}
            >
              {loading ? (
                <span className="loading-spinner">
                  <svg className="spinner" viewBox="0 0 24 24">
                    <circle className="spinner-circle" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  </svg>
                  登入中...
                </span>
              ) : (
                '登入'
              )}
            </button>
          </form>

          <div className="login-footer">
            <p className="login-hint">
              ⚠️ 此為內部系統，僅限授權人員使用
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
