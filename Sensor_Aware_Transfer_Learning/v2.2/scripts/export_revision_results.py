"""Export completed jobs only; incomplete runs never become final evidence."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from revision_common import ROOT, paired_summary, dump


def save(out, relative, frame):
    path=out/relative;path.parent.mkdir(parents=True,exist_ok=True)
    frame.to_csv(path,index=False)


def export(run):
    out=run/'exports';out.mkdir(exist_ok=True)
    jobs=[json.loads(p.read_text()) for p in sorted((run/'jobs').glob('*.json'))]
    drift=[json.loads(p.read_text()) for p in sorted((run/'drift_jobs').glob('*.json'))]
    manifest={'source_run':str(run.relative_to(ROOT)), 'protocol':json.loads((run/'protocol.json').read_text()),
              'raw_jobs':len(jobs),'drift_jobs':len(drift),
              'completed_suites':[p.stem.removesuffix('_completed') for p in run.glob('*_completed.json')]}
    dump(out/'manifest.json',manifest)
    if jobs:
        df=pd.DataFrame([row for job in jobs for row in job['metrics']])
        pred=pd.DataFrame([row for job in jobs for row in job['predictions']])
        save(out,'predictions/raw_response_predictions.csv',pred)
        save(out,'policy_selection/all_policy_results.csv',df)
        primary=df[df.policy.isin(['scratch','frozen','fine_tuned'])]
        fixed=primary[(primary.fold==0)&(primary.design=='farthest')&(primary.window=='early')]
        save(out,'policy_selection/primary_policy_results.csv',df[df.policy=='fine_tuned'])
        save(out,'10_seed_runs/raw_response_all_runs.csv',fixed)
        keys=['dataset','fold','budget','design','window','policy','gas']
        summary=df.groupby(keys).agg(mae_mean=('mae','mean'),mae_sd=('mae','std'),
                     rmse_mean=('rmse','mean'),r2_mean=('r2','mean'),q90_mean=('q90','mean'),
                     n_seeds=('seed','nunique')).reset_index()
        save(out,'10_seed_runs/summary_raw_response.csv',summary[summary.fold==0])
        folds=primary[primary.fold>0]
        for dataset in ['nh3_h2','co_ethylene']:
            save(out,f'multifold/{dataset}_fold_results.csv',folds[folds.dataset==dataset])
        save(out,'multifold/fold_level_summary.csv',summary[summary.fold>0])
        tests=paired_summary(primary[primary.fold==0])
        save(out,'statistics/paired_tests.csv',tests)
        # Full calibration coverage can contain different numbers of unique
        # pairs in different rolling folds. Keep actual counts in raw CSVs.
        fullfolds=folds.copy();fullfolds['budget']='full_available'
        foldtests=paired_summary(fullfolds) if len(folds) else pd.DataFrame()
        save(out,'multifold/paired_bootstrap_summary.csv',foldtests)
        save(out,'statistics/q90_all_policies.csv',primary[keys+['seed','q90']])
        sizes=pd.DataFrame([j['identity']|j['model_size'] for j in jobs if j['model_size']])
        save(out,'statistics/model_size.csv',sizes)
        for policy in ['plsr','svr']:
            save(out,f'baselines/{policy}_results.csv',df[df.policy==policy])
        save(out,'baselines/baseline_summary.csv',summary[(summary.fold==0)&(summary.design=='farthest')&(summary.window=='early')])
        save(out,'ssl_baselines/generic_ssl_results.csv',df[df.policy=='generic_ssl'])
        save(out,'ssl_baselines/proposed_vs_generic_ssl.csv',paired_summary(df[df.fold==0],left='generic_ssl'))
        design=df[(df.fold==0)&df.policy.isin(['scratch','fine_tuned'])&(df.window=='early')]
        save(out,'calibration_design/random_vs_farthest.csv',design)
        save(out,'calibration_design/factorial_summary.csv',summary[(summary.fold==0)&summary.policy.isin(['scratch','fine_tuned'])&(summary.window=='early')])
        # Reuse paired policy statistics with design encoded as the comparator.
        design_tests=[]
        for policy in ['scratch','fine_tuned']:
            d=design[design.policy==policy].copy();d['policy']=d.design;d['design']='paired_design'
            t=paired_summary(d,left='random',right='farthest')
            t['training_policy']=policy;design_tests.append(t)
        save(out,'calibration_design/paired_design_statistics.csv',pd.concat(design_tests,ignore_index=True))
        sensitivity=summary[(summary.dataset=='nh3_h2')&(summary.fold==0)&summary.policy.isin(['scratch','fine_tuned'])&(summary.design=='farthest')]
        save(out,'window_sensitivity/window_position_results.csv',sensitivity)
        if sensitivity.window.nunique()>1:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            plt.rcParams.update({'font.size':11,'pdf.fonttype':42,'svg.fonttype':'none'})
            fig,axes=plt.subplots(1,2,figsize=(7.2,3.0))
            for ax,gas in zip(axes,['NH3','H2']):
                for policy in ['scratch','fine_tuned']:
                    d=sensitivity[(sensitivity.gas==gas)&(sensitivity.policy==policy)]
                    d=d[d.budget==d.budget.max()].set_index('window').reindex(['early','middle','late','full'])
                    ax.errorbar(d.index,d.mae_mean,yerr=d.mae_sd,marker='o',capsize=3,label=policy)
                ax.set(title=gas,ylabel='MAE (ppm)');ax.tick_params(axis='x',rotation=20)
            axes[1].legend(fontsize=9);fig.tight_layout()
            fig.savefig(out/'window_sensitivity/window_position_plot.pdf');plt.close(fig)
    if drift:
        df=pd.DataFrame([row for job in drift for row in job['metrics']])
        # Test-partition ranges are zero for several gas/partition combinations.
        # Preserve that diagnostic, but use a common historical reference range
        # for an all-six-gas macro-NMAE. Reference labels enter reporting only.
        import sensor_drift_transfer as drift_source
        source=drift_source.load_dataset(drift_source.DATA)
        reference=[]
        for gas,name in enumerate(drift_source.GASES):
            values=source['concentration'][(source['batch']<=6)&(source['label']==gas)]
            reference.append(dict(gas=name,minimum=float(values.min()),maximum=float(values.max()),range=float(np.ptp(values))))
        reference=pd.DataFrame(reference)
        assert (reference['range']>0).all()
        df['nmae_test_range']=df['nmae']
        df['historical_reference_range']=df.gas.map(reference.set_index('gas')['range'])
        df['nmae']=df.mae/df.historical_reference_range
        save(out,'sensor_drift/normalization_reference_ranges.csv',reference)
        pred=pd.DataFrame([row for job in drift for row in job['predictions']])
        save(out,'predictions/sensor_drift_predictions.csv',pred)
        save(out,'sensor_drift/constant_baseline.csv',df[df.policy=='constant'])
        save(out,'sensor_drift/per_gas_error.csv',df)
        save(out,'sensor_drift/normalized_error.csv',df)
        save(out,'sensor_drift/label_budget_sensor_drift.csv',df)
        save(out,'sensor_drift_loss/target_transform_comparison.csv',df)
        scaling=pd.DataFrame([dict(file=p.name,**json.loads(p.read_text())['training']) for p in (run/'drift_jobs').glob('*.json')])
        save(out,'sensor_drift_loss/scaling_sensitivity.csv',scaling)
        main=df[(df.budget==20)&(df['transform']=='log_huber')]
        save(out,'10_seed_runs/sensor_drift_all_runs.csv',main)
        summary=df.groupby(['fold','budget','transform','policy','gas']).agg(mae_mean=('mae','mean'),mae_sd=('mae','std'),
                       nmae_mean=('nmae','mean'),nmae_sd=('nmae','std'),n_seeds=('seed','nunique')).reset_index()
        save(out,'10_seed_runs/summary_sensor_drift.csv',summary)
        macro=df.groupby(['fold','seed','budget','transform','policy']).agg(mae=('mae','mean'),nmae=('nmae','mean'),
                         n_gases=('gas','nunique')).reset_index()
        save(out,'sensor_drift/macro_error.csv',macro)
        statistics=[]
        for transform in df['transform'].unique():
            for fold in [8,9,10]:
                d=df[(df['transform']==transform)&(df.fold==fold)].copy()
                for right in ['frozen','fine_tuned']:
                    t=paired_summary(d,right=right);t['transform']=transform;t['partition']=fold
                    statistics.append(t)
        stats=pd.concat(statistics,ignore_index=True)
        macro_stats=[]
        for transform in macro['transform'].unique():
            for partition in [8,9,10]:
                d=macro[(macro['transform']==transform)&(macro.fold==partition)].copy()
                d['dataset']='sensor_drift';d['design']='farthest';d['window']='descriptors';d['gas']='MacroMAE';d['n_test']=1
                for right in ['frozen','fine_tuned']:
                    t=paired_summary(d,right=right);t['transform']=transform;t['partition']=partition
                    macro_stats.append(t)
        stats=pd.concat([stats,*macro_stats],ignore_index=True)
        save(out,'sensor_drift/partition10_statistics.csv',stats[stats.partition==10])
        save(out,'sensor_drift/paired_statistics.csv',stats)
        drift_sizes=[]
        for job in drift:
            if job.get('model_size'):
                identity={key:job['metrics'][0][key] for key in ['dataset','seed','budget','policy','transform']}
                drift_sizes.append(identity|job['model_size'])
        previous=pd.read_csv(out/'statistics/model_size.csv') if (out/'statistics/model_size.csv').exists() else pd.DataFrame()
        save(out,'statistics/model_size.csv',pd.concat([previous,pd.DataFrame(drift_sizes)],ignore_index=True))
        drift_q=df[df.policy.isin(['scratch','frozen','fine_tuned'])]
        save(out,'statistics/q90_sensor_drift_all_policies.csv',drift_q)
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);args=p.parse_args()
    print(json.dumps(export(ROOT/'revision_artifacts/runs'/args.run_id),indent=2))
