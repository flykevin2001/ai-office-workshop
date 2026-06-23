param(
    [string]$BasePath = (Split-Path -Parent $PSScriptRoot),
    [datetime]$Today = (Get-Date).Date
)

$ErrorActionPreference = "Stop"

function Get-FieldValue {
    param([string[]]$Lines, [string]$Name)
    $pattern = "^- " + [regex]::Escape($Name) + "：(.+)$"
    foreach ($line in $Lines) {
        if ($line -match $pattern) { return $Matches[1].Trim() }
    }
    return ""
}

function Get-PriorityScore {
    param([string]$Priority)
    switch ($Priority) {
        "高" { 3 }
        "中" { 2 }
        "低" { 1 }
        default { 0 }
    }
}

function Get-TaskPriority {
    param([string]$Task)
    if ($Task -match "priority:(高|中|低)") { return $Matches[1] }
    return "中"
}

function Get-TaskDueDate {
    param([string]$Task)
    if ($Task -match "due:(\d{4}-\d{2}-\d{2})") {
        return [datetime]::ParseExact($Matches[1], "yyyy-MM-dd", $null)
    }
    return $null
}

$projectsRoot = Join-Path $BasePath "01_專案"
$dashboardDir = Join-Path $BasePath "00_今日工作"
New-Item -ItemType Directory -Path $dashboardDir -Force | Out-Null

$projects = @()
foreach ($projectDir in Get-ChildItem -LiteralPath $projectsRoot -Directory) {
    $statusPath = Join-Path $projectDir.FullName "專案狀態.md"
    $todoPath = Join-Path $projectDir.FullName "待辦事項.md"
    if (!(Test-Path -LiteralPath $statusPath) -or !(Test-Path -LiteralPath $todoPath)) { continue }

    $statusLines = Get-Content -LiteralPath $statusPath -Encoding UTF8
    $todoLines = Get-Content -LiteralPath $todoPath -Encoding UTF8
    $projectId = Get-FieldValue -Lines $statusLines -Name "專案ID"
    $state = Get-FieldValue -Lines $statusLines -Name "狀態"
    $priority = Get-FieldValue -Lines $statusLines -Name "優先級"
    $lastUpdatedText = Get-FieldValue -Lines $statusLines -Name "最後更新日期"
    $lastUpdated = $null
    if ($lastUpdatedText -match "^\d{4}-\d{2}-\d{2}$") {
        $lastUpdated = [datetime]::ParseExact($lastUpdatedText, "yyyy-MM-dd", $null)
    }

    $projectName = $projectDir.Name
    if ($projectName -match "^[^_]+_(.+)$") { $projectName = $Matches[1] }

    $openTasks = @($todoLines | Where-Object { $_ -match "^\s*- \[ \] " })
    $overdue = 0
    $dueToday = 0
    $high = 0
    $medium = 0
    $low = 0
    foreach ($task in $openTasks) {
        switch (Get-TaskPriority $task) {
            "高" { $high++ }
            "中" { $medium++ }
            "低" { $low++ }
        }
        $due = Get-TaskDueDate $task
        if ($null -ne $due) {
            if ($due.Date -lt $Today) { $overdue++ }
            elseif ($due.Date -eq $Today) { $dueToday++ }
        }
    }

    $staleDays = 9999
    if ($null -ne $lastUpdated) { $staleDays = [int]($Today - $lastUpdated.Date).TotalDays }

    $projects += [pscustomobject]@{
        Id = $projectId
        Name = $projectName
        FolderName = $projectDir.Name
        State = $state
        Priority = $priority
        PriorityScore = Get-PriorityScore $priority
        LastUpdated = $lastUpdatedText
        StaleDays = $staleDays
        OpenTasks = $openTasks
        OpenCount = $openTasks.Count
        Overdue = $overdue
        DueToday = $dueToday
        High = $high
        Medium = $medium
        Low = $low
    }
}

$sorted = $projects | Sort-Object `
    @{ Expression = "Overdue"; Descending = $true },
    @{ Expression = "DueToday"; Descending = $true },
    @{ Expression = "PriorityScore"; Descending = $true },
    @{ Expression = "StaleDays"; Descending = $true },
    @{ Expression = "OpenCount"; Descending = $true }

$dateText = $Today.ToString("yyyy-MM-dd")
$todayLines = @()
$todayLines += "# 今日工作"
$todayLines += ""
$todayLines += "日期：$dateText"
$todayLines += ""
$todayLines += "## 今日優先順序"
$todayLines += ""
$todayLines += "| 排名 | 專案 | 狀態 | 優先級 | 逾期 | 今日到期 | 未完成 | 最後更新 | 今日建議 |"
$todayLines += "|---:|---|---|---|---:|---:|---:|---|---|"
$rank = 1
foreach ($project in $sorted) {
    $suggestion = "檢查下一步並更新專案狀態。"
    if ($project.Overdue -gt 0) { $suggestion = "先處理逾期待辦，再安排今日到期事項。" }
    elseif ($project.DueToday -gt 0) { $suggestion = "先完成今日到期待辦。" }
    elseif ($project.StaleDays -ge 3) { $suggestion = "先更新專案狀態，避免資料過期。" }
    $todayLines += "| $rank | $($project.Id) $($project.Name) | $($project.State) | $($project.Priority) | $($project.Overdue) | $($project.DueToday) | $($project.OpenCount) | $($project.LastUpdated) | $suggestion |"
    $rank++
}
$todayLines += ""
$todayLines += "## 今天要完成"
$todayLines += ""
$todayTasks = @()
foreach ($project in $sorted) {
    foreach ($task in $project.OpenTasks) {
        $due = Get-TaskDueDate $task
        if ($null -ne $due -and $due.Date -le $Today) { $todayTasks += $task }
    }
}
if ($todayTasks.Count -eq 0) {
    $todayLines += "- 無今日到期或逾期待辦。"
} else {
    $todayLines += $todayTasks
}
$todayLines += ""
$todayLines += "## 待歸檔"
$todayLines += ""
$todayLines += "- 無"

Set-Content -LiteralPath (Join-Path $dashboardDir "今日工作.md") -Value $todayLines -Encoding UTF8

$summaryLines = @()
$summaryLines += "# 任務總表"
$summaryLines += ""
$summaryLines += "更新時間：$dateText"
$summaryLines += ""
$summaryLines += "| 專案 | 未完成 | 逾期 | 今日到期 | 高優先 | 中優先 | 低優先 |"
$summaryLines += "|---|---:|---:|---:|---:|---:|---:|"
foreach ($project in $sorted) {
    $summaryLines += "| $($project.Id) $($project.Name) | $($project.OpenCount) | $($project.Overdue) | $($project.DueToday) | $($project.High) | $($project.Medium) | $($project.Low) |"
}
Set-Content -LiteralPath (Join-Path $dashboardDir "任務總表.md") -Value $summaryLines -Encoding UTF8

Write-Host "Updated dashboard for $($sorted.Count) projects at $dashboardDir"

