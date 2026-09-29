from PIL import Image, ImageDraw
from pathlib import Path
d=Path(r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\rendered_final_docx')
fs=sorted(d.glob('page-*.png'),key=lambda p:int(p.stem.split('-')[1]))
print('pages',len(fs))
out=d/'sheets'; out.mkdir(exist_ok=True)
for start in range(0,len(fs),12):
 group=fs[start:start+12]; sheet=Image.new('RGB',(840,1650),(220,220,220))
 for j,p in enumerate(group):
  im=Image.open(p).convert('RGB'); im.thumbnail((200,520)); x=(j%4)*210+(210-im.width)//2; y=(j//4)*550+20
  sheet.paste(im,(x,y)); ImageDraw.Draw(sheet).text(((j%4)*210+5,(j//4)*550+2),p.stem,fill='black')
 sheet.save(out/f'sheet-{start+1}.jpg',quality=85)

