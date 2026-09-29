import pandas as pd
p=r'D:\Baretta\Skripsi\program\sora_academic\thesis_output_academic\results\multi_subject_comparison.csv'; d=pd.read_csv(p)
for c in d.columns[1:]: print(c,d[c].mean(),d[c].median(),d[c].std(),d[c].min(),d[c].max())
for a,b in [('sora_fit','greedy_fit'),('sora_fit','fixed_fit'),('sora_fatigue','greedy_fatigue'),('sora_fatigue','fixed_fatigue'),('sora_sleep','greedy_sleep'),('sora_sleep','fixed_sleep')]:
 z=d[a]-d[b];print('DELTA',a,b,z.mean(),z.median(),(z>0).sum(),(z==0).sum(),(z<0).sum())
