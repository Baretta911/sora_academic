from docx import Document
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_format_template.docx'; d=Document(p)
for n in [32,33,34]:
 t=d.tables[n]; print('\nTABLE',n)
 for r in t.rows: print(' | '.join(c.text.replace('\n',' / ') for c in r.cells))
