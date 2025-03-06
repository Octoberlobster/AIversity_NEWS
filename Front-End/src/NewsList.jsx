import React from 'react';
import { Link } from 'react-router-dom';

function NewsList({ newsData }) {
  // 先嘗試從 localStorage 中取得資料
  newsData = JSON.parse(localStorage.getItem('newsData')) || newsData;

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>新聞列表</h2>
      {newsData.length === 0 ? (
        <p style={styles.message}>尚未有新聞，請點擊上方「取得最新新聞」按鈕。</p>
      ) : (
        <ul style={styles.list}>
          {newsData.map((news) => (
            <li key={news.Index} style={styles.listItem}>
              <Link style={styles.link} to={`/news/${news.Index}`}>
                {news.Title}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default NewsList;

const styles = {
  container: {
    padding: "16px",
  },
  title: {
    fontSize: "24px",
    marginBottom: "16px",
    textAlign: "center",
    color: "#333",
  },
  message: {
    fontSize: "16px",
    textAlign: "center",
    color: "#666",
  },
  list: {
    listStyle: "none",
    padding: 0,
  },
  listItem: {
    margin: "10px 0",
    padding: "12px",
    backgroundColor: "#f0f4f8",
    borderRadius: "4px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  },
  link: {
    textDecoration: "none",
    fontSize: "18px",
    color: "#0066cc",
  },
};
