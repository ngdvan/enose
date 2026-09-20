"""Prespecified seed-order sensitivity; never choose the reported seed count."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
from revision_common import ROOT, SEEDS, paired_summary

RUN=ROOT/'revision_artifacts/runs/major_revision_001'
OUT=ROOT/'author_review/full_revision_001/evidence/seed_stability'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw=pd.DataFrame([m for p in (RUN/'jobs').glob('*.json') for m in json.loads(p.read_text())['metrics']])
    raw=raw[raw.policy.isin(['scratch','fine_tuned']) & (raw.design=='farthest') & (raw.window=='early')]
    multi=raw[raw.fold>0].copy();multi['budget']='full_available'
    fixed=raw[raw.fold==0].copy()
    families=[('primary_multifold',multi),('fixed_split',fixed)]
    drift=pd.DataFrame([m for p in (RUN/'drift_jobs').glob('*.json') for m in json.loads(p.read_text())['metrics']])
    if len(drift):
        drift=drift[(drift.budget==20)&(drift['transform']=='log_huber')&drift.policy.isin(['scratch','fine_tuned'])]
        macro=drift.groupby(['dataset','fold','seed','budget','design','window','policy']).agg(mae=('mae','mean'),n_test=('n_test','sum')).reset_index()
        macro['gas']='MacroMAE'
        for fold in [8,9,10]:families.append((f'drift_partition_{fold}',macro[macro.fold==fold]))
    result=[];comparisons=[];random_rows=[]
    for family,df in families:
        for k in range(1,11):
            sub=df[df.seed.isin(SEEDS[:k])]
            # Exclude unfinished configurations, never silently compare unequal seeds.
            valid=sub.groupby(['dataset','budget','gas']).filter(lambda x: x.groupby(['fold','policy']).seed.nunique().eq(k).all() and set(x.policy)=={'scratch','fine_tuned'})
            if not len(valid):continue
            t=paired_summary(valid);t['family']=family;t['n_prefix_seeds']=k
            result.append(t)
        for (dataset,budget,gas),d in df.groupby(['dataset','budget','gas']):
            a=d[d.policy=='scratch'].pivot(index='seed',columns='fold',values='mae').reindex(SEEDS)
            b=d[d.policy=='fine_tuned'].pivot(index='seed',columns='fold',values='mae').reindex_like(a)
            if a.isna().any().any() or b.isna().any().any():continue
            x=a.mean(axis=1).to_numpy();y=b.mean(axis=1).to_numpy();delta=x-y
            rng=np.random.default_rng(719)
            # Random order envelope quantifies order sensitivity, not a population CI.
            for k in range(1,11):
                values=[]
                for _ in range(2000):
                    idx=rng.choice(10,k,replace=False)
                    values.append(100*(x[idx].mean()-y[idx].mean())/x[idx].mean())
                lo,med,hi=np.quantile(values,[.025,.5,.975])
                random_rows.append(dict(family=family,dataset=dataset,budget=budget,gas=gas,n_seeds=k,order_low=lo,order_median=med,order_high=hi))
            comparisons.append(dict(family=family,dataset=dataset,budget=budget,gas=gas,
                first3_scratch=x[:3].mean(),first3_transfer=y[:3].mean(),all10_scratch=x.mean(),all10_transfer=y.mean(),
                first3_gain_pct=100*delta[:3].mean()/x[:3].mean(),all10_gain_pct=100*delta.mean()/x.mean(),
                later7_gain_pct=100*delta[3:].mean()/x[3:].mean(),first3_delta=delta[:3].mean(),all10_delta=delta.mean(),
                positive_seeds=int((delta>0).sum()),seed_delta_sd=delta.std(ddof=1)))
    cumulative=pd.concat(result,ignore_index=True)
    comparison=pd.DataFrame(comparisons)
    cumulative.to_csv(OUT/'cumulative_seed_statistics.csv',index=False)
    comparison.to_csv(OUT/'first3_vs_all10.csv',index=False)
    pd.DataFrame(random_rows).to_csv(OUT/'random_order_envelopes.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(2,2,figsize=(7.2,5.0),sharex=True)
    envelope=pd.DataFrame(random_rows)
    for ax,gas in zip(axs.flat,['NH3','H2','CO','Ethylene']):
        q=cumulative[(cumulative.family=='primary_multifold')&(cumulative.gas==gas)]
        e=envelope[(envelope.family=='primary_multifold')&(envelope.gas==gas)]
        ax.fill_between(e.n_seeds,e.order_low,e.order_high,alpha=.18,color='#24557d',label='Random-order 95% envelope')
        ax.plot(q.n_prefix_seeds,q.relative_improvement_pct,'o-',color='#24557d',label='Predefined seed order')
        ax.axhline(0,color='black',linewidth=.6);ax.set(title=gas,xlabel='Number of seeds',ylabel='MAE reduction (%)',xticks=[1,3,5,7,10])
    axs[0,0].legend(fontsize=6);fig.tight_layout()
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'seed_stability.{ext}',dpi=220)
    lines=['# Seed-count stability audit','',
        'All ten predefined seeds remain the reporting set. Prefixes use 42, 142, ..., 942 in that order. The first three here are from the revised, matched-holdout protocol, not the historical manuscript. Differences from the original publication cannot be attributed to seed count alone.',
        '', 'Positive reduction favors fine-tuning. Primary multi-fold results weight folds equally. Bootstrap intervals resample paired seeds and folds, conditional on the observed exposures. The random-order envelope is a subset/order diagnostic, not a confidence interval. No seed count or model is selected from this audit.','',
        '| Analysis | Gas | First 3 reduction (%) | All 10 reduction (%) | Later 7 reduction (%) | Positive seeds / 10 |',
        '|---|---|---:|---:|---:|---:|']
    for _,r in comparison.iterrows():
        if r.family=='fixed_split' and int(r.budget) not in [24,57]:continue
        lines.append(f'| {r.family} | {r.gas} | {r.first3_gain_pct:.2f} | {r.all10_gain_pct:.2f} | {r.later7_gain_pct:.2f} | {r.positive_seeds} |')
    lines+=['','Adding seeds changes the estimated average; it does not degrade a trained model. Read the change in relative reduction together with absolute scratch/fine-tuned errors and paired uncertainty. Ten seeds characterize training variability, but do not create additional independent physical test exposures.']
    (OUT/'SEED_STABILITY.md').write_text('\n'.join(lines),encoding='utf-8')
    print(comparison[comparison.family=='primary_multifold'].to_string(index=False))

if __name__=='__main__':main()
