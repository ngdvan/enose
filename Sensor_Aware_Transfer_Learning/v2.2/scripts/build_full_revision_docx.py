"""Full evidence-grounded revision of original IEEE source, preserving OMML.

Run only after all immutable experiments and exports are complete. Yellow is a
content comparison, not Word tracked changes. Supplement carries detailed tables.
"""
from copy import deepcopy
from pathlib import Path
import json
import re
import shutil
import sys
import numpy as np
import pandas as pd
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph
from lxml import etree
import build_minimal_revision_docx as edit
from build_revision_manuscript import ADDITIONS
FULL_ADDITIONS = ADDITIONS + ['Dang Thi Thu Ha, Nguyen Dinh Van, Nguyen Duc Hoa, and Nguyen Van Duy, “Design and Analysis of a Volatile Organic Compounds Mixture Dataset for Indoor Air Quality Monitoring,” in Proceedings of the 4th Annual International Conference on Material, Machines, and Methods for Sustainable Development (MMMS2024), Lecture Notes in Mechanical Engineering. Cham: Springer, 2025, pp. 85–92, doi: 10.1007/978-3-031-93816-0_11.']
FULL_ADDITIONS.append('D.-V. Nguyen, "Nano MEMS Electronic Nose Responses to Ammonia and Hydrogen," Harvard Dataverse, V1, 2026, doi: 10.7910/DVN/LWUSKO.')
FULL_ADDITIONS.append('DangThiThu Ha, NguyenDinh Van, and NguyenDuc Hoa, "Image-Based Hybrid Autoencoder–LSTM for Mixed-Gas Estimation in Electronic Nose," IEEE Sensors Journal, vol. 26, no. 3, pp. 4739–4748, Feb. 2026, doi: 10.1109/JSEN.2025.3642226.')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from revision_common import ROOT, SEEDS, sha256, dump

RUN=ROOT/'revision_artifacts/runs/major_revision_001'
OUT=ROOT/'author_review/full_revision_001'
E=OUT/'evidence'
GASES=['NH3','H2','CO','Ethylene']
POLICIES=['scratch','frozen','fine_tuned']
LABEL={'scratch':'Scratch','frozen':'Frozen','fine_tuned':'Fine-tuned','generic_ssl':'Generic SSL',
       'extra_trees':'Extra Trees','xgboost':'XGBoost','plsr':'PLSR','svr':'SVR','constant':'Constant'}
claims=[]

def read(path):return pd.read_csv(E/'exports'/path)
def n(x,gas='',digits=None):return f'{float(x):.{digits if digits is not None else 3 if gas=="Ethylene" else 2}f}'
def ms(r,gas='',metric='mae'):return n(r[metric+'_mean'],gas)+' ± '+n(r[metric+'_sd'],gas)
def one(df,**keys):
    for k,v in keys.items():df=df[df[k]==v]
    assert len(df)==1,(keys,len(df))
    return df.iloc[0]
def record_table(title,headers,rows):
    claims.append(dict(title=title,headers=headers,rows=[[str(c) for c in row] for row in rows]))

class Insert:
    def __init__(self,doc,anchor,styles):self.doc,self.anchor,self.styles=doc,anchor,styles
    def p(self,text,kind='body'):
        node=OxmlElement('w:p');self.anchor.addprevious(node)
        p=Paragraph(node,self.doc._body);p.style=self.styles[kind]
        p.paragraph_format.keep_with_next=kind in ['h1','h2','caption']
        edit.replace(p,text,'Full revision: '+text[:80])
        return p
    def table(self,title,headers,rows,widths=None):
        self.p(title,'caption')
        t=self.doc.add_table(rows=1,cols=len(headers));t.style='Table Grid'
        self.anchor.addprevious(t._tbl)
        for cell,txt in zip(t.rows[0].cells,headers):edit.cell_text(cell,str(txt),title)
        for values in rows:
            for cell,txt in zip(t.add_row().cells,values):edit.cell_text(cell,str(txt),title)
        edit.configure_table(t,widths or [3.45/len(headers)]*len(headers))
        # Tight but readable column tables: avoid arbitrary word breaks caused
        # by Word's wider default cell padding and inherited body fonts.
        for row in t.rows:
            for cell in row.cells:
                margins=OxmlElement('w:tcMar')
                for side in ['left','right']:
                    node=OxmlElement('w:'+side);node.set(qn('w:w'),'45');node.set(qn('w:type'),'dxa');margins.append(node)
                cell._tc.get_or_add_tcPr().append(margins)
                for p in cell.paragraphs:
                    p.paragraph_format.left_indent=Pt(0);p.paragraph_format.right_indent=Pt(0);p.paragraph_format.first_line_indent=Pt(0)
                    for r in p.runs:r.font.name='Times New Roman'
        if len(rows)<=7:
            for index,row in enumerate(t.rows):
                for cell in row.cells:
                    for p in cell.paragraphs:p.paragraph_format.keep_with_next=index<len(t.rows)-1
        for cell in t.rows[0].cells:
            for r in cell.paragraphs[0].runs:r.bold=True
        record_table(title,headers,rows)
        return t
    def figure(self,path,caption):
        p=self.p('');p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.left_indent=Pt(0);p.paragraph_format.right_indent=Pt(0)
        p.paragraph_format.keep_with_next=True
        p.add_run().add_picture(str(path),width=Inches(3.45))
        self.p(caption,'caption')

def snapshot():
    required={'fixed','classical','multifold','generic','design','window','ablation','drift'}
    assert required<={p.stem.removesuffix('_completed') for p in RUN.glob('*_completed.json')}
    assert len(list((RUN/'jobs').glob('*.json')))==1390
    assert len(list((RUN/'drift_jobs').glob('*.json')))==290
    E.mkdir(parents=True,exist_ok=True)
    shutil.copytree(RUN/'exports',E/'exports',dirs_exist_ok=True)
    shutil.copy2(RUN/'protocol.json',E/'protocol.json')
    for folder in ['hardware','leakage_audit','window_sensitivity','ssl_baselines','baselines']:
        src=ROOT/'revision_artifacts'/folder
        if src.exists():shutil.copytree(src,E/folder,dirs_exist_ok=True)
    manifest={str(p.relative_to(E)):sha256(p) for p in E.rglob('*') if p.is_file()}
    dump(E/'snapshot_manifest.json',manifest)

def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    plt.rcParams.update({'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'legend.fontsize':8.5,'pdf.fonttype':42,'svg.fonttype':'none'})
    out=OUT/'figures'
    out.mkdir(parents=True,exist_ok=True)
    fig,axs=plt.subplots(3,1,figsize=(3.45,4.2))
    for ax,name,pattern in zip(axs,['NH3/H2','CO/ethylene','Sensor drift'],['nh3_h2_f0_early_s*_full.json','co_ethylene_f0_early_s*_full.json','drift_s*.json']):
        a=np.array([json.loads(p.read_text())['loss'] for p in sorted((RUN/'checkpoints').glob(pattern))])
        assert len(a)==10
        x=np.arange(1,a.shape[1]+1);m=a.mean(0);sd=a.std(0,ddof=1)
        ax.fill_between(x,m-sd,m+sd,facecolor='#E69F00',alpha=.68,edgecolor='#B56B00',linewidth=.55,zorder=2)
        ax.plot(x,m,color='#164B75',linewidth=1.05,zorder=3)
        ax.set(title=name,xlabel='Epoch',ylabel='Loss');ax.grid(alpha=.14,zorder=0)
        ax.tick_params(labelsize=7.5)
    handles=[Line2D([],[],color='#164B75',lw=1.4,label='Mean'),Patch(facecolor='#E69F00',edgecolor='#B56B00',alpha=.68,label='Mean \u00b1 1 SD')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,0),ncol=2,frameon=False,handlelength=2,handleheight=1.15,prop={'size':8.5,'weight':'bold'})
    fig.tight_layout(pad=.65,rect=[0,.065,1,1])
    for ext in ['png','pdf','svg']:
        target=out/f'fig3_pretraining.{ext}';fig.savefig(target,dpi=400)
    plt.close(fig)
    pred=read('predictions/raw_response_predictions.csv')
    fig,axs=plt.subplots(2,2,figsize=(3.45,3.55))
    colors=['#555555','#0072B2','#D55E00'];markers=['o','s','^']
    for ax,gas in zip(axs.flat,GASES):
        d=pred[(pred.gas==gas)&(pred.fold==0)&(pred.design=='farthest')&(pred.window=='early')]
        d=d[(d.budget==d.budget.max())&d.policy.isin(POLICIES)]
        for policy,color,marker in zip(POLICIES,colors,markers):
            r=d[d.policy==policy];ax.scatter(r.true,r.prediction,s=4,alpha=.42,color=color,marker=marker,linewidths=0,rasterized=True)
        limit=20 if gas=='Ethylene' else 533.33 if gas=='CO' else 500
        ax.plot([0,limit],[0,limit],'k--',lw=.7);ax.set(title=gas,xlabel='Reference (ppm)',ylabel='Prediction (ppm)',xlim=(0,limit),ylim=(0,limit));ax.tick_params(labelsize=6.5)
    handles=[Line2D([],[],linestyle='none',marker=marker,markersize=7,markerfacecolor=color,markeredgecolor=color,label=LABEL[policy]) for policy,color,marker in zip(POLICIES,colors,markers)]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.005),ncol=3,frameon=True,edgecolor='#777777',framealpha=1,handlelength=.85,handletextpad=.4,columnspacing=.85,borderpad=.55,prop={'size':8.5,'weight':'bold'})
    fig.tight_layout(pad=.55,rect=[0,.10,1,1])
    for ext in ['png','pdf','svg']:
        target=out/f'fig4_predictions.{ext}';fig.savefig(target,dpi=400)
    plt.close(fig)


