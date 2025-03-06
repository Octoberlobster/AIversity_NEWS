import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import NewsRole from './NewsRole';

function NewsDetail({ newsData }) {
  // 先嘗試從 localStorage 中取得資料
  newsData = JSON.parse(localStorage.getItem('newsData')) || newsData;
  const { newsId } = useParams();

  // 找出相對應的新聞物件
  const selectedNews = newsData.find(
    (news) => parseInt(news.Index) === parseInt(newsId)
  );

  if (!selectedNews) {
    return (
      <div style={styles.messageContainer}>
        <h2 style={styles.message}>找不到該新聞或尚未抓取新聞</h2>
        <Link style={styles.backLink} to="/">返回新聞列表</Link>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>{selectedNews.Title}</h2>
      <p style={styles.content}>{selectedNews.Content}</p>
      <NewsRole/>
      <Link style={styles.backLink} to="/">← 返回新聞列表</Link>
    </div>
  );
}

export default NewsDetail;

const styles = {
  container: {
    padding: "16px",
    lineHeight: "1.6",
  },
  title: {
    fontSize: "28px",
    marginBottom: "16px",
    color: "#333",
  },
  content: {
    fontSize: "18px",
    color: "#555",
    marginBottom: "24px",
  },
  backLink: {
    textDecoration: "none",
    fontSize: "16px",
    color: "#0066cc",
  },
  messageContainer: {
    textAlign: "center",
    padding: "40px 16px",
  },
  message: {
    fontSize: "20px",
    color: "#666",
  },
  date: {
    fontSize: "16px",
    color: "rebeccapurple",
    marginBottom: "16px",
  },
};
