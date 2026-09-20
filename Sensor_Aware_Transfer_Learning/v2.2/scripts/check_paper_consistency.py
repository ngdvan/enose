"""Fail-closed publication gate; never certify smoke or partial experiments."""
import argparse
import json
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from revision_common import ROOT, SEEDS, sha256


def check(run, manuscript):
    failures=[]
    protocol=json.loads((run/'protocol.json').read_text())
    if protocol['smoke']:failures.append('Smoke artifacts cannot support manuscript claims')
    if protocol['seeds']!=SEEDS:failures.append('Main protocol must contain all ten predefined seeds')
    if protocol['pretrain_epochs']!=60 or protocol['epochs']!=120:
        failures.append('Final evidence requires the predefined 60/120 raw-response epoch schedule')
    if protocol['primary_policy']!='fine_tuned':failures.append('Primary policy differs from predefined fine-tuning')
    for name,digest in protocol['code_hashes'].items():
        if sha256(ROOT/'code'/name)!=digest:failures.append(f'Code changed since run creation: {name}')
    required={'fixed','multifold','classical','generic','design','window','ablation','drift'}
    completed={p.stem.removesuffix('_completed') for p in run.glob('*_completed.json')}
    for name in sorted(required-completed):failures.append(f'Incomplete suite: {name}')
    jobs=[json.loads(p.read_text()) for p in (run/'jobs').glob('*.json')]
    driftjobs=[json.loads(p.read_text()) for p in (run/'drift_jobs').glob('*.json')]
    if len(jobs)!=1390:failures.append(f'Expected 1390 raw-response jobs; found {len(jobs)}')
    if len(driftjobs)!=290:failures.append(f'Expected 290 drift jobs; found {len(driftjobs)}')
    if jobs:
        identities=pd.DataFrame([j['identity'] for j in jobs])
        groups=['dataset','fold','budget','design','window','policy']
        if not (identities.groupby(groups).seed.nunique()==10).all():
            failures.append('Some raw-response configurations do not have ten distinct seeds')
    for job in jobs:
        if set(job['fit_groups'])&set(job['validation_groups']):failures.append('Adaptation fitting/validation overlap')
        if (set(job['fit_groups'])|set(job['validation_groups']))&set(job['split']['test_groups']):failures.append('Adaptation/test overlap')
        if set(job['split']['pre_groups'])&set(job['split']['test_groups']):failures.append('Pretraining/test overlap')
        pred=pd.DataFrame(job['predictions'])
        for metric in job['metrics']:
            p=pred[pred.gas==metric['gas']];err=np.abs(p.true-p.prediction)
            if not np.isclose(err.mean(),metric['mae'],rtol=1e-6):failures.append('Saved MAE differs from predictions')
            # Neural jobs compute NumPy quantiles on float32 errors; pandas
            # silently promotes serialized predictions to float64. Reproduce
            # the recorded arithmetic, rather than relaxing the tolerance.
            dtype=np.float64 if job['identity']['policy'] in ['plsr','svr','extra_trees'] else np.float32
            q90=np.quantile(np.abs(p.true.to_numpy(dtype=dtype)-p.prediction.to_numpy(dtype=dtype)),.9)
            if not np.isclose(q90,metric['q90'],rtol=1e-6):failures.append('Saved Q90 differs from predictions')
    for job in driftjobs:
        if set(job['fit_indices'])&set(job['validation_indices']):failures.append('Drift adaptation overlap')
        pred=pd.DataFrame(job['predictions'])
        for metric in job['metrics']:
            subset=pred[(pred.gas==metric['gas'])&(pred.fold==metric['fold'])]
            error=np.abs(subset.true-subset.prediction)
            if not np.isclose(error.mean(),metric['mae'],rtol=1e-6):failures.append('Drift MAE differs from predictions')
            q90=np.quantile(np.abs(subset.true.to_numpy(dtype=np.float32)-subset.prediction.to_numpy(dtype=np.float32)),.9)
            if not np.isclose(q90,metric['q90'],rtol=1e-6):failures.append('Drift Q90 differs from predictions')
            if metric['normalization_range']>0 and not np.isclose(error.mean()/metric['normalization_range'],metric['nmae'],rtol=1e-6):
                failures.append('Drift NMAE differs from specified reporting range')
    if not manuscript.exists():failures.append('Final revised manuscript is not generated')
    else:
        text=manuscript.read_text(encoding='utf-8')
        for pattern in [r'\bbest policy\b',r'\bTODO\b',r'\bSYST\b',r'\bplaceholder\b',r'\bthree seeds\b',r'\b3.seed\b',r'\boveral\b',r'\btrainning\b',r'\bcomparision\b',r'Multif-fold']:
            if re.search(pattern,text,re.I):failures.append(f'Forbidden/obsolete wording: {pattern}')
        if '10 seeds' not in text:failures.append('Manuscript does not state 10 seeds')
        if '## References' not in text:failures.append('Missing references section')
        else:
            body,refs=text.split('## References',1)
            cited=set(re.findall(r'\[(\d+)\]',body));listed=set(re.findall(r'^\[(\d+)\]',refs,re.M))
            if cited!=listed:failures.append(f'Citation mismatch: uncited={listed-cited}; undefined={cited-listed}')
        claims_path=manuscript.with_suffix('.claims.json')
        if not claims_path.exists():failures.append('Missing numerical claim provenance manifest')
        else:
            claims=json.loads(claims_path.read_text())
            if not claims:failures.append('Empty numerical claim manifest')
            for claim in claims:
                source=pd.read_csv(run/'exports'/claim['csv'])
                for key,value in claim['where'].items():source=source[source[key].astype(str)==str(value)]
                if len(source)!=1:failures.append(f'Ambiguous/missing claim source: {claim}');continue
                expected=f"{float(source.iloc[0][claim['column']]):.{claim['decimals']}f}"
                if expected!=claim['rendered'] or claim['text'] not in text:
                    failures.append(f'Claim differs from result CSV/text: {claim}')
        if re.search(r'partition 10.{0,80}(significant|clear gain)',text,re.I):
            failures.append('Partition 10 significance language requires explicit manual statistical review')
    if failures:
        print('\n'.join('FAIL: '+s for s in sorted(set(failures))))
        return 1
    print('PASS: manuscript numbers consistent with final experiment artifacts')
    return 0


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--manuscript',type=Path)
    args=p.parse_args();run=ROOT/'revision_artifacts/runs'/args.run_id
    sys.exit(check(run,args.manuscript or run/'manuscript/revised_manuscript.md'))
