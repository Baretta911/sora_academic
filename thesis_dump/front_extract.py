from pypdf import PdfReader
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\rendered_final_docx\Skripsi_123220204_BarettaP_final_bab4_bab5.pdf';r=PdfReader(p)
for i in range(14): print(i+1,repr((r.pages[i].extract_text() or '')[:250].replace('\n',' ')))
