"""Create checksums and environment metadata for the final experiment package."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent


def sha256(path: Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""): h.update(chunk)
    return h.hexdigest()


files=[
    PROJECT/"2407"/"TONG_NH3H2_CHUAN.xlsx",
    PROJECT/"Hoi quy"/"ethylene_CO.txt",
    PROJECT/"Hoi quy"/"ec_improvements"/"raw_sequences.npz",
    ROOT/"code"/"same_device_session_transfer.py",
    ROOT/"code"/"co_ethylene_session_transfer.py",
    ROOT/"code"/"advanced_validation.py",
]
manifest={
    "environment":{"python":platform.python_version(),"platform":platform.platform(),
                   "torch":torch.__version__,"cuda_available":torch.cuda.is_available(),
                   "cuda_device":torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                   "numpy":np.__version__},
    "commands":[
        "python code/advanced_validation.py --mode smoke",
        "python code/advanced_validation.py --mode ablations --pretrain-epochs 60 --epochs 120 --repeats 3",
        "python code/advanced_validation.py --mode folds --pretrain-epochs 60 --epochs 120 --repeats 3",
        "python code/advanced_validation.py --mode stats",
        "python paper_draft/generate_figures.py",
    ],
    "files":{},
}
for p in files:
    manifest["files"][str(p.relative_to(PROJECT))]={"bytes":p.stat().st_size,"sha256":sha256(p)}
try:
    manifest["pip_freeze"]=subprocess.check_output(["python","-m","pip","freeze"],text=True).splitlines()
except Exception as exc: manifest["pip_freeze_error"]=str(exc)
(Path(__file__).resolve().parent/"reproducibility_manifest.json").write_text(json.dumps(manifest,indent=2))
print("Wrote paper_draft/reproducibility_manifest.json")
