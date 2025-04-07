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

## 專案結構
```
project_directory/
├── Back-End/                       # 後端
│   ├── GenerateNews_EachEvent/     # 測試用的輸入檔案資料夾
│   ├── Roles/                      # 儲存生成之角色資料
│   ├── RolesAnalyze/               # 儲存角色分析圖與資料
│   ├── __pycache__/                # Python 編譯暫存檔
│   ├── static/                     # 前端靜態資源（JS/CSS）
│   ├── templates/                  # HTML 模板（Jinja2）
│   ├── app.py                      # Flask 啟動主程式（整合所有模組）
│   ├── Categorize.py               # 新聞分類模組
│   ├── ChatRoom.py                 # 智慧對話處理（生成摘要、觀點）
│   ├── Combined.py                 # 多新聞台整合模組
│   ├── DivideEvent.py              # 將新聞切分為事件段落
│   ├── GenerateNews.py             # 新聞生成與重構模組
│   ├── GenerateRoles.py            # 角色抽取模組
│   ├── GenerateRolesAnalyze.py     # 角色立場與情緒分析模組
│   ├── Summarize.py                # 多段新聞摘要生成（整合 Gemini）
│   ├── clean.py                    # 預處理腳本（去除雜訊）
│   ├── crawler_news.py             # 新聞爬蟲（多來源）
│   ├── event_progress.py           # 事件進展分析
│   ├── event_progress_LLM.py       # 使用 LLM 判斷事件進展階段
│   ├── google_translator.py        # Google 翻譯 API 模組
│   ├── predict.py                  # 分類預測模組（如立場、分類）
│   ├── similarity.py               # 向量語意相似度計算
│   ├── similarityLLM.py            # 使用 LLM 計算觀點語意差異
│   └── summary_news.py             # 整理後的新聞摘要生成
├── Front-End/                      # 前端
│   ├── public/                     
│   ├── src/                        # 前端主要頁面
│   ├── .gcloudignore
│   ├── .gitignore
│   ├── app.yaml
│   ├── package-lock.json
│   └── package.json
├── 醜醜的新聞架構第一版.pdf     
└── README.md                       # 本說明文件
```

---

## 安裝與執行

### 安裝依賴
本專案不需要額外的外部依賴，確認系統已安裝 Python 3.8 或以上版本即可。

📷 預覽畫面

🤝 貢獻方式
歡迎提出 Issue 或發送 Pull Request！若有想法或合作需求，也歡迎私訊聯繫我們。

📜 授權條款
本專案採用 MIT License 授權。

🙌 特別感謝
- 高雄大學資訊工程系-吳俊興教授指導
- Gemini 技術支援
