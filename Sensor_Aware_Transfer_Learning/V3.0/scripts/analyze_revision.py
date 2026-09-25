"""Recompute revision statistics from immutable V2.2 exports; no model selection."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'v2.2/author_review/full_revision_001/evidence/exports'
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)
frames = [pd.read_csv(SOURCE / f'multifold/{d}_fold_results.csv') for d in ['nh3_h2', 'co_ethylene']]
rows = []
for gas, frame in pd.concat(frames).groupby('gas'):
    a = frame[frame.policy == 'scratch'].pivot(index='seed', columns='fold', values='mae')
    b = frame[frame.policy == 'fine_tuned'].pivot(index='seed', columns='fold', values='mae').reindex_like(a)
    assert a.shape == b.shape and not a.isna().any().any() and not b.isna().any().any()
    delta = (a-b).to_numpy()
    for seed in [42, 2026]:
        rng = np.random.default_rng(seed)
        n = 200000
        # Independent resampling of seed and fold axes, exactly the original estimand.
        seeds = rng.integers(delta.shape[0], size=(n, delta.shape[0]))
        folds = rng.integers(delta.shape[1], size=(n, delta.shape[1]))
        boot = delta[seeds[:, :, None], folds[:, None, :]].mean(axis=(1, 2))
        low, high = np.quantile(boot, [.00625, .99375])
        rows.append(dict(gas=gas, rng_seed=seed, resamples=n, folds=delta.shape[1], seeds=delta.shape[0],
                         scratch=a.to_numpy().mean(), fine_tuned=b.to_numpy().mean(),
                         difference=delta.mean(), gain_pct=100*delta.mean()/a.to_numpy().mean(),
                         adjusted_low=low, adjusted_high=high, marginal_coverage=.9875))
result = pd.DataFrame(rows)
result.to_csv(OUT/'multiplicity_sensitivity.csv', index=False)
print(result.to_string(index=False))
allruns = pd.read_csv(SOURCE/'policy_selection/all_policy_results.csv')
co = allruns[(allruns.gas=='CO') & (allruns.fold==0) & (allruns.budget==24) & (allruns.design=='farthest') & (allruns.window=='early')]
base = co[co.policy=='fine_tuned'].set_index('seed').mae
ablation = []
for variant in ['no_attention','no_temporal_mask']:
    diff = (co[co.policy==variant].set_index('seed').mae-base).to_numpy()
    boot = np.random.default_rng(42).choice(diff,(200000,len(diff))).mean(axis=1)
    lo, hi = np.quantile(boot,[.025,.975])
    ablation.append(dict(variant=variant,mean=diff.mean(),sd=diff.std(ddof=1),ci_low=lo,ci_high=hi))
pd.DataFrame(ablation).to_csv(OUT/'co_ablation_sensitivity.csv',index=False)
budget = pd.read_csv(SOURCE/'10_seed_runs/raw_response_all_runs.csv')
selected = budget[((budget.policy=='fine_tuned') & (budget.budget==10)) | ((budget.policy=='scratch') & (budget.budget==20))]
selected.groupby(['gas','policy','budget']).mae.agg(['mean','std','count']).reset_index().to_csv(OUT/'label_efficiency.csv',index=False)
inputs = [SOURCE/'multifold/nh3_h2_fold_results.csv', SOURCE/'multifold/co_ethylene_fold_results.csv', SOURCE/'10_seed_runs/raw_response_all_runs.csv', SOURCE/'policy_selection/all_policy_results.csv']
(OUT/'analysis_provenance.json').write_text(json.dumps({
    'method':'Post-review sensitivity: Bonferroni four-comparison family; crossed seed/fold percentile bootstrap, 200000 draws; second RNG seed checks Monte Carlo stability. Conditional descriptive inference; no claim of independent acquisition days.',
    'inputs':{str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}},indent=2),encoding='utf-8')
