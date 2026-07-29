# Sensor-Aware Transfer Learning for Electronic-Nose Regression

## Purpose

This folder consolidates the current sensor-aware transfer-learning research
for the ENose project. It contains the study design, executable experiments,
latest numerical results, detailed reports, held-out predictions, pretrained
encoders, and preprocessing parameters for:

1. NH3/H2 regression using a 20-sensor device.
2. CO/ethylene regression using a 16-sensor device.

The central question is whether unlabeled measurements from the same physical
sensor system can teach an encoder a reusable signal representation, reducing
the amount of labeled calibration data required for gas-concentration
regression.

## Study hypothesis

Transfer learning should be most useful when:

- source and target recordings use the same sensor identities and acquisition
  hardware;
- unlabeled signals are abundant but concentration labels are expensive;
- the representation learns both temporal response dynamics and interactions
  among sensor channels; and
- evaluation uses a later, untouched measurement session or chronological
  acquisition block.

Earlier cross-domain transfer from CO/ethylene to NH3/H2 did not consistently
help because the gases and sensor configurations differed. These studies
instead use same-device self-supervised pretraining.

## What was implemented

### Sensor-aware encoder

The encoder combines:

1. A shared dilated temporal CNN that converts each 64-sample sensor response
   into a compact token.
2. A learned identity embedding for every physical sensor channel.
3. A two-layer, four-head Transformer that models interactions among sensor
   tokens.
4. A multilayer regression head that predicts both gases jointly.

The temporal CNN shares response-shape knowledge across sensors, while identity
embeddings prevent the model from treating every channel as interchangeable.
Cross-sensor attention captures selectivity patterns that only become
meaningful when several sensors are considered together.

### Unlabeled pretraining

Let an input batch be $X \in \mathbb{R}^{B \times T \times S}$, where
$T=64$ time samples and $S$ is 20 sensors for NH3/H2 or 16 sensors for
CO/ethylene. A binary visibility mask $M$ has the same shape:

$$
M_{b,t,s} =
\begin{cases}
1 & \text{if sample }(b,t,s)\text{ is visible}, \\
0 & \text{if sample }(b,t,s)\text{ is hidden}.
\end{cases}
$$

For every example $b$, three temporal spans are drawn. For span $k$, the width
is $w_k \sim \mathcal{U}\{6,\ldots,16\}$, its valid start position is
$a_k \sim \mathcal{U}\{0,\ldots,64-w_k\}$, and every sensor is independently
selected with probability 0.45. The span mask is therefore

$$
M_{b,t,s}=0
\quad \text{if} \quad
a_k \le t < a_k+w_k
\quad \text{and} \quad
Z_{b,k,s}=1,
\qquad
Z_{b,k,s}\sim\mathrm{Bernoulli}(0.45).
$$

In addition, $c_b \sim \mathcal{U}\{1,2,3\}$ sensor identities are sampled
uniformly without replacement and completely hidden:

$$
M_{b,t,s}=0
\quad \text{for every } t
\quad \text{when } s\in H_b,
\qquad
|H_b|=c_b.
$$

The encoder receives both the corrupted signal and its visibility indicator,
$[X\odot M,\ M]$, so a true zero is distinguishable from a masked value.
With $\widehat X$ denoting the reconstruction, the optimized objective is

$$
\mathcal{L}_{\mathrm{SSL}}
=
\underbrace{
\frac{\sum_{b,t,s}(1-M_{b,t,s})
(\widehat{X}_{b,t,s}-X_{b,t,s})^2}
{\max\left(1,\sum_{b,t,s}(1-M_{b,t,s})\right)}
}_{\text{error on hidden samples}}
+
0.05
\underbrace{
\frac{\sum_{b,t,s}M_{b,t,s}
(\widehat{X}_{b,t,s}-X_{b,t,s})^2}
{\sum_{b,t,s}M_{b,t,s}}
}_{\text{error on visible samples}}.
$$

Temporal masking teaches response-curve dynamics. Complete-sensor masking
forces the encoder to exploit relationships among channels. Gas concentration
labels are not used during this stage. A span has mean width 11 samples, or
17.2% of the 64-sample curve. Ignoring overlap and boundary effects, the
combined temporal and complete-sensor operations hide approximately 29% of
NH3/H2 values and 31% of CO/ethylene values per example.

### Supervised comparisons

Each study compares:

- training the same neural architecture from scratch;
- freezing the pretrained encoder and training only its regression head;
- fine-tuning the pretrained encoder at a lower learning rate;
- a deterministic physics-feature tree baseline; and
- for CO/ethylene, a matched physics + XGBoost baseline.

