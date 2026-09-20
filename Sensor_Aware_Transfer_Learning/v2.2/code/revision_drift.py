"""Oracle-class drift controls with shared splits and tiny-budget safe scaling."""
from copy import deepcopy
import json
import time
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
import sensor_drift_transfer as drift
from revision_common import SEEDS, dump, metrics


def split(selected, labels, seed):
    rng=np.random.default_rng(seed)
    train,valid=[],[]
    for gas in range(6):
        ids=selected[labels[selected]==gas].copy(); rng.shuffle(ids)
        if len(ids)==1:
            train.extend(ids)
        else:
            n=max(1,round(.2*len(ids)))
            valid.extend(ids[:n]); train.extend(ids[n:])
    return np.array(train,dtype=int),np.array(valid,dtype=int)


def fit(x, labels, conc, tr, va, state, policy, transform, epochs, seed, device):
    drift.seed_all(seed)
    means=np.zeros(6,np.float32); scales=np.ones(6,np.float32)
    logged=transform.startswith('log')
    base=np.log1p(conc) if logged else conc
    if transform=='log_huber':
        for gas in range(6):
            values=base[tr[labels[tr]==gas]]
            means[gas]=values.mean()
            # Historical method retained only for the explicit scaling control.
            scales[gas]=max(values.std(),1e-3)
    elif logged:
        scales[:]=np.log1p(1000.)
    else:
        scales[:]=1000.  # Predeclared common ppm unit; no test/extra label fitting.
    targets=((base-means[labels])/scales[labels]).astype(np.float32)
    model=drift.DriftPredictor().to(device)
    if state is not None:
        model.encoder.load_state_dict(state)
    if policy=='frozen':
        for p in model.encoder.parameters(): p.requires_grad=False
    groups=[{'params':list(model.pool.parameters())+list(model.regressor.parameters()),'lr':8e-4}]
    encoder=[p for p in model.encoder.parameters() if p.requires_grad]
    if encoder: groups.append({'params':encoder,'lr':8e-5 if state is not None else 5e-4})
    opt=torch.optim.AdamW(groups,weight_decay=2e-4)
    loader=DataLoader(TensorDataset(torch.from_numpy(x[tr]),torch.from_numpy(labels[tr]),torch.from_numpy(targets[tr])),
                      batch_size=min(64,len(tr)),shuffle=True,generator=torch.Generator().manual_seed(seed))
    loss_fn=nn.functional.l1_loss if transform=='linear_mae' else lambda p,y: nn.functional.huber_loss(p,y,delta=.5)
    best=None; best_loss=float('inf'); history=[]
    for epoch in range(epochs):
        model.train()
        if policy=='frozen': model.encoder.eval()
        for xb,gb,yb in loader:
            picked=model(xb.to(device)).gather(1,gb.to(device)[:,None]).squeeze(1)
            loss=loss_fn(picked,yb.to(device)); opt.zero_grad(set_to_none=True);loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(),2.);opt.step()
        model.eval()
        if len(va):
            with torch.no_grad():
                pred=model(torch.from_numpy(x[va]).to(device)).gather(1,torch.from_numpy(labels[va]).to(device)[:,None]).squeeze(1)
                value=loss_fn(pred,torch.from_numpy(targets[va]).to(device)).item()
            history.append(value)
            if value<best_loss: best_loss,best=value,deepcopy(model.state_dict())
        # A single label/gas cannot support a disjoint validation split: final
        # checkpoint at the fixed epoch count; never duplicate a label into both.
    if best is not None: model.load_state_dict(best)
    return model,means,scales,dict(validation_loss=history,selection='adaptation holdout' if len(va) else 'fixed final epoch',
                                 means=means.tolist(),scales=scales.tolist())


