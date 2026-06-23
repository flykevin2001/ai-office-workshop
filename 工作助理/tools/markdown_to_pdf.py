# -*- coding: utf-8 -*-
"""Simple Markdown-to-PDF fallback for weekly reports."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def register_cjk_font() -> str:
    candidates = [
        Path(r"C:\Windows\Fonts\msjh.ttc"),
        Path(r"C:\Windows\Fonts\msjh.ttf"),
        Path(r"C:\Windows\Fonts\mingliu.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]
    for font_path in candidates:
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("CJK", str(font_path)))
                return "CJK"
            except Exception:
                continue
    return "Helvetica"


def clean_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def table_from_lines(lines: list[str], font_name: str) -> Table | None:
    rows = []
    for line in lines:
        cells = [clean_inline(cell.strip()) for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return None
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def markdown_to_story(markdown: str, font_name: str):
    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "CJKBase",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=15,
        spaceAfter=4,
    )
    h1 = ParagraphStyle("CJKH1", parent=base, fontSize=18, leading=24, spaceBefore=8, spaceAfter=10)
    h2 = ParagraphStyle("CJKH2", parent=base, fontSize=14, leading=20, spaceBefore=8, spaceAfter=6)
    bullet = ParagraphStyle("CJKBullet", parent=base, leftIndent=12, firstLineIndent=-8)

    story = []
    table_buffer: list[str] = []

    def flush_table():
        nonlocal table_buffer
        if table_buffer:
            table = table_from_lines(table_buffer, font_name)
            if table is not None:
                story.append(table)
                story.append(Spacer(1, 4))
            table_buffer = []

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("|") and line.endswith("|"):
            table_buffer.append(line)
            continue
        flush_table()
        if not line.strip():
            story.append(Spacer(1, 4))
        elif line.startswith("# "):
            story.append(Paragraph(clean_inline(line[2:].strip()), h1))
        elif line.startswith("## "):
            story.append(Paragraph(clean_inline(line[3:].strip()), h2))
        elif line.startswith("- "):
            story.append(Paragraph("• " + clean_inline(line[2:].strip()), bullet))
        else:
            story.append(Paragraph(clean_inline(line), base))
    flush_table()
    return story


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: markdown_to_pdf.py input.md output.pdf", file=sys.stderr)
        return 2
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    font_name = register_cjk_font()
    markdown = input_path.read_text(encoding="utf-8-sig")
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    doc.build(markdown_to_story(markdown, font_name))
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