def prepare_original(primary):
    d=Document(edit.SOURCE);p=list(d.paragraphs)
    styles={'body':p[109].style,'h1':p[102].style,'h2':p[103].style,'caption':p[107].style}
    abstract=next(q for t in d.tables for row in t.rows for c in row.cells for q in c.paragraphs if q.text.startswith('Abstract'))
    headline=', '.join(f'{g} {n(one(primary,gas=g).relative_improvement_pct,digits=1)}%' for g in GASES)
    edit.replace(abstract,'Abstract— Precisely labeled gas mixtures require concentration control or reference quantification, whereas mixtures without carefully controlled ppm can provide inexpensive unlabeled sensor responses. This motivates self-supervised pretraining on a large unquantified mixture pool followed by calibration with a small precisely labeled set. The authors evaluate the label-efficiency premise using existing datasets with concentration labels withheld during pretraining. A shared temporal encoder, sensor-identity embeddings, cross-sensor attention, and structured masked reconstruction are evaluated with a predefined fine-tuned transfer policy and 10 seeds. Primary evaluation uses six held-partition NH3/H2 folds and three rolling chronological CO/ethylene folds. Relative MAE reductions against scratch are '+headline+'. Paired seed-and-fold bootstrap intervals exclude zero for these four comparisons, conditional on the observed exposures. Fixed-split experiments compare all adaptation policies, calibration designs, classical regression, a compact PatchTST-style SSL control, architectural ablations, and window placement. The proposed architecture is not uniformly superior to generic SSL or classical models. Long-term drift evaluation includes constant controls, normalized errors, small budgets, and target-loss sensitivity; regression is conditional on known gas identity. These results support label-efficient same-system recalibration. Prospective pretraining on cheaply acquired, unquantified mixtures and its cost savings remain to be evaluated.','Abstract')
    changes={
        6:p[6].text.replace('Collecting these labels becomes costly', 'Obtaining precise concentration labels through controlled delivery or reference measurement becomes costly'),
        7:'The practical motivation is the cost difference between producing gas mixtures and establishing their precise gas-phase concentrations at the sensors. Mixtures prepared without carefully controlling ppm can supply inexpensive response recordings for self-supervised learning; only a small calibration set needs precise concentration labels. Source identities or preparation settings, when available, do not substitute for measured gas-phase ppm. The intended workflow therefore learns temporal response patterns and relationships among sensors from an unquantified mixture pool, then adapts the representation using precisely labeled calibration samples. In this study, existing controlled-exposure datasets with labels withheld during pretraining provide a retrospective test of that label-efficiency premise. They do not directly test a newly acquired low-cost mixture pool.',
        10:p[10].text.replace('Transfer improves two-gas regression and oracle-class gas-conditional concentration estimates under drift.','The authors evaluate multi-fold generalization, calibration-design controls, and oracle-class conditional concentration regression under drift, retaining null and adverse comparisons.'),
        17:'The present study connects masked representation learning to quantitative same-system recalibration. Its contribution is an evaluation of a sensor-aware encoder under controlled label budgets, held-out partitions, chronological tests, generic SSL and chemometric controls. The research objective is to reduce dependence on expensive, precisely labeled mixtures by learning from responses that do not require ppm labels. The present benchmarks test label efficiency; actual acquisition-cost savings and performance on unquantified mixtures require prospective evaluation.',
        25:p[25].text.replace('a larger set of unlabeled exposures is available', 'a larger set of mixture responses without precise concentration labels is available').replace('A small adaptation set', 'The present benchmark emulates this setting by withholding existing pretraining labels; reconstruction uses sensor responses alone and does not require known mixture ratios or ppm. A small precisely labeled adaptation set'),
        41:p[41].text+' The embeddings are tied to physical channel correspondence. Current experiments use the same array within each dataset and do not establish cross-device transfer.',
        67:'Adaptation Policies and Calibration-Pair Design',
        68:'Three adaptation policies are evaluated: scratch, frozen transfer, and fine-tuned transfer. Scratch fits the complete model from random initialization. Frozen transfer trains the supervised head with the pretrained encoder fixed. Fine-tuning updates the pretrained encoder at a lower learning rate than the head. Fine-tuning is predefined as the primary policy for every gas; test MAE never selects between policies. The concentration coordinates in (16) are known only for the labeled calibration-design pool; the unlabeled pretraining pool does not require concentration coordinates. Farthest-point selection is a retrospective coverage control among labeled samples, not a label-free selection rule for cheap mixtures. Its selected-pair budget counts fitting and validation labels, not the cost of quantifying the larger candidate pool.',
        74:'The NH3/H2 dataset [29] contains 162,404 observations from 20 Nano MEMS sensor channels, grouped into 378 recorded sequences, with concentrations of 0–500 ppm for each gas. The authors form six partitions of 63 sequences using consecutive Combination identifiers; these partitions do not establish separate acquisition days or physically independent measurements.',
        75:'The primary NH3/H2 evaluation holds out each of the six partitions in turn, uses the preceding cyclic partition for adaptation, and uses the remaining four for pretraining. Because some pretraining partitions follow the test partition, this is held-partition validation, not prospective forecasting. The secondary fixed split uses partitions 1–4 for pretraining (252 exposures; 1,260 windows), partition 5 for adaptation, and partition 6 for testing. Five 64-sample training windows use offsets 0–4; tests use offset zero only. Related image-based mixed-gas estimation is described by Ha et al. [30].',
        76:'Within every fold, complete exposures are assigned before window extraction. Response scaling is fitted exclusively to that fold’s pretraining responses. Adaptation fitting and validation exposures are disjoint, and all policies use identical group assignments within each seed and budget. Test exposures are excluded from preprocessing fits, pretraining, calibration design, fitting, and checkpoint selection. A budget counts both fitting and validation concentration pairs.',
        79:'Primary CO/ethylene validation divides the 245 acquisition-ordered groups into seven blocks and evaluates three rolling folds, each with three pretraining blocks followed by one adaptation block and one future test block. Secondary fixed-split experiments retain five blocks of 49 groups: blocks 1–3 pretrain, block 4 adapts, and block 5 tests. Budgets are 5, 10, 20, and 24 unique concentration pairs. Training uses five stored offsets; the test uses one window per group.',
        82:'Partitions 1–6 (months 1–20) pretrain the descriptor encoder; partition 7 (month 21) provides adaptation labels; partitions 8–10 are separate future tests. The authors evaluate 1, 2, 5, 10, and 20 labels per gas with 10 seeds. At 20 labels/gas, 16 fit and four validate each gas, identically across policies. One label/gas has no disjoint holdout and therefore uses the predefined final epoch; larger budgets select checkpoints using adaptation-only validation.',
        84:p[84].text.replace('Per-gas concentrations are mapped to normalized log space as in (17).','The predefined 20-label analysis uses the normalized log targets in (17); fixed-scale log and linear losses are additional sensitivity controls.'),
        85:'Figure 2 preserves the original secondary fixed-split schematic and the primary chronological drift roles. Primary NH3/H2 cyclic folds and CO/ethylene rolling folds are specified above. Pretraining withholds concentration labels; adaptation and test roles remain disjoint.',
        87:'Fig. 2. Leakage-controlled secondary fixed splits and chronological drift roles; the primary multi-fold protocols are specified in Section IV.',
        172:'Original study repository: https://github.com/ngdvan/Transfer-learning-Enose. Revision-specific code, the fixed protocol, input hashes, predictions and result tables are supplied in the supplementary reproducibility package.',
    }
    for i,t in changes.items():edit.replace(p[i],t,f'Original paragraph {i}')
    edit.replace_literal(p[69],'The calibration pairs are selected to cover the available concentration space by farthest-point sampling,','Calibration pairs are designed using known concentration coordinates by farthest-point sampling,','Equation (16) interpretation')
    edit.replace_literal(p[92],'at most 120 epochs','120 epochs','Drift schedule')
    edit.replace_literal(p[92],'adaptation-only early stopping with patience 20','adaptation-only minimum-loss checkpoint selection, except for the one-label final-epoch protocol','Drift checkpoint selection')
    for child in list(p[92]._p):
        if list(child.iter(qn('w:drawing'))) or 'Summary of Full-Budget Regression Performance' in ''.join(t.text or '' for t in child.iter(qn('w:t'))):
            edit.delete(child,'Obsolete floating result table','Remove test-selected summary and its VML fallback.')
    # Add related work without discarding the detailed original review and equations.
    rel=Insert(d,p[18]._p,styles)
    rel.p('Masked time-series representation learning includes channel-independent patch Transformers such as PatchTST [18] and multivariate Transformer reconstruction [19], while TS2Vec learns hierarchical contrastive representations [20]. The authors implement a compact PatchTST-style gas-regression control with explicit deviations from the forecasting model. It tests whether the complete sensor-aware design helps beyond generic masked learning; differing encoders mean it does not isolate sensor identity alone.')
    rel.p('PLSR [21] and SVR [22] provide chemometric controls alongside Extra Trees [26] and XGBoost [27]. Farthest-point design is related to concentration-space coverage methods [23]. Nonexchangeable conformal inference [24] and covariate-shift conformal prediction [25] motivate a cautious interpretation of uncertainty under chronological sensor drift.')
    dat=Insert(d,p[95]._p,styles)
    dat.p('All revised experiments use seeds 42, 142, 242, 342, 442, 542, 642, 742, 842, and 942, with seed-specific pretraining. Approximately 20% of selected exposure groups are reserved for validation. Random and farthest-point calibration designs are crossed with scratch and fine-tuning at every fixed-split budget. Full multi-fold coverage uses all available adaptation pairs, whose number can differ between rolling folds.')
    dat.p('Dataset-specific hardware and environmental settings remain unverified; the related VOC-array study [28] does not establish the NH3/H2 acquisition configuration. Digital audits found no identical stored signal fingerprints or identifier overlap across 11 split definitions, but do not prove physical acquisition independence. The concentration range does not validate low-concentration ambient monitoring. Supplementary ?NH3/H2 dataset and acquisition details? provides the metadata limitations and audit scope.')
    dat.p('NH3/H2 sensitivity tests compare early, middle, late, and full-exposure 64-sample inputs, refitting scalers on the corresponding pretraining windows. Early windows remain predefined. Exact sample-position definitions are supplied in the supplement; without a verified sampling frequency, positions cannot be interpreted as durations.')
    dat.p('The generic SSL control uses eight nonoverlapping length-8 patches per channel, 32-dimensional tokens, two four-head Transformer layers, 96-unit feed-forward blocks, shared channel weights, temporal positions, and three masked patches per channel. It has no physical sensor embeddings or cross-channel attention. Temporal mean pooling feeds the same concatenated-channel regression head, so channel ordering remains available. Instance normalization is omitted to preserve absolute responses and match preprocessing; capacity differs and is reported. Pretraining/adaptation data, budgets, seeds, scaling and checkpoint rules match the proposed model.')
    dat.p('Classical regressors receive flattened pretraining-scaled windows: 1,280 NH3/H2 or 1,024 CO/ethylene features. PLSR and separate-target RBF SVR additionally standardize features using fitting data only. Hyperparameters are selected by adaptation-validation normalized MAE. Tree settings are fixed. At 20 drift labels/gas, historical log-Huber is compared with log1p(c)/log1p(1000), linear c/1000 Huber, and linear c/1000 MAE. Below 20 labels/gas the fixed log scale avoids estimating a standard deviation from tiny fitting sets. The 1000-ppm divisor is a numerical unit, not an asserted physical maximum. Constant controls use only the per-gas fitting mean.')
    metrics=Insert(d,p[102]._p,styles)
    metrics.p('The authors report seed means and sample SD (ddof=1). Paired 95% bootstrap intervals use 5,000 crossed seed-and-fold resamples, weighting folds equally and conditioning on observed test exposures. Repeated predictions are not independent exposures, and overlapping training folds limit population inference. Fixed-split controls resample paired seeds; the control comparisons are exploratory and not multiplicity-adjusted. Drift NMAE divides each gas MAE by its concentration range in historical partitions 1–6, whose labels are used for reporting only. This permits an equal-gas macro-NMAE when a test-partition range is zero; the test-range diagnostic is also retained.')
    # Replace all outdated Results/Discussion, including native tables, as one block.
    first=p[102]._p;stop=p[145]._p;node=first
    while node is not stop:
        nxt=node.getnext();edit.delete(node,'Original Results and Discussion','Replaced by complete ten-seed results and controls.');node=nxt
    return d,p,styles,Insert(d,stop,styles)