def run(out,args):
    data=drift.load_dataset(drift.DATA)
    pre=np.flatnonzero(data['batch']<=6); adapt=np.flatnonzero(data['batch']==7)
    scaler=drift.FeatureScaler().fit(data['x'][pre]);x=scaler.transform(data['x'])
    labels,conc=data['label'],data['concentration']
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    for seed in (SEEDS[:1] if args.smoke else SEEDS):
        cp=out/'checkpoints'/f'drift_s{seed}.pt';cp.parent.mkdir(parents=True,exist_ok=True)
        if cp.exists(): state=torch.load(cp,map_location='cpu',weights_only=True)
        else:
            state,history=drift.pretrain(x[pre],min(40,args.pretrain_epochs),seed,device)
            torch.save({k:v.cpu() for k,v in state.items()},cp);dump(cp.with_suffix('.json'),{'loss':history})
        for budget in ([2] if args.smoke else [1,2,5,10,20]):
            selected=drift.coverage_subset(labels,conc,adapt,budget,seed)
            tr,va=split(selected,labels,seed)
            # Primary historical transform at 20 labels; tiny budgets use fixed
            # scaling to avoid degenerate standard deviation estimates.
            transforms=['log_huber','log_fixed_huber','linear_huber','linear_mae'] if budget==20 else ['log_fixed_huber']
            for transform in transforms:
              for policy in ['constant','scratch','frozen','fine_tuned']:
                if policy=='constant' and transform!=transforms[0]: continue
                path=out/'drift_jobs'/f's{seed}_b{budget}_{transform}_{policy}.json'
                if path.exists():continue
                started=time.time()
                history={};size={}
                if policy=='constant':
                    means=np.array([conc[tr[labels[tr]==gas]].mean() for gas in range(6)])
                else:
                    model,means,scales,history=fit(x,labels,conc,tr,va,None if policy=='scratch' else state,
                                                 policy,transform,args.epochs,seed,device)
                    total=sum(p.numel() for p in model.parameters());enc=sum(p.numel() for p in model.encoder.parameters())
                    size=dict(total=total,encoder=enc,head=total-enc,trainable=sum(p.numel() for p in model.parameters() if p.requires_grad),
                              fitting_exposures=len(tr),parameters_per_fitting_exposure=total/len(tr))
                rows=[];predictions=[]
                for partition in [8,9,10]:
                    ids=np.flatnonzero(data['batch']==partition)
                    if policy=='constant': pred=means[labels[ids]]
                    else:
                        model.eval()
                        with torch.no_grad():
                            reg=np.concatenate([model(torch.from_numpy(x[chunk]).to(device)).cpu().numpy()
                                                for chunk in np.array_split(ids,max(1,int(np.ceil(len(ids)/256))))])
                        value=reg[np.arange(len(ids)),labels[ids]]*scales[labels[ids]]+means[labels[ids]]
                        pred=np.maximum(0,np.expm1(np.minimum(value,30)) if transform.startswith('log') else value)
                    for gas,name in enumerate(drift.GASES):
                        mask=labels[ids]==gas
                        if not mask.any():continue
                        # Reporting denominator only, never used for fitting or
                        # selection. Constant test concentrations yield undefined NMAE.
                        span=float(np.ptp(conc[ids[mask]]))
                        identity=dict(dataset='sensor_drift',fold=partition,seed=seed,budget=budget,design='farthest',window='descriptors',
                                      policy=policy,transform=transform,gas=name)
                        m=metrics(conc[ids[mask]],pred[mask],span if span else 1)
                        if not span:m['nmae']=None
                        rows.append(identity|m|{'normalization_range':span})
                        for idx,prediction in zip(ids[mask],pred[mask]):
                            predictions.append(identity|dict(exposure=int(idx),true=float(conc[idx]),prediction=float(prediction)))
                dump(path,dict(metrics=rows,predictions=predictions,training=history,model_size=size,
                               fit_indices=tr.tolist(),validation_indices=va.tolist(),seconds=time.time()-started))
                print(json.dumps({'dataset':'drift','seed':seed,'budget':budget,'transform':transform,'policy':policy,
                                  'seconds':round(time.time()-started,2)}),flush=True)
