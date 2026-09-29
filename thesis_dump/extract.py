import docx
from docx.document import Document as _Doc
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = r"D:\Baretta\Skripsi\program\sora_academic\thesis_dump"
OUT = r"D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP.txt"

doc = docx.Document(r"D:\Baretta\Skripsi\penulisan\Skripsi_123220204_BarettaP.docx")

def iter_block_items(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)

lines = []
for block in iter_block_items(doc):
    if isinstance(block, Paragraph):
        t = block.text.strip()
        if t:
            style = block.style.name if block.style else ""
            prefix = f"[{style}] " if style.startswith("Heading") else ""
            lines.append(prefix + t)
    else:
        lines.append("[TABLE]")
        for row in block.rows:
            cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            lines.append(" | ".join(cells))
        lines.append("[/TABLE]")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("LINES", len(lines))
import os
print("BYTES", os.path.getsize(OUT))