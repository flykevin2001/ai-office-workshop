---
name: file-to-markdown
description: 檔案轉 Markdown 轉換器 1.1 - 整合微軟 MarkItDown 開源工具與圖片 OCR / 多模態轉寫路由，統一入口。MarkItDown 負責 DOCX、PPTX、XLSX、EPUB、ZIP、CSV/JSON/XML（純本地不接 API）；JPG/PNG/WebP 等圖片走圖片 OCR / Claude 多模態直接轉 Markdown；PDF 路由到 extract_pdf.py；音訊路由到 local-speech-to-text；YouTube 路由到 notebooklm-codex-ops；HTML/網頁路由到 web-to-knowledge-graph。支援快速轉換、圖片轉寫、知識圖譜、批次轉換。當使用者說「轉 Markdown」「轉 MD」「轉 MK」「幫我轉」「轉知識圖譜」「整理成筆記」「批次轉換」「MarkItDown」，或丟入 DOCX/PPTX/XLSX/EPUB/ZIP/CSV/JSON/XML/JPG/PNG/WebP 檔案時觸發。
---

# 檔案轉 Markdown 轉換器 1.1

統一入口路由器 — 不管丟什麼格式進來，它知道該叫誰處理。

核心工具：微軟 [MarkItDown](https://github.com/microsoft/markitdown) 開源工具（v0.1.5）
圖片工具：Claude / Codex 多模態直接讀圖轉寫（不經 MarkItDown）
設計者：江江教練
建立日期：2026-04-13

---

## 定位

這個技能包不是從零開始，而是把既有的轉換能力整合成統一入口：

**MarkItDown 負責的格式（全部純本地、不接 API）：**
- DOCX（Word 文件）
- PPTX（PowerPoint 簡報）
- XLSX / XLS（Excel 試算表）
- EPUB（電子書）
- ZIP（遞迴解壓轉換）
- CSV / JSON / XML（結構化資料）

**路由到既有工具的格式（它們做得更好）：**
- PDF → `extract_pdf.py`（三種類型判斷：文字/掃描/混合）→ admin-assistant
- 圖片 JPG / PNG / WebP / HEIC / TIFF → 圖片 OCR / Claude 多模態直接轉寫
- 音訊 → `local-speech-to-text`（本地 Whisper，免費又好）
- YouTube → `notebooklm-codex-ops`（完整字幕流程）
- HTML / 網頁 → `web-to-knowledge-graph`（爬取 + 整理）→ admin-assistant

**圖片硬規則：**
- 圖片不是 MarkItDown 任務，不要先嘗試 `markitdown image.jpg`。
- 不要為圖片 OCR 優先測 macOS Vision、Tesseract、Gemini CLI 等不穩路線；除非使用者明確要求比較 OCR 工具。
- 先用多模態直接讀圖，將可見文字轉成 Markdown。
- 使用者要求「盡量還原排版」「所有文字保留」時，優先保留標題層級、段落、項目符號、表格、數字與圖中文字；不要摘要、不要改寫。
- 若局部小字無法辨識，在 Markdown 以「原圖局部小字未辨識」註明，不要猜字。

---

## 四種模式

### 模式一：快速轉換

觸發詞：「轉 Markdown」「轉 MD」「幫我轉」+ 丟檔案

流程：
1. 偵測檔案格式
2. 判斷走 MarkItDown 還是路由到其他工具（見路由表）
3. 走 MarkItDown 的格式：直接執行轉換
4. 產出 .md 存到使用者指定位置（預設知識庫根目錄）
5. 檔名加時間戳：`YYYY-MM-DD-HHMM 原始檔名.md`

快速轉換指令（CLI）：
```bash
export PATH="$HOME/.local/bin:$PATH" && markitdown "/path/to/file.docx" -o "/path/to/output.md"
```

或用管線：
```bash
export PATH="$HOME/.local/bin:$PATH" && markitdown "/path/to/file.docx" > "/path/to/output.md"
```

### 模式二：知識圖譜

觸發詞：「轉知識圖譜」「整理成筆記」「拆成 Obsidian」

流程：
1. 先走模式一，轉出 Markdown
2. AI 讀取 Markdown 純文字（不碰原始檔）
3. 判斷拆分策略：
   - **輕量版**（預設）：一份文件 = 一個 .md + 標籤 + 基本 `[[]]` 連結
   - **完整版**（使用者說「完整版」「拆深一點」時）：拆章節、建 MOC 索引頁、跨文件交叉連結、四維度標籤
4. 上標籤（走既有四維度標籤流程）

知識圖譜的連結邏輯複用 `admin-assistant/references/web-to-knowledge-graph.md`。

### 模式三：圖片轉寫

觸發詞：「圖片轉 Markdown」「JPG 轉 Markdown」「照片轉文字」「把圖片裡的文字轉 MK / MD」「盡量還原排版」

流程：
1. 掃描檔案格式；若資料夾主要是 `.jpg` `.jpeg` `.png` `.webp` `.heic` `.tif` `.tiff`，直接判定為圖片轉寫任務。
2. 每張圖建立一份 Markdown；檔名加時間戳：`YYYY-MM-DD-HHMM 原始檔名.md`。
3. 檔首保留原圖連結：
   ```markdown
   ![原圖](/absolute/path/to/image.jpg)
   ```
4. 依視覺版面轉成 Markdown：
   - 大標題 → `#`
   - 區塊標題 → `##`
   - 小標籤 / 子段 → `###`
   - 條列 → `-`
   - 表格 / 指標卡 / 對照資料 → Markdown table
   - QR code、照片牆、圖示文字 → 另列「圖中文字」或「圖示文字」
5. 嚴格保留原文，不自行潤稿、摘要或補充。
6. 批次完成後列出全部產出檔案的完整絕對路徑。

圖片批次不需要先請使用者確認；如果使用者已明確說「這個資料夾轉成 MK / MD」，直接做。只有在圖片數量很多（例如超過 30 張）或圖片文字極小、品質明顯不足時，才先回報風險並詢問是否分批。

### 模式四：批次轉換

觸發詞：「整個資料夾轉」「批次轉」

流程：
1. 掃描資料夾，列出所有可轉換的檔案
2. 若全是或主要是圖片，走「模式三：圖片轉寫」
3. 若是 MarkItDown 支援格式，告知使用者：共 N 個檔案，格式分布如何
4. 使用者確認後開始轉換（使用者已明確要求轉整個資料夾時，可直接做）
5. 逐一轉換，跳過已轉換的（檢查同名 .md 是否存在）
6. 產出轉換報告

用 convert.py 腳本：
```bash
/Users/jiangyude2/.local/pipx/venvs/markitdown/bin/python3 "/Users/jiangyude2/Library/Mobile Documents/iCloud~md~obsidian/Documents/江昱德 主知識庫/_agent/skills/file-to-markdown/scripts/convert.py" "/path/to/folder/" --batch
```

---

## 路由表

收到檔案時，依副檔名判斷交給誰處理：

| 副檔名 | 處理者 | 指令 / 路由 |
|--------|--------|------------|
| `.docx` | MarkItDown | `markitdown file.docx` |
| `.pptx` | MarkItDown | `markitdown file.pptx` |
| `.xlsx` `.xls` | MarkItDown | `markitdown file.xlsx` |
| `.epub` | MarkItDown | `markitdown file.epub` |
| `.zip` | MarkItDown | `markitdown file.zip`（遞迴解壓） |
| `.csv` | MarkItDown | `markitdown file.csv` |
| `.json` | MarkItDown | `markitdown file.json` |
| `.xml` | MarkItDown | `markitdown file.xml` |
| `.pdf` | 路由到 admin-assistant | 讀取 `pdf-to-markdown.md`，走 `extract_pdf.py` |
| `.jpg` `.jpeg` `.png` `.webp` `.heic` `.tif` `.tiff` | 圖片 OCR / Claude 多模態 | 直接讀圖轉寫成 Markdown；不要用 MarkItDown |
| `.mp3` `.wav` `.m4a` 等 | 路由到 local-speech-to-text | 讀取該技能包 SKILL.md |
| YouTube URL | 路由到 notebooklm-codex-ops | 讀取該技能包 SKILL.md |
| `.html` / 網址 | 路由到 admin-assistant | 讀取 `web-to-knowledge-graph.md` |

不認識的副檔名 → 告知使用者目前不支援，問要不要嘗試用 MarkItDown 跑看看。

---

## 環境依賴與安裝

### 已安裝

- MarkItDown v0.1.5（via pipx）
- Python 3.14.3（Homebrew）
- pipx（Homebrew）

### 關鍵路徑

| 用途 | 路徑 |
|------|------|
| MarkItDown CLI | `/Users/jiangyude2/.local/bin/markitdown` |
| MarkItDown venv Python | `/Users/jiangyude2/.local/pipx/venvs/markitdown/bin/python3` |
| convert.py 腳本 | `_agent/skills/file-to-markdown/scripts/convert.py` |

### 重新安裝指南（換機器時用）

```bash
# 1. 安裝 pipx
brew install pipx
pipx ensurepath

# 2. 安裝 MarkItDown（只裝需要的格式，不裝 API 相關的）
pipx install 'markitdown[docx,pptx,xlsx,xls]'

# 3. 驗證
markitdown --help
/Users/jiangyude2/.local/pipx/venvs/markitdown/bin/python3 -c "from markitdown import MarkItDown; print('OK')"
```

基礎套件自帶 CSV/JSON/XML/EPUB/ZIP 支援，不需要額外 extra。

### 不需要安裝的（已有替代方案）

- `markitdown[audio-transcription]` → 用 local-speech-to-text（本地 Whisper）
- `markitdown[youtube-transcription]` → 用 notebooklm-codex-ops
- `markitdown-ocr` plugin → 用 Claude 多模態 / extract_pdf.py
- `markitdown[az-doc-intel]` → 不需要 Azure

---

## 與其他技能包的關係

| 技能包 | 關係 |
|--------|------|
| admin-assistant | PDF 和網頁轉換仍由它負責，本技能包路由過去 |
| local-speech-to-text | 音訊轉文字由它負責，本技能包路由過去 |
| notebooklm-codex-ops | YouTube 字幕由它負責，本技能包路由過去 |
| content-organizer | 它做觀點報告，本技能包做格式轉換，互補 |
| personal-director-v90 | 標籤、檔名、看板操作走雷總管 |

---

## 版本紀錄

### v1.0（2026-04-13）
- 初版建立
- 整合微軟 MarkItDown v0.1.5
- 支援格式：DOCX、PPTX、XLSX/XLS、EPUB、ZIP、CSV/JSON/XML
- 三種模式：快速轉換、知識圖譜、批次轉換
- 統一路由表：MarkItDown + 既有工具各司其職
- convert.py 包裝腳本（批次 + 時間戳 + 來源資訊）

### v1.1（2026-04-25）
- 補上 JPG/PNG/WebP/HEIC/TIFF 圖片轉 Markdown 的明確路由
- 新增「圖片轉寫」模式：每張圖一份 Markdown，保留原圖連結、標題、段落、表格、條列與圖中文字
- 明定圖片不是 MarkItDown 任務；不要先測 Vision/Tesseract/Gemini 等不穩路線
- 批次資料夾若主要是圖片，直接走圖片 OCR / 多模態轉寫流程
