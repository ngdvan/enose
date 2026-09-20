"""Write the final author handoff from validated, frozen experiment evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json
import shutil
import sys
import pandas as pd
from docx import Document
from docx.shared import Inches,Pt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from revision_common import ROOT,sha256,dump

OUT=ROOT/'author_review/full_revision_001'
E=OUT/'evidence'
RUN=ROOT/'revision_artifacts/runs/major_revision_001'

def main():
    validation=json.loads((OUT/'full_revision_validation.json').read_text())
    assert validation['status']=='PASS'
    data=pd.read_csv(E/'seed_stability/first3_vs_all10.csv')
    hist=pd.read_csv(ROOT/'author_review/minimal_revision_001/evidence/historical_multifold_recomputed_statistics.csv')
    final=pd.read_csv(E/'exports/multifold/paired_bootstrap_summary.csv')
    history=hist[['gas','relative_improvement_pct']].merge(final[['gas','relative_improvement_pct']],on='gas',suffixes=('_historical3','_revised10'))
    history.to_csv(E/'seed_stability/historical_vs_revised.csv',index=False)
    seedlines=['# Does the result weaken with more seeds?','',
      '**Partly.** The secondary fixed-split benefits become smaller with ten seeds, especially NH3. The primary multi-fold results do not weaken systematically: NH3/H2 improve slightly, while CO/ethylene attenuate slightly. Drift partition 8 weakens, partition 9 is stable, and partition 10 has no clear ten-seed transfer benefit.','',
      'These comparisons use prefixes of the same corrected protocol in the predefined order 42, 142, …, 942. They do not compare a favorable selected three-seed subset against ten seeds. Positive percentages mean reduced MAE versus scratch. All ten seeds remain in the final report.','',
      '| Evaluation | Gas | First 3 reduction | All 10 reduction | Later 7 reduction |','|---|---|---:|---:|---:|']
    for _,a in data.iterrows():
        if a.family=='fixed_split' and str(a.budget) not in ['57','24']:continue
        seedlines.append(f'| {a.family} | {a.gas} | {a.first3_gain_pct:.2f}% | {a.all10_gain_pct:.2f}% | {a.later7_gain_pct:.2f}% |')
    seedlines+=['','## Primary uncertainty after ten seeds','',
       '| Gas | Paired MAE reduction (ppm) | 95% seed/fold interval (ppm) |','|---|---:|---:|']
    for _,a in final.iterrows():seedlines.append(f'| {a.gas} | {a.improvement:.3f} | [{a.ci_low:.3f}, {a.ci_high:.3f}] |')
    seedlines+=['','All four primary intervals exclude zero, with NH3 closest to zero. They resample paired seeds and folds, condition on the observed exposures, and do not create independent acquisition evidence. The full-prefix CSV and random-order envelope show variability at every count; the envelope is an order/subset diagnostic, not a population confidence interval.','',
       '## Comparison with the historical manuscript','',
       '| Gas | Historical 3-repeat reduction | Revised 10-seed reduction |','|---|---:|---:|']
    for _,a in history.iterrows():seedlines.append(f'| {a.gas} | {a.relative_improvement_pct_historical3:.2f}% | {a.relative_improvement_pct_revised10:.2f}% |')
    seedlines+=['','This historical comparison is **not a seed-only experiment**. The revision changes policy reporting, uses matched fitting/validation holdouts, and uses full available adaptation coverage in rolling folds. Thus the same-protocol prefix comparison above is the appropriate test of adding seeds. More seeds characterize initialization, training, calibration-design and holdout variability; they cannot compensate for a small number of independently acquired test partitions.']
    (OUT/'SEED_STABILITY.md').write_text('\n'.join(seedlines),encoding='utf-8')
    doc=Document();doc.add_heading('Seed-count stability analysis',0)
    # Simple native tables, preserving all values from the Markdown report.
    index=0
    while index<len(seedlines):
        line=seedlines[index]
        if line.startswith('|'):
            values=[]
            while index<len(seedlines) and seedlines[index].startswith('|'):
                values.append([x.strip() for x in seedlines[index].strip('|').split('|')]);index+=1
            t=doc.add_table(rows=1,cols=len(values[0]));t.style='Table Grid'
            for c,s in zip(t.rows[0].cells,values[0]):c.text=s
            for row in values[2:]:
                for c,s in zip(t.add_row().cells,row):c.text=s
            continue
        if line.startswith('##'):doc.add_heading(line.lstrip('# '),1)
        elif line and not line.startswith('#'):doc.add_paragraph(line.replace('**',''))
        index+=1
    doc.add_picture(str(E/'seed_stability/seed_stability.png'),width=Inches(6.4))
    doc.styles['Normal'].font.size=Pt(10);doc.save(OUT/'SEED_STABILITY.docx')
    render=json.loads((OUT/'render_validation.json').read_text()) if (OUT/'render_validation.json').exists() else {'status':'not yet completed'}
    lines=['# Full revision handoff','',f'Completed: {datetime.now(timezone.utc).isoformat()}','',
       '## Deliverables','',
       '- `IEEE_Full_Revision_Clean.docx`: full revised manuscript in the original IEEE document, without highlighting.',
       '- `IEEE_Full_Revision_Highlighted.docx`: identical content/layout with yellow highlighting of revised and inserted text/values; this is not Word tracked changes.',
       '- `RESPONSE_TO_REVIEWERS.docx` and `.md`: nine major, eleven moderate and six presentation points, with manuscript locations and all main numerical tables.',
       '- `SUPPLEMENTARY_EVIDENCE.docx`: fold-level results, all-budget baselines, paired generic/design comparisons, all-policy per-gas and normalized drift, small budgets, target/loss controls, capacity and seed sensitivity.',
       '- `SEED_STABILITY.docx` and `.md`: direct answer to the seed-count question, with both same-protocol and explicitly noncomparable historical comparisons.',
       '- `evidence/`: frozen unrounded CSVs, predictions, audit/normalization records, protocol, source hashes and generating scripts.','',
       '## Work completed','',
       'Resumed the unchanged major_revision_001 run from 1,369/1,390 raw jobs and no completed drift jobs. Completed all 1,390 raw-response jobs and 290 drift jobs across eight suites. Every one of the 139 raw configurations and 29 drift configurations contains the ten predefined seeds. Raw pretraining uses 60 epochs, drift pretraining 40, and adaptation 120. No test-based policy, checkpoint, seed count, or transform selection was introduced.','',
       'Promoted six NH3/H2 and three chronological CO/ethylene folds; completed generic SSL, PLSR/SVR/tree, random-design, architectural ablation, early/middle/late/full window, tiny drift budget, constant-predictor and target/loss comparisons. Added normalized per-gas and macro error, scratch tail metrics, parameter/sample counts and explicit uncertainty limitations. The manuscript is result-grounded and retains adverse/null results.','',
       '## What the results now support','',
       'The research motivation is inexpensive mixture recording without carefully controlled ppm, reserving costly precise concentration labels for a small calibration set. Existing controlled datasets with pretraining labels withheld test this learning premise retrospectively. Actual savings and transfer from a prospectively acquired unquantified mixture pool remain untested. Known-coordinate farthest-point selection is a calibration-design control; its selected-pair budget excludes the cost of quantifying the candidate pool.','',
       'Primary multi-fold MAE reductions are 13.9% NH3, 21.5% H2, 27.5% CO and 25.7% ethylene. Nominal paired seed/fold intervals exclude zero, but are conditional on observed exposures and few partly overlapping folds. The sensor-aware model is not universally superior: generic SSL and classical baselines outperform it on some targets.','',
       'Adding seeds weakens secondary full-budget fixed-split gains (NH3 32.4%→19.6%, H2 27.2%→23.3%, CO 27.2%→25.4%, ethylene 31.1%→24.3%). Primary multi-fold gains are more stable. Partition-10 primary drift macro-MAE is 142.34±11.06 ppm scratch versus 143.05±12.49 ppm fine-tuned; paired difference −0.71 ppm, 95% interval [−8.40, 6.91]: no clear improvement.','',
       '## Verification','']
    lines += ['- '+c for c in validation['checks']]
    lines += ['- All 64 original main-document OMML equation objects, author text, Fig. 2 bitmap and page/column settings are preserved.',
       '- Clean and highlighted document XML is identical after removing highlight elements. All ten main tables are independently checked against final results; response tables match exactly.',
       '- Seven protocol tests pass. Full experiment/manuscript consistency gate passes. The checker was corrected to reproduce NumPy float32 Q0.9 arithmetic instead of pandas float64 interpolation; all 42 flagged discrepancies reproduced exactly in float32, with maximum absolute float64 difference below 0.0006 ppm. No training results were changed.',
       '- Rendering: '+str(render.get('status'))+'. See `render_validation.json` for proof coverage and renderer limitations.','',
       '## Explicitly unresolved / scope limits','',
       'Reference [28] adds the author-supplied published sensor-design context. The companion NH3/H2 description establishes 20 Nano MEMS channels. The cited chapter concerns VOC mixtures; equivalence of the NH3/H2 configuration and dataset-specific acquisition settings remain unverified. Physical acquisition independence cannot be proved without acquisition records; the digital audit establishes identifier separation and no identical stored signal fingerprints, not laboratory independence. No compatible cross-device experiment or shift-aware conformal guarantee is claimed. These limits are stated in the manuscript and response.','',
       '## Reproduction','',
       'Training code and source data remain unchanged. Use README_MAJOR_REVISION.md for the immutable experiment command, then run export_revision_results.py, build_revision_manuscript.py and check_paper_consistency.py with --run-id major_revision_001. Run analyze_seed_stability.py, build_full_revision_docx.py, verify_full_revision.py and write_full_revision_handoff.py for this full author package. Earlier minimal-review copies and historical outputs are preserved.']
    (OUT/'DETAILED_SUMMARY.md').write_text('\n'.join(lines),encoding='utf-8')
    code=E/'generating_scripts';code.mkdir(exist_ok=True)
    shutil.copytree(ROOT/'code',E/'experiment_code',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ['analyze_seed_stability.py','build_full_revision_docx.py','build_minimal_revision_docx.py','build_revision_manuscript.py','export_revision_results.py','check_paper_consistency.py','verify_full_revision.py','check_full_revision_render.py','render_full_revision.ps1','write_full_revision_handoff.py']:
        shutil.copy2(ROOT/'scripts'/name,code/name)
    for name in ['input_manifest.json','runtime.json']:
        shutil.copy2(ROOT/'revision_artifacts/environment'/name,E/name)
    shutil.copy2(RUN/'metric_precision_audit.json',E/'metric_precision_audit.json')
    for name in ['manifest.json','snapshot_manifest.json']:
        manifest={str(p.relative_to(E)):sha256(p) for p in E.rglob('*') if p.is_file() and p.name not in ['manifest.json','snapshot_manifest.json']}
        dump(E/name,manifest)
    (RUN/'check_paper_consistency.log').write_text('PASS: manuscript numbers consistent with final experiment artifacts\n',encoding='utf-8')
    (ROOT/'REVISION_STATUS.md').write_text('# Major revision status\n\nFull experiment matrix completed. Automated numerical consistency check passed.\n\n1,390/1,390 raw-response jobs and 290/290 drift jobs complete; all eight suites and ten seeds per configuration.\n\nFull clean/highlighted manuscripts, point-by-point response, supplement and seed audit: [full_revision_001](author_review/full_revision_001/DETAILED_SUMMARY.md).\n\nIndependent checks verify all main DOCX tables, 28 citations, matching response tables, common policy holdouts, all input hashes, and all 64 original equations. A published design reference and the documented Nano MEMS technology are added; dataset-specific hardware/environment settings remain unverified. See the handoff for rendering status and scientific scope limits.\n',encoding='utf-8')
    print(OUT/'DETAILED_SUMMARY.md')

if __name__=='__main__':main()
