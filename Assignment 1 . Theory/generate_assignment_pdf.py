from pathlib import Path
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

BASE_PATH = Path(__file__).resolve().parent
MD_FILE = BASE_PATH / "Assignment 1 · Theory.md"
PDF_FILE = BASE_PATH / "Assignment 1 · Theory.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CodeBlock', fontName='Courier', fontSize=9, leading=12, leftIndent=12, backColor='#f4f4f4', borderPadding=4, spaceBefore=6, spaceAfter=6))
styles['Heading1'].fontSize = 22
styles['Heading1'].leading = 26
styles['Heading1'].spaceAfter = 12
styles['Heading2'].fontSize = 16
styles['Heading2'].leading = 20
styles['Heading2'].spaceBefore = 12
styles['Heading2'].spaceAfter = 8
styles['BodyText'].fontSize = 11
styles['BodyText'].leading = 15
styles['BodyText'].spaceAfter = 6
styles.add(ParagraphStyle(name='MyBullet', parent=styles['BodyText'], leftIndent=18, bulletIndent=9, bulletFontSize=11))


def parse_markdown(lines):
    blocks = []
    current = []
    in_code = False
    code_lines = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            current.append(Preformatted('\n'.join(code_lines), styles['CodeBlock']))
            code_lines = []

    def flush_block():
        nonlocal current
        if current:
            blocks.append(KeepTogether(current.copy()))
            current = []

    for raw in lines:
        line = raw.rstrip('\n')
        if line.startswith('```'):
            if in_code:
                flush_code()
            in_code = not in_code
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            if current and not isinstance(current[-1], Spacer):
                current.append(Spacer(1, 8))
            continue

        if line.startswith('# '):
            flush_block()
            current.append(Paragraph(line[2:].strip(), styles['Heading1']))
            continue

        if line.startswith('## '):
            flush_block()
            current.append(Paragraph(line[3:].strip(), styles['Heading2']))
            continue

        if line.startswith('### '):
            current.append(Paragraph(line[4:].strip(), styles['Heading3']))
            continue

        stripped = line.strip()
        if re.match(r'^[-*] ', stripped):
            current.append(Paragraph(stripped, styles['MyBullet'], bulletText='•'))
            continue

        if line.startswith('    ') or line.startswith('\t'):
            current.append(Preformatted(line.lstrip(), styles['CodeBlock']))
            continue

        current.append(Paragraph(stripped, styles['BodyText']))

    flush_code()
    flush_block()
    return blocks


def build_pdf():
    if not MD_FILE.exists():
        raise FileNotFoundError(f"Markdown file not found: {MD_FILE}")

    with MD_FILE.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    story = parse_markdown(lines)
    doc = SimpleDocTemplate(str(PDF_FILE), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    doc.build(story)
    print(f"PDF created: {PDF_FILE}")


if __name__ == '__main__':
    build_pdf()
