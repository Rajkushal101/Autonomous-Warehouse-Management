"""
build_master_report.py
Assembles all phases (1 to 16 and Final Audit) into:
1. FINAL_FULL_EXAM_REPORT.md (Complete Markdown Master Report)
2. FINAL_FULL_EXAM_REPORT.docx (Publication-Grade Microsoft Word Document with all 33 embedded images, styled tables, code callouts, and exact typography)
"""

import sys
import os
import re
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.report_sections.phase1_to_4 import get_markdown_phase1_to_4
from scripts.report_sections.phase5_to_8 import get_markdown_phase5_to_8
from scripts.report_sections.phase9_to_12 import get_markdown_phase9_to_12
from scripts.report_sections.phase13_to_16 import get_markdown_phase13_to_16

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# Color Palette Constants
COLOR_NAVY_HEX = "1B365D"      # #1B365D Deep Navy
COLOR_BLUE_HEX = "2E5B88"      # #2E5B88 Slate Blue
COLOR_SLATE_HEX = "334155"     # #334155 Dark Slate
COLOR_BORDER_HEX = "CBD5E1"    # #CBD5E1 Light Border
COLOR_ZEBRA_HEX = "F8FAFC"     # #F8FAFC Subtle Gray/Ice
COLOR_CODE_BG_HEX = "F1F5F9"   # #F1F5F9 Code Block Shading
COLOR_WHITE_HEX = "FFFFFF"

RGB_NAVY = RGBColor(27, 54, 93)
RGB_BLUE = RGBColor(46, 91, 136)
RGB_SLATE = RGBColor(51, 65, 85)
RGB_BODY = RGBColor(34, 34, 34)
RGB_MUTED = RGBColor(100, 116, 139)
RGB_CODE = RGBColor(15, 23, 42)

def set_cell_background(cell, hex_color):
    """Sets background shading of a docx table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    """Sets internal padding (in dxa) of a docx table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
    """Applies clean subtle borders to an entire docx table."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def mark_row_as_header(row):
    """Configures table row to repeat as header on every page."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

