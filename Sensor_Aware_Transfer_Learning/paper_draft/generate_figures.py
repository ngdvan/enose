"""Generate traceable SVG figures and derived tail-error metrics for the paper."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
    "axes.labelsize": 9, "legend.fontsize": 8, "svg.fonttype": "none",
    "axes.spines.top": False, "axes.spines.right": False,
})
COL = {"scratch": "#777777", "frozen_transfer": "#0072B2",
       "finetuned_transfer": "#D55E00", "transfer": "#009E73",
       "physics_extratrees": "#CC79A7", "physics_xgboost": "#E69F00"}
LABEL = {"scratch": "Scratch", "frozen_transfer": "Frozen transfer",
         "finetuned_transfer": "Fine-tuned transfer", "transfer": "Best transfer",
         "physics_extratrees": "Physics + Extra Trees", "physics_xgboost": "Physics + XGBoost"}


def load(dataset):
    base = ROOT / "results" / dataset
    return json.loads((base / "results.json").read_text()), pd.read_csv(base / "predictions.csv")


NH, nhp = load("nh3_h2")
CO, cop = load("co_ethylene")


def save(fig, name):
    fig.savefig(FIG / name, format="svg", bbox_inches="tight", metadata={"Creator": "generate_figures.py"})
    plt.close(fig)


def summary_metric(obj, budget, model, gas, metric="mae_ppm"):
    return obj["summary"][str(budget)][model][gas][metric]["mean"]


def summary_sd(obj, budget, model, gas, metric="mae_ppm"):
    return obj["summary"][str(budget)][model][gas][metric]["sd"]


def method_pipeline():
    fig, ax = plt.subplots(figsize=(12, 3.3)); ax.set_xlim(0, 12); ax.set_ylim(0, 3.3); ax.axis("off")
    boxes = [(0.15, 1.05, 1.5, 1.15, "Raw exposures\n$X_i\\in\\mathbb{R}^{64\\times S}$", "#E8F1FA"),
             (2.0, 1.05, 1.65, 1.15, "Leakage-controlled\nsession/block split", "#FFF2CC"),
             (4.0, 1.75, 1.75, 1.15, "Unlabeled $\\mathcal{U}$\nscaling + masking", "#DDF3E4"),
             (6.1, 1.75, 2.05, 1.15, "Sensor-aware encoder\nCNN + IDs + attention", "#DDF3E4"),
             (4.0, 0.25, 1.75, 1.15, "Labeled $\\mathcal{A}_K$\nfarthest-point pairs", "#FCE4D6"),
             (6.1, 0.25, 2.05, 1.15, "Scratch / frozen /\nfine-tuned adaptation", "#FCE4D6"),
             (8.55, 0.95, 1.45, 1.15, "Two-gas\npredictions", "#E8F1FA"),
             (10.35, 0.95, 1.45, 1.15, "Untouched test\nMAE, RMSE, $R^2$, $Q_{.9}$", "#FFF2CC")]
    for x,y,w,h,t,c in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.04",fc=c,ec="#333333",lw=1)); ax.text(x+w/2,y+h/2,t,ha="center",va="center")
    arrows=[((1.65,1.62),(2,1.62)),((3.65,1.62),(4,2.32)),((3.65,1.45),(4,0.82)),((5.75,2.32),(6.1,2.32)),((5.75,.82),(6.1,.82)),((8.15,2.2),(8.55,1.7)),((8.15,.82),(8.55,1.35)),((10,1.52),(10.35,1.52))]
    for a,b in arrows: ax.annotate("",xy=b,xytext=a,arrowprops=dict(arrowstyle="->",lw=1.4,color="#333"))
    ax.plot([3.83,3.83],[.12,3.05],"--",color="#B22222",lw=1); ax.text(3.73,3.1,"test-data barrier",color="#B22222",ha="right",fontsize=8)
    ax.text(7.1,3.12,"masked reconstruction",ha="center",color="#007A3D"); ax.text(7.1,.05,"Huber regression",ha="center",color="#A33C00")
    save(fig,"method_pipeline.svg")


def dataset_figures():
    fig, axes=plt.subplots(2,1,figsize=(10,3.8),sharex=False)
    specs=[("Private NH$_3$/H$_2$: documented sessions",[1,2,3,4,5,6],["Pretrain"]*4+["Adapt","Test"],63),
           ("Public CO/ethylene: chronological blocks",[1,2,3,4,5],["Pretrain"]*3+["Adapt","Test"],49)]
    colors={"Pretrain":"#56B4E9","Adapt":"#E69F00","Test":"#D55E00"}
    for ax,(title,ids,roles,count) in zip(axes,specs):
        for i,(v,role) in enumerate(zip(ids,roles)):
            ax.barh([0],[1],left=i,color=colors[role],edgecolor="white"); ax.text(i+.5,0,f"{role}\n{count} exposures",ha="center",va="center",fontsize=8)
            ax.text(i+.5,.55,f"{('Session' if len(ids)==6 else 'Block')} {v}",ha="center",fontsize=8)
        ax.axvline(len(ids)-1,color="#8B0000",ls="--",lw=1.2); ax.set_xlim(0,len(ids)); ax.set_ylim(-.65,.85); ax.axis("off"); ax.set_title(title,loc="left",fontweight="bold")
    fig.legend([mpl.patches.Patch(color=colors[k]) for k in colors],colors,loc="lower center",ncol=3,frameon=False)
    save(fig,"dataset_splits.svg")

    fig,ax=plt.subplots(figsize=(9,3)); ax.axis("off")
    rows=[["Access","Private","Public UCI"],["Targets","NH$_3$, H$_2$","CO, ethylene"],["Sensors","20","16"],["Raw exposures","378","245 prepared runs"],["Pretrain windows","1,260","735"],["Adaptation pairs","57 available","24 available"],["Holdout","Session 6","Future block 5"]]
    tbl=ax.table(cellText=rows,colLabels=["Property","NH$_3$/H$_2$","CO/ethylene"],cellLoc="center",loc="center",colColours=["#E8EEF4"]*3); tbl.auto_set_font_size(False);tbl.set_fontsize(9);tbl.scale(1,1.45)
    save(fig,"dataset_structure.svg")


def pretraining():
    fig,ax=plt.subplots(figsize=(7,3.6))
    for obj,label,color in [(NH,"NH$_3$/H$_2$","#0072B2"),(CO,"CO/ethylene","#D55E00")]: ax.plot(range(1,61),obj["pretraining_loss"],label=label,color=color,lw=1.8)
    ax.set(xlabel="Pretraining epoch",ylabel="Stochastic masked-reconstruction loss"); ax.grid(alpha=.2); ax.legend(frameon=False); save(fig,"pretraining_loss.svg")


def label_eff(obj,budgets,gases,name):
    fig,axes=plt.subplots(1,2,figsize=(9,3.4))
    for ax,gas in zip(axes,gases):
        for model in ["scratch","frozen_transfer","finetuned_transfer"]:
            y=[summary_metric(obj,b,model,gas) for b in budgets]; e=[summary_sd(obj,b,model,gas) for b in budgets]
            ax.errorbar(budgets,y,yerr=e,marker="o",capsize=2,lw=1.5,color=COL[model],label=LABEL[model])
        ax.set(title=gas,xlabel="Labeled concentration pairs",ylabel="Held-out MAE (ppm)");ax.grid(alpha=.2)
    axes[0].legend(frameon=False); save(fig,name)


def freeze_plot():
    fig,axes=plt.subplots(2,2,figsize=(9,6)); panels=[(NH,[5,10,20,40,57],"NH3"),(NH,[5,10,20,40,57],"H2"),(CO,[5,10,20,24],"CO"),(CO,[5,10,20,24],"Ethylene")]
    for ax,(obj,budgets,gas) in zip(axes.flat,panels):
        f=np.array([summary_metric(obj,b,"frozen_transfer",gas) for b in budgets]); t=np.array([summary_metric(obj,b,"finetuned_transfer",gas) for b in budgets])
        ax.axhline(0,color="#333",lw=.8); ax.plot(budgets,100*(f-t)/f,marker="o",color="#6A3D9A"); ax.set(title=gas,xlabel="Labeled pairs",ylabel="Fine-tuning gain vs frozen (%)");ax.grid(alpha=.2)
    fig.subplots_adjust(hspace=0.72, wspace=0.30)
    save(fig,"freeze_vs_finetune.svg")


def baseline_plot():
    nhx=json.loads((ROOT/"results/nh3_h2/physics_xgboost_comparison.json").read_text()); cox=json.loads((ROOT/"results/co_ethylene/physics_xgboost_comparison.json").read_text())
    fig,axes=plt.subplots(2,2,figsize=(9,6)); panels=[(NH,nhx,[5,10,20,40,57],"NH3"),(NH,nhx,[5,10,20,40,57],"H2"),(CO,cox,[5,10,20,24],"CO"),(CO,cox,[5,10,20,24],"Ethylene")]
    for ax,(obj,xobj,budgets,gas) in zip(axes.flat,panels):
        best=[min(summary_metric(obj,b,"frozen_transfer",gas),summary_metric(obj,b,"finetuned_transfer",gas)) for b in budgets]
        xgb=[xobj["summary"][str(b)]["physics_xgboost"][gas]["mae_ppm"]["mean"] for b in budgets]
        ax.plot(budgets,best,"o-",color=COL["transfer"],label="Best transfer");ax.plot(budgets,xgb,"s--",color=COL["physics_xgboost"],label="Physics + XGBoost")
        if gas in ("NH3","H2"):
            extra=[summary_metric(obj,b,"physics_extratrees",gas) for b in budgets];ax.plot(budgets,extra,"^:",color=COL["physics_extratrees"],label="Physics + Extra Trees")
        ax.set(title=gas,xlabel="Labeled pairs",ylabel="Held-out MAE (ppm)");ax.grid(alpha=.2)
    axes[0,0].legend(frameon=False); fig.subplots_adjust(hspace=0.72, wspace=0.30); save(fig,"baseline_comparison.svg")


def derived_metrics():
    out={}
    for ds,df,gases in [("nh3_h2",nhp,["NH3","H2"]),("co_ethylene",cop,["CO","Ethylene"])]:
        out[ds]={}
        for (budget,model),g in df.groupby(["budget","model"]):
            out[ds].setdefault(str(int(budget)),{})[model]={}
            for gas in gases:
                ae=(g[f"{gas}_true"]-g[f"{gas}_pred"]).abs()
                out[ds][str(int(budget))][model][gas]={"q90_abs_error_ppm_pooled":float(ae.quantile(.9)),"n_predictions":int(len(ae))}
    (OUT/"derived_tail_metrics.json").write_text(json.dumps(out,indent=2))
    return out


def full_metrics(tail):
    fig,axes=plt.subplots(2,2,figsize=(9,6)); panels=[(NH,"nh3_h2",57,"NH3"),(NH,"nh3_h2",57,"H2"),(CO,"co_ethylene",24,"CO"),(CO,"co_ethylene",24,"Ethylene")]
    models=["scratch","frozen_transfer","finetuned_transfer"]
    for ax,(obj,ds,b,gas) in zip(axes.flat,panels):
        mae=[summary_metric(obj,b,m,gas) for m in models]; q=[tail[ds][str(b)][m][gas]["q90_abs_error_ppm_pooled"] for m in models]
        x=np.arange(3);w=.36; ax.bar(x-w/2,mae,w,label="MAE",color="#56B4E9");ax.bar(x+w/2,q,w,label="$Q_{0.9}$ abs. error",color="#D55E00")
        ax.set_xticks(x,["Scratch","Frozen","Fine-tuned"],rotation=15);ax.set_title(gas);ax.set_ylabel("Error (ppm)");ax.grid(axis="y",alpha=.2)
    axes[0,0].legend(frameon=False);fig.subplots_adjust(hspace=0.72, wspace=0.30);save(fig,"full_budget_metrics.svg")


def prediction_scatter():
    fig,axes=plt.subplots(2,2,figsize=(8,7)); panels=[(nhp,57,"NH3"),(nhp,57,"H2"),(cop,24,"CO"),(cop,24,"Ethylene")]
    for ax,(df,b,gas) in zip(axes.flat,panels):
        d=df[(df.budget==b)&(df.model=="finetuned_transfer")]; ax.scatter(d[f"{gas}_true"],d[f"{gas}_pred"],s=10,alpha=.45,color="#0072B2")
        lo=min(d[f"{gas}_true"].min(),d[f"{gas}_pred"].min());hi=max(d[f"{gas}_true"].max(),d[f"{gas}_pred"].max());ax.plot([lo,hi],[lo,hi],"--",color="#555",lw=1)
        ax.set(title=f"{gas} (fine-tuned, pooled repeats)",xlabel="True (ppm)",ylabel="Predicted (ppm)");ax.grid(alpha=.15)
    fig.subplots_adjust(hspace=0.72, wspace=0.32)
    save(fig,"prediction_scatter.svg")


def advanced_figures():
    """Generate figures from the completed ablation and multi-fold studies."""
    adv = ROOT / "results" / "advanced_validation"
    nh_ab = adv / "nh3_h2" / "ablation_results.json"
    co_ab = adv / "co_ethylene" / "ablation_results.json"
    if nh_ab.exists() and co_ab.exists():
        objs = {"nh3_h2": json.loads(nh_ab.read_text()),
                "co_ethylene": json.loads(co_ab.read_text())}
        panels=[("nh3_h2",57,"NH3"),("nh3_h2",57,"H2"),
                ("co_ethylene",24,"CO"),("co_ethylene",24,"Ethylene")]
        order=["full","no_sensor_ids","no_attention","no_sensor_mask","no_temporal_mask"]
        short=["Full","No IDs","No attention","No sensor mask","No temporal mask"]
        fig,axes=plt.subplots(2,2,figsize=(10,7.5))
        for ax,(ds,budget,gas) in zip(axes.flat,panels):
            rows=[r for r in objs[ds]["runs"] if r["budget"]==budget]
            means=[];sds=[]
            for variant in order:
                vals=[r["metrics"][gas]["mae_ppm"] for r in rows if r["variant"]==variant]
                means.append(np.mean(vals));sds.append(np.std(vals,ddof=1))
            ax.bar(range(len(order)),means,yerr=sds,capsize=3,color=["#009E73"]+["#9ECAE1"]*4)
            ax.set_xticks(range(len(order)),short,rotation=24,ha="right");ax.set_title(gas);ax.set_ylabel("Held-out MAE (ppm)");ax.grid(axis="y",alpha=.2)
        fig.subplots_adjust(hspace=.92,wspace=.32);save(fig,"architectural_ablation.svg")

        histories=[]
        for ds,obj in objs.items():
            gas_label="NH$_3$/H$_2$" if ds=="nh3_h2" else "CO/ethylene"
            full_budget=57 if ds=="nh3_h2" else 24
            selected=[]
            for key,h in obj["supervised_histories"].items():
                if key.startswith("full/") and key.endswith(f"b{full_budget}"):
                    selected.append((gas_label,key,h))
            histories.extend(selected[:2])
        fig,axes=plt.subplots(2,2,figsize=(9,7))
        for ax,(label,key,h) in zip(axes.flat,histories[:4]):
            ax.plot(h["train_loss"],label="Train",color="#0072B2")
            ax.plot(h["validation_loss"],label="Adaptation validation",color="#D55E00")
            ax.axvline(h["best_epoch"]-1,color="#555",ls="--",lw=1,label="Selected epoch")
            ax.set_title(f"{label}: {key.split('/')[1]}");ax.set_xlabel("Epoch");ax.set_ylabel("Huber loss");ax.grid(alpha=.2)
        axes[0,0].legend(frameon=False);fig.subplots_adjust(hspace=.78,wspace=.3);save(fig,"supervised_learning_curves.svg")

    nhcv=adv/"nh3_h2"/"session_cv_results.json"; cocv=adv/"co_ethylene"/"rolling_cv_results.json"
    if nhcv.exists() and cocv.exists():
        cvobjs={"nh3_h2":json.loads(nhcv.read_text()),"co_ethylene":json.loads(cocv.read_text())}
        panels=[("nh3_h2",57,"NH3"),("nh3_h2",57,"H2"),("co_ethylene",20,"CO"),("co_ethylene",20,"Ethylene")]
        fig,axes=plt.subplots(2,2,figsize=(9.5,7.5))
        for ax,(ds,budget,gas) in zip(axes.flat,panels):
            rows=cvobjs[ds]["runs"]
            folds=sorted({r["fold"] for r in rows if r["budget"]==budget})
            for model,color in [("scratch","#777777"),("transfer","#009E73")]:
                vals=[];errs=[]
                for fold in folds:
                    v=[r["metrics"][gas]["mae_ppm"] for r in rows if r["fold"]==fold and r["budget"]==budget and r["model"]==model]
                    vals.append(np.mean(v));errs.append(np.std(v,ddof=1))
                ax.errorbar(folds,vals,yerr=errs,marker="o",capsize=3,color=color,label=model.title())
            ax.set_title(gas);ax.set_xlabel("Session fold" if ds=="nh3_h2" else "Rolling fold");ax.set_ylabel("MAE (ppm)");ax.grid(alpha=.2)
        axes[0,0].legend(frameon=False);fig.subplots_adjust(hspace=.78,wspace=.3);save(fig,"multifold_validation.svg")


method_pipeline(); dataset_figures(); pretraining()
label_eff(NH,[5,10,20,40,57],["NH3","H2"],"nh3_h2_label_efficiency.svg")
label_eff(CO,[5,10,20,24],["CO","Ethylene"],"co_ethylene_label_efficiency.svg")
freeze_plot(); baseline_plot(); tail=derived_metrics(); full_metrics(tail); prediction_scatter()
advanced_figures()
print(f"Generated {len(list(FIG.glob('*.svg')))} SVG figures in {FIG}")
