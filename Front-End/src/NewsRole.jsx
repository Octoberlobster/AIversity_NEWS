import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';

export default function NewsRole() {
  // 1. 讀取 localStorage 中的資料
  const newsData = JSON.parse(localStorage.getItem('newsData')) || [];
  const newsRole = JSON.parse(localStorage.getItem('newsRole')) || [];
  const [expandedRole, setExpandedRole] = useState(null);
  const { newsId } = useParams();

  // 2. 找出對應新聞
  const selectedNews = newsData.find(
    (news) => parseInt(news.Index) === parseInt(newsId)
  );

  if (!selectedNews) {
    return (
      <div style={styles.container}>
        <p>找不到該新聞或尚未有新聞資料</p>
        <Link style={styles.backLink} to="/">
          ← 返回新聞列表
        </Link>
      </div>
    );
  }

  // 3. 依你的資料結構，找出符合標題的角色資料
  const selectedItem = newsRole.find((element) => {
    const keys = Object.keys(element);
    const theKey = keys[0];
    const pureTitle = theKey.replace(/^"Title":\s*/, "");
    return pureTitle === selectedNews.Title;
  });

  if (!selectedItem) {
    return (
      <div style={styles.container}>
        <h3 style={styles.sectionTitle}>角色因果分析</h3>
        <p>尚未有角色分析資料</p>
        <Link style={styles.backLink} to={`/news/${newsId}`}>
          ← 返回新聞詳細
        </Link>
      </div>
    );
  }

  // 4. 取出角色物件並取得所有角色鍵
  const theKey = Object.keys(selectedItem)[0];
  const roleObject = selectedItem[theKey]; // { Role1: {...}, Role2: {...} }
  const roleKeys = Object.keys(roleObject);

  

  const handleToggleRole = (roleKey) => {
    setExpandedRole((prev) => (prev === roleKey ? null : roleKey));
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.sectionTitle}>角色因果分析</h3>
      <div style={styles.roleContainer}>
        {roleKeys.map((rk) => {
          const role = roleObject[rk];
          const isActive = expandedRole === rk;

          return (
            <div key={rk} style={styles.roleItem}>
              {/* 頭像與名字 */}
              <div
                style={styles.avatarWrapper}
                onClick={() => handleToggleRole(rk)}
              >
                <div style={styles.roleCircle}>
                  <span style={styles.iconPlaceholder}>?</span>
                </div>
                <p style={styles.roleName}>{role.Role_Name}</p>
              </div>

              {/* 若被點擊，顯示分析 */}
              {isActive && (
                <div style={styles.analyzeBox}>
                  <p style={styles.analyze}>{role.Analyze}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '16px',
    maxWidth: '800px',
    margin: '0 auto',
    fontFamily: 'sans-serif',
  },
  sectionTitle: {
    fontSize: '20px',
    marginBottom: '12px',
  },
  roleContainer: {
    display: 'flex',
    justifyContent: 'center',
    flexWrap: 'wrap',
    gap: '40px',
    marginBottom: '24px',
  },
  roleItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    width: '480px',
    cursor: 'pointer',
  },
  avatarWrapper: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  roleCircle: {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    backgroundColor: '#ccc',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '8px',
  },
  iconPlaceholder: {
    fontSize: '24px',
    color: '#fff',
  },
  roleName: {
    margin: 0,
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#333',
  },
  analyzeBox: {
    marginTop: '8px',
    backgroundColor: '#f9f9f9',
    borderRadius: '8px',
    padding: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    width: '100%',       // 與 roleItem 等寬
    textAlign: 'left',   // 可改為 'center' 看需求
  },
  analyze: {
    margin: 0,
    fontSize: '14px',
    lineHeight: '1.5',
    color: '#555',
  },
  backLink: {
    display: 'block',
    textDecoration: 'none',
    color: '#0066cc',
    marginTop: '20px',
    textAlign: 'center',
  },
};
