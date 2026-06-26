# Phase 2B 安裝前安全評估

本檔案用於 Pi / DeepSeek 安裝前評估。Phase 2B 不安裝 Pi、不串接 DeepSeek、不讀寫正式 `工作助理`。

## 目前狀態

- PR：`https://github.com/Jiang-Yude/ai-office-workshop/pull/1`
- PR 狀態：OPEN，尚未合併到正式 `main`
- 沙盒分支：`flykevin2001:codex/pi-deepseek-sandbox`
- DeepSeek：`pending_test`
- Pi：`pending_test`
- 正式資料權限：不允許

## 第二台電腦取得沙盒

### PR 已合併時

在第二台 AI Office repo 執行：

```powershell
git pull --ff-only origin main
```

確認存在：

```text
工作助理_Pi_Test/
```

### PR 尚未合併時

不要切換或污染第二台正式 `main`。使用獨立 worktree：

```powershell
git fetch https://github.com/flykevin2001/ai-office-workshop.git codex/pi-deepseek-sandbox
git worktree add "..\AI Office_Pi_Test_PR" FETCH_HEAD
```

只在 `..\AI Office_Pi_Test_PR\工作助理_Pi_Test` 測試。

## 安裝前檢查結果

- [ ] 已確認第二台可取得 `工作助理_Pi_Test`。
- [ ] 已確認測試只在 `工作助理_Pi_Test` 或 `AI Office_Pi_Test_PR` 內執行。
- [ ] 已確認不讀取正式 `工作助理`。
- [ ] 已確認不讀取 OneDrive 其他資料夾。
- [ ] 已確認不輸入 DeepSeek API key。
- [ ] 已確認不保存 API key、token、密碼到 Git、OneDrive 或工作助理資料夾。
- [ ] 已確認 Pi 官方來源、下載網址、權限需求與卸載方式。
- [ ] 已確認 Pi 能限制工作目錄到沙盒；若不能，禁止安裝或禁止連正式資料。
- [ ] 已確認重複整理 `已整理` 每日紀錄時，不會重複追加同一批內容。

## 安全結論

在 Pi 官方來源、工作目錄限制能力、DeepSeek API key 保存方式都確認前，結論維持：

```text
Do not install Pi.
Do not connect DeepSeek.
Do not grant production data access.
```

## 進入 Phase 2C 條件

- Kevin 已提供或確認 Pi 官方來源。
- DeepSeek 帳號/API key 已準備好，但只存放於安全位置，不進 Git 或 OneDrive。
- 第二台與第一台都能取得相同沙盒資料。
- 沙盒重複整理測試通過。
- Kevin 明確批准進入實機試跑。