Calibration pairs are selected through seeded farthest-point sampling in
normalized two-gas concentration space. This provides broad coverage at small
label budgets.

### Data use, augmentation, and splitting

No held-out measurement is used for scaling, pretraining, or model fitting.
Percentages in the split tables refer to independent raw exposures; augmented
windows from one exposure always remain in the same task.

#### NH3/H2

The workbook contains 162,404 rows, 378 exposures, six repeated sessions of 63
exposures each, and 20 sensor channels. Every session contains 57 unique
concentration pairs; six of its 63 exposures repeat an existing pair. Eleven
transition rows had an adjacent exposure's label, so each exposure's modal
`(NH3, H2)` pair was used to correct those labels.

| Task | Sessions | Raw exposures | Share of all exposures | Windows actually used |
|---|---|---:|---:|---:|
| Unlabeled pretraining | 1--4 | 252 | 66.67% | 1,260 |
| Labeled adaptation pool | 5 | 63 | 16.67% | Budget-dependent |
| Untouched testing | 6 | 63 | 16.67% | 63 |

Pretraining creates five overlapping 64-sample windows per exposure at start
offsets 0, 1, 2, 3, and 4: $252\times5=1{,}260$ unlabeled windows.
Adaptation uses the same five-window augmentation, but selects only one
exposure for each chosen unique concentration pair. Testing uses only offset
zero, producing exactly one prediction for each of the 63 independent test
exposures instead of five correlated predictions.

| Labeled-pair budget | Share of 57-pair adaptation set | Raw adaptation exposures | Augmented training windows | Share of all 378 exposures |
|---:|---:|---:|---:|---:|
| 5 | 8.77% | 5 | 25 | 1.32% |
| 10 | 17.54% | 10 | 50 | 2.65% |
| 20 | 35.09% | 20 | 100 | 5.29% |
| 40 | 70.18% | 40 | 200 | 10.58% |
| 57 | 100% | 57 | 285 | 15.08% |

The robust per-sensor scaler is fitted on the 1,260 session-1--4 pretraining
windows only, then reused unchanged for adaptation and testing.

#### CO/ethylene

The prepared dataset contains 245 chronological exposure runs, 16 sensor
channels, and 1,225 sequence windows. Each exposure contributes five
64-sample windows at offsets 0, 20, 40, 60, and 80. Because the source has no
documented session IDs, the exposures are kept in chronological order and
split into five contiguous blocks of 49 exposures.

| Task | Blocks | Raw exposures | Share of all exposures | Windows actually used |
|---|---|---:|---:|---:|
| Unlabeled pretraining | 1--3 | 147 | 60.00% | 735 |
| Labeled adaptation pool | 4 | 49 | 20.00% | Budget-dependent |
| Untouched future testing | 5 | 49 | 20.00% | 49 |

All five windows from each pretraining exposure are used:
$147\times5=735$ unlabeled windows. Block 4 contains 24 unique concentration
pairs among its 49 exposures. As in NH3/H2, one exposure is selected per
chosen pair and expanded to five training windows. Only the offset-zero window
from every block-5 exposure is scored; the other 196 possible augmented test
windows are deliberately excluded.

| Labeled-pair budget | Share of 24-pair adaptation set | Raw adaptation exposures | Augmented training windows | Share of all 245 exposures |
|---:|---:|---:|---:|---:|
| 5 | 20.83% | 5 | 25 | 2.04% |
| 10 | 41.67% | 10 | 50 | 4.08% |
| 20 | 83.33% | 20 | 100 | 8.16% |
| 24 | 100% | 24 | 120 | 9.80% |

The scaler is fitted only on the 735 windows from blocks 1--3. Concentration
labels from those blocks are never supplied to the self-supervised encoder.
The three supervised repeats change the seeded farthest-point ordering and
model initialization; they do not change the chronological split or test set.

## Model configuration

Both studies use the same sensor-aware network; only the number of sensor
tokens and target scaling differ.