def results(w):
    s=read('10_seed_runs/summary_raw_response.csv')
    s=s[(s.fold==0)&(s.design=='farthest')&(s.window=='early')]
    primary=read('multifold/paired_bootstrap_summary.csv')
    def r(gas,policy,budget=None):return one(s,gas=gas,policy=policy,budget=budget or (57 if gas in ['NH3','H2'] else 24))
    def paired_text(row):return f'{n(row.improvement,row.gas)} ppm (95% interval {n(row.ci_low,row.gas)} to {n(row.ci_high,row.gas)})'
    w.p('Results','h1')
    w.p('Self-Supervised Pretraining','h2')
    w.p('Figure 3 reports reconstruction loss over ten independently seeded pretraining runs. These curves are optimization diagnostics; lower reconstruction loss across differently scaled datasets is not a concentration-accuracy comparison. All quantitative claims below use held-out concentration predictions.')
    w.figure(OUT/'figures/fig3_pretraining.png','Fig. 3. Reconstruction loss over 10 seeds: blue line, mean; orange band, mean ± one seed SD. Raw-response pretraining uses 60 epochs; descriptor pretraining uses 40.')
    w.p('Primary Multi-Fold Validation','h2')
    w.p('Table I is the primary generalization analysis. Fine-tuning is compared with scratch using the same adaptation groups and validation holdout in each seed. Positive paired differences favor fine-tuning. All four intervals exclude zero in the revised analysis; NH3 has the lower bound closest to zero. These intervals describe seed/fold variation conditional on the observed exposures, rather than guaranteed improvements on new arrays or acquisition campaigns.')
    rows=[]
    for gas in GASES:
        a=one(primary,gas=gas)
        rows.append([gas,n(a.scratch_mae,gas),n(a.transfer_mae,gas),n(a.improvement,gas),f'[{n(a.ci_low,gas)}, {n(a.ci_high,gas)}]'])
    w.table('Table I. Primary Multi-Fold MAE and Paired Difference (ppm)', ['Gas','Scratch','Fine-tuned','Difference','95% interval'],rows,[.56,.60,.65,.62,1.02])
    w.p('Relative reductions are '+', '.join(f'{g}: {n(one(primary,gas=g).relative_improvement_pct,digits=1)}%' for g in GASES)+'. Across-fold SD of fine-tuned mean MAE is '+', '.join(f'{g}: {n(one(primary,gas=g).across_fold_sd,g)} ppm' for g in GASES)+'. NH3/H2 includes 378 distinct test identifiers over six folds (3,780 predictions per gas across seeds); CO/ethylene includes 105 identifiers over three rolling tests (1,050 predictions per gas). Supplementary Table S1 retains every fold and all policies.')
    seeds=pd.read_csv(E/'seed_stability/first3_vs_all10.csv')
    w.p('The planned ten-seed set does not show systematic erosion as seeds accumulate. Within this revised protocol, first-three to all-ten relative reductions are '+', '.join(f'{g}: {n(one(seeds,family="primary_multifold",gas=g).first3_gain_pct,digits=1)}% to {n(one(seeds,family="primary_multifold",gas=g).all10_gain_pct,digits=1)}%' for g in GASES)+'. The CO/ethylene estimates attenuate slightly, while the NH3/H2 estimates increase. This comparison isolates seed count within the revised protocol; differences from the original manuscript also reflect corrected holdouts and policy reporting. Supplementary Table S2 and Fig. S1 show all prefixes and random-order sensitivity; all ten seeds are retained.')
    w.p('Fixed-Split Label-Budget Analysis','h2')
    w.p('Table II reports all adaptation policies as mean ± seed SD. Budgets include validation labels. These fixed-split experiments are secondary to the multi-fold evaluation; neither the policy nor the budget is chosen from test performance. At full budget the paired means favor fine-tuning over scratch, but errors do not decrease monotonically at every budget.')
    rows=[]
    for gas in GASES:
        for budget in ([5,10,20,40,57] if gas in ['NH3','H2'] else [5,10,20,24]):rows.append([gas,str(budget)]+[ms(r(gas,policy,budget),gas) for policy in POLICIES])
    w.table('Table II. Fixed-Split MAE (ppm), Mean ± SD Over Ten Seeds',['Gas','Pairs','Scratch','Frozen','Fine-tuned'],rows,[.56,.35,.84,.84,.86])
    w.p('For example, fine-tuned CO MAE is '+ms(r('CO','fine_tuned',20))+' ppm at 20 pairs and '+ms(r('CO','fine_tuned',24))+' ppm at 24 pairs. Figure 4 retains all three policies rather than a test-selected policy summary.')
    w.p('The secondary full-budget fixed-split gains do attenuate as seeds accumulate: first three → all ten reductions are '+', '.join(f'{g}: {n(one(seeds,family="fixed_split",gas=g,budget=str(57 if g in ["NH3","H2"] else 24)).first3_gain_pct,digits=1)}% to {n(one(seeds,family="fixed_split",gas=g,budget=str(57 if g in ["NH3","H2"] else 24)).all10_gain_pct,digits=1)}%' for g in GASES)+'. The larger attenuation for NH3 shows why a favorable small seed set should not determine the headline. All ten seeds remain included, and the main conclusion rests on multi-fold evidence.')
    w.figure(OUT/'figures/fig4_predictions.png','Fig. 4. Secondary full-budget predictions from all 10 seeds: gray circles, Scratch; blue squares, Frozen; orange triangles, Fine-tuned. Points repeat test exposures across seeds; the dashed line is identity, not a fitted trend.')
    w.p('Calibration-Design Control','h2')
    design=read('calibration_design/factorial_summary.csv')
    rows=[]
    for gas in GASES:
        for des in ['random','farthest']:
            rows.append([gas,des.title()]+[ms(one(design,gas=gas,budget=5,design=des,policy=policy),gas) for policy in ['scratch','fine_tuned']])
    w.table('Table III. Five-Pair Design Control, MAE (ppm), Mean ± SD',['Gas','Design','Scratch','Fine-tuned'],rows,[.56,.67,1.11,1.11])
    tests=read('calibration_design/paired_design_statistics.csv')
    five=tests[(tests.budget==5)&(tests.training_policy=='fine_tuned')]
    w.p('Random and farthest-point designs are crossed with both training policies at every budget. At five pairs, random minus farthest-point fine-tuned MAE is '+ '; '.join(f'{g}: {paired_text(one(five,gas=g))}' for g in GASES)+'. The design effect is therefore target-dependent. It uses known concentration coordinates and must not be interpreted as active acquisition of unknown labels. All-budget paired design and transfer contrasts are in Supplementary Table S3.')
    w.p('Baseline Comparison','h2')
    rows=[]
    for policy in ['scratch','extra_trees','xgboost','plsr','svr','generic_ssl','fine_tuned']:
        rows.append([LABEL[policy]]+[ms(r(gas,policy),gas) for gas in GASES])
    w.table('Table IV. Full-Budget Baseline MAE (ppm), Mean ± SD',['Model']+GASES,rows,[.73,.68,.68,.68,.68])
    w.p('The sensor-aware model is not uniformly strongest. PLSR CO MAE is '+ms(r('CO','plsr'))+' ppm versus '+ms(r('CO','fine_tuned'))+' ppm for fine-tuning; Extra Trees ethylene MAE is '+ms(r('Ethylene','extra_trees'),'Ethylene')+' ppm versus '+ms(r('Ethylene','fine_tuned'),'Ethylene')+' ppm. These are observed means under the declared fixed split, not a claim of universal statistical superiority. PLSR/SVR validation grids and all budget results are documented in the supplement.')
    generic=read('ssl_baselines/proposed_vs_generic_ssl.csv')
    w.p('At full budget, generic SSL minus sensor-aware MAE is '+ '; '.join(f'{g}: {paired_text(one(generic,gas=g,budget=57 if g in ["NH3","H2"] else 24))}' for g in GASES)+'. The matched control favors the sensor-aware design on H2 and the generic design on NH3 and ethylene; the CO interval includes zero. Lower and medium budgets are also mixed. This limits the general sensor-aware superiority claim, while preserving the separate comparison with scratch. Capacity and encoder differences prevent attributing the entire difference to sensor identity.')
    w.p('Ablation and Window Sensitivity','h2')
    raw=read('policy_selection/all_policy_results.csv')
    raw=raw[(raw.fold==0)&(raw.design=='farthest')&(raw.window=='early')]
    variants=['no_sensor_ids','no_attention','no_temporal_mask','no_sensor_mask']
    ab=[];rows=[]
    for variant,label in zip(variants,['No sensor ID','No attention','No time mask','No sensor mask']):
        line=[label]
        for gas in GASES:
            budget=57 if gas in ['NH3','H2'] else 24
            a=raw[(raw.gas==gas)&(raw.budget==budget)&(raw.policy==variant)].set_index('seed').mae
            b=raw[(raw.gas==gas)&(raw.budget==budget)&(raw.policy=='fine_tuned')].set_index('seed').mae
            delta=(a-b).reindex(SEEDS);assert len(delta.dropna())==10
            line.append(n(delta.mean(),gas)+' ± '+n(delta.std(ddof=1),gas))
            ab.append(dict(gas=gas,variant=variant,budget=budget,delta_mean=delta.mean(),delta_sd=delta.std(ddof=1)))
        rows.append(line)
    pd.DataFrame(ab).to_csv(E/'ablation_paired_differences.csv',index=False)
    w.table('Table V. Full-Budget Ablation Minus Full-Model MAE (ppm), Mean ± SD',['Removed']+GASES,rows,[.83,.65,.65,.65,.67])
    w.p('Positive values in Table V indicate an increase in error after removing the component; negative values indicate that the ablated variant performed better. Paired differences include uncertainty over all ten seeds. Sensor-ID effects differ by gas, but these data cannot distinguish physical selectivity from optimization and sampling variation. Missing sensor characterization prevents a chemistry-based explanation; no component is claimed to be uniformly beneficial.')
    a=pd.DataFrame(ab)
    w.p('Removing sensor identity changes NH3 MAE by '+n(one(a,gas='NH3',variant='no_sensor_ids').delta_mean)+' ± '+n(one(a,gas='NH3',variant='no_sensor_ids').delta_sd)+' ppm, compared with '+n(one(a,gas='H2',variant='no_sensor_ids').delta_mean)+' ± '+n(one(a,gas='H2',variant='no_sensor_ids').delta_sd)+' ppm for H2. Removing attention lowers NH3 error by '+n(-one(a,gas='NH3',variant='no_attention').delta_mean)+' ppm on average. Thus the original large cross-gas identity-effect ratio is not treated as a stable physical constant, and the attention module is not uniformly beneficial.')
    window=read('window_sensitivity/window_position_results.csv');rows=[]
    for pos in ['early','middle','late','full']:
        rows.append([pos.title()]+[ms(one(window,gas=g,budget=57,window=pos,policy=policy),g) for g,policy in [('NH3','scratch'),('NH3','fine_tuned'),('H2','scratch'),('H2','fine_tuned')]])
    w.table('Table VI. Window Sensitivity, MAE (ppm), Mean ± SD',['Window','NH3 scratch','NH3 transfer','H2 scratch','H2 transfer'],rows,[.53,.73,.73,.73,.73])
    w.p('Window placement materially changes both absolute error and the transfer contrast. Late windows are substantially worse for both gases; middle-window H2 does not improve with transfer. Full-exposure resampling is a useful control, but does not establish a unique physical optimum. The original early window remains the primary protocol, and the sensitivity result is not used to optimize that choice on the test set.')
    w.p('Long-Term Drift','h2')
    macro=read('sensor_drift/macro_error.csv')
    mac=macro.groupby(['fold','budget','transform','policy']).agg(mae_mean=('mae','mean'),mae_sd=('mae','std'),nmae_mean=('nmae','mean'),nmae_sd=('nmae','std'),n_seeds=('seed','nunique')).reset_index()
    mac.to_csv(E/'drift_macro_summary.csv',index=False)
    rows=[]
    for policy in ['constant']+POLICIES:
        rows.append([LABEL[policy]]+[ms(one(mac,fold=f,budget=20,transform='log_huber',policy=policy)) for f in [8,9,10]])
    w.table('Table VII. Oracle-Class Drift Macro-MAE (ppm), Mean ± SD',['Policy','Partition 8','Partition 9','Partition 10'],rows,[.65,.93,.93,.94])
    stats=read('sensor_drift/paired_statistics.csv')
    dst=stats[(stats.budget==20)&(stats['transform']=='log_huber')&(stats.gas=='MacroMAE')&(stats.policy=='fine_tuned')]
    w.p('The primary 20-label/gas transform is historical per-gas log-Huber; the constant predictor uses the same fitting records. Scratch minus fine-tuned macro-MAE is '+ '; '.join(f'partition {f}: {paired_text(one(dst,partition=f))}' for f in [8,9,10])+'. These intervals resample seeds, conditional on each test partition. The comparison describes concentration regression with true gas identity supplied; it excludes classification errors.')
    p10=one(dst,partition=10)
    verdict=('includes zero, so there is no clear improvement' if p10.ci_low<=0<=p10.ci_high else 'lies below zero, indicating higher fine-tuned error' if p10.ci_high<0 else 'lies above zero in this seed-conditional comparison')
    w.p('For partition 10, the revised paired interval '+verdict+'. This conclusion replaces the original interpretation of a small mean change. Neither a positive conditional interval nor an improved average establishes robust deployment performance under severe drift. The constant and normalized-error controls remain necessary to judge useful calibration accuracy.')
    pergas=read('10_seed_runs/summary_sensor_drift.csv')
    rows=[]
    drift_names=['Ethanol','Ethylene','Ammonia','Acetaldehyde','Acetone','Toluene']
    for gas in drift_names:
        rows.append([gas]+[n(100*one(pergas,fold=f,budget=20,transform='log_huber',policy='fine_tuned',gas=gas).nmae_mean)+' ± '+n(100*one(pergas,fold=f,budget=20,transform='log_huber',policy='fine_tuned',gas=gas).nmae_sd) for f in [8,9,10]])
    rows.append(['Macro']+[n(100*one(mac,fold=f,budget=20,transform='log_huber',policy='fine_tuned').nmae_mean)+' ± '+n(100*one(mac,fold=f,budget=20,transform='log_huber',policy='fine_tuned').nmae_sd) for f in [8,9,10]])
    w.table('Table VIII. Fine-Tuned Per-Gas NMAE (% of Historical Range), Mean ± SD',['Gas','Partition 8','Partition 9','Partition 10'],rows,[.8,.88,.88,.89])
    w.p('Table VIII uses each gas’s fixed historical concentration range and weights gases equally; it avoids allowing high-ppm analytes to dominate the normalized macro score. All-policy per-gas MAE and NMAE, reference ranges, and all five budgets are in Supplementary Tables S5–S6. A one-label/gas run is a fixed-epoch tiny-sample test, not a validated checkpoint comparison.')
    w.p('Under fixed-log scaling, fine-tuned one-label/gas macro-MAE is '+', '.join(f'{f}: {ms(one(mac,fold=f,budget=1,transform="log_fixed_huber",policy="fine_tuned"))} ppm' for f in [8,9,10])+'. Its large seed variation and the substantial partition-10 error limit claims of extreme label efficiency. Budget effects are not uniformly monotonic. The fixed-log 20-label control is retained to separate budget effects from the primary protocol’s change to fitted-log scaling at 20 labels.')
    rows=[]
    for transform,label in [('log_huber','Log fitted SD'),('log_fixed_huber','Log fixed'),('linear_huber','Linear Huber'),('linear_mae','Linear MAE')]:
        rows.append([label]+[ms(one(mac,fold=f,budget=20,transform=transform,policy='fine_tuned')) for f in [8,9,10]])
    w.table('Table IX. Fine-Tuned Loss/Scaling Sensitivity, Macro-MAE (ppm), Mean ± SD',['Target / loss','Partition 8','Partition 9','Partition 10'],rows,[.84,.87,.87,.87])
    w.p('Log-space Huber and linear-space MAE optimize different error geometry, so a log-space optimum need not minimize linear MAE. Table IX explicitly tests target/loss alternatives at the same label budget. Fixed scaling avoids estimating log-space variance from 16 fitting records per gas, but is not presumed uniformly superior. All alternatives remain sensitivity analyses; their test scores do not select a replacement primary transform. Supplementary Table S7 reports every policy and preserves the fitting-derived means and scales.')
    w.p('Historical fitted-log Huber has the lowest observed fine-tuned macro-MAE among these transforms in partitions 8 and 9. In partition 10, linear MAE gives '+ms(one(mac,fold=10,budget=20,transform='linear_mae',policy='fine_tuned'))+' ppm versus '+ms(one(mac,fold=10,budget=20,transform='log_huber',policy='fine_tuned'))+' ppm for fitted-log Huber, while fixed-log Huber rises to '+ms(one(mac,fold=10,budget=20,transform='log_fixed_huber',policy='fine_tuned'))+' ppm. The apparent severe-drift benefit of changing the loss is therefore not a uniform scaling improvement, and the linear-MAE transfer-versus-scratch interval also includes zero.')
    w.p('Tail Error, Capacity, and Uncertainty','h2')
    rows=[]
    for gas in GASES:
        for policy in POLICIES:
            a=r(gas,policy);rows.append([gas,LABEL[policy],n(a.r2_mean,digits=3),n(a.rmse_mean,gas),n(a.q90_mean,gas)])
    w.table('Table X. Full-Budget Mean R², RMSE and Q0.9 Across Ten Seeds',['Gas','Policy','R²','RMSE','Q0.9'],rows,[.56,.70,.57,.80,.82])
    w.p('CO remains quantitatively limited even after transfer: mean R² is '+n(r('CO','fine_tuned').r2_mean,digits=3)+', and Q0.9 is '+n(r('CO','fine_tuned').q90_mean)+' ppm on the 0–533.33 ppm scale. Relative improvement must not be equated with adequate quantitative calibration. Table X includes scratch tail errors and frozen transfer as well as fine-tuning.')
    sizes=read('statistics/model_size.csv')
    lines=[]
    for ds,label,budget in [('nh3_h2','NH3/H2',57),('co_ethylene','CO/ethylene',24)]:
        base=sizes[(sizes.dataset==ds)&(sizes.fold==0)&(sizes.seed==42)&(sizes.design=='farthest')&(sizes.window=='early')]
        a=one(base,budget=budget,policy='fine_tuned');b=one(base,budget=budget,policy='frozen');g=one(base,budget=budget,policy='generic_ssl')
        lines.append(f'{label}: {int(a.total):,} proposed parameters ({int(a.encoder):,} encoder; {int(a["head"]):,} head), all trainable in fine-tuning versus {int(b.trainable):,} in frozen transfer; generic SSL has {int(g.total):,}. The seed-42 full-budget fitting subset has {int(a.fitting_exposures)} distinct exposures, giving {a.parameters_per_fitting_exposure:,.0f} proposed parameters per fitting exposure.')
    w.p(' '.join(lines)+' Five overlapping windows do not multiply the independent sample count. Supplementary Table S8 gives low/full-budget model sizes and drift counts; high parameter-to-exposure ratios remain an overfitting concern despite regularization and validation.')
    w.p('Standard split-conformal coverage relies on exchangeability between calibration and test residuals. The chronological/session shift in these experiments violates that assumption, so earlier split-conformal intervals are diagnostic, not guaranteed deployment-shift coverage [24], [25]. The authors do not recycle earlier three-repeat coverage percentages as new ten-seed measurements. A shift-aware uncertainty method requires separate evaluation; it is not claimed as an implemented remedy.')
    w.p('Discussion and Conclusion','h1')
    w.p('This study investigates sensor-aware self-supervised learning for label-efficient multigas electronic-nose calibration. A shared temporal encoder, sensor-identity embeddings, cross-sensor attention and structured masked reconstruction support representation reuse with limited concentration labels. Under a predefined fine-tuning policy, primary multi-fold evaluation yields mean MAE reductions of 13.9% for NH3, 21.5% for H2, 27.5% for CO and 25.7% for ethylene relative to training from scratch. These results support self-supervised pretraining for same-system recalibration under the evaluated protocols.')
    w.p('The benefit of pretraining does not establish that the sensor-aware architecture is uniformly superior. Generic masked self-supervision and classical regressors are competitive or stronger on several targets. Ablations show gas-dependent effects of sensor identity and attention, while window placement materially affects both absolute error and the transfer contrast. Calibration-design effects are also target-dependent, and label-budget trends are not uniformly monotonic. The evidence therefore supports the complete training procedure in specific settings without attributing its gains solely to physical sensor embeddings. Remaining absolute and tail errors, particularly for CO, limit conclusions about practical calibration adequacy.')
    w.p('Long-term drift remains a substantial limitation. Oracle-class concentration regression improves over scratch in future partitions 8 and 9, but shows no clear improvement in partition 10. This evaluation assumes that gas identity is known and does not include gas-classification errors. Constant-predictor controls, per-gas normalized errors and target/loss sensitivity show that performance depends on the gas, future partition and optimization objective. Same-system representation reuse alone does not establish robust performance under severe drift; temporal adaptation and shift-aware uncertainty require further investigation.')
    w.p('Ten independently seeded runs characterize variability in initialization, training, calibration design and adaptation holdouts. They do not replace independent acquisition sessions or additional devices. Primary paired intervals are conditional on the observed exposures; the NH3 interval approaches zero, only three chronological CO/ethylene folds are available, and training folds overlap. Secondary fixed-split estimates are sensitive to seed sampling. Dataset-specific acquisition settings and physical exposure independence remain unverified. Learned sensor identities also depend on channel correspondence, so cross-device generalization requires separate evaluation on compatible, characterized arrays.')
    w.p('The practical motivation is to learn from inexpensive mixture-response recordings and reserve precise concentration measurements for a small calibration set. Withholding existing labels tests this learning premise retrospectively, but does not demonstrate acquisition-cost savings or equivalent coverage from unquantified mixtures. Farthest-point design additionally requires known candidate concentrations, whose quantification cost is outside the selected-pair budget. A prospective study should combine cheaply prepared unquantified mixtures, a small precisely labeled adaptation set and independent quantified test exposures, with complete cost accounting and acquisition metadata. Within these limits, the present findings support label-efficient same-system recalibration through self-supervised representation reuse, while identifying the conditions that must be tested before broader deployment.')
    return s,primary,mac

