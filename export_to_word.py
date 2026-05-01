"""
Export Portfolio_Recommendations.md to a styled Word document.
Usage: py export_to_word.py
"""

import re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

MD_FILE = Path(__file__).parent / "Portfolio_Recommendations.md"
DOCX_FILE = Path(__file__).parent / "Portfolio_Recommendations.docx"

# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------

def set_cell_shading(cell, color_hex: str):
    """Set background color on a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def style_table(table):
    """Apply professional styling to a table."""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(table.rows):
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_before = Pt(2)
                paragraph.paragraph_format.space_after = Pt(2)
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                    run.font.name = "Calibri"
            if i == 0:
                # Header row styling
                set_cell_shading(cell, "1F3864")
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.color.rgb = RGBColor(255, 255, 255)
                        run.font.bold = True
            elif i % 2 == 0:
                set_cell_shading(cell, "E8EDF3")


def add_styled_paragraph(doc, text: str, style_name: str = "Normal",
                          bold: bool = False, italic: bool = False,
                          font_size: int | None = None,
                          color: RGBColor | None = None,
                          space_after: int | None = None):
    """Add a paragraph with inline formatting."""
    p = doc.add_paragraph(style=style_name)
    # Process bold/italic markers in text
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            run = p.add_run(part[2:-2])
            run.bold = True
        else:
            run = p.add_run(part)
        run.bold = run.bold or bold
        run.italic = italic
        if font_size:
            run.font.size = Pt(font_size)
        if color:
            run.font.color.rgb = color
        run.font.name = "Calibri"
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    return p


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def parse_table(lines: list[str]) -> list[list[str]]:
    """Parse markdown table lines into a list of rows (list of cells)."""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        # Skip separator rows (---|---|---)
        if all(re.match(r'^[-:]+$', c) for c in cells):
            continue
        rows.append(cells)
    return rows


def convert_md_to_docx(md_path: Path, docx_path: Path):
    doc = Document()

    # ---- Page setup ----
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # ---- Define/modify styles ----
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)
    style.paragraph_format.space_after = Pt(6)

    for level in range(1, 5):
        heading_style = doc.styles[f"Heading {level}"]
        heading_style.font.name = "Calibri"
        heading_style.font.color.rgb = RGBColor(31, 56, 100)

    lines = md_path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Horizontal rules
        if stripped == "---":
            # Add a thin horizontal line
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            pPr = p._p.get_or_add_pPr()
            pBdr = parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                '  <w:bottom w:val="single" w:sz="4" w:space="1" w:color="CCCCCC"/>'
                '</w:pBdr>'
            )
            pPr.append(pBdr)
            i += 1
            continue

        # Headings
        heading_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            # Clean markdown bold markers from heading text
            text = text.replace("**", "")
            h = doc.add_heading(text, level=level)
            h.style.font.name = "Calibri"
            i += 1
            continue

        # Blockquotes
        if stripped.startswith(">"):
            quote_text = stripped.lstrip("> ").strip()
            # Clean markdown formatting
            quote_text = quote_text.replace("**", "")
            p = doc.add_paragraph(style="Normal")
            p.paragraph_format.left_indent = Cm(1)
            run = p.add_run(quote_text)
            run.italic = True
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(100, 100, 100)
            run.font.name = "Calibri"
            i += 1
            continue

        # Tables — collect all contiguous table lines
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = parse_table(table_lines)
            if rows:
                num_cols = len(rows[0])
                table = doc.add_table(rows=len(rows), cols=num_cols)
                table.autofit = True
                for r_idx, row_data in enumerate(rows):
                    for c_idx, cell_text in enumerate(row_data):
                        if c_idx < num_cols:
                            cell = table.cell(r_idx, c_idx)
                            cell.text = ""
                            p = cell.paragraphs[0]
                            # Handle bold within cells
                            parts = re.split(r'(\*\*.*?\*\*)', cell_text)
                            for part in parts:
                                if part.startswith("**") and part.endswith("**"):
                                    run = p.add_run(part[2:-2])
                                    run.bold = True
                                else:
                                    run = p.add_run(part)
                                run.font.size = Pt(9)
                                run.font.name = "Calibri"
                style_table(table)
            continue

        # Bullet points
        bullet_match = re.match(r'^(\*|-)\s+(.+)$', stripped)
        if bullet_match:
            text = bullet_match.group(2)
            add_styled_paragraph(doc, text, style_name="List Bullet", font_size=10)
            i += 1
            continue

        # Numbered lists
        num_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if num_match:
            text = num_match.group(2)
            add_styled_paragraph(doc, text, style_name="List Number", font_size=10)
            i += 1
            continue

        # Code blocks (skip)
        if stripped.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            if code_lines:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(1)
                for cl in code_lines:
                    run = p.add_run(cl + "\n")
                    run.font.name = "Consolas"
                    run.font.size = Pt(9)
                    run.font.color.rgb = RGBColor(50, 50, 50)
                set_cell_shading_p = parse_xml(
                    f'<w:shd {nsdecls("w")} w:fill="F5F5F5"/>'
                )
                p._p.get_or_add_pPr().append(set_cell_shading_p)
            continue

        # Regular paragraph
        add_styled_paragraph(doc, stripped, font_size=10)
        i += 1

    # ---- Save ----
    doc.save(str(docx_path))
    print(f"Exported to: {docx_path}")


if __name__ == "__main__":
    convert_md_to_docx(MD_FILE, DOCX_FILE)
