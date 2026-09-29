from docx import Document
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_final_bab4_bab5.docx';d=Document(p)
for i,x in enumerate(d.paragraphs):
 if 'Ringkasan Metodologi' in x.text: print(i,repr(x.text),x.style.name)
