from docx import Document
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_final_bab4_bab5.docx';d=Document(p)
for i,x in enumerate(d.paragraphs):
 if x.style.name in ['Heading 1','Heading 2','Heading 3','Title'] and x.text.strip(): print(i,x.style.name,repr(x.text.strip()))
