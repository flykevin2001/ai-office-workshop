param(
    [string]$BasePath = (Split-Path -Parent $PSScriptRoot),
    [datetime]$Date = (Get-Date).Date,
    [string]$PythonPath = "C:\Users\Kevin1.wang\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

$ErrorActionPreference = "Stop"

$culture = [System.Globalization.CultureInfo]::InvariantCulture
$calendar = $culture.Calendar
$weekNumber = $calendar.GetWeekOfYear($Date, [System.Globalization.CalendarWeekRule]::FirstFourDayWeek, [DayOfWeek]::Monday)
$weekId = "{0}-W{1:D2}" -f $Date.Year, $weekNumber
$daysSinceMonday = ([int]$Date.DayOfWeek + 6) % 7
$startDate = $Date.AddDays(-$daysSinceMonday).Date
$endDate = $startDate.AddDays(6)

$weeklyDir = Join-Path (Join-Path $BasePath "03_週報") $weekId
New-Item -ItemType Directory -Path $weeklyDir -Force | Out-Null

$projectsRoot = Join-Path $BasePath "01_專案"
$dailyRoot = Join-Path $BasePath "02_每日紀錄"

function Get-FieldValue {
    param([string[]]$Lines, [string]$Name)
    $pattern = "^- " + [regex]::Escape($Name) + "：(.+)$"
    foreach ($line in $Lines) {
        if ($line -match $pattern) { return $Matches[1].Trim() }
    }
    return ""
}

function Get-SectionBullets {
    param([string[]]$Lines, [string]$Heading)
    $inSection = $false
    $items = @()
    foreach ($line in $Lines) {
        if ($line -eq "## $Heading") {
            $inSection = $true
            continue
        }
        if ($inSection -and $line -match "^## ") { break }
        if ($inSection -and $line -match "^- ") {
            $items += (($line -replace "^- ", "").Trim())
        }
    }
    return $items
}

$dailyFiles = @()
if (Test-Path -LiteralPath $dailyRoot) {
    $dailyFiles = Get-ChildItem -LiteralPath $dailyRoot -Filter "*.md" | Where-Object {
        if ($_.BaseName -match "^\d{4}-\d{2}-\d{2}$") {
            $d = [datetime]::ParseExact($_.BaseName, "yyyy-MM-dd", $null)
            return $d -ge $startDate -and $d -le $endDate
        }
        return $false
    }
}

$lines = @()
$lines += "# 週報：$weekId"
$lines += ""
$lines += "期間：$($startDate.ToString('yyyy-MM-dd')) ~ $($endDate.ToString('yyyy-MM-dd'))"
$lines += ""
$lines += "## 一、本週總結"
$lines += ""
if ($dailyFiles.Count -eq 0) {
    $lines += "- 本週尚無每日紀錄。"
} else {
    $lines += "- 本週共有 $($dailyFiles.Count) 份每日紀錄，請依正式週報口吻整理重點。"
}
$lines += ""
$lines += "## 二、專案進度"
$lines += ""
$lines += "| 專案 | 狀態 | 優先級 | 目前進度 | 下一步 |"
$lines += "|---|---|---|---|---|"

foreach ($projectDir in Get-ChildItem -LiteralPath $projectsRoot -Directory) {
    $statusPath = Join-Path $projectDir.FullName "專案狀態.md"
    if (!(Test-Path -LiteralPath $statusPath)) { continue }
    $content = Get-Content -LiteralPath $statusPath -Encoding UTF8
    $state = Get-FieldValue -Lines $content -Name "狀態"
    $priority = Get-FieldValue -Lines $content -Name "優先級"
    $projectId = Get-FieldValue -Lines $content -Name "專案ID"
    $name = $projectDir.Name
    if ($name -match "^[^_]+_(.+)$") { $name = $Matches[1] }
    $progressItems = @(Get-SectionBullets -Lines $content -Heading "目前進度")
    $nextItems = @(Get-SectionBullets -Lines $content -Heading "下一步")
    $progress = if ($progressItems.Count -gt 0) { $progressItems -join "；" } else { "未填寫" }
    $next = if ($nextItems.Count -gt 0) { $nextItems -join "；" } else { "未填寫" }
    $lines += "| $projectId $name | $state | $priority | $progress | $next |"
}

$lines += ""
$lines += "## 三、本週完成事項"
$lines += ""
$completed = @()
foreach ($todoPath in Get-ChildItem -LiteralPath $projectsRoot -Recurse -Filter "待辦事項.md") {
    $completed += Get-Content -LiteralPath $todoPath.FullName -Encoding UTF8 | Where-Object {
        if ($_ -notmatch "^\s*- \[x\] " -or $_ -notmatch "done:(\d{4}-\d{2}-\d{2})") { return $false }
        $doneDate = [datetime]::ParseExact($Matches[1], "yyyy-MM-dd", $null)
        return $doneDate -ge $startDate -and $doneDate -le $endDate
    }
}
if ($completed.Count -eq 0) { $lines += "- 本週尚無已完成任務。" } else { $lines += $completed }

$lines += ""
$lines += "## 四、目前阻礙與風險"
$lines += ""
foreach ($importantPath in Get-ChildItem -LiteralPath $projectsRoot -Recurse -Filter "重要事項.md") {
    $projectName = Split-Path -Leaf (Split-Path -Parent $importantPath.FullName)
    $importantContent = Get-Content -LiteralPath $importantPath.FullName -Encoding UTF8
    $riskLines = @(Get-SectionBullets -Lines $importantContent -Heading "風險")
    foreach ($risk in $riskLines) { $lines += "- $projectName：$risk" }
}

$lines += ""
$lines += "## 五、下週工作安排"
$lines += ""
foreach ($projectDir in Get-ChildItem -LiteralPath $projectsRoot -Directory) {
    $statusPath = Join-Path $projectDir.FullName "專案狀態.md"
    if (!(Test-Path -LiteralPath $statusPath)) { continue }
    $content = Get-Content -LiteralPath $statusPath -Encoding UTF8
    $projectId = Get-FieldValue -Lines $content -Name "專案ID"
    $nextItems = @(Get-SectionBullets -Lines $content -Heading "下一步")
    foreach ($item in $nextItems) { $lines += "- $projectId：$item" }
}

$lines += ""
$lines += "## 六、待主管/窗口確認"
$lines += ""
$waitingItems = @()
foreach ($importantPath in Get-ChildItem -LiteralPath $projectsRoot -Recurse -Filter "重要事項.md") {
    $projectName = Split-Path -Leaf (Split-Path -Parent $importantPath.FullName)
    $importantContent = Get-Content -LiteralPath $importantPath.FullName -Encoding UTF8
    foreach ($item in @(Get-SectionBullets -Lines $importantContent -Heading "等待他人")) {
        if ($item -ne "無") { $waitingItems += "- $projectName：$item" }
    }
}
if ($waitingItems.Count -eq 0) { $lines += "- 無" } else { $lines += $waitingItems }

$mdPath = Join-Path $weeklyDir "$weekId`_週報.md"
Set-Content -LiteralPath $mdPath -Value $lines -Encoding UTF8

$docxPath = Join-Path $weeklyDir "$weekId`_週報.docx"
$pdfPath = Join-Path $weeklyDir "$weekId`_週報.pdf"
$pandoc = Get-Command pandoc -ErrorAction SilentlyContinue
$outputs = @("Markdown")

if ($pandoc) {
    & $pandoc.Source $mdPath -o $docxPath
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $docxPath)) { $outputs += "DOCX" }

    $pdfExitCode = 1
    $oldErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $pandoc.Source $mdPath -o $pdfPath 2>$null
        $pdfExitCode = $LASTEXITCODE
    } catch {
        $pdfExitCode = 1
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
    if ($pdfExitCode -eq 0 -and (Test-Path -LiteralPath $pdfPath)) {
        $outputs += "PDF"
    } elseif (Test-Path -LiteralPath $PythonPath) {
        $fallback = Join-Path $PSScriptRoot "markdown_to_pdf.py"
        & $PythonPath $fallback $mdPath $pdfPath
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $pdfPath)) { $outputs += "PDF" }
    }
} elseif (Test-Path -LiteralPath $PythonPath) {
    $fallback = Join-Path $PSScriptRoot "markdown_to_pdf.py"
    & $PythonPath $fallback $mdPath $pdfPath
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $pdfPath)) { $outputs += "PDF" }
}

Write-Host ("Exported " + ($outputs -join ", ") + " to " + $weeklyDir)
