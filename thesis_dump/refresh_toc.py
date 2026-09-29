import re, zipfile, unicodedata
from copy import deepcopy
from pathlib import Path
from lxml import etree
from docx import Document
from pypdf import PdfReader

root=Path(r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump')
docx=root/'Skripsi_123220204_BarettaP_final_bab4_bab5.docx'
pdf=root/'rendered_final_docx'/'Skripsi_123220204_BarettaP_final_bab4_bab5.pdf'
doc=Document(docx); pdfpages=[p.extract_text() or '' for p in PdfReader(pdf).pages]
def norm(s):
    return re.sub(r'[^a-z0-9]+','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def find_page(title):
    key=norm(title)
    for ix,page in enumerate(pdfpages[13:],13):
        lines=[line.strip() for line in page.splitlines() if line.strip()]
        if any(norm(line).startswith(key) for line in lines): return str(ix+1-13)
    for ix,page in enumerate(pdfpages[13:],13):
        if key and key in norm(page): return str(ix+1-13)
    key=norm(re.sub(r'^\d+(?:\.\d+)*\s*','',title))
    for ix,page in enumerate(pdfpages[13:],13):
        if key and key in norm(page): return str(ix+1-13)
    raise ValueError('Heading not found in rendered pages: '+title)

entries=[]
chapter_pages={'PENDAHULUAN':'1','TINJAUAN LITERATUR':'7','METODOLOGI PENELITIAN':'22',
               'HASIL DAN PEMBAHASAN':'43','PENUTUP':'52'}
def find_chapter_page(chapter,title):
    chapter_key=norm(chapter); title_key=norm(title)
    for ix,page in enumerate(pdfpages[13:],13):
        lines=[norm(line.strip()) for line in page.splitlines() if line.strip()]
        for n,line in enumerate(lines[:-1]):
            if line==chapter_key and lines[n+1]==title_key:
                return str(ix+1-13)
    return chapter_pages[title]
ps=doc.paragraphs
for i,p in enumerate(ps):
    txt=p.text.strip()
    if p.style.name=='Heading 1' and re.match(r'^BAB [IVX]+(?:\n|$)',txt):
        if '\n' in txt:
            chapter,title=txt.split('\n',1); shown=chapter+' '+title.strip()
        else:
            chapter=txt; title=''
            for q in ps[i+1:]:
                if q.style.name=='Heading 1' and q.text.strip():
                    title=q.text.strip(); break
            shown=chapter+' '+title
        if title.strip()=='3.8 Baseline Comparison': title='3.9.2 Baseline Comparison'
        entries.append(('TOC1',shown,find_chapter_page(chapter,title.strip())))
    elif p.style.name in {'Heading 2','Heading 3','Title'} and re.match(r'^\d+(?:\.\d+){1,4}\s+',txt):
        if p.style.name=='Title' and txt=='3.8 Baseline Comparison': txt='3.9.2 Baseline Comparison'
        level=len(re.match(r'^(\d+(?:\.\d+)*)',txt).group(1).split('.'))
        page=find_page(txt)
        entries.append(('TOC2' if level==2 else 'TOC3',txt,page))

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ns={'w':W[1:-1]}
with zipfile.ZipFile(docx) as z: files={n:z.read(n) for n in z.namelist()}
xml=etree.fromstring(files['word/document.xml'])
sdt=xml.xpath('.//w:sdt[w:sdtPr/w:docPartObj]',namespaces=ns)[0]
content=sdt.xpath('./w:sdtContent',namespaces=ns)[0]
paras=content.findall(W+'p'); titlep=paras[0]
front=[]
for p in paras[1:]:
    text=''.join(p.xpath('.//w:t/text()',namespaces=ns))
    if text.startswith(('SURAT PERNYATAAN','KARYA ASLI TUGAS AKHIR','PERNYATAAN BEBAS PLAGIASI')): front.append(p)
templates={}
for p in paras:
    style=p.xpath('./w:pPr/w:pStyle/@w:val',namespaces=ns)
    if style and style[0] in {'TOC1','TOC2','TOC3'}: templates.setdefault(style[0],p)
for p in list(content): content.remove(p)
content.append(titlep)
content.append(etree.Element(W+'p'))
for old in front: content.append(old)
for style,text,page in entries:
    p=etree.fromstring(etree.tostring(templates.get(style,templates['TOC2'])))
    pPr=p.find(W+'pPr')
    for child in list(p):
        if child is not pPr: p.remove(child)
    run=etree.SubElement(p,W+'r'); etree.SubElement(run,W+'t').text=text
    run=etree.SubElement(p,W+'r'); etree.SubElement(run,W+'tab')
    run=etree.SubElement(p,W+'r'); etree.SubElement(run,W+'t').text=page
    content.append(p)

# Add the three Chapter IV result tables to the cached List of Tables. The
# original template field was only cached through Chapter III and LibreOffice
# did not rebuild it from the static caption paragraphs.
table_rows=[]
for p in xml.xpath('.//w:p[w:pPr/w:pStyle[@w:val="TableofFigures"]]',namespaces=ns):
    txt=''.join(p.xpath('.//w:t/text()',namespaces=ns))
    if txt.startswith('Tabel 4.'):
        p.getparent().remove(p)
    elif txt.startswith('Tabel '): table_rows.append((p,txt))
last_table=table_rows[-1][0]
template=next(p for p,t in table_rows if t.startswith('Tabel 3. 2'))
parent=last_table.getparent(); insert_at=parent.index(last_table)+1
for n,(caption,page) in enumerate([
    ('Tabel 4.1 Persamaan Fitness yang Diterapkan dalam Implementasi',find_page('Tabel 4.1 Persamaan Fitness yang Diterapkan dalam Implementasi')),
    ('Tabel 4.2 Hasil Kalibrasi Parameter Menggunakan Grid Search',find_page('Tabel 4.2 Hasil Kalibrasi Parameter Menggunakan Grid Search')),
    ('Tabel 4.3 Statistik Optimasi Mingguan Seluruh Subjek',find_page('Tabel 4.3 Statistik Hasil Pengujian Optimasi Mingguan pada Seluruh Subjek Pengujian')),
    ('Tabel 4.4 Statistik dan Hasil Berpasangan Metode pada Hari Rabu',find_page('Tabel 4.4 Statistik dan Hasil Berpasangan Metode pada Hari Rabu')),
    ('Tabel 4.5 Rincian Perhitungan Komponen Fitness pada Kasus Ekstrem',find_page('Tabel 4.5 Rincian Perhitungan Komponen Fitness pada Kasus Ekstrem')),
],1):
    p=deepcopy(template)
    link=p.find(W+'hyperlink')
    link.set(W+'anchor',f'_TocTable4{n}')
    for instr in p.xpath('.//w:instrText',namespaces=ns):
        if 'PAGEREF' in (instr.text or ''): instr.text=f' PAGEREF _TocTable4{n} \\h '
    nodes=link.xpath('.//w:t',namespaces=ns)
    nodes[0].text=caption
    nodes[-1].text=page
    parent.insert(insert_at,p); insert_at+=1

# Keep Chapter IV figures in the template's cached List of Figures as well.
figure_rows=[]
for p in xml.xpath('.//w:p[w:pPr/w:pStyle[@w:val="TableofFigures"]]',namespaces=ns):
    txt=''.join(p.xpath('.//w:t/text()',namespaces=ns))
    if txt.startswith('Gambar 4.'):
        p.getparent().remove(p)
    elif txt.startswith('Gambar '):
        figure_rows.append((p,txt))
if figure_rows:
    last_figure=figure_rows[-1][0]
    figure_template=next(p for p,t in figure_rows if t.startswith('Gambar 3.'))
    figure_parent=last_figure.getparent(); figure_insert=figure_parent.index(last_figure)+1
    for n,(caption,page) in enumerate([
        ('Gambar 4.1 Alur implementasi SORA Academic',find_page('Gambar 4.1 Alur implementasi SORA Academic')),
        ('Gambar 4.2 Rerata, median, dan hasil berpasangan fitness menurut hari',find_page('Gambar 4.2 Rerata, median, dan hasil berpasangan fitness menurut hari')),
    ],1):
        p=deepcopy(figure_template)
        link=p.find(W+'hyperlink')
        link.set(W+'anchor',f'_TocFigure4{n}')
        for instr in p.xpath('.//w:instrText',namespaces=ns):
            if 'PAGEREF' in (instr.text or ''): instr.text=f' PAGEREF _TocFigure4{n} \\h '
        nodes=link.xpath('.//w:t',namespaces=ns)
        nodes[0].text=caption
        nodes[-1].text=page
        figure_parent.insert(figure_insert,p); figure_insert+=1

files['word/document.xml']=etree.tostring(xml,xml_declaration=True,encoding='UTF-8',standalone=True)
tmp=docx.with_suffix('.tmp.docx')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in files.items(): z.writestr(name,data)
tmp.replace(docx)
print('TOC entries refreshed:',len(entries),'body pages:',len(pdfpages))
