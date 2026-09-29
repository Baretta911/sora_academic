import zipfile
from lxml import etree
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_final_bab4_bab5.docx'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
r=etree.fromstring(zipfile.ZipFile(p).read('word/document.xml'))
for i,sdt in enumerate(r.xpath('.//w:sdt',namespaces=ns)):
 text='|'.join(''.join(x.xpath('.//w:t/text()',namespaces=ns)) for x in sdt.xpath('.//w:p',namespaces=ns))
 print('SDT',i,'paragraphs',len(sdt.xpath('.//w:p',namespaces=ns)),'text',text[:500])
print('fields',len(r.xpath('.//w:instrText',namespaces=ns)))
for f in r.xpath('.//w:instrText',namespaces=ns): print(repr(f.text))
