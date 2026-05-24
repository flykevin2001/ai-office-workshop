---
name: convert-to-markdown
description: 第一階段操作指南 — 任意檔案轉 Markdown 的完整執行流程，含 CLI 用法、後處理步驟、常見問題排解。
---

# 第一階段：任意檔案 → Markdown

## 執行流程

```
使用者丟檔案
    ↓ 偵測副檔名
    ↓ 查路由表（SKILL.md）
    ↓
  A. MarkItDown 格式 → 直接轉換
  B. 圖片格式 → 圖片 OCR / 多模態直接轉寫
  C. 其他格式 → 路由到對應技能包
```

---

## CLI 用法

每次 Bash 都是新 shell，PATH 不延續，所以完整寫：

### 單檔轉換

```bash
export PATH="$HOME/.local/bin:$PATH" && markitdown "/path/to/file.docx" -o "/path/to/output.md"
```

或用管線輸出：
```bash
export PATH="$HOME/.local/bin:$PATH" && markitdown "/path/to/file.docx" > "/path/to/output.md"
```

### 從 stdin 讀取

```bash
export PATH="$HOME/.local/bin:$PATH" && cat "/path/to/file.xlsx" | markitdown > "/path/to/output.md"
```

### 用 Python API（需要用 pipx venv 的 Python）

```python
#!/Users/jiangyude2/.local/pipx/venvs/markitdown/bin/python3
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)
result = md.convert("/path/to/file.docx")
print(result.text_content)
```

---

## 圖片轉 Markdown

適用：`.jpg` `.jpeg` `.png` `.webp` `.heic` `.tif` `.tiff`

圖片轉寫不使用 MarkItDown CLI。執行方式是直接讀圖，將可見文字與版面結構轉成 Markdown。

### 單張圖片流程

1. 先執行 `date +"%Y-%m-%d-%H%M"` 取得時間戳。
2. 產出檔名：`YYYY-MM-DD-HHMM 原始圖片檔名.md`。
3. 檔首保留原圖連結：
   ```markdown
   ![原圖](/absolute/path/to/image.jpg)
   ```
4. 依原圖排版轉寫：
   - 主標題 → `#`
   - 章節標題 → `##`
   - 標籤 / 小區塊 → `###`
   - 條列 → `-`
   - 表格 / 指標卡 → Markdown table
5. 原文照抄，不摘要、不改寫、不腦補。

### 圖片常見版面對應

| 原圖元素 | Markdown 對應 |
|---|---|
| 大標題 | `# 大標題` |
| 編號章節 | `## 1. 需求背景` |
| 色塊小標 | `### 計畫目標` |
| 卡片式資訊 | Markdown table 或小節條列 |
| 指標數字 | 保留數字與單位，例如 `150人`、`50% UP` |
| QR code 旁文字 | 保留為「QR Code：...」 |
| 照片牆 | 不描述照片內容，除非照片內有可見文字 |

### 圖片 OCR 避免事項

- 不要先跑 `markitdown image.jpg`。
- 不要優先測 Vision / Tesseract / Gemini CLI；這些只在使用者要求或多模態無法讀取時才考慮。
- 看不清楚的小字標註「原圖局部小字未辨識」，不要猜。

---

## 後處理步驟

MarkItDown 轉出來的是乾淨的 Markdown，但需要加上知識庫的規範：

### 1. 檔名加時間戳

轉出的 .md 檔名格式：`YYYY-MM-DD-HHMM 原始檔名.md`

例：`report.docx` → `2026-04-13-1427 report.md`

### 2. 加來源資訊

在檔案開頭加一段來源記錄（不是 YAML frontmatter，除非使用者要求）：

```markdown
> 來源：report.docx
> 轉換時間：2026-04-13 14:27
> 轉換工具：MarkItDown v0.1.5
```

### 3. 存檔位置

預設存到知識庫根目錄，除非使用者指定其他位置。

---

## 常見問題

### Q: 轉出來亂碼？

A: 檢查原始檔案編碼。MarkItDown 預設 UTF-8。如果是舊版 Office 檔案（.xls），可能是 Big5 或 GBK 編碼，轉出後需要手動確認。

### Q: 表格跑掉？

A: Markdown 表格的限制。如果 Excel 有合併儲存格、多層表頭，轉出後需要手動調整。大量數據建議只轉重點區域。

### Q: 圖片不見？

A: MarkItDown 會標記圖片位置（`![](...)` 語法），但不會抽出圖片檔案。如果需要圖片，從原始檔案手動匯出。

### Q: PPTX 排版亂掉？

A: 正常。Markdown 是線性的，PPT 的空間佈局無法保留。轉出的是文字稿，不是視覺複製。

### Q: ZIP 裡面有不支援的格式？

A: MarkItDown 會跳過不支援的格式，只轉它認識的。不會報錯，只是那些檔案不在輸出裡。
