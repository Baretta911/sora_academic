import os, runpy, sys, tempfile
from pathlib import Path
renderer = r'C:\Users\ASUS\.codex\plugins\cache\openai-primary-runtime\documents\26.905.11957\skills\documents\render_docx.py'
out = Path(r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\rendered_final_docx')
out.mkdir(parents=True, exist_ok=True)
tmp = Path(r'C:\Users\ASUS\.codex\visualizations\2026\09\28\01a0e7d4-aae5-7733-9b27-7862ecbd0bcc')
tmp.mkdir(parents=True, exist_ok=True)
os.environ['PATH'] = r'C:\Program Files\LibreOffice\program;' + os.environ.get('PATH', '')
os.environ['TMP'] = str(tmp)
os.environ['TEMP'] = str(tmp)
tempfile.tempdir = str(tmp)
sys.argv = [renderer, r'D:\Baretta\Skripsi\program\sora_academic\thesis_dump\Skripsi_123220204_BarettaP_final_bab4_bab5.docx', '--output_dir', str(out), '--emit_pdf']
runpy.run_path(renderer, run_name='__main__')


