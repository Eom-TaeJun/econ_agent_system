#!/usr/bin/env python3
from __future__ import annotations

import io
import re
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


ROOT = Path("/home/tj/projects/economics")
IMAGE_PDF = ROOT / "KB_mock_screenshots_upload_ready.pdf"
OCR_PDF = ROOT / "KB_mock_screenshots_upload_ready (1).pdf"

OUT_VISUAL_PDF = ROOT / "KB_mock_screenshots_upload_ready_no_watermark.pdf"
OUT_MD = ROOT / "KB_mock_screenshots_upload_ready_ocr_clean.md"
OUT_TXT = ROOT / "KB_mock_screenshots_upload_ready_ocr_clean.txt"


WATERMARK_PATTERNS = [
    re.compile(r"K\s*Y\s*O\s*B\s*O", re.IGNORECASE),
    re.compile(r"K\s*Y\s*O\s*B", re.IGNORECASE),
    re.compile(r"[A-Za-z]*e?B[o03]{1,2}k", re.IGNORECASE),
    re.compile(r"[A-Za-z]*eB[o0]3", re.IGNORECASE),
    re.compile(r"B[o0]{2,}", re.IGNORECASE),
    re.compile(r"\bB[o0]{1,3}(?=\d|\b)", re.IGNORECASE),
    re.compile(r"\bB[O0]B[O0]{1,2}", re.IGNORECASE),
    re.compile(r"\bY?O?B[O0]\b", re.IGNORECASE),
    re.compile(r"\bO[o0]k\b", re.IGNORECASE),
    re.compile(r"\b[0-9]{0,2}[o0]{1,2}[Kk]\b"),
    re.compile(r"\b6223\s*1504\s*824\b"),
    re.compile(r"\b6223\s*1504\b"),
    re.compile(r"622315\d*"),
    re.compile(r"\d{0,3}1504824"),
    re.compile(r"22315048[-0-9]*"),
    re.compile(r"\b15048\b"),
    re.compile(r"\b504824\b"),
    re.compile(r"\b6222(?=\S*융기관)"),
    re.compile(r"\b26\.0?4\.2\d{0,2}\b"),
    re.compile(r"\b26\.0?4\.\s*"),
    re.compile(r"\b6\.04\.20\b"),
]

DROP_LINE_PATTERNS = [
    re.compile(r"^\s*26\.?\s*$"),
    re.compile(r"^\s*\d{1,2}/\d{1,2}\s*$"),
    re.compile(r"^\s*KB국민은행\s*필기전형\s*$"),
    re.compile(r"^\s*제\d+회\s*모의고사\s*$"),
    re.compile(r"^\s*파본은\s*구입처.*$"),
]


def normalize_line(line: str) -> str:
    line = line.replace("\u00a0", " ")
    for pattern in WATERMARK_PATTERNS:
        line = pattern.sub("", line)

    line = re.sub(r"\s+", " ", line).strip()
    line = re.sub(r"^[\-–|·•]\s*$", "", line)
    line = re.sub(r"\s+([,.?])", r"\1", line)
    return line


def clean_page_text(text: str) -> list[str]:
    lines: list[str] = []
    previous = ""

    for raw_line in text.splitlines():
        line = normalize_line(raw_line)
        if not line:
            continue
        if "출판물의 무단복제" in line or "저작권법" in line:
            continue
        if any(pattern.match(line) for pattern in DROP_LINE_PATTERNS):
            continue
        if line == previous:
            continue

        if re.match(r"^\d{2}\s+", line) and lines and lines[-1] != "":
            lines.append("")
        lines.append(line)
        previous = line

    while lines and lines[-1] == "":
        lines.pop()
    return lines


def clean_ocr_pdf() -> str:
    doc = fitz.open(OCR_PDF)
    chunks: list[str] = [
        "# KB mock screenshots OCR clean",
        "",
        f"- Source: `{OCR_PDF.name}`",
        "- Removed: viewer watermark text, buyer/date stamps, repeated exam footers.",
        "- Format: page-separated Markdown for search and LLM study.",
        "",
    ]
    txt_chunks: list[str] = []

    for page_index, page in enumerate(doc, start=1):
        lines = clean_page_text(page.get_text("text"))
        if not lines:
            continue

        page_block = "\n".join(lines)
        chunks.extend([f"## OCR page {page_index}", "", page_block, ""])
        txt_chunks.extend([f"[OCR page {page_index}]", page_block, ""])

    markdown = "\n".join(chunks).rstrip() + "\n"
    text = "\n".join(txt_chunks).rstrip() + "\n"
    OUT_MD.write_text(markdown, encoding="utf-8")
    OUT_TXT.write_text(text, encoding="utf-8")
    return f"{len(doc)} OCR pages -> {OUT_MD.name}, {OUT_TXT.name}"


def clean_visual_pdf(threshold: int = 180, zoom: float = 2.0) -> str:
    src = fitz.open(IMAGE_PDF)
    out = fitz.open()
    matrix = fitz.Matrix(zoom, zoom)

    for page in src:
        pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csGRAY, alpha=False)
        image = Image.frombytes("L", (pix.width, pix.height), pix.samples)
        gray = np.asarray(image)
        cleaned = np.where(gray > threshold, 255, 0).astype(np.uint8)

        buf = io.BytesIO()
        Image.fromarray(cleaned, mode="L").save(buf, format="PNG", optimize=True)

        new_page = out.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(page.rect, stream=buf.getvalue())

    out.save(OUT_VISUAL_PDF, garbage=4, deflate=True)
    return f"{len(src)} rendered pages -> {OUT_VISUAL_PDF.name}"


def main() -> None:
    print(clean_ocr_pdf())
    print(clean_visual_pdf())


if __name__ == "__main__":
    main()
