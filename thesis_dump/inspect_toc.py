from docx import Document
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_final_bab4_bab5.docx';d=Document(p)
for i,x in enumerate(d.paragraphs):
 if 'TOC' in x.style.name.upper() or i in range(270,320): print(i,x.style.name,repr(x.text[:180]))
