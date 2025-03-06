import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import NewsList from './NewsList';
import NewsDetail from './NewsDetail';
import NewsRole from './NewsRole';

function App() {
  // 用來存放後端回傳的新聞清單
  const [newsData, setNewsData] = useState([]);
  const [newsRole, setnewsRole] = useState([]);
  
  // 點擊按鈕後，fetch 後端的 /get_news
  const handleFetchNews = () => {
    fetch('http://localhost:5000/get_news')
      .then(response => {
        if (!response.ok) {
          throw new Error(`Network response was not ok: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('後端回傳的新聞資料：', data);
        setNewsData(data);
        localStorage.setItem('newsData', JSON.stringify(data));
      })
      .catch(error => {
        console.error('Fetch error:', error);
      });
  };

  const handleRoleClick = () => {
      fetch('http://localhost:5000/get_roles',{
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newsData) // 將新聞資料轉成 JSON 格式
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('後端回傳的新聞資料：', data);
          setnewsRole(data);
          localStorage.setItem('newsRole', JSON.stringify(data));
        })
        .catch(error => {
          console.error('Fetch error:', error);
        });
    };

  return (
    <Router>
      <div style={styles.container}>
        {/* 頂端導覽列 */}
        <header style={styles.header}>
          <div style={styles.headerContent}>
            <h1 style={styles.headerTitle}>Intelexis</h1>
            <nav>
              <Link style={styles.navLink} to="/">新聞列表</Link>
            </nav>
          </div>
        </header>

        {/* 按鈕 */}
        <div style={styles.buttonWrapper}>
          <button style={styles.button} onClick={handleFetchNews}>
            取得最新新聞
          </button>
        </div>

        {/* 路由配置 */}
        <main style={styles.main}>
          <Routes>
            <Route path="/" element={<NewsList newsData={newsData} />} />
            <Route path="/news/:newsId" element={<NewsDetail newsData={newsData} />} />
          </Routes>
        </main>

        <div style={styles.buttonWrapper}>
          <button style={styles.button} onClick={handleRoleClick}>
            開始角色因果分析
          </button>
        </div>

        {/* 頁尾 */}
        <footer style={styles.footer}>
          <p style={styles.footerText}>© 2025 Intelexis. All rights reserved.</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;

const styles = {
  container: {
    fontFamily: "'Noto Sans TC', sans-serif",
    backgroundColor: "#f7f9fc",
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    background: "linear-gradient(90deg, #0066cc, #003366)",
    padding: "16px 24px",
    color: "#fff",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  },
  headerContent: {
    maxWidth: "900px",
    margin: "0 auto",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerTitle: {
    margin: 0,
    fontSize: "28px",
    fontWeight: "bold",
  },
  navLink: {
    color: "#fff",
    textDecoration: "none",
    fontSize: "16px",
    marginLeft: "16px",
  },
  buttonWrapper: {
    textAlign: "center",
    margin: "20px 0",
  },
  button: {
    padding: "10px 20px",
    fontSize: "16px",
    borderRadius: "4px",
    border: "none",
    backgroundColor: "#0066cc",
    color: "#fff",
    cursor: "pointer",
    transition: "background-color 0.3s ease",
  },
  main: {
    flex: 1,
    maxWidth: "900px",
    margin: "0 auto",
    padding: "24px",
    backgroundColor: "#fff",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
  },
  footer: {
    backgroundColor: "#003366",
    padding: "12px 24px",
    textAlign: "center",
  },
  footerText: {
    margin: 0,
    color: "#fff",
    fontSize: "14px",
  },
};
