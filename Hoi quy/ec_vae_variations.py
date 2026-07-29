#!/usr/bin/env python3
"""Repeated-seed VAE/AAE representation study for 16x64 EC sensor matrices."""
from __future__ import annotations
import copy, json, random, time
from pathlib import Path
import numpy as np
from sklearn.preprocessing import RobustScaler
from xgboost import XGBRegressor
from ec_improvement_benchmark import features, score

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'ec_vae_variations'
SEEDS=(42,123,2026)
CONFIGS=(
 {'name':'vae_beta_1e-5_z64','kind':'vae','beta':1e-5,'latent':64,'supervised':0.0},
 {'name':'vae_beta_1e-3_z64','kind':'vae','beta':1e-3,'latent':64,'supervised':0.0},
 {'name':'vae_beta_1e-4_z32','kind':'vae','beta':1e-4,'latent':32,'supervised':0.0},
 {'name':'supervised_vae_z64','kind':'vae','beta':1e-4,'latent':64,'supervised':0.2},
 {'name':'aae_z64','kind':'aae','beta':0.0,'latent':64,'supervised':0.0},
)

def seed_all(seed):
 random.seed(seed); np.random.seed(seed)
 import torch
 torch.manual_seed(seed)
 if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)

def main():
 import torch
 from torch import nn
 from torch.utils.data import DataLoader,TensorDataset
 d=dict(np.load(ROOT/'ec_improvements'/'raw_sequences.npz'))
 x,y,groups,folds,offsets=(d[k] for k in ('sequences','targets','groups','folds','offsets'))
 device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); rows=[]
 class Rep(nn.Module):
  def __init__(self,z):
   super().__init__(); self.z=z
   self.enc=nn.Sequential(nn.Conv2d(1,16,3,2,1),nn.GELU(),nn.Conv2d(16,32,3,2,1),nn.GELU())
   self.mu=nn.Linear(2048,z); self.lv=nn.Linear(2048,z); self.fc=nn.Linear(z,2048)
   self.dec=nn.Sequential(nn.ConvTranspose2d(32,16,4,2,1),nn.GELU(),nn.ConvTranspose2d(16,1,4,2,1))
   self.gas=nn.Sequential(nn.Linear(z,32),nn.GELU(),nn.Linear(32,2))
  def encode(self,a):
   h=self.enc(a).flatten(1); return self.mu(h),self.lv(h).clamp(-10,10)
  def decode(self,z): return self.dec(self.fc(z).reshape(-1,32,4,16))
 class Disc(nn.Module):
  def __init__(self,z): super().__init__(); self.n=nn.Sequential(nn.Linear(z,64),nn.LeakyReLU(.2),nn.Linear(64,32),nn.LeakyReLU(.2),nn.Linear(32,1))
  def forward(self,z): return self.n(z)
 def image(a): return torch.from_numpy(a.transpose(0,2,1)[:,None]).float()
 for seed in SEEDS:
  for fold in range(1,6):
   og=np.unique(groups[folds!=fold]); rng=np.random.default_rng(seed+fold); rng.shuffle(og); vg=og[:max(1,len(og)//10)]
   tr=(folds!=fold)&~np.isin(groups,vg); va=(folds!=fold)&np.isin(groups,vg)&(offsets==0); te=(folds==fold)&(offsets==0)
   sx=RobustScaler().fit(x[tr].reshape(-1,16)); tx=lambda m:sx.transform(x[m].reshape(-1,16)).reshape(-1,64,16).astype('float32')
   xtr,xv,xt=tx(tr),tx(va),tx(te); yscale=np.std(y[tr],0); ymean=np.mean(y[tr],0)
   ys=lambda m:((y[m]-ymean)/yscale).astype('float32')
   loader=DataLoader(TensorDataset(image(xtr),torch.from_numpy(ys(tr))),64,shuffle=True)
   iv=image(xv).to(device); yv=torch.from_numpy(ys(va)).to(device)
   for ci,cfg in enumerate(CONFIGS):
    runseed=seed+1000*fold+100000*ci; seed_all(runseed); started=time.perf_counter()
    net=Rep(cfg['latent']).to(device); opt=torch.optim.AdamW(net.parameters(),1e-3)
    disc=Disc(cfg['latent']).to(device) if cfg['kind']=='aae' else None
    dopt=torch.optim.AdamW(disc.parameters(),3e-4) if disc else None
    best=np.inf; state=None; patience=10
    for epoch in range(60):
     net.train()
     for xb,yb in loader:
      xb,yb=xb.to(device),yb.to(device); mu,lv=net.encode(xb)
      z=mu+torch.exp(.5*lv)*torch.randn_like(mu) if cfg['kind']=='vae' else mu
      if disc:
       dopt.zero_grad(set_to_none=True); real=torch.randn_like(z)
       dl=nn.functional.binary_cross_entropy_with_logits(disc(real),torch.ones((len(z),1),device=device))+nn.functional.binary_cross_entropy_with_logits(disc(z.detach()),torch.zeros((len(z),1),device=device)); dl.backward(); dopt.step()
      opt.zero_grad(set_to_none=True); rec=nn.functional.mse_loss(net.decode(z),xb)
      kl=-.5*torch.mean(1+lv-mu.square()-lv.exp()) if cfg['kind']=='vae' else torch.zeros((),device=device)
      adv=nn.functional.binary_cross_entropy_with_logits(disc(z),torch.ones((len(z),1),device=device)) if disc else torch.zeros((),device=device)
      sup=nn.functional.huber_loss(net.gas(mu),yb) if cfg['supervised'] else torch.zeros((),device=device)
      loss=rec+cfg['beta']*kl+1e-3*adv+cfg['supervised']*sup; loss.backward(); opt.step()
     net.eval()
     with torch.no_grad():
      mu,lv=net.encode(iv); z=mu; rec=nn.functional.mse_loss(net.decode(z),iv); kl=-.5*torch.mean(1+lv-mu.square()-lv.exp()) if cfg['kind']=='vae' else torch.zeros((),device=device); sup=nn.functional.huber_loss(net.gas(mu),yv) if cfg['supervised'] else 0; vl=float(rec+cfg['beta']*kl+cfg['supervised']*sup)
     if vl<best-1e-5: best=vl;patience=10;state=copy.deepcopy(net.state_dict())
     else:
      patience-=1
      if patience==0: break
    net.load_state_dict(state);net.eval()
    def enc(a):
     with torch.no_grad(): return net.encode(image(a).to(device))[0].cpu().numpy()
    ztr,zv,zte=enc(xtr),enc(xv),enc(xt)
    for model_name,a,b,c in [('latent_xgboost',ztr,zv,zte),('latent_physics_xgboost',np.c_[ztr,features(x[tr],'physics')],np.c_[zv,features(x[va],'physics')],np.c_[zte,features(x[te],'physics')])]:
     model=XGBRegressor(n_estimators=600,max_depth=3,learning_rate=.03,subsample=.8,colsample_bytree=.8,objective='reg:squarederror',n_jobs=-1,random_state=runseed)
     model.fit(a,y[tr],eval_set=[(b,y[va])],verbose=False); pred=model.predict(c)
     rows.append({'seed':seed,'run_seed':runseed,'fold':fold,'configuration':cfg,'downstream':model_name,'epochs':epoch+1,'val_objective':best,'seconds':time.perf_counter()-started,'metrics':score(y[te],pred)})
    if cfg['supervised']:
     with torch.no_grad(): pred=net.gas(torch.from_numpy(zte).to(device)).cpu().numpy()*yscale+ymean
     rows.append({'seed':seed,'run_seed':runseed,'fold':fold,'configuration':cfg,'downstream':'supervised_head','epochs':epoch+1,'val_objective':best,'seconds':time.perf_counter()-started,'metrics':score(y[te],pred)})
    print(json.dumps({'seed':seed,'fold':fold,'config':cfg['name'],'epochs':epoch+1}),flush=True)
 OUT.mkdir(exist_ok=True); result={'seeds':SEEDS,'configs':CONFIGS,'protocol':'five run-group folds; 10% group validation; train-only scaling; offset-0 validation/test','results':rows}
 (OUT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
if __name__=='__main__': main()
