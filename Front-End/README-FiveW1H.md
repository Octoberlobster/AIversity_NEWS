# FiveW1H 視覺化組件

## 功能概述

這個組件提供了一個互動式的 5W1H (Who, What, When, Where, Why, How) 視覺化介面，用於展示和分析新聞事件或專題議題。

## 主要特性

### 1. 節點類型
- **中心節點 (Center)**: 顯示事件的核心概述
- **5W1H 節點**: 六個主要分析維度
- **詳細節點**: 每個維度下的具體資訊

### 2. 互動功能
- 點擊節點顯示詳細資訊
- 拖拽節點調整位置
- 縮放和平移視圖
- 自動佈局和力導向圖

### 3. 資料結構支援
支援以下 JSON 格式的資料結構：

```json
{
  "center_node": {
    "id": "center",
    "label": "事件概述",
    "description": "事件的整體描述"
  },
  "main_nodes": [
    {
      "id": "who",
      "label": "相關人物",
      "description": "涉及的人物描述"
    }
    // ... 其他 5W1H 節點
  ],
  "detailed_nodes": {
    "who_nodes": [
      {
        "id": "who1",
        "label": "具體人物",
        "description": "詳細描述"
      }
    ]
    // ... 其他類別的詳細節點
  }
}
```

## 使用方法

### 1. 基本使用

```javascript
import { FiveW1HVisualization } from './components/FiveW1HVisualization.js';

// 創建實例
const viz = new FiveW1HVisualization('container-id', {
  width: 1200,
  height: 600,
  isHeaderMode: false
});

// 載入資料並渲染
await viz.loadData();
viz.setupD3();
viz.render();
```

### 2. 配置選項

- `width`: 視覺化寬度 (預設: 1200)
- `height`: 視覺化高度 (預設: 600)
- `isHeaderMode`: 是否為標題模式 (預設: false)
- `dragLimit`: 拖拽限制 (預設: 50)

### 3. 測試頁面

使用 `test-fivew1h.html` 來測試功能：

```bash
# 啟動開發伺服器
npm start

# 或直接開啟 HTML 檔案
open test-fivew1h.html
```

## 節點點擊功能

### 中心節點
點擊中心節點會顯示：
- 事件概述
- 所有主要要素的摘要

### 5W1H 節點
點擊 5W1H 節點會顯示：
- 該維度的基本描述
- 對應的詳細節點列表

### 詳細節點
點擊詳細節點會顯示：
- 具體的標籤和描述
- 相關的詳細資訊

## 自定義樣式

組件支援自定義樣式，可以通過修改 CSS 類別來調整外觀：

- `.node`: 節點樣式
- `.node-center`: 中心節點樣式
- `.node-5w1h`: 5W1H 節點樣式
- `.link`: 連接線樣式
- `.text`: 文字標籤樣式

## 資料來源

組件支援多種資料來源：
1. **Supabase**: 從資料庫載入資料
2. **預設資料**: 當外部資料載入失敗時使用
3. **自定義資料**: 通過 API 傳入

## 瀏覽器相容性

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 依賴項目

- D3.js v7.9.0+
- ES6 模組支援
- 現代瀏覽器 API

## 故障排除

### 常見問題

1. **節點不顯示**: 檢查資料格式是否正確
2. **點擊無反應**: 確認事件監聽器已正確綁定
3. **樣式異常**: 檢查 CSS 類別是否正確載入

### 除錯模式

開啟瀏覽器開發者工具查看控制台輸出，組件會輸出詳細的除錯資訊。

## 更新日誌

- v1.0.0: 初始版本，支援基本 5W1H 視覺化
- v1.1.0: 新增詳細節點支援和點擊互動功能
- v1.2.0: 優化資料結構和視覺化效果

