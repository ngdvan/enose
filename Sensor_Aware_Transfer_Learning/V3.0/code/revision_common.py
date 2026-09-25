"""Locked revision protocol and statistically explicit artifact helpers."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [42 + 100 * i for i in range(10)]
PRIMARY_POLICY = 'fine_tuned'


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')
    tmp.replace(path)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def metrics(y, pred, scale):
    y, pred = np.asarray(y), np.asarray(pred)
    if not len(y) or not np.isfinite(pred).all():
        raise ValueError('Empty or nonfinite predictions')
    error = y - pred
    denom = np.square(y - y.mean()).sum()
    return dict(mae=float(np.abs(error).mean()), rmse=float(np.sqrt(np.square(error).mean())),
                r2=float(1 - np.square(error).sum() / denom) if denom > 0 else None,
                q90=float(np.quantile(np.abs(error), .9)),
                nmae=float(np.abs(error).mean() / scale), n_test=len(y))


def split_groups(groups, seed):
    unique = np.unique(groups)
    if len(unique) < 2:
        raise ValueError('At least two adaptation groups required for holdout')
    np.random.default_rng(seed).shuffle(unique)
    val = unique[:max(1, round(.2 * len(unique)))]
    return ~np.isin(groups, val), np.isin(groups, val)


def paired_summary(frame, left='scratch', right=PRIMARY_POLICY, n_boot=5000):
    """Crossed seed/fold bootstrap of paired MAEs; never pool repeated predictions.

    Folds are equally weighted. Seed and fold indices are sampled independently.
    Conditional on the observed test exposures. Overlapping training folds mean
    these intervals are descriptive, not independent-population confidence bounds.
    """
    keys = ['dataset', 'fold', 'seed', 'budget', 'design', 'window', 'gas']
    a = frame[frame.policy == left]
    b = frame[frame.policy == right]
    paired = a.merge(b, on=keys, suffixes=('_a', '_b'), validate='one_to_one')
    rows = []
    for key, d in paired.groupby(['dataset', 'budget', 'design', 'window', 'gas']):
        matrix = d.pivot(index='seed', columns='fold', values='mae_a')
        other = d.pivot(index='seed', columns='fold', values='mae_b').reindex_like(matrix)
        if matrix.isna().any().any() or other.isna().any().any():
            raise ValueError('Incomplete seed/fold pairing')
        delta = (matrix - other).to_numpy()
        rng = np.random.default_rng(42)
        means = np.empty(n_boot)
        for i in range(n_boot):
            seeds = rng.integers(delta.shape[0], size=delta.shape[0])
            folds = rng.integers(delta.shape[1], size=delta.shape[1])
            means[i] = delta[np.ix_(seeds, folds)].mean()
        lo, hi = np.quantile(means, [.025, .975])
        rows.append(dict(zip(['dataset', 'budget', 'design', 'window', 'gas'], key)) | dict(
            comparator=left, policy=right, scratch_mae=float(matrix.to_numpy().mean()),
            transfer_mae=float(other.to_numpy().mean()), improvement=float(delta.mean()),
            relative_improvement_pct=float(100 * delta.mean() / matrix.to_numpy().mean()),
            ci_low=float(lo), ci_high=float(hi), n_seeds=len(matrix), n_folds=len(matrix.columns),
            across_fold_sd=float(other.mean().std(ddof=1)) if len(matrix.columns)>1 else None,
            n_paired_predictions=int(d.n_test_a.sum()),
            interpretation='clear improvement in this analysis' if lo > 0 else 'no clear improvement',
            bootstrap_unit='crossed seed and fold; conditional on observed exposures'))
    return pd.DataFrame(rows)
