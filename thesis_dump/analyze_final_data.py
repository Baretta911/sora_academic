import pandas as pd
from pathlib import Path
b=Path(r'D:\Baretta\Skripsi\program\sora_academic\thesis_output_academic')
s=pd.read_csv(b/'summary_report.csv')
frames=[pd.read_csv(b/r) for r in s.metrics_file]
d=pd.concat(frames,ignore_index=True)
print('rows',len(d),'files',len(frames),'cols',d.columns.tolist())
for c in ['fitness','fitness_delta','penalty','regularity_penalty','recovery','fatigue_end','sleep_hours','observed_sleep_hours','sleep_change_slots']:
 print(c,{k:round(v,6) for k,v in d[c].agg(['mean','median','min','max']).to_dict().items()})
for c in ['fitness','fitness_delta','penalty']:
 i=d[c].idxmin(); print('MIN',c,{k:d.loc[i,k] for k in ['day','fitness','fitness_delta','observed_fitness','sleep_hours','observed_sleep_hours','sleep_change_slots','penalty','regularity_penalty','fatigue_end']})
print('delta +/=/-',(d.fitness_delta>0).sum(),(d.fitness_delta==0).sum(),(d.fitness_delta<0).sum())
print('below -100/500',(d.fitness < -100).sum(),(d.fitness < -500).sum(),'regpen nonzero',(d.regularity_penalty<0).sum())
