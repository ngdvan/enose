"""Resumable revision experiments. All writes are contained in v2.2.

python code/run_major_revision.py --run-id revision_001 --suite all
Smoke runs are explicitly marked and cannot pass the publication gate.
"""
import argparse
import json
import time
from functools import lru_cache
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from sklearn.cross_decomposition import PLSRegression
from sklearn.svm import SVR
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from xgboost import XGBRegressor
import same_device_session_transfer as core
import co_ethylene_session_transfer as co
import advanced_validation as av
import generic_ssl
from revision_common import ROOT, SEEDS, PRIMARY_POLICY, dump, sha256, metrics, split_groups


def windows(data, indices, position='early', augmented=True):
    x, y, g = [], [], []
    for i in indices:
        raw = np.asarray(data['raw'][i], dtype=np.float32)
        if len(raw) < 68:
            raise ValueError('Exposure shorter than required window plus augmentation')
        if position == 'full':
            # Five equal-length phase grids; zero offset spans both endpoints.
            for offset in range(5 if augmented else 1):
                grid = np.linspace(offset, len(raw)-1, 64)
                x.append(np.stack([np.interp(grid, np.arange(len(raw)), raw[:, j])
                                   for j in range(raw.shape[1])], axis=1))
                y.append(data['targets'][i]); g.append(data['groups'][i])
        else:
            start = {'early': 0, 'middle': (len(raw)-68)//2, 'late': len(raw)-68}[position]
            for offset in range(5 if augmented else 1):
                x.append(raw[start+offset:start+offset+64])
                y.append(data['targets'][i]); g.append(data['groups'][i])
    return np.asarray(x, np.float32), np.asarray(y, np.float32), np.asarray(g)


@lru_cache(maxsize=2)
def load(dataset):
    av.configure(dataset)
    return core.load_exposures(core.DATA) if dataset == 'nh3_h2' else co.load_data(co.CACHE)


def prepare(dataset, data, fold=0, window='early'):
    av.configure(dataset)
    if dataset == 'nh3_h2':
        test_session = fold or 6
        adapt_session = (test_session-2) % 6 + 1
        pre = np.flatnonzero(~np.isin(data['sessions'], [test_session, adapt_session]))
        adapt = np.flatnonzero(data['sessions'] == adapt_session)
        test = np.flatnonzero(data['sessions'] == test_session)
        px, _, pg = windows(data, pre, window)
        tx, ty, tg = windows(data, test, window, False)
        ax, ay, ag = windows(data, adapt, window)
        ay0, ag0 = data['targets'][adapt], data['groups'][adapt]
    else:
        blocks = data['blocks']
        if fold:
            chunks = np.array_split(np.unique(data['groups']), 7)
            mapping = {int(g): i+1 for i, chunk in enumerate(chunks) for g in chunk}
            blocks = np.array([mapping[int(g)] for g in data['groups']])
        adapt_block = fold+3 if fold else 4
        pre = np.isin(blocks, range(adapt_block-3, adapt_block))
        adapt = blocks == adapt_block
        test = (blocks == adapt_block+1) & (data['offsets'] == 0)
        zero = adapt & (data['offsets'] == 0)
        px, pg = data['x'][pre], data['groups'][pre]
        ax, ay, ag = data['x'][adapt], data['y'][adapt], data['groups'][adapt]
        ay0, ag0 = data['y'][zero], data['groups'][zero]
        tx, ty, tg = data['x'][test], data['y'][test], data['groups'][test]
    assert not set(pg) & set(ag) and not set(pg) & set(tg) and not set(ag) & set(tg)
    scaler = core.SensorScaler().fit(px)
    return dict(px=scaler.transform(px), ax=scaler.transform(ax), ay=ay, ag=ag,
                ay0=ay0, ag0=ag0, tx=scaler.transform(tx), ty=ty, tg=tg,
                pre_groups=np.unique(pg).tolist(), adapt_groups=np.unique(ag).tolist(),
                test_groups=np.unique(tg).tolist())


def choose(prepared, budget, seed, design):
    y = prepared['ay0']
    unique, first = np.unique(y, axis=0, return_index=True)
    if budget > len(unique):
        raise ValueError(f'Requested {budget} pairs, only {len(unique)} available')
    if design == 'random':
        order = np.random.default_rng(seed).permutation(first)
    else:
        z = unique / core.TARGET_SCALE
        rng = np.random.default_rng(seed)
        chosen = [int(rng.integers(len(z)))]
        distance = np.linalg.norm(z-z[chosen[0]], axis=1)
        while len(chosen) < len(z):
            distance[chosen] = -np.inf
            idx = int(np.argmax(distance + rng.uniform(0, 1e-8, len(z))))
            chosen.append(idx)
            distance = np.minimum(distance, np.linalg.norm(z-z[idx], axis=1))
        order = first[chosen]
    selected = prepared['ag0'][order[:budget]]
    m = np.isin(prepared['ag'], selected)
    x, y, g = prepared['ax'][m], prepared['ay'][m], prepared['ag'][m]
    tr, va = split_groups(g, seed)
    return x, y, g, tr, va


def classical(policy, x, y, vx, vy, tx, seed):
    # Fit all transforms on fitting labels/windows only; choose hyperparameters
    # on the identical adaptation group holdout used by neural policies.
    fx, fv, ft = [a.reshape(len(a), -1) for a in (x, vx, tx)]
    ys, vys = y/core.TARGET_SCALE, vy/core.TARGET_SCALE
    if policy == 'plsr':
        candidates = [make_pipeline(StandardScaler(), PLSRegression(n_components=k, scale=False))
                      for k in [1, 2, 3, 5, 8, 12] if k < min(len(x), fx.shape[1])]
    elif policy == 'svr':
        candidates = [make_pipeline(StandardScaler(), MultiOutputRegressor(SVR(C=c, gamma=gamma, epsilon=e)))
                      for c in [.1, 1., 10.] for gamma in ['scale', .001] for e in [.01, .1]]
    elif policy == 'extra_trees':
        candidates = [ExtraTreesRegressor(n_estimators=300, min_samples_leaf=2, random_state=seed, n_jobs=4)]
    elif policy == 'xgboost':
        candidates = [MultiOutputRegressor(XGBRegressor(n_estimators=300, max_depth=3, learning_rate=.03,
                      subsample=.9, colsample_bytree=.9, random_state=seed, n_jobs=4))]
    else:
        raise ValueError(policy)
    best, score, config = None, float('inf'), None
    for candidate in candidates:
        candidate.fit(fx, ys)
        value = float(np.abs(candidate.predict(fv)-vys).mean())
        if value < score:
            score, best, config = value, candidate, str(candidate)
    pred = np.clip(best.predict(ft)*core.TARGET_SCALE, 0, core.TARGET_SCALE)
    return pred, {'selection': 'adaptation-only normalized MAE', 'validation_mae': score, 'estimator': config}


def state_for(out, dataset, fold, window, seed, p, args, generic=False, variant='full'):
    path = out/'checkpoints'/f'{dataset}_f{fold}_{window}_s{seed}_{"generic" if generic else variant}.pt'
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return torch.load(path, map_location='cpu', weights_only=True)
    if generic:
        state, history = generic_ssl.pretrain(p['px'], args.pretrain_epochs, seed)
    else:
        state, history = core.pretrain(p['px'], args.pretrain_epochs, seed, **av.VARIANTS[variant])
    torch.save({k: v.cpu() for k, v in state.items()}, path)
    dump(path.with_suffix('.json'), {'loss': history, 'seed': seed, 'pretrain_groups': p['pre_groups']})
    return state


def raw_suite(out, args, suite):
    for dataset in ['nh3_h2', 'co_ethylene']:
        data, audit = load(dataset)
        dump(out/'data_audit'/f'{dataset}.json', audit)
        folds = list(range(1, 7 if dataset=='nh3_h2' else 4)) if suite=='multifold' else [0]
        positions = ['middle', 'late', 'full'] if suite=='window' else ['early']
        if suite=='window' and dataset!='nh3_h2':
            continue
        for fold in folds:
          for window in positions:
            p = prepare(dataset, data, fold, window)
            maximum = len(np.unique(p['ay0'], axis=0))
            budgets = sorted(set([5, 10, 20, maximum] + ([40] if dataset=='nh3_h2' else [])))
            if suite in ['multifold', 'window', 'ablation']:
                budgets = [maximum] if suite!='ablation' else [5, maximum]
            if args.smoke:
                budgets = [5]
            policies = {'fixed': ['scratch', 'frozen', PRIMARY_POLICY],
                        'multifold': ['scratch', 'frozen', PRIMARY_POLICY],
                        'classical': ['plsr', 'svr', 'extra_trees', 'xgboost'],
                        'generic': ['generic_ssl'], 'design': ['scratch', PRIMARY_POLICY],
                        'window': ['scratch', PRIMARY_POLICY],
                        'ablation': list(av.VARIANTS)[1:]}[suite]
            designs = ['random'] if suite=='design' else ['farthest']
            for seed in (SEEDS[:1] if args.smoke else SEEDS):
              for budget in budgets:
                for design in designs:
                  x, y, g, tr, va = choose(p, budget, seed, design)
                  for policy in policies:
                    identity = dict(dataset=dataset, fold=fold, seed=seed, budget=budget,
                                    design=design, window=window, policy=policy)
                    stem = f'{dataset}_f{fold}_s{seed}_b{budget}_{design}_{window}_{policy}'
                    path = out/'jobs'/f'{stem}.json'
                    if path.exists():
                        continue
                    started = time.time(); model = None
                    if policy in ['plsr', 'svr', 'extra_trees', 'xgboost']:
                        pred, history = classical(policy, x[tr], y[tr], x[va], y[va], p['tx'], seed)
                    else:
                        generic = policy=='generic_ssl'
                        variant = policy if policy in av.VARIANTS else 'full'
                        initial = None if policy=='scratch' else state_for(out,dataset,fold,window,seed,p,args,generic,variant)
                        if generic:
                            model, history = generic_ssl.fit(x[tr],y[tr],x[va],y[va],initial,args.epochs,seed)
                        else:
                            v = av.VARIANTS[variant]
                            model, history = core.fit_neural_with_history(x[tr],y[tr],initial,policy=='frozen',args.epochs,seed,
                                val_x=x[va],val_y=y[va],use_sensor_ids=v['use_sensor_ids'],use_attention=v['use_attention'])
                        pred = core.predict(model, p['tx'])
                    rows = [identity | dict(gas=gas) | metrics(p['ty'][:,j],pred[:,j],core.TARGET_SCALE[j])
                            for j, gas in enumerate(core.TARGETS)]
                    predictions = [identity | dict(gas=gas, exposure=int(group), true=float(p['ty'][i,j]), prediction=float(pred[i,j]))
                                   for i, group in enumerate(p['tg']) for j,gas in enumerate(core.TARGETS)]
                    size = {}
                    if model is not None:
                        total = sum(a.numel() for a in model.parameters())
                        enc = sum(a.numel() for a in model.encoder.parameters())
                        size = dict(total=total,encoder=enc,head=total-enc,trainable=sum(a.numel() for a in model.parameters() if a.requires_grad),
                                    fitting_exposures=len(np.unique(g[tr])), fitting_windows=int(tr.sum()),
                                    parameters_per_fitting_exposure=total/len(np.unique(g[tr])))
                    dump(path, dict(identity=identity, metrics=rows, predictions=predictions, training=history, model_size=size,
                         fit_groups=np.unique(g[tr]).tolist(), validation_groups=np.unique(g[va]).tolist(),
                         split={k:p[k] for k in ['pre_groups','adapt_groups','test_groups']}, seconds=time.time()-started))
                    print(json.dumps(identity | {'seconds':round(time.time()-started,2)}),flush=True)
            if args.smoke:
                break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--suite', choices=['all','fixed','multifold','classical','generic','design','window','ablation','drift'],default='all')
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--pretrain-epochs',type=int,default=60)
    parser.add_argument('--epochs',type=int,default=120)
    args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():
        parser.error('run-id must be a simple directory name')
    if args.smoke:
        args.pretrain_epochs,args.epochs=1,2
    torch.set_num_threads(4)
    out=ROOT/'revision_artifacts'/'runs'/args.run_id
    out.mkdir(parents=True,exist_ok=True)
    config=dict(seeds=SEEDS[:1] if args.smoke else SEEDS,primary_policy=PRIMARY_POLICY,
                pretrain_epochs=args.pretrain_epochs,epochs=args.epochs,smoke=args.smoke,
                input_hashes={str(p):sha256(p) for p in [core.DATA,co.CACHE]},
                code_hashes={p.name:sha256(p) for p in (ROOT/'code').glob('*.py')})
    config_path=out/'protocol.json'
    if config_path.exists() and json.loads(config_path.read_text())!=config:
        raise ValueError('Immutable run configuration changed; use a new run-id')
    dump(config_path,config)
    suites=['classical','fixed','multifold','generic','design','window','ablation','drift'] if args.suite=='all' else [args.suite]
    for suite in suites:
        if suite=='drift':
            from revision_drift import run
            run(out,args)
        else:
            raw_suite(out,args,suite)
        dump(out/f'{suite}_completed.json',{'completed':True,'smoke':args.smoke})
    print('Requested suites completed.',flush=True)


if __name__=='__main__':
    main()
