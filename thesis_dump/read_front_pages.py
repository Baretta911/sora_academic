from pypdf import PdfReader
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\rendered_final_docx\Skripsi_123220204_BarettaP_final_bab4_bab5.pdf';r=PdfReader(p)
for i in range(8,13):
 print('PAGE',i+1);print((r.pages[i].extract_text() or '')[:5000])