def simple_doc(title):
    d=Document();d.add_heading(title,0)
    for section in d.sections:
        section.top_margin=section.bottom_margin=Inches(.7)
        section.left_margin=section.right_margin=Inches(.65)
    d.styles['Normal'].font.name='Calibri';d.styles['Normal'].font.size=Pt(10)
    return d

def plain_table(doc,title,headers,rows):
    doc.add_heading(title,2)
    t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid'
    for c,text in zip(t.rows[0].cells,headers):c.text=str(text)
    for values in rows:
        for c,text in zip(t.add_row().cells,values):c.text=str(text)
    edit.configure_table(t,[7.2/len(headers)]*len(headers))
    for c in t.rows[0].cells:
        for r in c.paragraphs[0].runs:r.bold=True
    return t

def supplement():
    d=simple_doc('Supplementary Evidence — Full Revision')
    d.add_paragraph('The authors provide additional experimental results, sensitivity analyses and details of the NH3/H2 measurement apparatus and acquisition protocol. Numerical summaries use ten predefined seeds and are conditional on the observed test exposures. The accompanying data exports retain unrounded results.')
    fold=read('multifold/fold_level_summary.csv');rows=[]
    for _,a in fold.iterrows():rows.append([a.gas,int(a.fold),int(a.budget),LABEL[a.policy],ms(a,a.gas)])
    plain_table(d,'Table S1. Fold-level MAE (ppm), mean ± seed SD',['Gas','Fold','Pairs','Policy','MAE'],rows)
    seeds=pd.read_csv(E/'seed_stability/first3_vs_all10.csv')
    rows=[[a.gas,n(a.first3_gain_pct),n(a.all10_gain_pct),n(a.later7_gain_pct),int(a.positive_seeds)] for _,a in seeds[seeds.family=='primary_multifold'].iterrows()]
    plain_table(d,'Table S2. Seed-count sensitivity within the revised primary protocol',['Gas','First 3 gain %','All 10 gain %','Later 7 gain %','Positive / 10'],rows)
    secondary=seeds[(seeds.family!='primary_multifold')&((seeds.family!='fixed_split')|seeds.budget.astype(str).isin(['57','24']))]
    plain_table(d,'Table S2b. Secondary full-budget fixed split and drift seed sensitivity',['Analysis','Gas','First 3 gain %','All 10 gain %','Later 7 gain %'],[[a.family,a.gas,n(a.first3_gain_pct),n(a.all10_gain_pct),n(a.later7_gain_pct)] for _,a in secondary.iterrows()])
    d.add_paragraph('Prefixes use the predefined order 42, 142, …, 942; all ten remain the reporting set. A random-order 95% envelope is a subset diagnostic, not a confidence interval. More seeds change an estimated mean; they do not weaken a trained model or increase the number of independent physical exposures.')
    d.add_picture(str(E/'seed_stability/seed_stability.png'),width=Inches(6.9));d.add_paragraph('Fig. S1. Primary relative MAE reduction against scratch as seeds accumulate; shading shows 2.5th–97.5th percentiles of 2,000 random subsets at each count.')
    cumulative=pd.read_csv(E/'seed_stability/cumulative_seed_statistics.csv')
    rows=[[a.gas,int(a.n_prefix_seeds),n(a.scratch_mae,a.gas),n(a.transfer_mae,a.gas),n(a.relative_improvement_pct),f'[{n(a.ci_low,a.gas)}, {n(a.ci_high,a.gas)}]'] for _,a in cumulative[cumulative.family=='primary_multifold'].iterrows()]
    plain_table(d,'Table S2a. Every primary seed prefix (errors and intervals in ppm)',['Gas','Seeds','Scratch','Fine-tuned','Gain %','Difference 95% interval'],rows)
    tests=read('calibration_design/paired_design_statistics.csv')
    rows=[[a.gas,int(a.budget),LABEL[a.training_policy],n(a.scratch_mae,a.gas),n(a.transfer_mae,a.gas),f'{n(a.improvement,a.gas)} [{n(a.ci_low,a.gas)}, {n(a.ci_high,a.gas)}]'] for _,a in tests.iterrows()]
    plain_table(d,'Table S3. Random minus farthest-point design MAE (ppm)',['Gas','Pairs','Policy','Random','Farthest','Difference [95% interval]'],rows)
    d.add_paragraph('The export column scratch_mae in this reused paired-comparison routine is the comparator mean (random design here); transfer_mae is the farthest-point mean. Positive differences favor farthest-point design. These exploratory comparisons are not multiplicity-adjusted.')
    generic=read('ssl_baselines/proposed_vs_generic_ssl.csv')
    rows=[[a.gas,int(a.budget),n(a.scratch_mae,a.gas),n(a.transfer_mae,a.gas),f'{n(a.improvement,a.gas)} [{n(a.ci_low,a.gas)}, {n(a.ci_high,a.gas)}]'] for _,a in generic.iterrows()]
    plain_table(d,'Table S4. Generic SSL minus sensor-aware MAE (ppm)',['Gas','Pairs','Generic','Sensor-aware','Difference [95% interval]'],rows)
    d.add_paragraph('The control is a compact reimplementation inspired by PatchTST, not the official forecasting configuration. See Section IV for architectural differences. PLSR candidates use 1, 2, 3, 5, 8 or 12 components when below the fitting-sample/feature bound. RBF SVR searches C ∈ {0.1, 1, 10}, gamma ∈ {scale, 0.001}, epsilon ∈ {0.01, 0.1}, on fixed-normalized targets. Selection minimizes adaptation-validation normalized MAE. Extra Trees uses 300 trees and minimum leaf size 2. XGBoost uses 300 trees, depth 3, learning rate 0.03, and row/feature fractions 0.9. Test predictions are clipped to the same target ranges as neural models.')
    base=read('baselines/baseline_summary.csv')
    base=base[base.policy.isin(['scratch','extra_trees','xgboost','plsr','svr','generic_ssl','fine_tuned'])]
    rows=[[a.gas,int(a.budget),LABEL[a.policy],ms(a,a.gas)] for _,a in base.iterrows()]
    plain_table(d,'Table S4a. All-budget baseline MAE (ppm), mean ± SD',['Gas','Pairs','Model','MAE'],rows)
    per=read('10_seed_runs/summary_sensor_drift.csv')
    main=per[(per.budget==20)&(per['transform']=='log_huber')]
    rows=[[int(a.fold),a.gas,LABEL[a.policy],ms(a),n(100*a.nmae_mean)+' ± '+n(100*a.nmae_sd)] for _,a in main.iterrows()]
    plain_table(d,'Table S5. All-policy per-gas drift errors at 20 labels/gas',['Partition','Gas','Policy','MAE ppm','NMAE %'],rows)
    ref=read('sensor_drift/normalization_reference_ranges.csv')
    plain_table(d,'Table S5a. Historical reporting ranges from partitions 1–6 (ppm)',['Gas','Minimum','Maximum','Range'],[[a.gas,n(a.minimum),n(a.maximum),n(a['range'])] for _,a in ref.iterrows()])
    mac=pd.read_csv(E/'drift_macro_summary.csv')
    primary=mac[((mac.budget<20)&(mac['transform']=='log_fixed_huber'))|((mac.budget==20)&(mac['transform']=='log_huber'))]
    rows=[[int(a.fold),int(a.budget),LABEL[a.policy],ms(a),n(100*a.nmae_mean)+' ± '+n(100*a.nmae_sd)] for _,a in primary.iterrows()]
    plain_table(d,'Table S6. Small-budget drift macro errors, mean ± SD',['Partition','Labels/gas','Policy','Macro-MAE ppm','Macro-NMAE %'],rows)
    d.add_paragraph('Below 20 labels/gas the predefined target is fixed-log Huber; at 20 it is historical fitted-log Huber. Therefore this primary budget series also changes scaling at 20. The fixed-log 20-label rows in Table S7 provide a like-for-like scaling control. One-label runs have no validation holdout.')
    loss=mac[mac.budget==20]
    plain_table(d,'Table S7. All-policy 20-label loss/scaling controls',['Partition','Transform','Policy','Macro-MAE ppm','Macro-NMAE %'],[[int(a.fold),a['transform'],LABEL[a.policy],ms(a),n(100*a.nmae_mean)+' ± '+n(100*a.nmae_sd)] for _,a in loss.iterrows()])
    sizes=read('statistics/model_size.csv');sizes=sizes[sizes.seed==42]
    raw=sizes[(sizes.dataset!='sensor_drift')&(sizes.fold==0)&(sizes.design=='farthest')&(sizes.window=='early')&sizes.policy.isin(POLICIES+['generic_ssl'])]
    raw=raw[(raw.budget==5)|(raw.budget==raw.groupby('dataset').budget.transform('max'))]
    drift=sizes[(sizes.dataset=='sensor_drift')&(sizes.budget.isin([1,20]))&sizes['transform'].isin(['log_huber','log_fixed_huber'])]
    rows=[]
    for _,a in pd.concat([raw,drift]).iterrows():rows.append([a.dataset,int(a.budget),LABEL[a.policy],int(a.total),int(a.trainable),int(a.encoder),int(a['head']),int(a.fitting_exposures)])
    plain_table(d,'Table S8. Capacity and distinct fitting records; seed 42',['Dataset','Budget','Policy','Total','Trainable','Encoder','Head','Records'],rows)
    d.add_paragraph('Architecture counts are constant for each dataset/policy. Fitting exposure counts can vary with selected repeated coordinates; complete per-seed counts are saved in statistics/model_size.csv. Parameter/exposure ratios are descriptive and do not alone quantify generalization.')
    d.add_heading('NH3/H2 dataset and acquisition details',1)
    d.add_heading('Sensor array',2)
    d.add_paragraph('The authors use an array of 20 MEMS metal-oxide gas-sensor channels based on SnO2 nanowires with Pt/Ag surface modification. The sensors operate using a thermal-gradient sensing principle and provide complementary responses to NH3 and H2. The chamber accommodates the array in a 5 x 4 arrangement. The authors monitor the channels in four groups: CH1-CH5, CH6-CH10, CH11-CH15 and CH16-CH20, with electrical supply settings in the range 3.0-3.4 V.')
    d.add_heading('Gas chamber and delivery system',2)
    d.add_paragraph('The authors deliver NH3 and H2 to the sensor chamber through an automated mass-flow-controlled mixing system. The apparatus comprises gas supplies, background-gas delivery, mass-flow controllers, a switching valve, the sensor chamber, a power supply and a computer for control and recording. The switching valve directs the prepared mixture to the chamber during exposure. The outlet is connected to an exhaust line, and a cleaning-gas flow supports recovery between exposures. Figure S2 shows the system layout; Fig. S3 shows the sensor hardware, chamber assembly and mass-flow-controller installation.')
    d.add_heading('Acquisition protocol',2)
    d.add_paragraph('The authors program a sequence of single-gas and binary NH3/H2 conditions spanning 0-500 ppm for each gas. Nonzero concentration settings are 25, 50, 100, 200, 300, 400 and 500 ppm. For each condition, the authors expose the array to the prepared gas mixture for 180 s, then apply a 700-s recovery period, giving an 880-s measurement cycle. The authors record the multichannel responses throughout exposure and recovery, using a nominal 2.0-s sampling setting in the acquisition interface. The response increases during gas delivery and returns toward its baseline during recovery. The authors repeat the acquisition protocol on six separate measurement days. The computer interface controls the programmed sequence and records the response channels for subsequent concentration-regression analysis.')
    from zipfile import ZipFile
    from io import BytesIO
    from PIL import Image
    with ZipFile(next(OUT.glob('*NH3_H2.docx'))) as source_images:
        def acquisition_image(name, size):
            im=Image.open(BytesIO(source_images.read('word/media/'+name)))
            im.thumbnail(size)
            buf=BytesIO();im.convert('RGB').save(buf,format='PNG');buf.seek(0)
            return buf
        d.add_picture(acquisition_image('image2.png',(2200,1500)),width=Inches(5.7))
        d.add_paragraph('Fig. S2. Layout of their NH3/H2 mixing and measurement system, including gas supplies, mass-flow control, sensor array, power supply, exhaust and computer interface.')
        t=d.add_table(rows=1,cols=3);t.autofit=False
        for cell,name,label in zip(t.rows[0].cells,['image3.jpeg','image4.jpeg','image5.jpeg'],['(a) MEMS sensor hardware','(b) Sensor chamber','(c) Mass-flow controllers']):
            cell.width=Inches(2)
            cell.paragraphs[0].add_run().add_picture(acquisition_image(name,(800,1067)),width=Inches(1.8))
            cell.add_paragraph(label)
        d.add_paragraph('Fig. S3. Photographs of their experimental hardware: (a) sensor devices, (b) the chamber assembly containing the sensor array, and (c) the mass-flow-controller installation.')
    d.save(OUT/'SUPPLEMENTARY_EVIDENCE.docx')

