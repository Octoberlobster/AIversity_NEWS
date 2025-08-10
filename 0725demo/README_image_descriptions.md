# 圖片生成與說明功能

這個模組提供了根據新聞摘要生成圖片，並為每張圖片添加說明文字的功能。

## 主要功能

### 1. 自動生成圖片與說明
- 根據新聞標題和摘要生成對應的圖片
- 為每張圖片自動產生適當的說明文字
- 將圖片路徑和說明儲存到JSON檔案中

### 2. 為現有圖片生成說明
- 為已存在的圖片批量生成說明文字
- 自動配對圖片與對應的新聞文章
- 產生完整的圖片metadata

## 使用方法

### 方法一：生成新圖片並附上說明

```python
from generate_picture import generate_from_json

# 生成圖片並建立說明
result = generate_from_json(
    input_json="cleaned_final_news1.json",
    output_dir="generated_images_with_descriptions",
    max_items=10,  # 限制處理數量，None代表全部
    max_images_per_article=1,
    retry_times=3,
    sleep_between_calls=0.6
)

print(f"生成了 {result['total_images']} 張圖片")
print(f"Metadata儲存在: {result['metadata_path']}")
```

### 方法二：使用測試腳本

```bash
cd 0725demo
python test_image_with_description.py
```

### 方法三：為現有圖片生成說明

```bash
cd 0725demo
python generate_descriptions_for_existing_images.py
```

## 輸出格式

### image_metadata.json 結構

```json
{
  "total_images": 10,
  "generated_at": "2025-08-10 15:30:45",
  "images": [
    {
      "image_path": "generated_images/政治/北檢譴責柯文哲暴走黃國昌諷-自知理虧的小孩哭著回家找媽媽.png",
      "description": "政治事件相關場景：北檢譴責柯文哲暴走黃國昌諷：自知理虧的小孩哭著回家找媽媽",
      "article_title": "北檢譴責柯文哲暴走黃國昌諷：自知理虧的小孩哭著回家找媽媽| 政治",
      "category": "政治",
      "article_id": "926f11d8-8bb0-4224-bbcc-ad7a6ebff396",
      "generated": true
    }
  ]
}
```

## 說明文字生成規則

說明文字會根據新聞類別和標題自動生成：

- **政治**: "政治事件相關場景：[標題前30字]"
- **社會**: "社會議題相關情境：[標題前30字]"
- **國際**: "國際事務相關場面：[標題前30字]"
- **財經**: "財經事件相關景象：[標題前30字]"
- **科技**: "科技發展相關畫面：[標題前30字]"
- **環境**: "環境議題相關場景：[標題前30字]"
- **體育**: "體育活動相關情境：[標題前30字]"
- **其他**: "新聞事件相關場景：[標題前30字]"

## 自訂說明功能

你也可以自訂說明生成規則，修改 `core.py` 中的 `_generate_image_description` 函數：

```python
def _generate_image_description(news_title: str, news_summary: str, category: str) -> str:
    # 自訂你的說明生成邏輯
    return f"自訂說明：{news_title[:20]}"
```

## 檔案結構

```
0725demo/
├── generate_picture/
│   ├── __init__.py
│   └── core.py                          # 核心功能
├── test_image_with_description.py       # 測試腳本
├── generate_descriptions_for_existing_images.py  # 為現有圖片生成說明
└── generated_images_with_descriptions/   # 輸出資料夾
    ├── image_metadata.json              # 圖片說明metadata
    ├── errors.json                      # 錯誤記錄（如果有）
    └── [分類資料夾]/                     # 按類別分組的圖片
        └── [圖片檔案]
```

## 注意事項

1. 確保已設定 GEMINI_API_KEY 環境變數
2. 安裝必要的套件：`pip install -r requirements.txt`
3. 圖片生成可能需要較長時間，建議先用少量資料測試
4. metadata JSON檔案會記錄所有圖片的資訊，包括已存在和新生成的圖片

## 錯誤處理

- 如果圖片生成失敗，錯誤會記錄在 `errors.json` 檔案中
- 已存在的圖片不會重複生成，但會加入到metadata中
- 未能配對到新聞文章的圖片會使用基本資訊生成說明