def prevent_row_split(row):
    """Prevents row from being split across page boundaries."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

def parse_inline_markdown(paragraph, text, base_font="Aptos", base_size=Pt(10), base_color=RGB_BODY):
    """
    Parses Markdown inline styling (**bold**, *italic*, `code`, math) into distinct runs.
    """
    text = text.replace("<br>", "\n").replace("<br/>", "\n")
    # Tokenize by bold, italic, code, and math
    pattern = re.compile(
        r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\$[^$]+\$)'
    )
    parts = pattern.split(text)
    for part in parts:
        if not part:
            continue
        run = paragraph.add_run()
        run.font.name = base_font
        run.font.size = base_size
        run.font.color.rgb = base_color

        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            run.text = part[2:-2]
            run.bold = True
        elif part.startswith("*") and part.endswith("*") and len(part) >= 2:
            run.text = part[1:-1]
            run.italic = True
        elif part.startswith("`") and part.endswith("`") and len(part) >= 2:
            run.text = part[1:-1]
            run.font.name = "Consolas"
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(160, 30, 30)
        elif part.startswith("$") and part.endswith("$") and len(part) >= 2:
            # Clean math formatting
            cleaned_math = part[1:-1].replace("\\mathbf{", "").replace("}", "").replace("\\le", "≤").replace("\\ge", "≥").replace("\\longrightarrow", " → ").replace("\\text{", "").replace("\\", "")
            run.text = cleaned_math
            run.italic = True
            run.font.color.rgb = RGB_NAVY
        else:
            # Plain text
            run.text = part

def build_markdown_report():
    """Generates the master markdown string."""
    print("-> Concatenating report sections...")
    p1 = get_markdown_phase1_to_4()
    p2 = get_markdown_phase5_to_8()
    p3 = get_markdown_phase9_to_12()
    p4 = get_markdown_phase13_to_16()
    
    full_md = f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}\n"
    
    out_file = ROOT_DIR / "FINAL_FULL_EXAM_REPORT.md"
    print(f"-> Writing Markdown to {out_file}...")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(full_md)
    print(f"   Successfully wrote {len(full_md)} characters to FINAL_FULL_EXAM_REPORT.md")
    return full_md

def build_word_document(markdown_text):
    """Parses markdown and builds publication-grade Word document."""
    out_docx = ROOT_DIR / "FINAL_FULL_EXAM_REPORT.docx"
    print(f"-> Building Microsoft Word document at {out_docx}...")
    
    doc = docx.Document()
    
    # Configure 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # Configure Header & Footer
        footer = section.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        f_run = f_p.add_run("System 23: Autonomous Warehouse Management System (AWMS)  |  24CYS401 Secure Software Engineering")
        f_run.font.name = "Aptos"
        f_run.font.size = Pt(8.5)
        f_run.font.color.rgb = RGB_MUTED

    lines = markdown_text.splitlines()
    i = 0
    total_lines = len(lines)
    
    in_code_block = False
    code_lines = []
    code_lang = ""
    
    in_table = False
    table_lines = []
    
    is_first_h1 = True
    
    while i < total_lines:
        line = lines[i]
        stripped = line.strip()
        
        # 1. Code Block Handling
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_lines = []
                i += 1
                continue
            else:
                in_code_block = False
                # Render code block as shaded callout box
                code_text = "\n".join(code_lines)
                tbl = doc.add_table(rows=1, cols=1)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = tbl.cell(0, 0)
                cell.width = Inches(6.5)
                set_cell_background(cell, COLOR_CODE_BG_HEX)
                set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
                
                # Set thin border
                tcPr = cell._tc.get_or_add_tcPr()
                borders = parse_xml(
                    f'<w:tcBorders {nsdecls("w")}>'
                    f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{COLOR_BORDER_HEX}"/>'
                    f'<w:left w:val="single" w:sz="18" w:space="0" w:color="{COLOR_NAVY_HEX}"/>'
                    f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{COLOR_BORDER_HEX}"/>'
                    f'<w:right w:val="single" w:sz="6" w:space="0" w:color="{COLOR_BORDER_HEX}"/>'
                    f'</w:tcBorders>'
                )
                tcPr.append(borders)
                
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.05
                run = p.add_run(code_text)
                run.font.name = "Consolas"
                run.font.size = Pt(8.0)
                run.font.color.rgb = RGB_CODE
                
                # Add spacing after table
                sp_p = doc.add_paragraph()
                sp_p.paragraph_format.space_before = Pt(0)
                sp_p.paragraph_format.space_after = Pt(4)
                
                i += 1
                continue
                
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
            
        # 2. Table Handling
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines.append(stripped)
            i += 1
            # Check if next line is also a table row
            while i < total_lines and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
                
            # Process table
            if len(table_lines) >= 2:
                # Row 0: Header, Row 1: Separator, Row 2+: Data
                raw_headers = [c.strip() for c in table_lines[0].split("|")[1:-1]]
                data_rows = []
                for t_line in table_lines[2:]:
                    cols = [c.strip() for c in t_line.split("|")[1:-1]]
                    data_rows.append(cols)
                    
                num_cols = len(raw_headers)
                tbl = doc.add_table(rows=len(data_rows) + 1, cols=num_cols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl, color="CBD5E1", sz="4", val="single")
                
                # Format Header Row
                hdr_row = tbl.rows[0]
                mark_row_as_header(hdr_row)
                for c_idx, h_text in enumerate(raw_headers):
                    if c_idx < len(hdr_row.cells):
                        cell = hdr_row.cells[c_idx]
                        set_cell_background(cell, COLOR_NAVY_HEX)
                        set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
                        p = cell.paragraphs[0]
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(0)
                        parse_inline_markdown(p, h_text, base_font="Aptos", base_size=Pt(8.5), base_color=RGBColor(255, 255, 255))
                        for r in p.runs:
                            r.bold = True
                            r.font.color.rgb = RGBColor(255, 255, 255)
                            
                # Format Data Rows
                for r_idx, d_cols in enumerate(data_rows):
                    row = tbl.rows[r_idx + 1]
                    prevent_row_split(row)
                    fill_color = COLOR_ZEBRA_HEX if (r_idx % 2 == 1) else COLOR_WHITE_HEX
                    for c_idx in range(num_cols):
                        if c_idx < len(row.cells):
                            cell = row.cells[c_idx]
                            set_cell_background(cell, fill_color)
                            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
                            p = cell.paragraphs[0]
                            p.paragraph_format.space_before = Pt(0)
                            p.paragraph_format.space_after = Pt(0)
                            cell_text = d_cols[c_idx] if c_idx < len(d_cols) else ""
                            parse_inline_markdown(p, cell_text, base_font="Aptos", base_size=Pt(8.5), base_color=RGB_BODY)
                            
                # Add spacing after table
                sp_p = doc.add_paragraph()
                sp_p.paragraph_format.space_before = Pt(0)
                sp_p.paragraph_format.space_after = Pt(6)
                
            table_lines = []
            continue

        # 3. Image Handling
        img_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', stripped)
        if img_match:
            alt_text = img_match.group(1)
            img_rel_path = img_match.group(2)
            img_abs_path = ROOT_DIR / img_rel_path.replace("/", os.sep)
            
            # Check for caption on next line
            caption_text = ""
            if i + 1 < total_lines and lines[i + 1].strip().startswith("*Figure"):
                caption_text = lines[i + 1].strip().strip("*")
                i += 1  # consume caption line
                
            if img_abs_path.exists():
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(8)
                p_img.paragraph_format.space_after = Pt(2)
                
                # Insert image scaled to page width
                p_img.add_run().add_picture(str(img_abs_path), width=Inches(6.2))
                
                if caption_text:
                    p_cap = doc.add_paragraph()
                    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_cap.paragraph_format.space_before = Pt(2)
                    p_cap.paragraph_format.space_after = Pt(10)
                    c_run = p_cap.add_run(caption_text)
                    c_run.font.name = "Aptos"
                    c_run.font.size = Pt(8.5)
                    c_run.italic = True
                    c_run.font.color.rgb = RGB_MUTED
            else:
                print(f"WARNING: Image not found at {img_abs_path}")
                
            i += 1
            continue

        # 4. Heading 1 (# ...)
        if stripped.startswith("# "):
            h_text = stripped[2:].strip()
            # If major phase or title, insert page break (except first)
            if not is_first_h1 and (h_text.startswith("PHASE") or h_text.startswith("COMPREHENSIVE")):
                doc.add_page_break()
            is_first_h1 = False
            
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            
            if "24CYS401" in h_text or "FINAL COMPREHENSIVE" in h_text:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(h_text)
                run.bold = True
                run.font.name = "Aptos"
                run.font.size = Pt(16)
                run.font.color.rgb = RGB_NAVY
            else:
                run = p.add_run(h_text)
                run.bold = True
                run.font.name = "Aptos"
                run.font.size = Pt(15)
                run.font.color.rgb = RGB_NAVY
                
            i += 1
            continue

        # 5. Heading 2 (## ...)
        if stripped.startswith("## "):
            h_text = stripped[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            
            if "PROJECT TITLE" in h_text:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(h_text)
                run.bold = True
                run.font.name = "Aptos"
                run.font.size = Pt(13)
                run.font.color.rgb = RGB_BLUE
            else:
                run = p.add_run(h_text)
                run.bold = True
                run.font.name = "Aptos"
                run.font.size = Pt(12)
                run.font.color.rgb = RGB_BLUE
                
            i += 1
            continue

        # 6. Heading 3 (### ...)
        if stripped.startswith("### "):
            h_text = stripped[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            
            if "Cyber-Physical" in h_text:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(h_text)
                run.italic = True
                run.font.name = "Aptos"
                run.font.size = Pt(11)
                run.font.color.rgb = RGB_SLATE
            else:
                run = p.add_run(h_text)
                run.bold = True
                run.font.name = "Aptos"
                run.font.size = Pt(10.5)
                run.font.color.rgb = RGB_SLATE
                
            i += 1
            continue

        # 7. Horizontal Rule (---)
        if stripped == "---":
            # Add thin gray line / border
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            r = p.add_run("_________________________________________________________________________________")
            r.font.name = "Aptos"
            r.font.size = Pt(8)
            r.font.color.rgb = RGBColor(203, 213, 225)
            i += 1
            continue

        # 8. Blockquote / Alert (> ...)
        if stripped.startswith(">"):
            b_text = stripped.lstrip("> ").strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            parse_inline_markdown(p, b_text, base_font="Aptos", base_size=Pt(9.5), base_color=RGB_SLATE)
            for r in p.runs:
                r.italic = True
            i += 1
            continue

        # 9. Bullet Point (- or * or •)
        if stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("• "):
            b_text = stripped[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            parse_inline_markdown(p, b_text, base_font="Aptos", base_size=Pt(9.5), base_color=RGB_BODY)
            i += 1
            continue

        # 10. Numbered List Item (1. , 2. , etc.)
        num_match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if num_match:
            n_num = num_match.group(1)
            n_text = num_match.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            n_run = p.add_run(f"{n_num}.  ")
            n_run.bold = True
            n_run.font.name = "Aptos"
            n_run.font.size = Pt(9.5)
            n_run.font.color.rgb = RGB_BLUE
            parse_inline_markdown(p, n_text, base_font="Aptos", base_size=Pt(9.5), base_color=RGB_BODY)
            i += 1
            continue

        # 11. Empty Line
        if not stripped:
            i += 1
            continue

        # 12. Standard Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        
        # Center metadata lines on cover page
        if ("Course Code:" in stripped or "Academic Semester:" in stripped or 
            "Target Domain:" in stripped or "Submission Date:" in stripped):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            parse_inline_markdown(p, stripped, base_font="Aptos", base_size=Pt(10), base_color=RGB_SLATE)
        else:
            parse_inline_markdown(p, stripped, base_font="Aptos", base_size=Pt(10), base_color=RGB_BODY)
            
        i += 1

    # Primary target
    primary_docx = ROOT_DIR / "AWMS_FINAL_COMPREHENSIVE_EXAM_REPORT.docx"
    print(f"-> Saving Microsoft Word document to {primary_docx}...")
    doc.save(str(primary_docx))
    print(f"   Successfully generated {primary_docx}!")

    # Also attempt to save to FINAL_FULL_EXAM_REPORT.docx if not locked by Word
    fallback_docx = ROOT_DIR / "FINAL_FULL_EXAM_REPORT.docx"
    try:
        doc.save(str(fallback_docx))
        print(f"   Successfully generated {fallback_docx}!")
    except PermissionError:
        print(f"   Notice: {fallback_docx.name} is currently opened in Microsoft Word. Primary updated copy saved to {primary_docx.name}")

if __name__ == "__main__":
    print("================================================================================")
    print("AWMS MASTER REPORT GENERATOR (PHASES 1 TO 16 + ENVIRONMENT AUDIT)")
    print("================================================================================")
    md_content = build_markdown_report()
    build_word_document(md_content)
    print("================================================================================")
    print("GENERATION COMPLETED SUCCESSFULLY!")
    print("Outputs:")
    print("  1. FINAL_FULL_EXAM_REPORT.md")
    print("  2. AWMS_FINAL_COMPREHENSIVE_EXAM_REPORT.docx")
    print("  3. FINAL_FULL_EXAM_REPORT.docx (if not locked by Word)")
    print("================================================================================")