def reviewer_response(primary,mac):
    d=simple_doc('Point-by-Point Response to Reviewers')
    lines=['# Point-by-point response to reviewers','']
    intro='The authors have completed the revised ten-seed experiment matrix, predefined fine-tuning as the primary policy, promoted multi-fold validation and added the requested controls. In the supplementary information, the authors describe their NH3/H2 sensor array, gas chamber and acquisition protocol, with a system schematic and photographs of the experimental hardware. Yellow highlighting identifies revised or inserted manuscript content, not Word tracked changes. The manuscript is condensed to ten pages by removing repeated background and discussion. All four figures, ten main tables, 30 references and mathematical equations are retained; detailed seed sensitivity and generic-SSL comparisons remain in the supplementary tables.'
    d.add_paragraph(intro);lines += [intro,'']
    text=(ROOT/'revision_artifacts/environment/Comments to the Author.txt').read_text(encoding='utf-8')
    major=text.split('Major\n',1)[1].split('\nModerate',1)[0]
    quotes={int(m.group(1)):re.sub(r'\s+',' ',m.group(2)).strip() for m in re.finditer(r'(\d)\.\s+(.*?)(?=\n\d\.\s|\Z)',major,re.S)}
    summary='; '.join(f'{g}: scratch {n(one(primary,gas=g).scratch_mae,g)} → fine-tuned {n(one(primary,gas=g).transfer_mae,g)} ppm; reduction {n(one(primary,gas=g).relative_improvement_pct,digits=1)}%; paired interval [{n(one(primary,gas=g).ci_low,g)}, {n(one(primary,gas=g).ci_high,g)}] ppm' for g in GASES)
    per=read('sensor_drift/paired_statistics.csv');p10=one(per,budget=20,transform='log_huber',partition=10,gas='MacroMAE',policy='fine_tuned')
    drift10=f'Partition-10 scratch minus fine-tuned macro-MAE is {n(p10.improvement)} ppm, with paired seed interval [{n(p10.ci_low)}, {n(p10.ci_high)}] ppm.'
    generic=read('ssl_baselines/proposed_vs_generic_ssl.csv')
    gen='; '.join(f'{g}: generic minus proposed {n(one(generic,gas=g,budget=57 if g in ["NH3","H2"] else 24).improvement,g)} ppm [{n(one(generic,gas=g,budget=57 if g in ["NH3","H2"] else 24).ci_low,g)}, {n(one(generic,gas=g,budget=57 if g in ["NH3","H2"] else 24).ci_high,g)}]' for g in GASES)
    seed=pd.read_csv(E/'seed_stability/first3_vs_all10.csv')
    seedline='; '.join(f'{g}: {n(one(seed,family="primary_multifold",gas=g).first3_gain_pct,digits=1)}% → {n(one(seed,family="primary_multifold",gas=g).all10_gain_pct,digits=1)}%' for g in GASES)
    seedline+='; however, secondary full-budget fixed-split gains attenuate from 32.4% to 19.6% (NH3), 27.2% to 23.3% (H2), 27.2% to 25.4% (CO), and 31.1% to 24.3% (ethylene)'
    def add(title,quote,response,location,status='Addressed'):
        d.add_heading(title,1);d.add_paragraph(quote,style='Quote');d.add_paragraph('Response: '+response);d.add_paragraph('Location: '+location);d.add_paragraph('Status: '+status)
        lines.extend([f'## {title}','',f'> {quote}','','**Response:** '+response,'','**Location:** '+location,'','**Status:** '+status,''])
    answers={
      1:('The authors clarify that the research motivation is the expense of precise concentration control and labeling: mixtures without carefully controlled ppm can provide inexpensive unlabeled response recordings. The intended workflow pretrains on such recordings and reserves precise labels for a small calibration set. The revised Abstract, Introduction, problem formulation and Discussion preserve this motivation while identifying the present controlled-dataset experiments as a retrospective label-withholding test. They support label efficiency, but do not measure cost savings or demonstrate prospective learning from a cheaply acquired unquantified pool. The authors also distinguish the known-coordinate calibration-design control from label-free pretraining and from a total acquisition-cost budget.','Abstract; Sections I, III.A, VI'),
      2:('Fine-tuning is predefined for every target. Scratch, frozen and fine-tuned models share a group-disjoint adaptation holdout; only adaptation validation selects checkpoints. The authors removed the test-selected summary and recomputed the primary abstract: '+summary+'.','Abstract; Sections III.F, IV, V.B; Table I'),
      3:('All principal configurations now contain the ten seeds 42, 142, …, 942, including seed-specific pretraining. Budget, baseline, ablation, window and drift tables report SD, and paired comparisons report seed/fold bootstrap intervals. The 1,680 completed jobs retain predictions and identities. Seed accumulation does not show uniform erosion: first three → all ten primary reductions are '+seedline+'. Nonmonotonic budget behavior is retained.','Sections IV, V.B–H; Tables I–X; Supplementary Table S2 and Fig. S1'),
      4:('The primary quantitative result now leads with six NH3/H2 held-partition folds and three chronological CO/ethylene rolling folds. The authors replaced the historical results and its repeated-prediction bootstrap with equally weighted crossed seed-and-fold resampling. '+summary+'. Intervals are conditional on observed exposures, and overlapping training partitions limit population inference.','Abstract; Section V.B; Table I; Supplementary Table S1'),
      5:('The authors added a per-gas constant fitted only to the adaptation fitting subset, with matched subsets across policies, all ten seeds, per-gas normalized errors and paired partition-specific intervals. '+drift10+' The interpretation follows this revised interval; the former small-gain claim is removed. The new protocol should not be conflated with the old unmatched-holdout three-repeat estimate.','Section V.G; Tables VII–IX; Supplementary Tables S5–S7'),
      6:('The authors added a compact PatchTST-style masked, shared channel-independent Transformer without physical sensor-ID embeddings, evaluated at every fixed-split budget. Its departures from the forecasting configuration and differing capacity are stated. PLSR and RBF SVR use adaptation-only tuning; trees use flattened scaled windows (1,280/1,024 features). Full-budget paired generic comparisons are '+gen+'. These mixed results explicitly limit the superiority claim.','Sections II, IV, V.E; Table IV; Supplementary Tables S4, S4a, S8'),
      7:('Equation (16) is now described as coverage-based calibration-pair design using known concentrations. Random and farthest-point designs are crossed with scratch and fine-tuning at every budget and all ten seeds. Table III shows the five-pair experiment; Supplementary Table S3 reports every paired design contrast and interval. No claim of generic label acquisition remains.','Section III.F; Section V.D; Table III; Supplementary Table S3'),
      8:('The authors explicitly state that learned channel identities depend on array layout. The evidence concerns same-system recalibration. A valid cross-device test needs compatible arrays and documented correspondence; no such matched acquisition is established here, so no cross-device performance is claimed.','Sections III.C and VI','Addressed by scope limitation; optional cross-device experiment not performed'),
      9:('The authors provide additional details of their NH3/H2 apparatus and acquisition protocol in Supplementary "NH3/H2 dataset and acquisition details". The authors describe the 20-channel MEMS SnO2 array with Pt/Ag modification, electrical supply settings, mass-flow-controlled gas delivery, switching valve, chamber and exhaust. Each programmed condition uses 180 s of exposure followed by 700 s of recovery, with a nominal 2.0-s sampling setting. Figure S2 presents the system schematic and Fig. S3 shows the sensor devices, chamber and mass-flow-controller installation. The existing window-sensitivity analysis remains in Section V.F and Table VI. These additional apparatus and protocol details are supplied in the supplement; the main paper is unchanged.', 'Supplementary "NH3/H2 dataset and acquisition details", Figs. S2-S3; existing Section V.F and Table VI', 'Partly addressed: sensor/chamber descriptions, acquisition protocol and hardware images supplied; complete environmental and calibration characterization is not provided'),
    }
    assert len(quotes)==9,quotes
    for i in range(1,10):
        a=answers[i];add(f'Major comment {i}',quotes[i],a[0],a[1],a[2] if len(a)>2 else 'Addressed')
    moderate=[
        ('CO accuracy','CO performance is weak and should be acknowledged as such.','The authors explicitly report the remaining CO quantitative limitation and include scratch, frozen and fine-tuned R², RMSE and Q0.9. The table retains absolute errors, not just relative gains.','Section V.H; Table X'),
        ('Conformal assumption','The conformal coverage failure needs either a shift-aware variant or an explicit statement of the violated assumption.','The authors state that chronological/session shift violates the exchangeability assumption needed for standard split-conformal coverage guarantees. Earlier coverage percentages are not presented as new ten-seed evidence. The authors take the reviewer’s permitted explicit-limitation route; the authors do not claim to have implemented a shift-aware method.','Section V.H; references [24], [25]'),
        ('Ablation uncertainty','Table IV needs error bars.','The new Table V reports mean ± SD of within-seed ablation-minus-full-model MAE over ten repeats. All raw variant results remain available, including adverse effects and low-budget runs.','Section V.F; Table V; evidence/ablation_paired_differences.csv'),
        ('Sensor-ID variability', 'The spread in the sensor identity effect between H2 and NH3 needs explanation or attribution to noise.', 'Sensor-ID effects are gas-dependent and may reflect sampling/optimization variation as well as selectivity. The authors\' array uses SnO2 with Pt/Ag modification, but array-level material information does not establish a chemistry-based causal explanation for the ablation differences. The authors therefore retain a cautious interpretation.', 'Sections V.F and VI'),
        ('Normalized drift errors','MacroMAE in ppm is dominated by high-concentration analytes; report per-gas normalized error.','The authors report all six per-gas MAEs/NMAEs and macro-NMAE. The denominator is each gas’s historical partitions-1–6 range, used only for reporting, because some test-partition ranges are zero. Each gas receives equal weight; the original test-range diagnostic is preserved separately.','Section IV; Table VIII; Supplementary Table S5 and S5a'),
        ('Drift target and scaling','The log-target Huber optimum is biased for linear-space MAE and per-gas scaling is estimated from only 16 records.','The authors explicitly distinguish the objectives and run historical fitted-log Huber, fixed-log Huber, linear Huber and linear MAE at 20 labels/gas for all neural policies. Smaller budgets use a fixed log scale; one label/gas uses the final checkpoint without a validation split. The authors do not choose the primary transform using test performance.','Section IV; Table IX; Supplementary Tables S6–S7'),
        ('Model size','Please report parameter counts against effective sample size.','The main text reports total/encoder/head/trainable counts and parameter-to-distinct-fitting-exposure ratios. The supplement gives low/full budgets and drift. Five windows from one exposure are not counted as five independent exposures.','Section V.H; Supplementary Table S8'),
        ('Repeated exposures', 'Clarify whether repeated exposures appear in the test partition.', 'The authors repeat the acquisition protocol on separate measurement days and retain exposure identifiers when constructing the evaluation splits. Repeated concentration settings are distinct from duplicated response records. The digital audit checks identifier separation and stored-signal fingerprints; these checks alone do not establish physical independence of the exposures. CO/ethylene checks remain limited to cached windows.', 'Supplementary "NH3/H2 dataset and acquisition details"; evidence/leakage_audit', 'Acquisition protocol described; digital separation verified; physical independence not inferred from identifiers alone'),
        ('Scratch tail error','Add scratch Q0.9 values.','Table X reports scratch, frozen and fine-tuned Q0.9 alongside RMSE and R². Job-level raw-response and drift tail errors remain in the evidence CSVs.','Section V.H; Table X'),
        ('Competing method','Either reimplement one competing method or evaluate on a published split.','The authors implement the compact PatchTST-style matched SSL control and state the deviations from the official forecasting model, including token width, input patches, head and omitted instance normalization. This is not a reproduction of published forecasting scores, and the gas-regression partitions are not claimed to be an official PatchTST benchmark.','Section IV; Section V.E; Supplementary Table S4'),
        ('References','Seventeen references is thin.','Thirteen references on masked/contrastive time-series learning, chemometrics, experimental design, tree models, nonexchangeable uncertainty, sensor-array design, the NH3/H2 dataset, and related image-based mixed-gas estimation extend the bibliography to 30. Each is cited in context; citations do not substitute for the new direct baseline experiment.','Sections II and IV; References [18]–[30]'),
    ]
    for i,a in enumerate(moderate,1):add(f'Moderate comment {i}: {a[0]}',a[1],a[2],a[3],a[4] if len(a)>4 else 'Addressed')
    presentation=[
       ('Sign error','Section V.B states “increase MAE significantly” where “decrease” is meant.','The authors replaced this sentence with result-grounded paired comparisons. Positive scratch-minus-transfer differences are explicitly defined as reduced MAE.','Section V.B; Table I'),
       ('Typos','Correct “overal”, “trainning”, “comparision”, and “Multif-fold”.','The revised text corrects these terms, and a document-wide text check rejects the obsolete tokens.','Throughout'),
       ('Keywords','The Keywords field contains only “SYST”.','The supplied editable DOCX already contained substantive Index Terms. The authors retain valid electronic-nose, self-supervised-learning and calibration keywords and verify no SYST placeholder remains.','Front matter'),
       ('Duplicate tables','Tables I and II largely duplicate each other.','The test-selected floating summary and duplicated full-budget-only table are removed. New Table I is the primary multi-fold comparison; Table II is the single all-policy budget table.','Tables I–II'),
       ('Figure 3','Fig. 3 labels are unreadable at print size.','Figure 3 uses a contrasting orange mean-plus/minus-one-SD band with outlined bounds, a thinner blue mean line and a larger explicit legend. Figure 4 uses larger opaque legend symbols and bold labels for Scratch, Frozen and Fine-tuned, with distinct gray circles, blue squares and orange triangles. Numerical values and uncertainty bounds are unchanged; vector PDF/SVG and high-resolution PNG versions are supplied.','Fig. 3; figures/fig3_pretraining.pdf'),
       ('Figure 2','Fig. 2 is clear and should be kept.','The supplied Fig. 2 image is retained unchanged. Its caption now identifies the secondary fixed splits; the newly primary cyclic/rolling folds are specified in the protocol text.','Fig. 2; Section IV'),
    ]
    for i,a in enumerate(presentation,1):add(f'Presentation comment {i}: {a[0]}',a[1],a[2],a[3])
    d.add_heading('Numerical results cited above',1)
    for entry in claims:plain_table(d,entry['title'],entry['headers'],entry['rows'])
    d.save(OUT/'RESPONSE_TO_REVIEWERS.docx')
    (OUT/'RESPONSE_TO_REVIEWERS.md').write_text('\n'.join(lines),encoding='utf-8')

