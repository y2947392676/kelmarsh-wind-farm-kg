"""Side-by-side English | Chinese version of the Task 1 report (landscape A3, rows aligned).

Every paragraph, heading, table, figure and list item of TASK1_REPORT.md is paired with the
block at the same position in TASK1_REPORT_ZH.md and printed in one row, so the Chinese text
starts at the same height as the English text.

Usage:  python make_bilingual_pdf.py   ->  TASK1_REPORT_EN_ZH.pdf
"""
import re

import markdown

from make_pdf import (CSS, ROOT, TOC_CSS, TOC_MARK, anchor_headings, build_with_contents, headings,
                      toc_html)

EN, ZH = ROOT / "TASK1_REPORT.md", ROOT / "TASK1_REPORT_ZH.md"
HTML, PDF = ROOT / "TASK1_REPORT_EN_ZH.html", ROOT / "TASK1_REPORT_EN_ZH.pdf"

EXTRA = """
@page { size: 420mm 297mm; margin: 14mm 16mm; }
table.pair { width: 100%; border: none; margin: 0; table-layout: fixed; page-break-inside: auto; }
table.pair > tbody > tr > td { border: none; padding: 0 0 0 0; width: 50%; vertical-align: top; }
table.pair > tbody > tr > td.en { padding-right: 9mm; border-right: 0.4pt solid #888; }
table.pair > tbody > tr > td.zh { padding-left: 9mm; }
table.pair > tbody > tr { page-break-inside: avoid; }
td.zh { font-family: "Times New Roman", SimSun, serif; font-size: 11.5pt; line-height: 1.42; }
table.pair td.en, table.pair td.zh { text-align: justify; }
td.zh strong, td.zh h1, td.zh h2, td.zh th { font-family: "Times New Roman", SimHei, sans-serif; font-weight: normal; }
td ul { margin: 1pt 0; }
td.lvl1 ul { padding-left: 36pt; list-style-type: circle; }
td .toc { break-after: auto; }  /* the page break after the contents comes from the div below */
img[alt="Schema"] { width: 78%; }
img[alt="Q3 window"] { width: 85%; }
"""


def blocks(text: str) -> list[tuple[int, str]]:
    """Split markdown at blank lines; split lists further into one block per item."""
    out = []
    for blk in re.split(r"\n\s*\n", text.strip()):
        if blk.startswith("```") or not blk.lstrip().startswith("- "):
            out.append((0, blk))
            continue
        for line in blk.splitlines():
            m = re.match(r"( *)- (.*)", line)
            if m:
                out.append((len(m.group(1)) // 2, "- " + m.group(2)))
            else:  # continuation line of the current item
                lvl, cur = out[-1]
                out[-1] = (lvl, cur + " " + line.strip())
    return out


def render(md: str) -> str:
    return markdown.markdown(md, extensions=["tables", "fenced_code"])


def main():
    en_md, zh_md = EN.read_text(encoding="utf-8"), ZH.read_text(encoding="utf-8")
    en_heads, zh_heads = headings(en_md), headings(zh_md)
    if len(en_heads) != len(zh_heads):
        raise SystemExit("English and Chinese headings differ in number")
    # the title block goes above the contents; everything else follows on the next page
    en_head, en_rest = en_md.split(TOC_MARK)
    zh_head, zh_rest = zh_md.split(TOC_MARK)
    top = pair_rows(blocks(en_head), blocks(zh_head))
    body = pair_rows(blocks(en_rest), blocks(zh_rest))
    # heading anchors: headings in the English column get en-n, in the Chinese column zh-n
    en_n = zh_n = 1
    parts, body, side = re.split(r"(<td class='(?:en|zh)(?: lvl1)?'>)", body), "", None
    for p in parts:
        if p.startswith("<td class='en"):
            side = "en"
        elif p.startswith("<td class='zh"):
            side = "zh"
        elif side == "en":
            p, en_n = anchor_headings(p, "en", en_n)
        elif side == "zh":
            p, zh_n = anchor_headings(p, "zh", zh_n)
        body += p

    def render(pages):
        toc = (f"<tr><td class='en'>{toc_html(en_heads, pages, 'Contents', 'en')}</td>"
               f"<td class='zh'>{toc_html(zh_heads, pages, '目录', 'zh')}</td></tr>")
        return ("<!doctype html><html><head><meta charset='utf-8'><title>Task 1 Report EN-ZH</title>"
                f"<style>{CSS}{TOC_CSS}{EXTRA}</style></head><body>"
                f"<table class='pair'><tbody>{top}{toc}</tbody></table>"
                "<div style='break-after: page'></div>"
                f"<table class='pair'><tbody>{body}</tbody></table></body></html>")

    build_with_contents(render, en_heads, PDF, HTML)
    print(f"saved {PDF}")


def pair_rows(en, zh) -> str:
    if len(en) != len(zh):
        raise SystemExit(f"block count differs: English {len(en)}, Chinese {len(zh)}")
    rows = []
    for i, ((le, e), (lz, z)) in enumerate(zip(en, zh), start=1):
        kind = lambda s: re.match(r"(#+ |\||!\[|```|- |)", s).group(1)
        if le != lz or kind(e) != kind(z):
            raise SystemExit(f"block {i} has a different kind:\n{e[:80]}\n{z[:80]}")
        cls = " lvl1" if le else ""
        rows.append(f"<tr><td class='en{cls}'>{render(e)}</td><td class='zh{cls}'>{render(z)}</td></tr>")
    return "\n".join(rows)


if __name__ == "__main__":
    main()
