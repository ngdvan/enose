# Generic masked SSL control

The control is a compact **PatchTST-style reimplementation**, not the official forecasting benchmark configuration. Source: Nie et al., [A Time Series is Worth 64 Words](https://arxiv.org/abs/2211.14730), and the [official repository](https://github.com/yuqinie98/PatchTST).

Each 64-sample channel becomes eight nonoverlapping length-8 patches. A shared linear patch embedding, 32-dimensional tokens, two four-head Transformer layers, 96-unit feed-forward blocks, and learned temporal patch positions process every channel with the same weights. Three of eight patches are masked per channel; the decoder minimizes MSE on masked patches. There are no physical sensor-ID embeddings or cross-channel attention. The supervised head receives concatenated channel representations, as in the proposed model: fixed channel ordering is retained, so the control is not claimed to be a permutation-invariant whole regressor.

Pretraining data, scaler, budgets, seeds, adaptation/test exposures, epoch counts, supervised target scaling, holdout selection, and regression head are matched. Instance normalization is omitted to retain absolute response levels and match preprocessing. Temporal patch features are mean-pooled for the shared regression-head interface. These implementation adaptations and differing parameter counts must be reported; the comparison is not a claim of reproducing published forecasting scores.

Run all fixed-split budgets, exceeding the required low/medium/full comparisons. Paired proposed-versus-generic results are exported from the same seeds and exposures.
