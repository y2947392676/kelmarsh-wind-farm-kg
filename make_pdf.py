"""Render TASK1_REPORT.md to TASK1_REPORT.pdf (A4, black and white, 11 pt) via headless Edge/Chrome.

Usage:  python make_pdf.py
(The side-by-side English | Chinese version is made by make_bilingual_pdf.py.)
"""
import html
import re
import shutil
import subprocess
from pathlib import Path

import fitz  # PyMuPDF, only to read back page numbers for the contents
import markdown

ROOT = Path(__file__).resolve().parent
SRC, HTML, PDF = ROOT / "TASK1_REPORT.md", ROOT / "TASK1_REPORT.html", ROOT / "TASK1_REPORT.pdf"

# Layout after SPbPU / GOST 7.32 practice: margins 20/15/20/30 mm, justified text with 1 cm
# first-line indent, numbered headings, "Table N –" captions above tables, "Figure N –" below
# figures, page numbers at the bottom centre.
CSS = """
@page { size: A4; margin: 20mm 15mm 20mm 30mm;
        @bottom-center { content: counter(page); font-family: "Times New Roman", serif; font-size: 10pt; } }
body { font-family: "Times New Roman", Times, serif; font-size: 12pt; line-height: 1.3; color: #000; }
.head { text-align: center; font-size: 11pt; margin-bottom: 10pt; }
.head p { margin: 0; text-indent: 0; text-align: center; }
h1 { font-size: 14pt; text-align: center; margin: 4pt 0 4pt; }
p.sub { text-align: center; text-indent: 0; margin: 0 0 12pt; }
h2 { font-size: 13pt; margin: 14pt 0 5pt; page-break-after: avoid; }
h3 { font-size: 12pt; margin: 9pt 0 4pt; page-break-after: avoid; }
p { margin: 0 0 4pt; text-align: justify; text-indent: 1cm; }
li { margin: 2pt 0; text-align: justify; }
ol, ul { margin: 2pt 0 4pt; padding-left: 1.6cm; }
p.cap { text-indent: 0; text-align: left; margin: 8pt 0 2pt; page-break-after: avoid; }
img + p.cap, p:has(img) + p.cap { text-align: center; margin: 2pt 0 10pt; }
table { border-collapse: collapse; margin: 0 0 8pt; font-size: 10.5pt; width: 100%; page-break-inside: avoid; }
th, td { border: 0.6pt solid #000; padding: 2pt 5pt; text-align: left; vertical-align: top; }
th { font-weight: bold; text-align: center; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.5pt; }
pre { border: 0.6pt solid #000; padding: 4pt 6pt; font-size: 9.5pt; white-space: pre-wrap; }
p:has(img) { text-indent: 0; }
img { display: block; margin: 6pt auto 0; page-break-inside: avoid; }
img[alt="Schema"] { width: 66%; }
img[alt="Q3 window"] { width: 78%; }
"""


def print_pdf(html: Path, pdf: Path):
    browser = next(p for p in [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        shutil.which("msedge") or "", shutil.which("chrome") or ""] if p and Path(p).exists())
    subprocess.run([browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", html.as_uri()], check=True, timeout=120)


TOC_MARK = "<!-- contents -->"
TOC_CSS = """
.toc { break-after: page; }
.toc h2 { text-align: center; margin-top: 6pt; }
.tl { display: flex; align-items: flex-end; margin: 2pt 0; }
.tl span:first-child { max-width: 88%; }
.tl .dots { margin-bottom: 4pt !important; }
.tl.l3 { padding-left: 1cm; }
.tl .dots { flex: 1; border-bottom: 0.8pt dotted #000; margin: 0 4pt; }
"""


def headings(md: str) -> list[tuple[int, str]]:
    """(level, text) of every ## and ### heading, in order."""
    return [(len(m.group(1)), m.group(2).strip())
            for m in re.finditer(r"^(#{2,3}) (.+)$", md, flags=re.M)]


def toc_html(heads, pages, title) -> str:
    rows = "".join(f"<div class='tl l{lvl}'><span>{html.escape(t)}</span><span class='dots'></span>"
                   f"<span>{pg}</span></div>" for (lvl, t), pg in zip(heads, pages))
    return f"<div class='toc'><h2>{title}</h2>{rows}</div>"


def heading_pages(pdf: Path, heads) -> list[int]:
    """Page of each heading: its second occurrence in the PDF text (the first is the contents)."""
    norm = lambda s: re.sub(r"\s+", "", s)
    doc = fitz.open(pdf)
    texts = [norm(p.get_text()) for p in doc]
    starts, pos = [], 0
    for t in texts:
        starts.append(pos)
        pos += len(t)
    full, pages, cur = "".join(texts), [], 0
    for _, h in heads:
        first = full.find(norm(h), cur)
        hit = full.find(norm(h), first + 1)
        if first < 0 or hit < 0:
            raise SystemExit(f"heading not found in PDF: {h}")
        pages.append(max(i for i, s in enumerate(starts) if s <= hit) + 1)
        cur = first + 1
    doc.close()
    return pages


def build_with_contents(render, heads, pdf: Path, html_path: Path):
    """render(pages) -> html text. Re-render until the contents page numbers are stable."""
    pages = ["–"] * len(heads)
    for _ in range(4):
        html_path.write_text(render(pages), encoding="utf-8")
        print_pdf(html_path, pdf)
        new = heading_pages(pdf, heads)
        if new == pages:
            return
        pages = new
    raise SystemExit("contents page numbers did not settle")


def main():
    md = SRC.read_text(encoding="utf-8")
    heads = headings(md)
    body = markdown.markdown(md, extensions=["tables", "fenced_code"])

    def render(pages):
        return (f"<!doctype html><html><head><meta charset='utf-8'><title>Task 1 Report</title>"
                f"<style>{CSS}{TOC_CSS}</style></head><body>"
                f"{body.replace(TOC_MARK, toc_html(heads, pages, 'Contents'))}</body></html>")

    build_with_contents(render, heads, PDF, HTML)
    print("saved", PDF)


if __name__ == "__main__":
    main()