def apply_page_limit_edits(d):
    replacements={'lectronic nose systems infer gas properties from the combined response of partially selective sensors. For concentration estimation, they are normally calibrated through controlled exposures with known compositions. Obtaining precise concentration labels through controlled delivery or reference measurement becomes costly as the number of gases, mixtures, and measurement sessions grows. Moreover, aging sensors may require the calibration process to be repeated.': 'lectronic noses estimate gas properties from partially selective sensor arrays. Precise concentration labels require controlled delivery or reference measurement, making calibration costly across gases, mixtures and sessions. Sensor aging can require repeated calibration.', 'The practical motivation is the cost difference between producing gas mixtures and establishing their precise gas-phase concentrations at the sensors. Mixtures prepared without carefully controlling ppm can supply inexpensive response recordings for self-supervised learning; only a small calibration set needs precise concentration labels. Source identities or preparation settings, when available, do not substitute for measured gas-phase ppm. The intended workflow therefore learns temporal response patterns and relationships among sensors from an unquantified mixture pool, then adapts the representation using precisely labeled calibration samples. In this study, existing controlled-exposure datasets with labels withheld during pretraining provide a retrospective test of that label-efficiency premise. They do not directly test a newly acquired low-cost mixture pool.': 'The authors seek to learn from inexpensive mixture-response recordings and reserve precise concentration measurements for a small calibration set. Preparation settings do not substitute for measured gas-phase ppm. Controlled-exposure datasets with labels withheld during pretraining test this premise retrospectively; they do not establish the cost or performance of a prospectively acquired unquantified mixture pool.', 'Several earlier studies have already made use of limited or unlabeled electronic nose data. M-Training [1] and M-S4VMs [2], for example, use pseudo-labeling for gas recognition. Drift research has taken other directions, including domain adaptation, few-shot learning, and meta-learning [3]–[7]. Quantitative calibration appears less often in this literature, even though it is important for monitoring applications.': 'Limited-label electronic-nose research includes pseudo-labeling for recognition [1], [2] and domain adaptation, few-shot learning and meta-learning for drift [3]–[7]. Quantitative calibration remains less studied.', 'There is also evidence that temporal responses contain useful concentration information. Reservoir computing has tracked changing concentrations despite slow sensor dynamics [8]. More recently, CNN-LSTM models and lightweight transferred networks have supported both recognition and concentration estimation [9], [10]. Small-data transfer and domain-adaptive regression offer further options when calibration data are limited [11], [12].': 'Temporal modeling [8]–[10], small-data transfer [11] and domain-adaptive regression [12] motivate reusable representations for concentration estimation.', 'In this work, the sensor array is treated as more than an anonymous multivariate series. Each channel belongs to a physical sensor and may have its own response behavior. Accordingly, a shared temporal encoder learns common dynamics, while sensor identities and cross-sensor attention preserve the organization of the array. Pretraining hides time spans and complete channels, which must be recovered from the remaining measurements. The encoder is later frozen or cautiously fine-tuned for concentration regression. The study tests this approach on two raw-response datasets and across several label budgets. It also follows the public sensor drift dataset into future partitions. The authors evaluate multi-fold generalization, calibration-design controls, and oracle-class conditional concentration regression under drift, retaining null and adverse comparisons. The complete pipeline is shown in Fig. 1.': 'The authors\' shared temporal encoder learns response dynamics, while sensor identities and cross-sensor attention retain array structure. Masked intervals and channels are reconstructed before frozen or fine-tuned concentration regression. Two raw-response datasets support label-budget and multi-fold evaluation; a descriptor benchmark tests oracle-class regression under future drift. Generic SSL, chemometric, calibration-design and ablation controls retain adverse and null results. Figure 1 summarizes the pipeline.', 'Quantitative estimation becomes important when an electronic nose is used as a measuring instrument rather than only as a recognizer. Fonollosa et al. [8] used reservoir computing to estimate rapidly changing concentrations from slower sensor responses. Their study drew attention to transient dynamics, which may be lost when a response is reduced to a steady-state value.': 'Fonollosa et al. [8] used reservoir computing to recover rapidly changing concentrations from slow sensor responses, demonstrating transient information beyond steady-state features.', 'Deep models have since combined recognition and regression in several ways. Ni et al. [9] used GAF-MTF representations with a CNN-LSTM model, reporting 95.31% classification accuracy and an R^2 of 0.9510. Tang et al. [10] instead paired a single MEMS sensor with a lightweight transferred network. Work on smaller datasets includes parameter-feature transfer [11], while OT-DARN uses teacher-student domain adaptation with selected pseudo-labels [12].': 'Quantitative models include GAF-MTF/CNN-LSTM feature fusion [9], a lightweight transferred network with a single MEMS sensor [10], small-data parameter-feature transfer [11], and teacher-student domain-adaptive regression [12].', 'M-Training [1] and M-S4VMs [2] bring unlabeled samples into electronic nose recognition through predicted labels. This strategy can be helpful when labels are scarce, although incorrect predictions may be reinforced as training continues.': 'M-Training [1] and M-S4VMs [2] use predicted labels for gas recognition, with potential reinforcement of incorrect pseudo-labels.', 'Self-supervised learning avoids that particular dependence by taking its pretraining target from the measurements themselves. Common time-series objectives include masking, reconstruction, contrastive learning, and adversarial learning [13]. Masked reconstruction is a natural fit for sensor arrays because missing intervals require temporal context. Likewise, missing channels encourage the model to use information shared across sensors. CEGNN [6] takes a different route by combining contrastive learning, graph reasoning, and a small reference set.': 'Self-supervision instead derives targets from measurements. Time-series objectives include reconstruction, masking, contrastive and adversarial learning [13]. Masking intervals and channels encourages temporal and cross-sensor inference without concentration pseudo-labels.', ' In addition to accurately estimating gas concentrations, sensor drift due to aging is also a challenging problem. Sensor drift gradually changes the response distribution, so models trained at one time may not behave in the same way later. TDACNN [3] addresses source-target differences, whereas SAD-CNN [5] combines a one-dimensional CNN with adversarial adaptation and pseudo-labeling. MDCN [4] uses metric learning with a small reference set. Other studies extend the setting through contrastive graph reasoning [6] or model-agnostic meta-learning [7], including tests involving class asymmetry, different devices, and future drift. Most evaluations on the 36-month benchmark emphasize whether gas identity survives the shift, while concentration behavior receives less attention. For this reason, the authors use its future partitions to study oracle-class gas-conditional concentration regression under temporal drift.': 'Drift changes the response distribution. TDACNN [3] and SAD-CNN [5] address domain differences; MDCN [4], CEGNN [6] and meta-learning [7] use limited reference data or transferable representations. Most 36-month-benchmark studies emphasize gas identity. The authors examine concentration regression in future partitions with true identity supplied.', 'The present study connects masked representation learning to quantitative same-system recalibration. Its contribution is an evaluation of a sensor-aware encoder under controlled label budgets, held-out partitions, chronological tests, generic SSL and chemometric controls. The research objective is to reduce dependence on expensive, precisely labeled mixtures by learning from responses that do not require ppm labels. The present benchmarks test label efficiency; actual acquisition-cost savings and performance on unquantified mixtures require prospective evaluation.': 'The authors\' contribution is a controlled evaluation of masked sensor-aware learning for quantitative same-system recalibration, with limited labels, held-out partitions, chronological tests and direct competing controls.', 'Masked time-series representation learning includes channel-independent patch Transformers such as PatchTST [18] and multivariate Transformer reconstruction [19], while TS2Vec learns hierarchical contrastive representations [20]. The authors implement a compact PatchTST-style gas-regression control with explicit deviations from the forecasting model. It tests whether the complete sensor-aware design helps beyond generic masked learning; differing encoders mean it does not isolate sensor identity alone.': 'PatchTST [18] and multivariate Transformers [19] use masked time-series learning; TS2Vec [20] uses hierarchical contrastive representations. The authors\' compact PatchTST-style regression control compares the complete sensor-aware design with generic masking. Different encoders and capacities prevent isolating sensor identity alone.', 'The goal is not simply to train a regressor on all labeled data. Instead, the authors assume that a larger set of mixture responses without precise concentration labels is available before the final calibration stage. The present benchmark emulates this setting by withholding existing pretraining labels; reconstruction uses sensor responses alone and does not require known mixture ratios or ppm. A small precisely labeled adaptation set is written as in (3), and the pretrained encoder and regression head are then adapted under the objective in (4)': 'Pretraining reconstructs responses without concentration labels, emulating an unlabeled mixture pool. The small precisely labeled adaptation set in (3) trains the encoder and regression head under (4).', 'Mean pooling captures the overall response level, while maximum pooling keeps stronger local activation. The shared encoder also limits the number of sensor-specific parameters. Thanks to shared weights, the model can learn common response dynamics from all channels rather than fitting a separate temporal model for each sensor.': 'Shared weights learn common channel dynamics with fewer sensor-specific parameters; mean and maximum pooling retain overall and strong local responses.', 'The identity embedding in (7) is learned jointly with the encoder. It does not contain hand-coded gas knowledge. Instead, it gives the model a stable way to know which physical channel generated a token. This is a useful inductive bias for heterogeneous sensor arrays because channel identity is part of the sensing system itself.': 'The jointly learned embedding in (7) preserves physical channel identity without hand-coded gas selectivity.', 'The sensor-ID mechanism is deliberately simple. It does not assume that one sensor is selective to one gas. It only preserves channel meaning and lets downstream attention learn how each sensor participates in the array response. The embeddings are tied to physical channel correspondence. Current experiments use the same array within each dataset and do not establish cross-device transfer.': 'Sensor identities encode channel correspondence, not one-sensor/one-gas selectivity. Experiments reuse the same array within each dataset and do not establish cross-device transfer.', 'This layer allows one sensor token to be interpreted in the context of the rest of the array. The motivation is physical. A gas mixture is not identified from one sensor in isolation; it is inferred from a pattern of cross-sensitive responses. Attention gives a flexible mechanism for learning this pattern.': 'Cross-sensor attention models the joint pattern of cross-sensitive responses used to infer gas mixtures.', 'The self-supervised task hides physically meaningful parts of the input and asks the model to reconstruct them. For raw time-series data, the authors use two masking modes.': 'Pretraining reconstructs inputs corrupted by temporal-span and complete-channel masks.', 'Three temporal spans are sampled for each example. This masking forces the encoder to infer missing local behavior from the remaining response.': 'Three temporal spans are sampled per example to encourage inference of missing dynamics.', 'Second, one to three full sensor channels are hidden. No temporal value from those sensors remains visible, so reconstruction must draw on the rest of the array. Besides encouraging cross-sensor learning, this setup offers an initial test of how the representation behaves when channel information is absent.': 'The authors also hide one to three complete sensor channels, requiring reconstruction from the remaining array responses.', 'Three adaptation policies are evaluated: scratch, frozen transfer, and fine-tuned transfer. Scratch fits the complete model from random initialization. Frozen transfer trains the supervised head with the pretrained encoder fixed. Fine-tuning updates the pretrained encoder at a lower learning rate than the head. Fine-tuning is predefined as the primary policy for every gas; test MAE never selects between policies. The concentration coordinates in (16) are known only for the labeled calibration-design pool; the unlabeled pretraining pool does not require concentration coordinates. Farthest-point selection is a retrospective coverage control among labeled samples, not a label-free selection rule for cheap mixtures. Its selected-pair budget counts fitting and validation labels, not the cost of quantifying the larger candidate pool.': 'Scratch trains from random initialization; frozen transfer fits only the head; fine-tuning updates the pretrained encoder at a lower learning rate. Fine-tuning is predefined for every gas, without test-based policy selection. Farthest-point design requires known candidate concentrations, unlike label-free pretraining. Its budget includes fitting and validation labels but excludes candidate-pool quantification costs.', 'This study investigates sensor-aware self-supervised learning for label-efficient multigas electronic-nose calibration. A shared temporal encoder, sensor-identity embeddings, cross-sensor attention and structured masked reconstruction support representation reuse with limited concentration labels. Under a predefined fine-tuning policy, primary multi-fold evaluation yields mean MAE reductions of 13.9% for NH3, 21.5% for H2, 27.5% for CO and 25.7% for ethylene relative to training from scratch. These results support self-supervised pretraining for same-system recalibration under the evaluated protocols.': 'Sensor-aware masked pretraining supports label-efficient same-system recalibration. Under predefined fine-tuning, primary multi-fold MAE reductions versus scratch are 13.9% for NH3, 21.5% for H2, 27.5% for CO and 25.7% for ethylene.', 'The benefit of pretraining does not establish that the sensor-aware architecture is uniformly superior. Generic masked self-supervision and classical regressors are competitive or stronger on several targets. Ablations show gas-dependent effects of sensor identity and attention, while window placement materially affects both absolute error and the transfer contrast. Calibration-design effects are also target-dependent, and label-budget trends are not uniformly monotonic. The evidence therefore supports the complete training procedure in specific settings without attributing its gains solely to physical sensor embeddings. Remaining absolute and tail errors, particularly for CO, limit conclusions about practical calibration adequacy.': 'These gains do not establish architectural superiority: generic SSL and classical regressors outperform the proposed model on some targets. Ablation, window, calibration-design and budget effects are target-dependent. Remaining absolute and tail errors, especially for CO, limit practical calibration adequacy.', 'Long-term drift remains a substantial limitation. Oracle-class concentration regression improves over scratch in future partitions 8 and 9, but shows no clear improvement in partition 10. This evaluation assumes that gas identity is known and does not include gas-classification errors. Constant-predictor controls, per-gas normalized errors and target/loss sensitivity show that performance depends on the gas, future partition and optimization objective. Same-system representation reuse alone does not establish robust performance under severe drift; temporal adaptation and shift-aware uncertainty require further investigation.': 'Oracle-class drift regression improves in partitions 8-9 but not clearly in partition 10. The evaluation assumes known gas identity. Constant, normalized-error and loss controls show that representation reuse alone does not establish severe-drift robustness.', 'Ten independently seeded runs characterize variability in initialization, training, calibration design and adaptation holdouts. They do not replace independent acquisition sessions or additional devices. Primary paired intervals are conditional on the observed exposures; the NH3 interval approaches zero, only three chronological CO/ethylene folds are available, and training folds overlap. Secondary fixed-split estimates are sensitive to seed sampling. Dataset-specific acquisition settings and physical exposure independence remain unverified. Learned sensor identities also depend on channel correspondence, so cross-device generalization requires separate evaluation on compatible, characterized arrays.': 'Ten seeds quantify training/design variability, not independent acquisitions. Intervals condition on observed exposures; NH3 is close to zero, chronological folds are few and training folds overlap. Fixed-split estimates are seed-sensitive. Physical exposure independence and cross-device generalization require further evidence; sensor identities depend on channel correspondence.', 'The practical motivation is to learn from inexpensive mixture-response recordings and reserve precise concentration measurements for a small calibration set. Withholding existing labels tests this learning premise retrospectively, but does not demonstrate acquisition-cost savings or equivalent coverage from unquantified mixtures. Farthest-point design additionally requires known candidate concentrations, whose quantification cost is outside the selected-pair budget. A prospective study should combine cheaply prepared unquantified mixtures, a small precisely labeled adaptation set and independent quantified test exposures, with complete cost accounting and acquisition metadata. Within these limits, the present findings support label-efficient same-system recalibration through self-supervised representation reuse, while identifying the conditions that must be tested before broader deployment.': 'Label withholding tests the learning premise retrospectively, not acquisition-cost savings. Known-coordinate calibration design excludes candidate-pool quantification costs. Prospective work should combine inexpensive unquantified mixtures, limited precise adaptation labels and independent quantified tests with cost accounting and acquisition metadata. Temporal adaptation and shift-aware uncertainty are further priorities.', 'The planned ten-seed set does not show systematic erosion as seeds accumulate. Within this revised protocol, first-three to all-ten relative reductions are NH3: 13.3% to 13.9%, H2: 18.4% to 21.5%, CO: 28.5% to 27.5%, Ethylene: 26.1% to 25.7%. The CO/ethylene estimates attenuate slightly, while the NH3/H2 estimates increase. This comparison isolates seed count within the revised protocol; differences from the original manuscript also reflect corrected holdouts and policy reporting. Supplementary Table S2 and Fig. S1 show all prefixes and random-order sensitivity; all ten seeds are retained.': 'Primary improvements do not erode systematically across ten seeds. Supplementary Table S2 and Fig. S1 report seed prefixes and random-order sensitivity; all ten seeds are retained.', 'The secondary full-budget fixed-split gains do attenuate as seeds accumulate: first three → all ten reductions are NH3: 32.4% to 19.6%, H2: 27.2% to 23.3%, CO: 27.2% to 25.4%, Ethylene: 31.1% to 24.3%. The larger attenuation for NH3 shows why a favorable small seed set should not determine the headline. All ten seeds remain included, and the main conclusion rests on multi-fold evidence.': 'Fixed-split gains attenuate with additional seeds, especially NH3 (32.4% for the first three versus 19.6% for all ten). Detailed seed sensitivity is supplementary; primary conclusions use multi-fold evidence.', 'At full budget, generic SSL minus sensor-aware MAE is NH3: -1.23 ppm (95% interval -2.46 to -0.16); H2: 3.58 ppm (95% interval 1.53 to 5.40); CO: 5.08 ppm (95% interval -2.31 to 12.72); Ethylene: -0.189 ppm (95% interval -0.336 to -0.034). The matched control favors the sensor-aware design on H2 and the generic design on NH3 and ethylene; the CO interval includes zero. Lower and medium budgets are also mixed. This limits the general sensor-aware superiority claim, while preserving the separate comparison with scratch. Capacity and encoder differences prevent attributing the entire difference to sensor identity.': 'Paired full-budget generic-SSL comparisons favor the sensor-aware model on H2, favor generic SSL on NH3 and ethylene, and are inconclusive for CO. Lower-budget effects are also mixed (Supplementary Table S4). Encoder and capacity differences preclude attributing these contrasts solely to sensor identity.', 'Figure 3 reports reconstruction loss over ten independently seeded pretraining runs. These curves are optimization diagnostics; lower reconstruction loss across differently scaled datasets is not a concentration-accuracy comparison. All quantitative claims below use held-out concentration predictions.': 'Figure 3 shows ten-seed reconstruction diagnostics. Losses across differently scaled datasets are not concentration-accuracy comparisons; subsequent results use held-out predictions.', 'Table I is the primary generalization analysis. Fine-tuning is compared with scratch using the same adaptation groups and validation holdout in each seed. Positive paired differences favor fine-tuning. All four intervals exclude zero in the revised analysis; NH3 has the lower bound closest to zero. These intervals describe seed/fold variation conditional on the observed exposures, rather than guaranteed improvements on new arrays or acquisition campaigns.': 'Table I compares fine-tuning with scratch under matched adaptation groups and holdouts. All four paired intervals exclude zero, with NH3 closest to zero. Inference is conditional on observed exposures, not new arrays or acquisition campaigns.', 'Positive values in Table V indicate an increase in error after removing the component; negative values indicate that the ablated variant performed better. Paired differences include uncertainty over all ten seeds. Sensor-ID effects differ by gas, but these data cannot distinguish physical selectivity from optimization and sampling variation. Missing sensor characterization prevents a chemistry-based explanation; no component is claimed to be uniformly beneficial.': 'Table V reports within-seed ablation-minus-full-model differences: positive values favor the complete model. Effects vary by gas; sampling and optimization cannot be separated from physical selectivity, and no component is uniformly beneficial.', 'Window placement materially changes both absolute error and the transfer contrast. Late windows are substantially worse for both gases; middle-window H2 does not improve with transfer. Full-exposure resampling is a useful control, but does not establish a unique physical optimum. The original early window remains the primary protocol, and the sensitivity result is not used to optimize that choice on the test set.': 'Window placement changes absolute error and transfer effects (Table VI): late windows are worse for both gases, and middle-window H2 does not improve. Full-exposure resampling is a control, not a test-selected optimum; early windows remain predefined.', 'For partition 10, the revised paired interval includes zero, so there is no clear improvement. This conclusion replaces the original interpretation of a small mean change. Neither a positive conditional interval nor an improved average establishes robust deployment performance under severe drift. The constant and normalized-error controls remain necessary to judge useful calibration accuracy.': 'Partition 10 shows no clear improvement: its paired interval includes zero. Constant and normalized-error controls remain necessary; favorable conditional comparisons do not establish severe-drift deployment robustness.', 'Log-space Huber and linear-space MAE optimize different error geometry, so a log-space optimum need not minimize linear MAE. Table IX explicitly tests target/loss alternatives at the same label budget. Fixed scaling avoids estimating log-space variance from 16 fitting records per gas, but is not presumed uniformly superior. All alternatives remain sensitivity analyses; their test scores do not select a replacement primary transform. Supplementary Table S7 reports every policy and preserves the fitting-derived means and scales.': 'Log-Huber and linear MAE optimize different error geometries. Table IX tests alternatives without choosing the primary transform from test scores. Fixed scaling avoids fitting log variance from 16 records per gas. Supplementary Table S7 retains every policy and fitted scale.', 'Standard split-conformal coverage relies on exchangeability between calibration and test residuals. The chronological/session shift in these experiments violates that assumption, so earlier split-conformal intervals are diagnostic, not guaranteed deployment-shift coverage [24], [25]. The authors do not recycle earlier three-repeat coverage percentages as new ten-seed measurements. A shift-aware uncertainty method requires separate evaluation; it is not claimed as an implemented remedy.': 'Chronological/session shift violates the exchangeability assumption of standard split-conformal coverage [24], [25]. Such intervals are diagnostic under shift, not deployment guarantees. Shift-aware uncertainty remains unevaluated.'}
    for q in d.paragraphs:
        before=q.text
        if before not in replacements:continue
        assert not q._p.xpath('.//m:oMath')
        nodes=[n for run in q.runs for n in run._r.findall(qn('w:t'))]
        assert nodes
        nodes[0].text=replacements[before]
        for n in nodes[1:]:n.text=''
        for run in q.runs:
            if run.text:run.font.highlight_color=WD_COLOR_INDEX.YELLOW
        edit.changes.append({'location':'Main text','kind':'Nine-page compression','before':before,'after':replacements[before]})

