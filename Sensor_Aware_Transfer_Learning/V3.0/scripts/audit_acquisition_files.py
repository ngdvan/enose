"""Audit new acquisition evidence against the exact model-input workbook.

Filename+Index times are nominal candidates, never verified timestamps.
No original files or predictive results are modified.
"""
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter
import hashlib,json,re
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'evidence/experiments'
OUT=ROOT/'evidence/acquisition_audit';OUT.mkdir(exist_ok=True)
MASTER=ROOT.parents[1]/'2407/TONG_NH3H2_CHUAN.xlsx'
COLS=[f'Response{i}' for i in range(1,21)]+['NH3','H2','Combination']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    cache=OUT/(p.stem+'.npz')
    digest=sha(p)
    if cache.exists():
        c=np.load(cache)
        if str(c['sha'])==digest:return pd.DataFrame(c['values'],columns=c['columns'].tolist())
    d=pd.read_excel(p) if p.suffix=='.xlsx' else pd.read_csv(p)
    cols=[c for c in ['Index']+COLS if c in d]
    d=d[cols]
    np.savez_compressed(cache,values=d.to_numpy(dtype=float),columns=np.array(cols),sha=np.array(digest))
    return d

def keys(a):return [np.round(row,9).astype('<f8').tobytes() for row in a]

