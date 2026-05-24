---
name: supported-formats
description: 檔案轉 Markdown 支援格式對照表 — 每種格式的轉換注意事項、產出品質、已知限制。
---

# 支援格式對照表

## MarkItDown 直接處理的格式

### DOCX（Word 文件）

- 保留：標題層級、粗體斜體、表格、項目符號、超連結
- 圖片：會標記圖片位置但不抽出圖片檔案（`![image](...)` 語法）
- 注意：頁首頁尾、浮水印不會保留
- 品質：★★★★★（最穩定的格式之一）

### PPTX（PowerPoint 簡報）

- 保留：每張投影片的標題、內文、項目符號
- 投影片備忘錄：會一併轉出
- 注意：排版佈局不保留（Markdown 是線性的），圖表變成文字描述
- 品質：★★★★☆（文字內容完整，視覺資訊會丟失）
- 適用：提取簡報的文字稿、整理演講大綱

### XLSX / XLS（Excel 試算表）

- 保留：表格結構、工作表名稱、儲存格數值
- 公式：轉出計算結果，不保留公式本身
- 多工作表：每個 sheet 獨立一段
- 注意：圖表不保留，合併儲存格可能排版不佳
- 品質：★★★★☆（數據完整，格式簡化）

### EPUB（電子書）

- 保留：章節結構、標題、內文、連結
- 圖片：標記位置但不抽出
- 注意：複雜排版（多欄、側邊欄）會簡化
- 品質：★★★★☆（內容完整，適合轉成筆記）

### ZIP（壓縮檔）

- 行為：遞迴解壓，逐一轉換裡面的檔案
- 支援：ZIP 裡面的 DOCX、PPTX、XLSX、EPUB、CSV 等都會被轉
- 注意：巢狀 ZIP 也會處理
- 品質：取決於裡面的檔案格式

### CSV（逗號分隔）

- 保留：轉成 Markdown 表格
- 注意：大量資料（>100 行）建議截取重點，不要全轉
- 品質：★★★★★

### JSON

- 保留：鍵值對結構，轉成可讀格式
- 注意：深層巢狀 JSON 可讀性會降低
- 品質：★★★★☆

### XML

- 保留：標籤結構，轉成可讀格式
- 品質：★★★☆☆（取決於 XML 結構複雜度）

---

## 路由到其他工具的格式

| 格式 | 為什麼不用 MarkItDown | 路由到哪裡 |
|------|---------------------|-----------|
| PDF | MarkItDown 只能抽文字層，掃描版和混合型沒辦法處理 | admin-assistant（extract_pdf.py 三種判斷） |
| 音訊 | MarkItDown 要接 OpenAI API（要錢），本地 Whisper 免費又好 | local-speech-to-text |
| YouTube | MarkItDown 只抓自動字幕，既有流程更完整 | notebooklm-codex-ops |
| HTML / 網頁 | MarkItDown 能轉但不會爬，既有工具能爬取 + 整理 | admin-assistant（web-to-knowledge-graph） |
| 圖片 | MarkItDown 要接 LLM API 做 OCR，Claude / Codex 本身就能看圖；圖片需要保留視覺版面與文字，不是一般文件解析 | 圖片 OCR / Claude 多模態 |

### 圖片 JPG / PNG / WebP / HEIC / TIFF

- 保留：可見標題、段落、項目符號、表格、指標卡、圖中文字、QR code 附近標籤文字
- 產出：每張圖片一份 Markdown，檔首用 `![原圖](/absolute/path)` 連回原圖
- 注意：不要摘要、不要改寫；使用者說「盡量還原排版」時，以 Markdown 結構還原資訊層次
- 小字限制：若局部小字無法辨識，標註「原圖局部小字未辨識」，不要猜字
- 禁止路線：不要先嘗試 `markitdown image.jpg`；不要優先測 Vision / Tesseract / Gemini CLI，除非使用者明確要求比較 OCR 工具
- 品質：★★★☆☆ 到 ★★★★★（取決於圖片解析度與字體大小）
