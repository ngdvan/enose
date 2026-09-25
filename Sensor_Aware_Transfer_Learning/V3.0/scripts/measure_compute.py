"""Representative seed-42 pretraining timing; never replaces historical results."""
from pathlib import Path
import sys, time, json, platform, hashlib
ROOT=Path(__file__).resolve().parents[1]
CODE=ROOT.parent/'v2.2/code'
sys.path.insert(0,str(CODE))
import torch
import run_major_revision as run
import sensor_drift_transfer as drift
import numpy as np

OUT=ROOT/'evidence'; OUT.mkdir(exist_ok=True)
result={'scope':'Representative rerun, seed 42, fixed-split pretraining; wall time includes model initialization and training, excludes data loading/scaling and disk checkpoint writes. Does not reconstruct historical campaign cost.',
        'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,
        'gpu':torch.cuda.get_device_name() if torch.cuda.is_available() else 'CPU','runs':[],
        'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [CODE/'same_device_session_transfer.py',CODE/'sensor_drift_transfer.py',CODE/'run_major_revision.py']}}
def sync():
    if torch.cuda.is_available():torch.cuda.synchronize()
def save(): (OUT/'compute_measurement.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for dataset in ['nh3_h2','co_ethylene']:
    data,_=run.load(dataset)
    p=run.prepare(dataset,data)
    sync(); start=time.perf_counter()
    state,history=run.core.pretrain(p['px'],60,42)
    sync(); seconds=time.perf_counter()-start
    assert np.isfinite(history).all()
    result['runs'].append(dict(dataset=dataset,epochs=60,batch_size=64,windows=len(p['px']),pretraining_groups=len(p['pre_groups']),seconds=seconds,finite_loss=True))
    save(); print('TIMING',result['runs'][-1],flush=True)
    del state
# Descriptor API is measured separately if needed; raw-response timing suffices
# for the principal label-efficiency comparisons.