master=read(MASTER); print('Loaded model workbook',len(master),flush=True)
manifest={str(MASTER):sha(MASTER)};runs=[];exposures=[];mismatches=[]
source_sequences=[]
for path in sorted(SOURCE.glob('*.xlsx')):
    d=read(path);manifest[path.name]=sha(path)
    run=int((int(d.Combination.min())-1)//63+1)
    match=re.search(r'(\d{4})_(\d+)_(\d+) (\d+)_(\d+)(?:_(\d+))?',path.name)
    year,month,day,hour,minute=map(int,match.groups()[:5]);second=int(match[6] or 0)
    anchor=datetime(year,month,day,hour,minute,second)
    indexed='Index' in d
    summary={'run':run,'filename':path.name,'filename_start':anchor.isoformat(sep=' '),
             'filename_precision':'second' if match[6] else 'minute; seconds absent',
             'source_rows':len(d),'combinations':int(d.Combination.nunique()),
             'combination_min':int(d.Combination.min()),'combination_max':int(d.Combination.max()),
             'has_index':indexed,'index_min':int(d.Index.min()) if indexed else None,
             'index_max':int(d.Index.max()) if indexed else None,
             'index_contiguous':bool((d.Index.diff().dropna()==1).all()) if indexed else None}
    source_offset=0
    for combination,part in d.groupby('Combination',sort=False):
        m=master[master.Combination==combination]
        a=part[COLS].to_numpy(float);b=m[COLS].to_numpy(float)
        same=a.shape==b.shape and np.array_equal(a,b)
        same_rounded=a.shape==b.shape and np.array_equal(np.round(a,9),np.round(b,9))
        ka,kb=keys(a),keys(b);overlap=sum((Counter(ka)&Counter(kb)).values())
        rec={'combination':int(combination),'run':run,'source_file':path.name,'source_rows':len(a),'model_rows':len(b),
             'exact_sequence_match':same,'rounded_9dp_sequence_match':same_rounded,
             'shared_row_multiset_count':overlap,'early_64_exact_match':len(a)>=64 and len(b)>=64 and np.array_equal(a[:64],b[:64]),
             'source_row_offset_0based':source_offset,'NH3':float(part.NH3.iloc[0]),'H2':float(part.H2.iloc[0]),
             'source_index_first':int(part.Index.iloc[0]) if indexed else None,
             'source_index_last':int(part.Index.iloc[-1]) if indexed else None,
             'filename_start':anchor.isoformat(sep=' '),'time_status':'nominal filename+Index candidate; unverified cadence' if indexed else 'no original Index; no absolute exposure time assigned'}
        if indexed:
            start=anchor+timedelta(seconds=2*(rec['source_index_first']-1))
            end=anchor+timedelta(seconds=2*(rec['source_index_last']-1))
            rec.update(nominal_start=start.isoformat(sep=' '),nominal_end=end.isoformat(sep=' '),
                       nominal_start_day=start.date().isoformat(),nominal_crosses_midnight=start.date()!=end.date())
        exposures.append(rec);source_offset+=len(a)
        source_sequences.append((rec,a))
        if not same_rounded:
            prefix=0
            for left,right in zip(ka,kb):
                if left!=right:break
                prefix+=1
            mismatches.append(rec|{'common_prefix_rows':prefix,'source_only_rows':len(a)-overlap,'model_only_rows':len(b)-overlap})
    selected=[e for e in exposures if e['run']==run]
    summary.update(model_rows=sum(e['model_rows'] for e in selected),exact_exposures=sum(e['exact_sequence_match'] for e in selected),
                   rounded_exact_exposures=sum(e['rounded_9dp_sequence_match'] for e in selected),early_exact_exposures=sum(e['early_64_exact_match'] for e in selected))
    runs.append(summary);print('RUN',summary,flush=True)

rawpath=next(SOURCE.glob('*.csv'));raw=read(rawpath);manifest[rawpath.name]=sha(rawpath)
first=read(next(p for p in SOURCE.glob('*.xlsx') if 'LAN1' in p.name))
joined=first.merge(raw,on='Index',suffixes=('_processed','_raw'),validate='one_to_one')
response_cols=[f'Response{i}' for i in range(1,21)]
diff=np.abs(joined[[c+'_processed' for c in response_cols]].to_numpy()-joined[[c+'_raw' for c in response_cols]].to_numpy())
rawcheck={'raw_rows':len(raw),'processed_rows':len(first),'joined_rows':len(joined),'index_first':float(raw.Index.iloc[0]),'index_last':float(raw.Index.iloc[-1]),
          'index_contiguous':bool((raw.Index.diff().dropna()==1).all()),'max_response_absolute_difference':float(diff.max()),'all_20_channels_exact':bool((diff==0).all())}
pd.DataFrame(runs).sort_values('run').to_csv(OUT/'run_inventory.csv',index=False)
pd.DataFrame(exposures).sort_values('combination').to_csv(OUT/'exposure_source_mapping.csv',index=False)
pd.DataFrame(mismatches).to_csv(OUT/'source_model_discrepancies.csv',index=False)
counts=pd.DataFrame(exposures).dropna(subset=['nominal_start_day']).groupby(['run','nominal_start_day']).size().reset_index(name='exposures_by_nominal_start')
counts.to_csv(OUT/'nominal_calendar_candidates.csv',index=False)
report={'model_rows':len(master),'source_rows':sum(r['source_rows'] for r in runs),'exposures':len(exposures),
        'exact_sequences':sum(e['exact_sequence_match'] for e in exposures),'rounded_exact_sequences':sum(e['rounded_9dp_sequence_match'] for e in exposures),
        'early_64_exact_sequences':sum(e['early_64_exact_match'] for e in exposures),'raw_run1_check':rawcheck,
        'source_sha256':manifest,'timestamp_caution':'Candidate only: assumes filename denotes acquisition start, Index 1 at that start, and constant 2.0 s cadence. L2 lacks seconds; L4-L6 lack Index. Do not use these candidates as verified leave-one-calendar-day-out labels.'}
# Match complete signal+target sequences independently of the editable Combination ID.
def sequence_hash(a):return hashlib.sha256(np.round(a[:,:-1],9).astype('<f8').tobytes()).hexdigest()
lookup={}
for rec,a in source_sequences:lookup.setdefault((len(a),sequence_hash(a)),[]).append((rec,a))
mapping=[]
for combination,part in master.groupby('Combination'):
    b=part[COLS].to_numpy(float)
    found=lookup.get((len(b),sequence_hash(b)),[])
    row={'model_combination':int(combination),'model_rows':len(b),'identifier_implied_partition':int((combination-1)//63+1),
         'NH3':float(part.NH3.iloc[0]),'H2':float(part.H2.iloc[0]),'matching_source_sequences':len(found)}
    if len(found)==1:
        rec,a=found[0]
        row.update(match_status='verified complete signal and targets',source_file=rec['source_file'],source_run=rec['run'],
                   source_combination=rec['combination'],combination_renumbered=int(combination)!=rec['combination'],
                   exact_float_sequence_match=bool(np.array_equal(a[:,:-1],b[:,:-1])),
                   source_index_first=rec['source_index_first'],source_index_last=rec['source_index_last'],
                   filename_start=rec['filename_start'],nominal_start=rec.get('nominal_start'),nominal_end=rec.get('nominal_end'),
                   nominal_start_day=rec.get('nominal_start_day'),time_status=rec['time_status'])
    else:row['match_status']='unresolved: no unique full-sequence source match'
    mapping.append(row)
mapped=pd.DataFrame(mapping)
mapped.to_csv(OUT/'model_exposure_provenance.csv',index=False)
mapped[mapped.matching_source_sequences!=1].to_csv(OUT/'unresolved_model_exposures.csv',index=False)
mapped.dropna(subset=['nominal_start_day']).groupby(['identifier_implied_partition','nominal_start_day']).size().reset_index(name='verified_exposures_with_nominal_start_day').to_csv(OUT/'model_nominal_calendar_candidates.csv',index=False)
report.update(full_signal_and_target_sequences_matched=int((mapped.matching_source_sequences==1).sum()),
              same_id_matches=int(((mapped.matching_source_sequences==1)&(mapped.model_combination==mapped.source_combination)).sum()),
              renumbered_matches=int(mapped.combination_renumbered.fillna(False).sum()),
              unresolved_model_combinations=mapped.loc[mapped.matching_source_sequences!=1,'model_combination'].tolist(),
              indexed_verified_model_exposures=int(mapped.nominal_start.notna().sum()),
              matched_source_runs_agree_with_identifier_partitions=bool((mapped.loc[mapped.matching_source_sequences==1,'source_run']==mapped.loc[mapped.matching_source_sequences==1,'identifier_implied_partition']).all()))
(OUT/'audit_summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2),flush=True)
