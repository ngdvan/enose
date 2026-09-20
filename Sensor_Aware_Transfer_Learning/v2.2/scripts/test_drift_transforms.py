"""Real-data smoke validation for all drift budgets and target/loss variants."""
import sys
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code'))
import sensor_drift_transfer as drift
import revision_drift as revised
from revision_common import dump


def main():
    torch.set_num_threads(4)
    data=drift.load_dataset(drift.DATA)
    pre=np.flatnonzero(data['batch']<=6);adapt=np.flatnonzero(data['batch']==7)
    x=drift.FeatureScaler().fit(data['x'][pre]).transform(data['x'])
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    rows=[]
    for budget in [1,2,5,10,20]:
        selected=drift.coverage_subset(data['label'],data['concentration'],adapt,budget,42)
        tr,va=revised.split(selected,data['label'],42)
        assert not set(tr)&set(va)
        assert len(tr)+len(va)==6*budget
        transforms=['log_huber','log_fixed_huber','linear_huber','linear_mae'] if budget==20 else ['log_fixed_huber']
        for transform in transforms:
            model,means,scales,history=revised.fit(x,data['label'],data['concentration'],tr,va,None,'scratch',transform,2,42,device)
            assert np.isfinite(means).all() and np.isfinite(scales).all() and (scales>0).all()
            with torch.no_grad():assert torch.isfinite(model(torch.from_numpy(x[tr]).to(device))).all()
            rows.append(dict(budget=budget,transform=transform,fit=len(tr),validation=len(va),selection=history['selection'],finite=True))
    dump(ROOT/'revision_artifacts/drift_transform_smoke_checks.json',rows)
    print(f'PASS: {len(rows)} real-data drift budget/loss smoke checks')


if __name__=='__main__':main()