| Component | Configuration |
|---|---|
| Input | 64 time samples per sensor, plus an observed/masked indicator |
| Sensor tokens | 20 for NH3/H2; 16 for CO/ethylene |
| Temporal encoder | Shared 1-D CNN: `2 -> 24 -> 32 -> 32` channels, kernel sizes `5, 5, 3`, dilations `1, 2, 4`, GELU activations |
| Token projection | Mean and maximum temporal pooling (`64` features), projected to a 32-dimensional token |
| Sensor identity | One learned 32-dimensional embedding per physical sensor |
| Cross-sensor encoder | 2 Transformer layers, 4 attention heads, 96-dimensional feed-forward layer, 0.1 dropout, pre-layer normalization |
| Reconstruction decoder | `32 -> 96 -> 64` per sensor |
| Regression head | Flattened sensor tokens, then `N_sensors * 32 -> 128 -> 32 -> 2`, GELU, 0.15 dropout |

### Training configuration

| Stage | Epochs | Optimizer and learning rate | Objective |
|---|---:|---|---|
| Masked pretraining | 60 | AdamW, `8e-4`, weight decay `1e-4` | Masked MSE + `0.05 *` visible-sample MSE |
| Scratch regression | 120 | AdamW, `5e-4`, weight decay `2e-4` | Huber loss, delta `0.1` |
| Frozen transfer | 120 | AdamW on the head, `1e-3`, weight decay `2e-4` | Huber loss, delta `0.1` |
| Fine-tuned transfer | 120 | AdamW: encoder `8e-5`, head `8e-4`, weight decay `2e-4` | Huber loss, delta `0.1` |

All neural stages use batches of at most 64 and gradient clipping at norm 2.0.
Pretraining masks three 6--16-sample spans and one to three complete sensors
per example. Supervised results are means over seeds 42, 142, and 242.

## Training and test curves

The saved training curve is the masked-autoencoder pretraining loss. Lower is
better; values below are sampled from the complete 60-epoch histories in the
result JSON files.

| Epoch | NH3/H2 loss | CO/ethylene loss |
|---:|---:|---:|
| 1 | 2.1595 | 1.9505 |
| 10 | 0.1934 | 0.7079 |
| 20 | 0.1414 | 0.3193 |
| 30 | 0.1183 | 0.2528 |
| 40 | 0.1100 | 0.2479 |
| 50 | 0.0839 | 0.2359 |
| 60 | 0.0762 | 0.3020 |

The held-out test curves below show mean MAE versus the number of labeled
adaptation pairs. Each transfer value is the better of the frozen and
fine-tuned policies at that budget.

### NH3/H2 held-out session test curve

| Labeled pairs | NH3 scratch | NH3 transfer | H2 scratch | H2 transfer |
|---:|---:|---:|---:|---:|
| 5 | 52.87 | **46.16** | 143.82 | **96.43** |
| 10 | 43.46 | **38.39** | 103.62 | **70.36** |
| 20 | 31.33 | **26.61** | 53.79 | **40.93** |
| 40 | 29.35 | **22.71** | 46.42 | **38.62** |
| 57 | 18.47 | **14.92** | 36.60 | **29.16** |

### CO/ethylene future-block test curve

| Labeled pairs | CO scratch | CO transfer | Ethylene scratch | Ethylene transfer |
|---:|---:|---:|---:|---:|
| 5 | 179.17 | **93.79** | 3.255 | **2.352** |
| 10 | 115.06 | **59.27** | 3.422 | **2.301** |
| 20 | 72.11 | **46.06** | 1.934 | **1.424** |
| 24 | 65.00 | **46.16** | 1.992 | **1.371** |

All test-curve values are ppm. Complete, unsampled pretraining histories and
per-run test metrics are available in
[`results/nh3_h2/results.json`](results/nh3_h2/results.json) and
[`results/co_ethylene/results.json`](results/co_ethylene/results.json).
Supervised epoch-by-epoch losses were not persisted by the current experiment
scripts, so the reported test curves are label-budget curves rather than
supervised learning curves.

## Comparison with traditional physics-feature models

This is an apples-to-apples comparison: every model uses the same seeded
calibration subsets and the same untouched test session or future block.
The traditional pipeline converts each sensor response into deterministic
temporal/physics descriptors before fitting a tree ensemble. CO/ethylene uses
13 descriptors per sensor with XGBoost (800 trees, maximum depth 3, learning
rate 0.03). NH3/H2 is now evaluated with both the original Extra Trees
baseline and a matched XGBoost baseline using 37 descriptors per sensor and
the same XGBoost configuration.

### NH3/H2: transfer versus physics + Extra Trees and XGBoost

