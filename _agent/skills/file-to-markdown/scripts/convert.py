#!/Users/jiangyude2/.local/pipx/venvs/markitdown/bin/python3
"""
檔案轉 Markdown 包裝腳本
整合微軟 MarkItDown，加上知識庫後處理邏輯。

用法：
    python3 convert.py /path/to/file.docx                     # 單檔
    python3 convert.py /path/to/folder/ --batch                # 批次
    python3 convert.py /path/to/file.pptx -o /path/output.md  # 指定輸出
    python3 convert.py /path/to/file.docx --no-header          # 不加來源資訊
"""

import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from markitdown import MarkItDown

# MarkItDown 直接處理的副檔名
SUPPORTED_EXTENSIONS = {
    '.docx', '.pptx', '.xlsx', '.xls',
    '.epub', '.zip',
    '.csv', '.json', '.xml'
}

# 路由到其他工具的副檔名（不處理，只提示）
ROUTED_EXTENSIONS = {
    '.pdf': 'admin-assistant（extract_pdf.py）',
    '.mp3': 'local-speech-to-text',
    '.wav': 'local-speech-to-text',
    '.m4a': 'local-speech-to-text',
    '.flac': 'local-speech-to-text',
    '.html': 'admin-assistant（web-to-knowledge-graph）',
    '.htm': 'admin-assistant（web-to-knowledge-graph）',
    '.jpg': 'Claude 多模態',
    '.jpeg': 'Claude 多模態',
    '.png': 'Claude 多模態',
    '.gif': 'Claude 多模態',
    '.webp': 'Claude 多模態',
}

# 台灣時區
TW_TZ = timezone(timedelta(hours=8))


def get_timestamp():
    """取得台灣時間戳 YYYY-MM-DD-HHMM"""
    now = datetime.now(TW_TZ)
    return now.strftime('%Y-%m-%d-%H%M')


def make_output_path(input_path: Path, output_dir: Path = None, timestamp: str = None):
    """
    產生輸出檔案路徑。
    格式：YYYY-MM-DD-HHMM 原始檔名.md
    """
    if timestamp is None:
        timestamp = get_timestamp()
    stem = input_path.stem
    out_name = f"{timestamp} {stem}.md"
    if output_dir:
        return output_dir / out_name
    return input_path.parent / out_name


def make_header(input_path: Path, timestamp: str):
    """產生來源資訊標頭"""
    return (
        f"> 來源：{input_path.name}\n"
        f"> 轉換時間：{timestamp[:10]} {timestamp[11:13]}:{timestamp[13:]}\n"
        f"> 轉換工具：MarkItDown\n\n"
    )


def convert_single(input_path: Path, output_path: Path = None, add_header: bool = True):
    """
    轉換單一檔案。
    回傳 (success: bool, output_path: Path, message: str)
    """
    ext = input_path.suffix.lower()

    # 檢查是否支援
    if ext not in SUPPORTED_EXTENSIONS:
        if ext in ROUTED_EXTENSIONS:
            return False, None, f"此格式請用 {ROUTED_EXTENSIONS[ext]} 處理"
        return False, None, f"不支援的格式：{ext}"

    # 檢查檔案存在
    if not input_path.exists():
        return False, None, f"檔案不存在：{input_path}"

    # 產生輸出路徑
    timestamp = get_timestamp()
    if output_path is None:
        output_path = make_output_path(input_path, timestamp=timestamp)

    # 檢查是否已轉換（斷點續傳）
    if output_path.exists():
        return False, output_path, f"已存在，跳過：{output_path.name}"

    # 轉換
    try:
        md = MarkItDown(enable_plugins=False)
        result = md.convert(str(input_path))

        content = ""
        if add_header:
            content += make_header(input_path, timestamp)
        content += result.text_content

        output_path.write_text(content, encoding='utf-8')
        return True, output_path, f"成功：{input_path.name} → {output_path.name}"

    except Exception as e:
        return False, None, f"失敗：{input_path.name}（{e}）"


def convert_batch(folder_path: Path, output_dir: Path = None, add_header: bool = True):
    """
    批次轉換資料夾裡的檔案。
    回傳轉換報告。
    """
    if output_dir is None:
        output_dir = folder_path

    # 掃描
    files = []
    routed = []
    unsupported = []

    for f in sorted(folder_path.iterdir()):
        if f.is_file():
            ext = f.suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                files.append(f)
            elif ext in ROUTED_EXTENSIONS:
                routed.append((f, ROUTED_EXTENSIONS[ext]))
            elif ext not in {'.md', '.txt', ''}:
                unsupported.append(f)

    # 轉換
    success = []
    skipped = []
    failed = []
    timestamp = get_timestamp()

    for f in files:
        out_path = make_output_path(f, output_dir, timestamp)
        ok, out, msg = convert_single(f, out_path, add_header)
        if ok:
            success.append(msg)
        elif out and out.exists():
            skipped.append(msg)
        else:
            failed.append(msg)

    # 報告
    report = []
    report.append("轉換報告")
    report.append("=" * 40)
    report.append(f"資料夾：{folder_path}")
    report.append(f"時間：{timestamp[:10]} {timestamp[11:13]}:{timestamp[13:]}")
    report.append(f"工具：MarkItDown")
    report.append("")

    report.append(f"成功：{len(success)} 個")
    for s in success:
        report.append(f"  - {s}")
    report.append("")

    if skipped:
        report.append(f"跳過（已存在）：{len(skipped)} 個")
        for s in skipped:
            report.append(f"  - {s}")
        report.append("")

    if failed:
        report.append(f"失敗：{len(failed)} 個")
        for s in failed:
            report.append(f"  - {s}")
        report.append("")

    if routed:
        report.append(f"路由到其他工具：{len(routed)} 個")
        for f, tool in routed:
            report.append(f"  - {f.name} → 建議用 {tool}")
        report.append("")

    if unsupported:
        report.append(f"不支援：{len(unsupported)} 個")
        for f in unsupported:
            report.append(f"  - {f.name}")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="檔案轉 Markdown — 整合微軟 MarkItDown"
    )
    parser.add_argument("input", help="檔案路徑或資料夾路徑")
    parser.add_argument("-o", "--output", help="輸出檔案路徑（單檔模式）", default=None)
    parser.add_argument("--batch", action="store_true", help="批次轉換資料夾")
    parser.add_argument("--no-header", action="store_true", help="不加來源資訊標頭")
    parser.add_argument("--output-dir", help="批次模式的輸出資料夾", default=None)

    args = parser.parse_args()
    input_path = Path(args.input).resolve()

    if args.batch or input_path.is_dir():
        if not input_path.is_dir():
            print(f"錯誤：{input_path} 不是資料夾", file=sys.stderr)
            sys.exit(1)
        output_dir = Path(args.output_dir).resolve() if args.output_dir else None
        report = convert_batch(input_path, output_dir, not args.no_header)
        print(report)
    else:
        output_path = Path(args.output).resolve() if args.output else None
        ok, out, msg = convert_single(input_path, output_path, not args.no_header)
        print(msg)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
