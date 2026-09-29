import pandas as pd
from pathlib import Path
b=Path(r'D:\Baretta\Skripsi\program\sora_academic\thesis_output_academic')
s=pd.read_csv(b/'summary_report.csv'); best=None
for _,r in s.iterrows():
 d=pd.read_csv(b/r.metrics_file); i=d.fitness.idxmin(); x=d.loc[i]
 if best is None or x.fitness<best[0]: best=(x.fitness,r.subject,x.day,r.schedule_file,r.metrics_file,x)
print(best[:5]); print(best[5].to_dict())
p=b/best[3]; print(pd.read_csv(p).columns.tolist()); print(pd.read_csv(p).to_string(index=False)[:3500])
