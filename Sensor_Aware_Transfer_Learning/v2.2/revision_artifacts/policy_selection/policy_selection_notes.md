# Predefined adaptation policy

The primary policy is **fine_tuned**, fixed for NH3, H2, CO, ethylene, and Sensor_Drift before the new results are inspected. Scratch, frozen, and fine-tuned results are always exported separately. Headline comparisons use fine-tuning even when frozen transfer has lower test MAE.

Adaptation-validation groups depend only on the shared seed and calibration design. Policies receive the same fitting and validation exposures. Checkpoints minimize adaptation-validation loss; no test labels enter training or checkpoint selection. Classical hyperparameters minimize adaptation-validation mean MAE after fixed target scaling. Every job stores its split IDs.

The historical PDFs and original-code snapshot are immutable evidence and may contain superseded wording. They are not the revised manuscript or the new analysis source.
