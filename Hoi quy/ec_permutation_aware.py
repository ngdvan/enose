#!/usr/bin/env python3
"""Group-safe permutation-aware sensor-set benchmarks for EC gas regression."""
from __future__ import annotations

import argparse
import copy
import json
import random
import time
from pathlib import Path

import numpy as np
from sklearn.preprocessing import RobustScaler, StandardScaler

from ec_improvement_benchmark import score

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ec_permutation_aware"


def seed_all(seed: int) -> None:
    random.seed(seed); np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def run(seed: int, max_epochs: int) -> dict:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    data = dict(np.load(ROOT / "ec_improvements" / "raw_sequences.npz"))
    x, y, groups, folds, offsets = (data[k] for k in
                                     ("sequences", "targets", "groups", "folds", "offsets"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    class SensorTokenEncoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv1d(1, 16, 5, padding=2), nn.GELU(),
                nn.Conv1d(16, 32, 5, padding=4, dilation=2), nn.GELU(),
                nn.AdaptiveAvgPool1d(1), nn.Flatten())
        def forward(self, z):
            b, t, s = z.shape
            return self.net(z.permute(0, 2, 1).reshape(b * s, 1, t)).reshape(b, s, 32)

    class SensorSetModel(nn.Module):
        def __init__(self, kind: str, use_identity: bool):
            super().__init__(); self.kind = kind; self.use_identity = use_identity
            self.temporal = SensorTokenEncoder()
            self.identity = nn.Embedding(16, 16) if use_identity else None
            dim = 48 if use_identity else 32
            self.project = nn.Sequential(nn.Linear(dim, 64), nn.GELU(), nn.LayerNorm(64))
            if kind == "set_transformer":
                layer = nn.TransformerEncoderLayer(64, 4, 128, .1, batch_first=True,
                                                   activation="gelu", norm_first=True)
                self.interact = nn.TransformerEncoder(layer, 2)
            else:
                self.interact = nn.Sequential(nn.Linear(64, 64), nn.GELU())
            self.head = nn.Sequential(nn.Linear(64, 48), nn.GELU(), nn.Dropout(.1), nn.Linear(48, 2))

        def forward(self, z, sensor_ids):
            token = self.temporal(z)
            if self.identity is not None:
                token = torch.cat([token, self.identity(sensor_ids)], dim=-1)
            token = self.interact(self.project(token))
            return self.head(token.mean(dim=1))

    configs = [("deepsets_identity", "deepsets", True),
               ("set_transformer_identity", "set_transformer", True),
               ("deepsets_no_identity", "deepsets", False)]
    permutation = np.random.default_rng(seed).permutation(16)
    rows = []
    for fold in range(1, 6):
        outer_groups = np.unique(groups[folds != fold])
        rng = np.random.default_rng(seed + fold); rng.shuffle(outer_groups)
        val_groups = outer_groups[:max(1, len(outer_groups) // 10)]
        train = (folds != fold) & ~np.isin(groups, val_groups)
        val = (folds != fold) & np.isin(groups, val_groups) & (offsets == 0)
        test = (folds == fold) & (offsets == 0)
        sx = RobustScaler().fit(x[train].reshape(-1, 16)); sy = StandardScaler().fit(y[train])
        transform_x = lambda m: sx.transform(x[m].reshape(-1, 16)).reshape(-1, 64, 16).astype("float32")
        transform_y = lambda m: sy.transform(y[m]).astype("float32")
        xtr, ytr, xv, yv, xt = transform_x(train), transform_y(train), transform_x(val), transform_y(val), transform_x(test)
        loader = DataLoader(TensorDataset(torch.from_numpy(xtr), torch.from_numpy(ytr)),
                            batch_size=64, shuffle=True)
        xv_t, yv_t, xt_t = torch.from_numpy(xv).to(device), torch.from_numpy(yv).to(device), torch.from_numpy(xt).to(device)
        ids = torch.arange(16, device=device).expand(len(xt), -1)
        ids_v = torch.arange(16, device=device).expand(len(xv), -1)
        perm_t = torch.as_tensor(permutation, device=device)

        for name, kind, use_identity in configs:
            seed_all(seed + fold)
            model = SensorSetModel(kind, use_identity).to(device)
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
            loss_fn = nn.HuberLoss(); best = np.inf; best_state = None; patience = 20
            started = time.perf_counter()
            for epoch in range(max_epochs):
                model.train()
                for xb, yb in loader:
                    xb, yb = xb.to(device), yb.to(device)
                    batch_ids = torch.arange(16, device=device).expand(len(xb), -1)
                    optimizer.zero_grad(set_to_none=True)
                    loss = loss_fn(model(xb, batch_ids), yb); loss.backward(); optimizer.step()
                model.eval()
                with torch.no_grad(): vloss = float(loss_fn(model(xv_t, ids_v), yv_t))
                if vloss < best - 1e-5:
                    best, patience, best_state = vloss, 20, copy.deepcopy(model.state_dict())
                else:
                    patience -= 1
                    if patience == 0: break
            model.load_state_dict(best_state); model.eval()
            with torch.no_grad():
                original = model(xt_t, ids).cpu().numpy()
                aligned = model(xt_t[:, :, perm_t], ids[:, perm_t]).cpu().numpy()
                mismatched = model(xt_t[:, :, perm_t], ids).cpu().numpy()
            pred_original = sy.inverse_transform(original)
            pred_aligned = sy.inverse_transform(aligned)
            pred_mismatched = sy.inverse_transform(mismatched)
            row = {"model": name, "fold": fold, "device": str(device), "epochs": epoch + 1,
                   "parameters": sum(p.numel() for p in model.parameters()),
                   "seconds": time.perf_counter() - started,
                   "permutation_zero_based": permutation.tolist(),
                   "max_aligned_prediction_difference_ppm": float(np.max(np.abs(pred_original - pred_aligned))),
                   "original_metrics": score(y[test], pred_original),
                   "aligned_permutation_metrics": score(y[test], pred_aligned),
                   "mismatched_identity_metrics": score(y[test], pred_mismatched)}
            rows.append(row); print(json.dumps(row), flush=True)
    result = {"seed": seed, "protocol": {"training": "four outer folds; 10% group validation",
              "augmentation": "five offsets in training; offset 0 only in validation/test",
              "aligned": "readings and sensor IDs permuted together",
              "mismatched": "readings permuted but IDs left fixed"}, "results": rows}
    OUT.mkdir(exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=150); a = p.parse_args()
    seed_all(a.seed); run(a.seed, a.epochs)
