#!/usr/bin/env python3
"""Nested group-CV gas-specific expert branches for CO and ethylene."""
from __future__ import annotations
import json, time
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from xgboost import XGBRegressor
from ec_improvement_benchmark import features, score

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'ec_gas_specific_experts'; SEED=42

SPECS={
 'ridge':{},
 'extra_trees':{'n_estimators':100,'min_samples_leaf':2,'max_features':.8},
 'random_forest':{'n_estimators':100,'min_samples_leaf':2,'max_features':.7},
 'xgb_depth2':{'n_estimators':100,'max_depth':2,'learning_rate':.03,'subsample':.8,'colsample_bytree':.8},
 'xgb_depth3':{'n_estimators':100,'max_depth':3,'learning_rate':.03,'subsample':.8,'colsample_bytree':.8},
 'xgb_depth4':{'n_estimators':100,'max_depth':4,'learning_rate':.02,'subsample':.8,'colsample_bytree':.8},
}

def make_model(name, seed, final=False):
 if name=='ridge': return make_pipeline(StandardScaler(),Ridge(alpha=10.0))
 if name=='extra_trees':
  params=dict(SPECS[name]); params['n_estimators']=500 if final else params['n_estimators']
  return ExtraTreesRegressor(**params,n_jobs=-1,random_state=seed)
 if name=='random_forest':
  params=dict(SPECS[name]); params['n_estimators']=500 if final else params['n_estimators']
  return RandomForestRegressor(**params,n_jobs=-1,random_state=seed)
 params=dict(SPECS[name])
 if final: params['n_estimators']=800
 return XGBRegressor(**params,objective='reg:squarederror',n_jobs=-1,random_state=seed)

def main():
 d=dict(np.load(ROOT/'ec_improvements'/'raw_sequences.npz'))
 x,y,groups,folds,offsets=(d[k] for k in ('sequences','targets','groups','folds','offsets'))
 cache={}
 def f(mode,drop):
  key=(mode,drop)
  if key not in cache:
   keep=np.ones(16,dtype=bool)
   if drop is not None: keep[drop]=False
   cache[key]=features(x[:,:,keep],mode)
  return cache[key]
 rows=[]; selections=[]
 for outer in range(1,6):
  start=time.perf_counter(); outer_mask=folds!=outer; outer_ids=np.unique(groups[outer_mask])
  assignments=[]
  for itr,iva in GroupKFold(2).split(outer_ids,groups=outer_ids):
   assignments.append((outer_ids[itr],outer_ids[iva]))
  test=(folds==outer)&(offsets==0); pred=np.zeros((test.sum(),2),dtype=np.float32)
  # Shared reference retains the principal frozen configuration.
  base=make_model('xgb_depth3',SEED+outer,final=True).fit(f('physics',None)[outer_mask],y[outer_mask])
  base_pred=np.asarray(base.predict(f('physics',None)[test])).reshape(-1,2)
  rows.append({'fold':outer,'branch':'shared_physics_xgboost','metrics':score(y[test],base_pred)})
  for target,gas in enumerate(('CO','Ethylene')):
   stage1=[]
   for mode in ('summary','physics'):
    ff=f(mode,None)
    for name in SPECS:
     losses=[]
     for k,(trids,vids) in enumerate(assignments):
      tr=outer_mask&np.isin(groups,trids); va=outer_mask&np.isin(groups,vids)&(offsets==0)
      m=make_model(name,SEED+100*outer+10*target+k).fit(ff[tr],y[tr,target])
      losses.append(float(np.mean(np.abs(y[va,target]-m.predict(ff[va])))))
     stage1.append({'model':name,'features':mode,'inner_mae':float(np.mean(losses))})
   chosen=min(stage1,key=lambda z:z['inner_mae'])
   stage2=[]
   for drop in [None]+list(range(16)):
    ff=f(chosen['features'],drop); losses=[]
    for k,(trids,vids) in enumerate(assignments):
     tr=outer_mask&np.isin(groups,trids); va=outer_mask&np.isin(groups,vids)&(offsets==0)
     m=make_model(chosen['model'],SEED+1000*outer+100*target+10*(drop or 0)+k).fit(ff[tr],y[tr,target])
     losses.append(float(np.mean(np.abs(y[va,target]-m.predict(ff[va])))))
    stage2.append({'dropped_sensor':None if drop is None else drop+1,'inner_mae':float(np.mean(losses))})
   sensor=min(stage2,key=lambda z:z['inner_mae']); drop=None if sensor['dropped_sensor'] is None else sensor['dropped_sensor']-1
   ff=f(chosen['features'],drop); expert=make_model(chosen['model'],SEED+10000*outer+target,final=True)
   expert.fit(ff[outer_mask],y[outer_mask,target]); pred[:,target]=expert.predict(ff[test])
   selections.append({'fold':outer,'gas':gas,'model':chosen['model'],'features':chosen['features'],
     'dropped_sensor':sensor['dropped_sensor'],'stage1_inner_mae':chosen['inner_mae'],
     'stage2_inner_mae':sensor['inner_mae'],'model_ranking':sorted(stage1,key=lambda z:z['inner_mae']),
     'sensor_ranking':sorted(stage2,key=lambda z:z['inner_mae'])})
  rows.append({'fold':outer,'branch':'gas_specific_experts','metrics':score(y[test],pred)})
  print(json.dumps({'fold':outer,'seconds':time.perf_counter()-start,
   'selected':[s for s in selections if s['fold']==outer]}),flush=True)
 result={'seed':SEED,'protocol':'five outer episode folds; nested 2-fold group selection; 100-tree screening; full-budget refit; all offsets train; offset-0 validation/test',
  'search':'per gas: select model+features with all sensors, then select all or one sensor dropped',
  'candidate_models':SPECS,'results':rows,'selections':selections}
 OUT.mkdir(exist_ok=True);(OUT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')

if __name__=='__main__': main()
