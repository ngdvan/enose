#!/usr/bin/env python3
"""Group-safe 16x64 VAE benchmarks: VAE-LSTM and VAE/XGBoost hybrids."""
from __future__ import annotations

import argparse
import copy
import json
import random
import time
from pathlib import Path

import numpy as np
from sklearn.preprocessing import RobustScaler, StandardScaler
from xgboost import XGBRegressor

from ec_improvement_benchmark import features, score

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ec_vae"


def seed_all(seed: int) -> None:
    random.seed(seed); np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def run(seed: int, vae_epochs: int, reg_epochs: int, beta: float) -> dict:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    d = dict(np.load(ROOT / "ec_improvements" / "raw_sequences.npz"))
    x, y, groups, folds, offsets = (d[k] for k in
                                     ("sequences", "targets", "groups", "folds", "offsets"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    class VAE(nn.Module):
        def __init__(self, latent=64):
            super().__init__(); self.latent = latent
            self.encoder = nn.Sequential(
                nn.Conv2d(1, 16, 3, 2, 1), nn.GELU(),   # 8 x 32
                nn.Conv2d(16, 32, 3, 2, 1), nn.GELU())  # 4 x 16
            self.mu = nn.Linear(32 * 4 * 16, latent); self.logvar = nn.Linear(32 * 4 * 16, latent)
            self.decode_fc = nn.Linear(latent, 32 * 4 * 16)
            self.decoder = nn.Sequential(
                nn.ConvTranspose2d(32, 16, 4, 2, 1), nn.GELU(),
                nn.ConvTranspose2d(16, 1, 4, 2, 1))
        def encode(self, z):
            h = self.encoder(z).flatten(1); return self.mu(h), self.logvar(h).clamp(-10, 10)
        def forward(self, z):
            mu, logvar = self.encode(z)
            sample = mu + torch.exp(.5 * logvar) * torch.randn_like(mu)
            return self.decoder(self.decode_fc(sample).reshape(-1, 32, 4, 16)), mu, logvar

    class LatentLSTM(nn.Module):
        def __init__(self):
            super().__init__(); self.rnn = nn.LSTM(8, 64, 2, batch_first=True, dropout=.2)
            self.head = nn.Sequential(nn.Linear(64, 32), nn.GELU(), nn.Linear(32, 2))
        def forward(self, z): return self.head(self.rnn(z.reshape(-1, 8, 8))[0][:, -1])

    rows = []
    for fold in range(1, 6):
        fold_start = time.perf_counter()
        outer_groups = np.unique(groups[folds != fold]); rng = np.random.default_rng(seed + fold)
        rng.shuffle(outer_groups); val_groups = outer_groups[:max(1, len(outer_groups) // 10)]
        train = (folds != fold) & ~np.isin(groups, val_groups)
        val = (folds != fold) & np.isin(groups, val_groups) & (offsets == 0)
        test = (folds == fold) & (offsets == 0)
        sx = RobustScaler().fit(x[train].reshape(-1, 16)); sy = StandardScaler().fit(y[train])
        tx = lambda m: sx.transform(x[m].reshape(-1, 16)).reshape(-1, 64, 16).astype("float32")
        ty = lambda m: sy.transform(y[m]).astype("float32")
        xtr, xv, xt = tx(train), tx(val), tx(test)
        # Images are explicitly sensor x time: B x 1 x 16 x 64.
        image = lambda a: torch.from_numpy(a.transpose(0, 2, 1)[:, None]).float()
        loader = DataLoader(TensorDataset(image(xtr)), batch_size=64, shuffle=True)
        iv, it = image(xv).to(device), image(xt).to(device)

        seed_all(seed + fold); vae = VAE().to(device); opt = torch.optim.AdamW(vae.parameters(), 1e-3)
        best, state, patience = np.inf, None, 15
        for ve in range(vae_epochs):
            vae.train()
            for (xb,) in loader:
                xb = xb.to(device); opt.zero_grad(set_to_none=True); rec, mu, lv = vae(xb)
                rec_loss = nn.functional.mse_loss(rec, xb)
                kl = -.5 * torch.mean(1 + lv - mu.square() - lv.exp())
                loss = rec_loss + beta * kl; loss.backward(); opt.step()
            vae.eval()
            with torch.no_grad():
                rec, mu, lv = vae(iv); vr = nn.functional.mse_loss(rec, iv)
                vk = -.5 * torch.mean(1 + lv - mu.square() - lv.exp()); vl = float(vr + beta * vk)
            if vl < best - 1e-5:
                best, patience, state = vl, 15, copy.deepcopy(vae.state_dict())
            else:
                patience -= 1
                if patience == 0: break
        vae.load_state_dict(state); vae.eval()
        def encode(a):
            with torch.no_grad(): return vae.encode(image(a).to(device))[0].cpu().numpy()
        ztr, zv, zt = encode(xtr), encode(xv), encode(xt)
        with torch.no_grad():
            rec, mu, lv = vae(iv)
            val_rec = float(nn.functional.mse_loss(rec, iv)); val_kl = float(-.5 * torch.mean(1 + lv - mu.square() - lv.exp()))

        # VAE-LSTM uses the posterior mean for deterministic concentration prediction.
        lstm = LatentLSTM().to(device); opt_l = torch.optim.AdamW(lstm.parameters(), 1e-3, weight_decay=1e-4)
        lloader = DataLoader(TensorDataset(torch.from_numpy(ztr), torch.from_numpy(ty(train))),
                             batch_size=64, shuffle=True)
        zv_t, yv_t = torch.from_numpy(zv).to(device), torch.from_numpy(ty(val)).to(device)
        lbest, lstate, lpat = np.inf, None, 20
        for le in range(reg_epochs):
            lstm.train()
            for zb, yb in lloader:
                zb, yb = zb.to(device), yb.to(device); opt_l.zero_grad(set_to_none=True)
                loss = nn.functional.huber_loss(lstm(zb), yb); loss.backward(); opt_l.step()
            lstm.eval()
            with torch.no_grad(): vl = float(nn.functional.huber_loss(lstm(zv_t), yv_t))
            if vl < lbest - 1e-5:
                lbest, lpat, lstate = vl, 20, copy.deepcopy(lstm.state_dict())
            else:
                lpat -= 1
                if lpat == 0: break
        lstm.load_state_dict(lstate); lstm.eval()
        with torch.no_grad(): pred = sy.inverse_transform(lstm(torch.from_numpy(zt).to(device)).cpu().numpy())
        common = {"fold": fold, "device": str(device), "latent_dim": 64, "beta": beta,
                  "vae_epochs": ve + 1, "vae_val_reconstruction_mse": val_rec, "vae_val_kl": val_kl}
        rows.append({**common, "model": "vae_lstm", "regressor_epochs": le + 1,
                     "metrics": score(y[test], pred)})

        for name, ftr, fva, fte in [
            ("vae_xgboost", ztr, zv, zt),
            ("physics_xgboost_control", features(x[train], "physics"),
             features(x[val], "physics"), features(x[test], "physics")),
            ("vae_physics_xgboost", np.c_[ztr, features(x[train], "physics")],
             np.c_[zv, features(x[val], "physics")], np.c_[zt, features(x[test], "physics")])]:
            model = XGBRegressor(n_estimators=800, max_depth=3, learning_rate=.03, subsample=.8,
                colsample_bytree=.8, objective="reg:squarederror", n_jobs=-1, random_state=seed)
            model.fit(ftr, y[train], eval_set=[(fva, y[val])], verbose=False)
            rows.append({**common, "model": name, "feature_count": int(ftr.shape[1]),
                         "metrics": score(y[test], model.predict(fte))})
        print(json.dumps({"fold": fold, "seconds": time.perf_counter() - fold_start,
                          "models": [r["model"] for r in rows[-4:]]}), flush=True)

    result = {"seed": seed, "image_shape": [1, 16, 64], "orientation": "sensor x time",
              "protocol": "five outer run folds; group validation; train-only scaling; offset-0 test",
              "results": rows}
    OUT.mkdir(exist_ok=True); (OUT / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--seed", type=int, default=42)
    p.add_argument("--vae-epochs", type=int, default=100); p.add_argument("--reg-epochs", type=int, default=150)
    p.add_argument("--beta", type=float, default=1e-4); a = p.parse_args(); seed_all(a.seed)
    run(a.seed, a.vae_epochs, a.reg_epochs, a.beta)