def align_author_table_placement(d):
    caption=next(q for q in d.paragraphs if q.text.startswith('Table IV. Full-Budget Baseline'))
    table=caption._p.getnext()
    assert table is not None and table.tag==qn('w:tbl')
    after=next(q for q in d.paragraphs if q.text.startswith('Paired full-budget generic-SSL comparisons'))
    after._p.addnext(caption._p)
    caption._p.addnext(table)

def optimize_paragraph_layout(d):
    # Remove empty body spacers without touching equations, drawings or section breaks.
    for i,q in enumerate(list(d.paragraphs)):
        meaningful=q._p.xpath('.//w:drawing | .//w:pict | .//m:oMath | .//m:oMathPara | .//w:sectPr | .//w:bookmarkStart | .//w:bookmarkEnd | .//w:fldChar | .//w:instrText | .//w:br')
        if i>4 and not q.text.strip() and not meaningful:
            q._p.getparent().remove(q._p);continue
        f=q.paragraph_format;name=q.style.name
        if name in ['Heading 1','Heading 2','Reference Head']:
            f.space_before=Pt(3 if name=='Heading 2' else 6);f.space_after=Pt(1)
            f.keep_with_next=True;f.keep_together=True
        elif q.text.startswith('Fig. '):
            f.space_before=Pt(1);f.space_after=Pt(2);f.keep_with_next=False;f.keep_together=True
            prev=q._p.getprevious()
            if prev is not None and prev.tag==qn('w:p') and prev.xpath('.//w:drawing'):
                pf=Paragraph(prev,d._body).paragraph_format;pf.space_before=Pt(2);pf.space_after=Pt(0);pf.keep_with_next=True
        elif q.text.startswith('Table '):
            f.space_before=Pt(2);f.space_after=Pt(1);f.keep_with_next=True;f.keep_together=True
        elif i>4 and q.text and name in ['Normal','PARA','PARA_Indent','Body Text']:
            f.space_before=Pt(0);f.space_after=Pt(0)
    qs=d.paragraphs
    start=next((i for i,q in enumerate(qs) if q.text.startswith('Dinh-Van Nguyen earned')),len(qs))
    for i in range(start,len(qs)):
        q=qs[i]
        if q.text.startswith('Original study repository:'):break
        nxt=qs[i+1] if i+1<len(qs) else None
        q.paragraph_format.keep_together=True
        q.paragraph_format.keep_with_next=nxt is not None and not nxt._p.xpath('.//w:drawing') and not nxt.text.startswith('Original study repository:')

