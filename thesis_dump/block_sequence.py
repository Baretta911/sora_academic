from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_format_template.docx'; d=Document(p)
i=j=0; active=False
for child in d._element.body.iterchildren():
 if child.tag.endswith('}p'):
  x=Paragraph(child,d); txt=x.text.strip()
  if txt=='BAB IV': active=True
  if active: print('P',i,x.style.name,repr(txt[:120]))
  i+=1
 elif child.tag.endswith('}tbl'):
  t=Table(child,d)
  if active: print('T',j,len(t.rows),len(t.columns),repr(' | '.join(c.text[:50] for c in t.rows[0].cells)))
  j+=1
