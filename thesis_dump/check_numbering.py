from docx import Document
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_final_bab4_bab5.docx';d=Document(p)
for s in ['Heading 2','Heading 3','Title']:
 st=d.styles[s]; print(s,'numPr',st._element.pPr.numPr.xml if st._element.pPr is not None and st._element.pPr.numPr is not None else None)
for x in d.paragraphs:
 if x.text.strip().startswith(('3.10','4.1','5.1','Ringkasan Metodologi')):
  print(x.text[:50],x.style.name,'numPr',x._p.pPr.numPr.xml if x._p.pPr is not None and x._p.pPr.numPr is not None else None,'styleid',x.style.style_id)