| Pairs | NH3 transfer | NH3 Extra Trees | NH3 XGBoost | H2 transfer | H2 Extra Trees | H2 XGBoost |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | **46.16** | 48.28 | 104.96 | **96.43** | 158.35 | 165.30 |
| 10 | 38.39 | 37.41 | **33.67** | **70.36** | 104.37 | 123.80 |
| 20 | **26.61** | 32.96 | 27.00 | **40.93** | 57.89 | 81.74 |
| 40 | **22.71** | 24.64 | 28.34 | **38.62** | 39.83 | 44.80 |
| 57 | **14.92** | 17.70 | 20.07 | **29.16** | 33.00 | 31.97 |

Transfer wins nine of the ten NH3/H2 target-budget comparisons against both
traditional alternatives. The exception is NH3 at 10 pairs, where XGBoost
achieves 33.67 ppm versus 38.39 ppm for transfer. At 20 NH3 pairs the methods
are nearly tied (26.61 versus 27.00 ppm). Transfer is best for H2 at every
budget, with its largest advantages in the 5--20-pair low-label regime.

### CO/ethylene: transfer versus physics + XGBoost

| Pairs | CO transfer | CO XGBoost | Better method | Ethylene transfer | Ethylene XGBoost | Better method |
|---:|---:|---:|---|---:|---:|---|
| 5 | **93.79** | 126.87 | Transfer (26.1%) | **2.352** | 3.516 | Transfer (33.1%) |
| 10 | **59.27** | 85.21 | Transfer (30.4%) | **2.301** | 2.595 | Transfer (11.3%) |
| 20 | 46.06 | **40.29** | XGBoost (12.5%) | **1.424** | 1.937 | Transfer (26.5%) |
| 24 | **46.16** | 46.44 | Tie (0.6%) | **1.371** | 2.015 | Transfer (32.0%) |

All values are mean held-out MAE in ppm across three repeated calibration
selections. Transfer is more label-efficient at 5--10 pairs and consistently
better for ethylene. For CO, XGBoost becomes competitive once about 20
representative pairs are available: it wins at 20 pairs and is effectively
tied with transfer at the full 24-pair budget.

The matched XGBoost results are preserved in
[`results/nh3_h2/physics_xgboost_comparison.json`](results/nh3_h2/physics_xgboost_comparison.json)
and
[`results/co_ethylene/physics_xgboost_comparison.json`](results/co_ethylene/physics_xgboost_comparison.json).

The older random five-fold CO/ethylene XGBoost result (about 14.60 ppm CO and
0.443 ppm ethylene MAE) is not directly comparable. It trained on roughly 196
labeled exposures per fold and randomly mixed chronological runs, whereas the
matched comparison above uses only 5--24 labeled pairs and an untouched future
block.

## Leakage controls

### NH3/H2

- Sessions 1–4: unlabeled pretraining.
- Session 5: labeled adaptation subsets.
- Session 6: untouched testing.
- Scaling is fit only on pretraining sessions.
- Test exposures contribute one offset-zero window each.

The workbook documents six repeated measurement rounds and contains 63
exposures per session, covering 57 unique concentration pairs.

### CO/ethylene

The source file has no explicit session IDs and no time resets. The 245
chronological exposure runs are divided into five contiguous 49-run blocks:

- Blocks 1–3: unlabeled pretraining.
- Block 4: labeled adaptation.
- Block 5: untouched future-block testing.

This is a chronological transfer experiment, not proof of transfer between
independently documented measurement sessions. This limitation must accompany
reported CO/ethylene results.

## Latest results

### NH3/H2

Using all 57 labeled adaptation pairs:

| Model | NH3 MAE | H2 MAE |
|---|---:|---:|
| Scratch | 18.47 ppm | 36.60 ppm |
| Frozen transfer | 17.57 ppm | 32.61 ppm |
| Fine-tuned transfer | **14.92 ppm** | **29.16 ppm** |
| Physics + Extra Trees | 17.70 ppm | 33.00 ppm |

Fine-tuned transfer reduces MAE relative to scratch by 19.2% for NH3 and 20.3%
for H2. Relative to mean test concentrations, its errors are 9.49% for NH3 and
15.63% for H2.

At 20 labeled pairs, frozen transfer reduces NH3 MAE from 31.33 to 26.61 ppm
and H2 MAE from 53.79 to 40.93 ppm.

### CO/ethylene

Using all 24 unique labeled adaptation pairs:

| Target | Scratch | Best transfer | Physics + XGBoost |
|---|---:|---:|---:|
| CO | 65.00 ppm | **46.16 ppm** frozen | 46.44 ppm |
| Ethylene | 1.99 ppm | **1.37 ppm** fine-tuned | 2.02 ppm |