def finalize(d,p,styles):
    refs=Insert(d,p[163]._p,styles)
    for i,reference in enumerate(FULL_ADDITIONS,18):refs.p(f'[{i}] {reference}')
    # Every newly added reference is cited in the retained related-work expansion.
    for q in d.paragraphs:
        q.paragraph_format.widow_control=True
        if 'Electronic nose' in q.text and not q._p.xpath('.//m:oMath'):
            edit.replace(q,q.text.replace('Electronic nose','electronic nose'),'Capitalization')
    seen=set()
    for section in d.sections:
        for story in [section.header,section.first_page_header,section.even_page_header,section.footer,section.first_page_footer,section.even_page_footer]:
            # Do not create undefined stories; preserve the supplied section
            # relationships, logos, fields and first/even-page settings.
            if not story._has_definition:continue
            if str(story.part.partname) in seen:continue
            seen.add(str(story.part.partname))
            for q in story.paragraphs:
                if 'VOL.' in q.text and 'XX' in q.text:
                    edit.replace(q,'IEEE SENSORS JOURNAL — REVISED MANUSCRIPT  |  ','Remove publication header placeholders')
                    r=q.add_run()
                    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)
                elif 'XXXX-XXXX' in q.text:
                    edit.replace(q,'Manuscript under review.','Remove unassigned journal copyright/issue placeholders')
                elif 'publications_standards/publications/rights' in q.text:
                    edit.replace(q,'','Remove leftover template rights footer')
    highlighted=OUT/'IEEE_Full_Revision_Highlighted.docx';clean=OUT/'IEEE_Full_Revision_Clean.docx'
    apply_page_limit_edits(d)
    align_author_table_placement(d)
    optimize_paragraph_layout(d)
    d.save(highlighted)
    for part in d.part.package.parts:
        element=getattr(part,'_element',None)
        if element is not None:
            for node in list(element.iter(qn('w:highlight'))):node.getparent().remove(node)
    d.save(clean)
    a,b=Document(clean),Document(highlighted)
    marked=len(b._element.xpath('.//w:highlight'))
    for node in list(b._element.xpath('.//w:highlight')):node.getparent().remove(node)
    assert etree.tostring(a._element)==etree.tostring(b._element)
    assert not a._element.xpath('.//w:highlight')
    for part in a.part.package.parts:
        element=getattr(part,'_element',None)
        if element is not None:assert not list(element.iter(qn('w:highlight')))
    source=Document(edit.SOURCE)
    def equations(doc):
        return [etree.tostring(m,method='c14n') for m in doc._element.xpath('.//m:oMath') if not any(x.tag in [qn('w:drawing'),qn('w:pict'),qn('w:txbxContent')] for x in m.iterancestors())]
    assert equations(source)==equations(a),'Original equations changed'
    assert [s._sectPr.xml for s in source.sections]==[s._sectPr.xml for s in a.sections]
    alltext='\n'.join(t.text or '' for t in a._element.iter(qn('w:t')))
    assert not re.search(r'\b(best policy|SYST|TODO|overal|trainning|comparision|Multif-fold)\b',alltext,re.I)
    assert 'historical three-repeat numerical' not in alltext
    for old in ['146.95','142.78','16.4%','14.5%']:assert old not in alltext,old
    listed=set(re.findall(r'^\[(\d+)\]', '\n'.join(x.text for x in a.paragraphs),re.M))
    assert listed==set(map(str,range(1,31))),listed
    # Preserve Fig. 2 bitmap exactly and author line verbatim.
    assert a.paragraphs[1].text==source.paragraphs[1].text
    original_fig=source.paragraphs[86]._p.xpath('.//a:blip')[0].get(qn('r:embed'))
    assert source.part.related_parts[original_fig].blob==a.part.related_parts[original_fig].blob
    dump(OUT/'document_validation.json',dict(clean_highlighted_identical_except_highlight=True,clean_highlights=0,highlighted_runs=marked,
        original_equation_objects_preserved=len(equations(a)),original_section_settings_preserved=True,figure2_preserved=True,
        original_sha256=sha256(edit.SOURCE),clean_sha256=sha256(clean),highlighted_sha256=sha256(highlighted),
        private_characterization_complete=False))
    dump(OUT/'change_manifest.json',edit.changes)
    dump(OUT/'table_manifest.json',claims)
    (OUT/'manuscript_text_for_audit.txt').write_text(alltext,encoding='utf-8')
    (OUT/'CHANGE_LOG.md').write_text('# Full revision change log\n\nThe source is the original IEEE V2.2 DOCX. All scientific equations, authors, biographies, Fig. 2 and page/column settings are retained. The abstract, protocol descriptions, Results and Discussion now use complete ten-seed evidence. The cost motivation distinguishes inexpensive unquantified mixtures from expensive precise concentration labels; retrospective label withholding is separated from a prospective low-cost acquisition study. Known-coordinate calibration design is explicitly separated from label-free pretraining and total acquisition cost. Generic SSL, classical, random-design, window, loss/scaling, normalized drift and seed-count analyses are added. Thirteen references are added in context, including the sensor-design chapter [28] and Harvard Dataverse NH3/H2 dataset [29]. The companion dataset description supports 20 Nano MEMS channels; the cited VOC study does not independently verify the NH3/H2 acquisition settings.\n\nYellow identifies revised or inserted text/values; it is not Word tracked changes. Deleted legacy Results, the test-selected floating table, duplicate summary and superseded Discussion are absent from both copies. `change_manifest.json` records deletions and replacements. Dataset-specific hardware/environment settings remain unverified despite the added design reference and documented Nano MEMS technology.\n',encoding='utf-8')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    snapshot();figures()
    primary=read('multifold/paired_bootstrap_summary.csv')
    d,p,styles,w=prepare_original(primary)
    s,primary,mac=results(w)
    finalize(d,p,styles)
    supplement();reviewer_response(primary,mac)
    print(OUT)

if __name__=='__main__':main()
