# Baseline input representations and selection

The **new revision comparison** uses flattened pretraining-scaled 64-sample raw windows for PLSR, RBF SVR, Extra Trees, and XGBoost: 1280 features for NH3/H2 and 1024 for CO/ethylene. Each window is flattened in time-major, then sensor order. All offset windows belonging to an exposure remain together in fitting or validation. This changes the historical tree representation and therefore requires rerunning trees, rather than copying old numbers.

PLSR and SVR additionally standardize features on the fitting subset only. Targets use the same predefined gas concentration scales as the neural model. PLSR components are selected from 1, 2, 3, 5, 8, 12 subject to matrix-size constraints. RBF SVR uses a separate model per target and a shared adaptation-validation search over C in {0.1, 1, 10}, gamma in {scale, 0.001}, epsilon in {0.01, 0.1}. Selection minimizes mean normalized validation MAE. No refit consumes the validation subset afterward, matching the neural fitting-label budget.

Extra Trees uses 300 trees, minimum leaf size 2. XGBoost uses 300 estimators, depth 3, learning rate 0.03, row and column subsampling 0.9. These settings are fixed. Effective fitting sample size is the number of exposures, not five times that number.

Historical Extra Trees called `descriptors`, which invokes `physics_features`; the physics-XGBoost comparator also used engineered descriptors. Those old comparisons are preserved only in the environment snapshot. They must not be mixed with the new flattened-window table.