The best transferred configuration reduces error relative to scratch by 29.0%
for CO and 31.2% for ethylene. CO transfer and physics + XGBoost are effectively
tied at the full budget, while transfer is 32.0% better for ethylene.

At 10 labeled pairs:

| Target | Best transfer | Physics + XGBoost | Transfer advantage |
|---|---:|---:|---:|
| CO | 59.27 ppm | 85.21 ppm | 30.4% |
| Ethylene | 2.301 ppm | 2.595 ppm | 11.3% |

Transfer is therefore particularly useful in the low-label regime.

## Current interpretation

The studies support four conclusions:

1. Same-device unlabeled pretraining is useful. It succeeds where transfer
   across different gas/sensor domains did not.
2. The main value is label efficiency. Gains are especially large with only
   5–20 labeled calibration pairs.
3. Freeze/fine-tune policy depends on label count and target. Freezing is safer
   with scarce labels and is consistently strong for CO; full-budget NH3/H2
   and ethylene benefit from cautious fine-tuning.
4. Physics + XGBoost remains a strong CO baseline once approximately 20
   representative labeled pairs are available. Transfer remains stronger for
   ethylene and low-label calibration.

## Future plan

### 1. Leave-one-session-out NH3/H2 evaluation

Repeat the full protocol six times, holding out each documented session in
turn. Use four sessions for unlabeled pretraining, one for adaptation, and one
for testing. This will produce six independent session-level estimates.

### 2. Recover CO/ethylene acquisition metadata

Identify true experiment days, sensor restarts, chamber cleanings, or device
sessions. Replace the current contiguous blocks with genuine session IDs. If
metadata cannot be recovered, run rolling chronological evaluations across
all feasible train-adapt-test block triplets.

### 3. Tune freezing schedules

Evaluate:

- head-only training;
- unfreezing only the cross-sensor Transformer;
- unfreezing the Transformer and upper temporal layers;
- full fine-tuning;
- discriminative learning rates; and
- regularization toward pretrained weights.

The goal is a stable automatic policy based on the labeled-pair budget.

### 4. Improve self-supervised objectives

Compare masked reconstruction with:

- contrastive windows from the same exposure;
- prediction of later response segments from early segments;
- sensor-dropout consistency;
- denoising under realistic drift and noise; and
- multi-resolution temporal reconstruction.

### 5. Model uncertainty

Add ensembles or conformal calibration to report prediction intervals, not
only point MAE. Evaluate interval coverage by gas, concentration, pure versus
mixed exposure, and measurement session.

### 6. Deployment validation

Test:

- longer input windows and recovery phases;
- inference latency and model size;
- calibration-pair selection under operational constraints;
- transfer to another physical e-nose unit; and
- robustness to missing or degraded sensors.

## Folder organization

```text
Sensor_Aware_Transfer_Learning/
├── README.md
├── requirements.txt
├── code/
│   ├── same_device_session_transfer.py
│   ├── compare_nh3_h2_transfer_physics_xgboost.py
│   ├── co_ethylene_session_transfer.py
│   ├── compare_co_transfer_physics_xgboost.py
│   └── supporting feature/preparation modules
├── reports/
│   ├── LATEST_RESULTS.md
│   ├── NH3_H2_DETAILED_REPORT.md
│   └── CO_ETHYLENE_DETAILED_REPORT.md
├── results/
│   ├── nh3_h2/
│   └── co_ethylene/
└── models/
    ├── nh3_h2/
    └── co_ethylene/
```

## Running the experiments

From the repository root:

```powershell
python "Sensor_Aware_Transfer_Learning/code/same_device_session_transfer.py"
python "Sensor_Aware_Transfer_Learning/code/compare_nh3_h2_transfer_physics_xgboost.py"
python "Sensor_Aware_Transfer_Learning/code/co_ethylene_session_transfer.py"
python "Sensor_Aware_Transfer_Learning/code/compare_co_transfer_physics_xgboost.py"
```

Fresh experiment outputs default to `Sensor_Aware_Transfer_Learning/runs/`.
The validated results used for the reports are preserved under `results/`, and
their pretrained encoders and scalers are preserved under `models/`.

## Reproducibility notes

- Both completed studies use base seed 42 and repeated supervised seeds 42,
  142, and 242.
- Both use 60 self-supervised epochs and 120 supervised epochs.
- The NH3/H2 run took 295.5 seconds.
- The CO/ethylene transfer run took 140.7 seconds.
- Raw source workbooks and the large prepared CO/ethylene cache remain in their
  existing repository locations and are intentionally not duplicated here.
