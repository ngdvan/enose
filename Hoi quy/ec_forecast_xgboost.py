#!/usr/bin/env python3
"""Forecast seconds 9-16 from seconds 1-8, then evaluate XGBoost.

The conditional VAE (CVAE) and conditional GAN (cGAN) are fitted inside each
outer run-group fold.  XGBoost comparisons use identical partitions:
observed 8 s, observed 8 s + generated 8 s, and an oracle real 16 s.
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import time
from pathlib import Path

import numpy as np
from sklearn.preprocessing import RobustScaler
from xgboost import XGBRegressor

from ec_improvement_benchmark import features, score

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ec_forecast_xgboost"


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def run(seed: int = 42, epochs: int = 100, mc_samples: int = 16, trees: int = 800) -> dict:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    d = dict(np.load(ROOT / "ec_improvements" / "raw_sequences.npz"))
    x, y, groups, folds, offsets = (d[k] for k in
        ("sequences", "targets", "groups", "folds", "offsets"))
    x = x[:, :16]  # exactly seconds 1-16 at the cache's one-second spacing
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    class CVAE(nn.Module):
        def __init__(self, latent: int = 32):
            super().__init__()
            self.context = nn.Sequential(nn.Flatten(), nn.Linear(8 * 16, 128), nn.GELU())
            self.prior = nn.Linear(128, 2 * latent)
            self.posterior = nn.Sequential(nn.Flatten(), nn.Linear(16 * 16, 192), nn.GELU(),
                                           nn.Linear(192, 2 * latent))
            self.decoder = nn.Sequential(nn.Linear(128 + latent, 192), nn.GELU(),
                                         nn.Linear(192, 8 * 16))
            self.latent = latent

        @staticmethod
        def split(params):
            mu, lv = params.chunk(2, dim=1)
            return mu, lv.clamp(-8, 8)

        def forward(self, context, future):
            h = self.context(context)
            pm, plv = self.split(self.prior(h))
            qm, qlv = self.split(self.posterior(torch.cat([context, future], dim=1)))
            z = qm + torch.exp(.5 * qlv) * torch.randn_like(qm)
            return self.decoder(torch.cat([h, z], 1)).reshape(-1, 8, 16), pm, plv, qm, qlv

        def generate(self, context, samples: int):
            h = self.context(context); pm, plv = self.split(self.prior(h)); predictions = []
            for _ in range(samples):
                z = pm + torch.exp(.5 * plv) * torch.randn_like(pm)
                predictions.append(self.decoder(torch.cat([h, z], 1)).reshape(-1, 8, 16))
            return torch.stack(predictions).mean(0)

    class Generator(nn.Module):
        def __init__(self, noise: int = 32):
            super().__init__(); self.noise = noise
            self.net = nn.Sequential(nn.Linear(8 * 16 + noise, 256), nn.GELU(),
                                     nn.Linear(256, 256), nn.GELU(), nn.Linear(256, 8 * 16))
        def forward(self, context, z):
            return self.net(torch.cat([context.flatten(1), z], 1)).reshape(-1, 8, 16)

    class Discriminator(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(16 * 16, 256), nn.LeakyReLU(.2),
                                     nn.Linear(256, 64), nn.LeakyReLU(.2), nn.Linear(64, 1))
        def forward(self, context, future):
            return self.net(torch.cat([context, future], 1).flatten(1))

    rows, forecast_rows = [], []
    for fold in range(1, 6):
        started = time.perf_counter()
        outer_groups = np.unique(groups[folds != fold]); rng = np.random.default_rng(seed + fold)
        rng.shuffle(outer_groups); val_groups = outer_groups[:max(1, len(outer_groups) // 10)]
        train = (folds != fold) & ~np.isin(groups, val_groups)
        val = (folds != fold) & np.isin(groups, val_groups) & (offsets == 0)
        test = (folds == fold) & (offsets == 0)
        scaler = RobustScaler().fit(x[train].reshape(-1, 16))
        transform = lambda m: scaler.transform(x[m].reshape(-1, 16)).reshape(-1, 16, 16).astype("float32")
        xtr, xv, xt = transform(train), transform(val), transform(test)
        loader = DataLoader(TensorDataset(torch.from_numpy(xtr[:, :8]), torch.from_numpy(xtr[:, 8:])),
                            batch_size=64, shuffle=True)
        cv, fv = torch.from_numpy(xv[:, :8]).to(device), torch.from_numpy(xv[:, 8:]).to(device)

        seed_all(seed + 1000 * fold); cvae = CVAE().to(device)
        opt = torch.optim.AdamW(cvae.parameters(), 1e-3); best = np.inf; state = None; patience = 15
        for ce in range(epochs):
            cvae.train()
            for context, future in loader:
                context, future = context.to(device), future.to(device); opt.zero_grad(set_to_none=True)
                pred, pm, plv, qm, qlv = cvae(context, future)
                rec = nn.functional.mse_loss(pred, future)
                kl = .5 * torch.mean(plv - qlv + (qlv.exp() + (qm - pm).square()) / plv.exp() - 1)
                (rec + 1e-3 * kl).backward(); opt.step()
            cvae.eval()
            with torch.no_grad():
                pred, pm, plv, qm, qlv = cvae(cv, fv)
                vl = float(nn.functional.mse_loss(pred, fv) + 1e-3 * .5 *
                    torch.mean(plv - qlv + (qlv.exp() + (qm - pm).square()) / plv.exp() - 1))
            if vl < best - 1e-5: best, state, patience = vl, copy.deepcopy(cvae.state_dict()), 15
            else:
                patience -= 1
                if patience == 0: break
        cvae.load_state_dict(state); cvae.eval()

        seed_all(seed + 2000 * fold); gen, disc = Generator().to(device), Discriminator().to(device)
        go, do = torch.optim.AdamW(gen.parameters(), 2e-4), torch.optim.AdamW(disc.parameters(), 2e-4)
        gb, gs, gpat = np.inf, None, 15
        for ge in range(epochs):
            gen.train(); disc.train()
            for context, future in loader:
                context, future = context.to(device), future.to(device); z = torch.randn(len(context), gen.noise, device=device)
                fake = gen(context, z)
                do.zero_grad(set_to_none=True)
                dl = nn.functional.binary_cross_entropy_with_logits(disc(context, future), torch.ones((len(context), 1), device=device)) + nn.functional.binary_cross_entropy_with_logits(disc(context, fake.detach()), torch.zeros((len(context), 1), device=device))
                dl.backward(); do.step(); go.zero_grad(set_to_none=True)
                adv = nn.functional.binary_cross_entropy_with_logits(disc(context, fake), torch.ones((len(context), 1), device=device))
                (nn.functional.l1_loss(fake, future) + .01 * adv).backward(); go.step()
            gen.eval()
            with torch.no_grad():
                vf = gen(cv, torch.zeros(len(cv), gen.noise, device=device)); vl = float(nn.functional.l1_loss(vf, fv))
            if vl < gb - 1e-5: gb, gs, gpat = vl, copy.deepcopy(gen.state_dict()), 15
            else:
                gpat -= 1
                if gpat == 0: break
        gen.load_state_dict(gs); gen.eval()

        def forecast(model_name, a):
            context = torch.from_numpy(a[:, :8]).to(device)
            with torch.no_grad():
                if model_name == "cvae": future = cvae.generate(context, mc_samples)
                else:
                    preds = [gen(context, torch.randn(len(context), gen.noise, device=device)) for _ in range(mc_samples)]
                    future = torch.stack(preds).mean(0)
            scaled = torch.cat([context, future], 1).cpu().numpy()
            return scaler.inverse_transform(scaled.reshape(-1, 16)).reshape(-1, 16, 16)

        observed8 = lambda m: features(x[m, :8], "physics")
        real16 = lambda m: features(x[m, :16], "physics")
        generated = {name: (forecast(name, xtr), forecast(name, xv), forecast(name, xt))
                     for name in ("cvae", "cgan")}
        variants = [("observed_8s", observed8(train), observed8(val), observed8(test)),
                    ("oracle_real_16s", real16(train), real16(val), real16(test))]
        variants += [(f"{name}_generated_16s", *(features(a, "physics") for a in arrays))
                     for name, arrays in generated.items()]
        for name, ftr, fva, fte in variants:
            model = XGBRegressor(n_estimators=trees, max_depth=3, learning_rate=.03, subsample=.8,
                colsample_bytree=.8, objective="reg:squarederror", n_jobs=-1, random_state=seed)
            model.fit(ftr, y[train], eval_set=[(fva, y[val])], verbose=False)
            rows.append({"fold": fold, "model": name, "metrics": score(y[test], model.predict(fte))})
        for name, arrays in generated.items():
            err = arrays[2][:, 8:] - x[test, 8:16]
            forecast_rows.append({"fold": fold, "generator": name, "mae": float(np.mean(np.abs(err))),
                                  "rmse": float(np.sqrt(np.mean(err ** 2)))})
        print(json.dumps({"fold": fold, "cvae_epochs": ce + 1, "cgan_epochs": ge + 1,
                          "seconds": time.perf_counter() - started}), flush=True)

    result = {"seed": seed, "observation_seconds": 8, "forecast_seconds": 8,
              "sampling": "first 16 cached one-second-spaced rows",
              "protocol": "five outer run folds; group validation; train-only scaling; offset-0 validation/test",
              "xgboost_trees": trees,
              "models": "CVAE and conditional GAN; Monte Carlo mean continuation; physics-feature XGBoost",
              "results": rows, "forecast_metrics": forecast_rows}
    OUT.mkdir(exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=100); p.add_argument("--mc-samples", type=int, default=16)
    p.add_argument("--trees", type=int, default=800)
    a = p.parse_args(); run(a.seed, a.epochs, a.mc_samples, a.trees)
