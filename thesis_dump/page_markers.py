from pypdf import PdfReader
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\rendered_final_docx\Skripsi_123220204_BarettaP_final_bab4_bab5.pdf';r=PdfReader(p)
print('pages',len(r.pages))
for i,x in enumerate(r.pages):
 t=x.extract_text() or ''
 if i>=53: print(i+1,repr(t[:130].replace('\n',' ')))
