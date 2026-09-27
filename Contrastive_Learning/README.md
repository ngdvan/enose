# Contrastive Learning for Sensor-Aware ENose Transfer

## Scope

This folder evaluates whether contrastive objectives improve the existing
sensor-aware masked-reconstruction encoder. It contains executable code,
pretrained encoders, predictions, complete JSON results, and reports for:

- NH3/H2 with documented session transfer;
- CO/ethylene with chronological acquisition-block transfer.

## Objectives tested

### Reconstruction-only reference

The existing baseline masks temporal spans and complete sensors, then
reconstructs the original signal. Its validated results are read from
`Sensor_Aware_Transfer_Learning`.

### Reconstruction + VICReg

Two concentration-preserving views of each exposure are encoded. VICReg adds:

- invariance between views;
- a variance constraint that prevents representation collapse;
- a covariance penalty that discourages redundant embedding dimensions.

### Reconstruction + NT-Xent

Two augmented views of the same exposure form a positive pair. Other
exposures in the batch act as negatives. Cosine similarity is optimized with
temperature 0.1.

## Concentration-preserving augmentations

Each view uses:

- an existing offset window from the same exposure;
- mild per-sensor gain variation;
- mild baseline drift;
- small Gaussian noise;
- random contiguous temporal masks; and
- complete dropout of one to three sensors.

Sensor order is never permuted, time is never reversed, and signals from
different concentrations are never mixed.

## Architecture

All objectives use the same encoder:

1. shared dilated temporal CNN;
2. learned physical-sensor identity embeddings;
3. two-layer cross-sensor Transformer;
4. exposure projection head used only during contrastive pretraining.

The downstream comparison includes both a frozen encoder and cautious
fine-tuning.

## Evaluation

Every contrastive experiment uses:

- 60 self-supervised epochs;
- 120 supervised adaptation epochs;
- three subset/training seeds: 42, 142, and 242;
- the same labeled-pair budgets and held-out data as the reconstruction-only
  sensor-aware study.

See [EXPERIMENT_REPORT.md](reports/EXPERIMENT_REPORT.md) for the consolidated
analysis and the dataset-specific reports for full tables.

## Main conclusion

Contrastive learning is useful selectively:

- NT-Xent is the best low-label objective for NH3/H2 at 5–10 pairs.
- NT-Xent produces the best full-budget CO result.
- Reconstruction-only pretraining remains best for NH3/H2 at 20–57 pairs and
  for ethylene at every budget.
- VICReg gives a small CO improvement at five labels but does not otherwise
  establish a consistent advantage.

## Structure

```text
Contrastive_Learning/
├── README.md
├── requirements.txt
├── code/
│   └── run_contrastive_transfer.py
├── reports/
│   ├── EXPERIMENT_REPORT.md
│   ├── NH3_H2_RESULTS.md
│   └── CO_ETHYLENE_RESULTS.md
├── results/
│   ├── nh3_h2/{vicreg,ntxent}/
│   └── co_ethylene/{vicreg,ntxent}/
└── models/
```

Each completed result directory contains `results.json`,
`predictions.csv`, and `pretrained_encoder.pt`.

## Reproduction

From the repository root:

```powershell
python "Contrastive_Learning/code/run_contrastive_transfer.py" --dataset nh3_h2 --variant vicreg
python "Contrastive_Learning/code/run_contrastive_transfer.py" --dataset nh3_h2 --variant ntxent
python "Contrastive_Learning/code/run_contrastive_transfer.py" --dataset co_ethylene --variant vicreg
python "Contrastive_Learning/code/run_contrastive_transfer.py" --dataset co_ethylene --variant ntxent
```

