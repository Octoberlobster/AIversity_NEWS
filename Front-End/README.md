# AIversity NEWS - 前端與後端服務

歡迎來到 AIversity NEWS 專案！這是一個提供新聞閱讀、分析與互動功能的平台。此 README 檔案將專注於 `Front-End` 目錄下的前端應用程式與其相關的後端服務。

## 專案描述

此專案包含一個使用 React 建立的現代化前端應用程式，以及一個使用 Python Flask 框架開發的後端 API 服務。使用者可以透過此平台瀏覽不同類別的新聞、進行深度搜尋、與 AI 助理互動，並取得新聞的摘要與事實查核。

## 主要功能

根據後端服務的模組，此平台提供了以下功能：

*   **新聞聊天室 (`/chat/single`)**: 使用者可以針對單一新聞文章，與 AI 助理進行問答互動。
*   **提示詞建議 (`/hint_prompt/*`)**: 系統會根據使用者正在瀏覽的新聞或主題，提供相關的提示詞建議，引導使用者進行更深入的探索。
*   **進階搜尋 (`/advanced_search`)**: 提供比關鍵字搜尋更強大的進階搜尋功能。
*   **單篇新聞證明 (`/proof/single_news`)**: 針對單一新聞，提供相關的佐證資料或摘要。
*   **事實查核 (`/check_fact`)**: 提供新聞內容的事實查核功能。

## 技術棧

### 前端

*   **框架**: [React](https://reactjs.org/)
*   **路由**: [React Router](https://reactrouter.com/)
*   **UI 元件**: [Styled Components](https://styled-components.com/)
*   **資料視覺化**: [D3.js](https://d3js.org/)
*   **後端整合**: [Supabase Client](https://supabase.io/)
*   **Markdown 渲染**: [React Markdown](https://github.com/remarkjs/react-markdown)

### 後端

*   **框架**: [Flask](https://flask.palletsprojects.com/)
*   **CORS**: [Flask-Cors](https://flask-cors.readthedocs.io/)
*   **語言**: Python

## 專案結構

```
Front-End/
├── build/              # 前端應用程式的生產版本
├── public/             # 公開靜態資源
├── src/                # React 應用程式原始碼
│   ├── components/     # React 元件
│   ├── css/            # CSS 樣式表
│   ├── App.js          # 主要應用程式元件
│   └── index.js        # 應用程式進入點
├── back-end/           # Python Flask 後端服務
│   ├── app.py          # Flask 應用程式進入點
│   ├── ChatRoom.py     # 聊天室功能模組
│   ├── check_real2.py  # 事實查核模組
│   └── ...             # 其他功能模組
├── package.json        # 前端專案設定與依賴
└── db.sql              # 資料庫結構 (可能)
```

## 安裝與啟動

### 前端

1.  **進入前端目錄**:
    ```bash
    cd Front-End
    ```

2.  **安裝依賴套件**:
    ```bash
    npm install
    ```

3.  **啟動開發伺服器**:
    ```bash
    npm start
    ```
    應用程式將會在 `http://localhost:3000` 上運行。

### 後端

1.  **進入後端目錄**:
    ```bash
    cd Front-End/back-end
    ```

2.  **安裝 Python 依賴**:
    建議建立一個虛擬環境。後端依賴 `Flask` 和 `Flask-Cors`。
    ```bash
    pip install Flask Flask-Cors
    # 可能還需要安裝其他 .py 檔案中 import 的套件
    ```

3.  **啟動後端服務**:
    ```bash
    flask run
    ```
    後端服務預設將會在 `http://localhost:5000` 上運行。

## API 端點

後端服務 (`app.py`) 提供了以下主要的 API 端點：

*   `POST /chat/single`: 處理單篇新聞的聊天請求。
*   `POST /hint_prompt/single`: 取得單篇新聞的提示詞建議。
*   `POST /hint_prompt/topic`: 取得特定主題的提示詞建議。
*   `POST /hint_prompt/search`: 取得搜尋頁面的提示詞建議。
*   `POST /advanced_search`: 執行進階搜尋。
*   `POST /proof/single_news`: 取得單篇新聞的佐證。
*   `POST /check_fact`: 進行事實查核。

---
此 `README.md` 檔案是根據專案結構自動產生。如有需要，請進一步修改以符合實際情況。
