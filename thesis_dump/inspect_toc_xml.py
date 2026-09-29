import zipfile
from lxml import etree
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_final_bab4_bab5.docx'; z=zipfile.ZipFile(p); root=etree.fromstring(z.read('word/document.xml')); ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
sdt=root.xpath('.//w:sdt',namespaces=ns)[0]
for i,p in enumerate(sdt.xpath('.//w:sdtContent/w:p',namespaces=ns)):
 text=''.join(p.xpath('.//w:t/text()',namespaces=ns))
 st=p.xpath('./w:pPr/w:pStyle/@w:val',namespaces=ns)
 tabs=p.xpath('./w:pPr/w:tabs/w:tab/@w:leader',namespaces=ns)
 if i<12 or i>85: print(i,st,text[:120],tabs)
print('COUNT',len(sdt.xpath('.//w:sdtContent/w:p',namespaces=ns)))
