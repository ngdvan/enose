"""Snapshot environment and audit exposure identity without inventing provenance."""
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from revision_common import ROOT, sha256, dump
from run_major_revision import load, prepare
import same_device_session_transfer as core
import co_ethylene_session_transfer as co
import sensor_drift_transfer as drift


def main():
    out=ROOT/'revision_artifacts';env=out/'environment'
    env.mkdir(parents=True,exist_ok=True)
    dump(env/'runtime.json',dict(python=sys.version,executable=sys.executable,platform=platform.platform(),
           pytorch=torch.__version__,cuda=torch.version.cuda,cuda_available=torch.cuda.is_available(),
           gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None))
    (env/'requirements_runtime.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True),encoding='utf-8')
    sources=[core.DATA,co.CACHE,*sorted(drift.DATA.glob('batch*.dat'))]
    dump(env/'input_manifest.json',[dict(path=str(p),sha256=sha256(p),bytes=p.stat().st_size) for p in sources])
    rows=[];foldrows=[]
    for dataset in ['nh3_h2','co_ethylene']:
        data,audit=load(dataset)
        dump(out/'leakage_audit'/f'{dataset}_source_audit.json',audit)
        if dataset=='nh3_h2':
            for i,group in enumerate(data['groups']):
                raw=np.asarray(data['raw'][i],np.float32)
                rows.append(dict(dataset=dataset,exposure=int(group),partition=int(data['sessions'][i]),
                    target_a=float(data['targets'][i,0]),target_b=float(data['targets'][i,1]),
                    source_samples=len(raw),unique_sensor_rows=len(np.unique(raw,axis=0)),
                    fingerprint=hashlib.sha256(raw.tobytes()).hexdigest(),fingerprint_scope='complete workbook exposure'))
        else:
            for i in np.flatnonzero(data['offsets']==0):
                rows.append(dict(dataset=dataset,exposure=int(data['groups'][i]),partition=int(data['blocks'][i]),
                    target_a=float(data['y'][i,0]),target_b=float(data['y'][i,1]),source_samples=64,
                    unique_sensor_rows=len(np.unique(data['x'][i],axis=0)),
                    fingerprint=hashlib.sha256(data['x'][i].tobytes()).hexdigest(),fingerprint_scope='cached zero-offset window only'))
        for fold in range(0,7 if dataset=='nh3_h2' else 4):
            p=prepare(dataset,data,fold)
            role_sets=[set(p[k]) for k in ['pre_groups','adapt_groups','test_groups']]
            overlap=sum(len(role_sets[a]&role_sets[b]) for a,b in [(0,1),(0,2),(1,2)])
            foldrows.append(dict(dataset=dataset,fold=fold,overlapping_exposure_ids=overlap,
                                 pre_exposures=len(role_sets[0]),adapt_exposures=len(role_sets[1]),test_exposures=len(role_sets[2])))
    df=pd.DataFrame(rows)
    df['same_pair_exposures_in_partition']=df.groupby(['dataset','partition','target_a','target_b']).exposure.transform('count')
    df['identical_signal_exposures']=df.groupby(['dataset','fingerprint']).exposure.transform('count')
    df.to_csv(out/'leakage_audit/repeated_exposure_audit.csv',index=False)
    pd.DataFrame(foldrows).to_csv(out/'leakage_audit/split_overlap_audit.csv',index=False)
    duplicates=df[df.identical_signal_exposures>1]
    duplicates.to_csv(out/'leakage_audit/identical_signal_exposures.csv',index=False)
    statement=(f'# Leakage and repeated-exposure audit\n\nChecked {len(df)} identified exposures/windows. '
        f'Found {len(duplicates)} records belonging to duplicated signal fingerprints. '
        f'All {len(foldrows)} evaluated split definitions have disjoint exposure IDs.\n\n'
        'Repeated concentration coordinates are not automatically duplicate measurements. Workbook Combination IDs and cached group IDs '
        'are used as exposure identifiers. Distinct IDs are not authoritative proof of independently acquired physical exposures. '
        'That claim still requires laboratory acquisition records. Offset windows remain within their parent exposure role. '
        'The CO/ethylene audit covers cached windows, not the unavailable full source trace. '
        'The six NH3/H2 partitions are inferred as consecutive groups of 63 Combination IDs, not verified experimental days. '
        'The NH3/H2 folds assess held-partition generalization and do not all preserve temporal order.\n')
    (out/'leakage_audit/leakage_statement.md').write_text(statement,encoding='utf-8')
    print(statement)


if __name__=='__main__':main()
