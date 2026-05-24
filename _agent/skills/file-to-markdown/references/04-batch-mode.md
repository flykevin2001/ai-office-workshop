---
name: batch-mode
description: 批次轉換操作指南 — 整個資料夾的檔案一次轉完，含 convert.py 用法、轉換報告格式、斷點續傳邏輯。
---

# 批次轉換模式

## 觸發

使用者說「整個資料夾轉」「批次轉」「把這個資料夾的檔案都轉成 Markdown」「把這資料夾圖片轉 MK / MD」

---

## 執行流程

### 步驟一：掃描

列出資料夾裡所有可轉換的檔案，包含 MarkItDown 格式與圖片：

```bash
find "/path/to/folder/" -maxdepth 1 -type f | grep -iE '\.(docx|pptx|xlsx|xls|epub|zip|csv|json|xml|jpe?g|png|webp|heic|tiff?)$'
```

告知使用者：
- 共幾個檔案
- 格式分布（幾個 DOCX、幾個 XLSX...）
- 預估轉換時間

如果掃描結果主要是圖片（JPG/PNG/WebP/HEIC/TIFF），直接切到「圖片批次轉寫」；不要跑 convert.py，也不要嘗試 MarkItDown。

### 步驟二：確認

等使用者確認才開始。不自動跑。

例外：使用者已明確要求「這個資料夾轉成 Markdown / MK / MD」時，可直接開始。圖片批次尤其不需要再問一次，除非圖片超過 30 張、解析度很低，或目標文字明顯太小。

### 步驟三：逐一轉換

用 convert.py 腳本：

```bash
/Users/jiangyude2/.local/pipx/venvs/markitdown/bin/python3 \
  "/Users/jiangyude2/Library/Mobile Documents/iCloud~md~obsidian/Documents/江昱德 主知識庫/_agent/skills/file-to-markdown/scripts/convert.py" \
  "/path/to/folder/" --batch
```

或手動逐一：

```bash
export PATH="$HOME/.local/bin:$PATH"
for f in /path/to/folder/*.docx; do
  markitdown "$f" -o "${f%.docx}.md"
done
```

### 圖片批次轉寫

資料夾主要是圖片時：

1. 先執行 `date +"%Y-%m-%d-%H%M"` 取得時間戳。
2. 每張圖片建立一份 Markdown，檔名：`YYYY-MM-DD-HHMM 原始檔名.md`。
3. 檔首保留原圖：
   ```markdown
   ![原圖](/absolute/path/to/image.jpg)
   ```
4. 直接用多模態讀圖，依原版面轉寫：
   - 大標題、區塊標題、小標籤
   - 段落原文
   - 條列原文
   - 表格、指標卡、對照資訊
   - 圖中文字與 QR code 標籤
5. 不摘要、不改寫、不補充；看不清楚就標「原圖局部小字未辨識」。
6. 完成後回報所有產出檔案完整絕對路徑。

圖片批次不使用 convert.py，因為 convert.py 是 MarkItDown 包裝器，無法處理圖片 OCR 與視覺版面。

### 步驟四：斷點續傳

convert.py 會自動檢查：如果同名 .md 已存在，跳過該檔案。

這樣中途斷掉，重新跑就好，不會重複轉換。

### 步驟五：轉換報告

轉完後輸出報告：

```
轉換報告
========
資料夾：/path/to/folder/
時間：2026-04-13 14:27
工具：MarkItDown v0.1.5

成功：12 個
  - report.docx → 2026-04-13-1427 report.md
  - slides.pptx → 2026-04-13-1427 slides.md
  - ...

跳過（已存在）：3 個
  - old-report.docx（已有 old-report.md）
  - ...

失敗：1 個
  - corrupted.xlsx（錯誤：無法讀取檔案）

不支援（跳過）：2 個
  - photo.jpg（圖片格式，建議用 Claude 多模態）
  - recording.mp3（音訊格式，建議用 local-speech-to-text）
```

---

## 注意事項

- 大量檔案（>50 個）建議先測 3-5 個，確認品質再全跑
- 大量圖片（>30 張）建議分批，避免多模態上下文過長導致漏字
- ZIP 檔案會遞迴解壓，注意巢狀 ZIP 可能產出大量檔案
- 批次轉完後不自動上標籤（標籤需要 AI 判斷，批次上標籤太消耗 token）
- 如果需要批次上標籤，另外跑一輪標籤流程
