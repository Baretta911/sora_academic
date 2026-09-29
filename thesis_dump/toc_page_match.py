import re,unicodedata
from docx import Document
from pypdf import PdfReader
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_final_bab4_bab5.docx'; d=Document(p)
pdf=PdfReader(r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\rendered_final_docx\Skripsi_123220204_BarettaP_final_bab4_bab5.pdf')
pages=[x.extract_text() or '' for x in pdf.pages]
def norm(s): return re.sub(r'[^a-z0-9]+','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
for i,p in enumerate(d.paragraphs):
 t=p.text.strip()
 if p.style.name in {'Heading 2','Heading 3','Title'} and re.match(r'^\d+(?:\.\d+){1,4}\b',t):
  key=norm(t); matches=[j+1 for j,x in enumerate(pages[13:],13) if key in norm(x)]
  if not matches: print('UNMATCHED',p.style.name,repr(t))
  else: print(matches[0]-13,t)
