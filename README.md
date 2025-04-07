# README

## 專案概述
本專案旨在開發一個致力於打造一個具前瞻性且能夠打破地域與語言限制的新聞整合平台。我們的專案目標是協助使用者從龐大、雜亂的新聞中提煉出清晰、有邏輯的資訊，並透過聊天室方式與事件人物進行深度互動。  

我們的平台包含以下主要功能：
- 多新聞台資料爬取與整合
- 自動分類新聞事件
- 利用 LLM（Gemini）進行摘要與角色提取
- 分析各角色在事件中的行為與立場
- 提供聊天室互動式介面與角色進行互動。
- 將新聞依時間脈絡進行整合與更新。

本專案強調「多來源報導」、「深層分析」與「互動體驗」，可應用於資料分析、教育輔助等場景。

---

## 環境需求
- **Python** 版本：3.8 或以上
- **React**  版本：19.1.0 或以上
---

## 安裝與執行

### 1. Clone 專案<br>
首先，將專案從 GitHub 或其他代管平台上 Clone 到本地機器。
### 2. 安裝 Python 依賴<br>
使用 pip 安裝專案所需的 Python 依賴。
```
python3 -m venv venv
source venv/bin/activate  # 在 Linux/macOS
venv\Scripts\activate  # 在 Windows

# 安裝依賴
pip install -r requirements.txt
```
### 3. 安裝 React 依賴<br>
前端部分使用 React，請先安裝 Node.js 和 npm（如果尚未安裝，請先安裝 Node.js 來獲得 npm）。
```
cd frontend
npm install
```
### 4. 配置環境變數<br>
根據需要，配置專案的環境變數。例如，API 金鑰、數據庫連線等。這些變數通常可以寫入 .env 檔案。
```
API_KEY=your_api_key_here
DATABASE_URL=your_database_url_here
```
### 5. 執行後端服務<br>
啟動後端服務，使其開始處理資料爬取、分類和摘要生成。
```
cd backend
python app.py
```
後端服務會啟動並開始監聽指定的端口（通常是 localhost:5000，具體視專案配置而定）。
<br>
### 6. 執行前端應用  
啟動前端 React 應用，讓使用者能夠與平台互動。
```
cd frontend
npm start
```
這樣，React 應用將會啟動並可以通過瀏覽器訪問（通常是 localhost:3000）。

📷 預覽畫面
### 新聞系統介面與多角色聊天室展示
![image](https://github.com/Octoberlobster/Intelexis/blob/HA's7-Branch/image.png)
![image](https://github.com/Octoberlobster/Intelexis/blob/HA's7-Branch/image1.png)
### 新聞時序分析與 AI 未來分析
![image](https://github.com/Octoberlobster/Intelexis/blob/HA's7-Branch/image2.png)
![image](https://github.com/Octoberlobster/Intelexis/blob/HA's7-Branch/image3.png)

🤝 貢獻方式
歡迎提出 Issue 或發送 Pull Request！若有想法或合作需求，也歡迎私訊聯繫我們。

📜 授權條款
本專案採用 MIT License 授權。
