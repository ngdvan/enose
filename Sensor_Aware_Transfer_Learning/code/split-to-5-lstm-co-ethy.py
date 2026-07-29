#!/usr/bin/env python3
"""Local, reproducible conversion of split-to-5-lstm-co-ethy.ipynb.

The script keeps the notebook's main experiment (five group-disjoint splits,
64x64 sensor images, convolutional autoencoder, and LSTM multi-output
regression) while fixing local paths, random seeds, target scaling leakage,
and use of the test set for early stopping.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler


COLUMNS = ["Time (seconds)", "CO conc (ppm)", "Ethylene conc (ppm)"] + [
    f"Sensor{i}" for i in range(1, 17)
]
SENSORS = COLUMNS[3:]
TARGETS = COLUMNS[1:3]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, default=Path(__file__).with_name("ethylene_CO.txt"))
    p.add_argument("--output", type=Path, default=Path(__file__).with_name("ec_run"))
    p.add_argument("--stage", choices=("inspect", "prepare", "full"), default="full")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--test-split", type=int, default=4, choices=range(1, 6))
    p.add_argument("--step-size", type=int, default=20)
    p.add_argument("--augmentations", type=int, default=5)
    p.add_argument("--autoencoder-epochs", type=int, default=30)
    p.add_argument("--lstm-epochs", type=int, default=1000)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--quick", action="store_true", help="Small smoke run (still reads the full data).")
    return p.parse_args()


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    # The source has a one-line header followed by 19 whitespace-separated fields.
    return pd.read_csv(path, sep=r"\s+", skiprows=1, header=None, names=COLUMNS)


def inspect_data(path: Path) -> dict:
    rows = active = missing_rows = 0
    minima = np.full(2, np.inf)
    maxima = np.full(2, -np.inf)
    for chunk in pd.read_csv(
        path, sep=r"\s+", skiprows=1, header=None, names=COLUMNS,
        chunksize=250_000, usecols=range(3)
    ):
        rows += len(chunk)
        missing_rows += int(chunk.isna().any(axis=1).sum())
        gas = chunk[TARGETS].to_numpy()
        active += int(np.any(gas != 0, axis=1).sum())
        minima = np.minimum(minima, np.nanmin(gas, axis=0))
        maxima = np.maximum(maxima, np.nanmax(gas, axis=0))
    return {
        "rows": rows, "columns": 19, "missing_rows": missing_rows,
        "active_gas_rows": active, "zero_gas_rows": rows - active,
        "target_min": dict(zip(TARGETS, minima.tolist())),
        "target_max": dict(zip(TARGETS, maxima.tolist())),
    }


def label_runs(df: pd.DataFrame) -> pd.DataFrame:
    changed = df[TARGETS].ne(df[TARGETS].shift()).any(axis=1)
    out = df.copy()
    out.insert(0, "Label", changed.cumsum().astype(np.int32))
    return out


def preprocess(df: pd.DataFrame, min_rows: int = 6400) -> tuple[pd.DataFrame, dict]:
    initial_rows = len(df)
    df = df.dropna().loc[~df[TARGETS].eq(0).all(axis=1)].reset_index(drop=True)
    active_rows = len(df)
    df = label_runs(df)
    run_sizes = df.groupby("Label", sort=False).size()
    short = run_sizes[run_sizes < min_rows].index.tolist()
    df = df.loc[~df["Label"].isin(short)].drop(columns="Label").reset_index(drop=True)
    df = label_runs(df)
    return df, {
        "raw_rows": initial_rows, "active_rows": active_rows,
        "retained_rows": len(df), "retained_runs": int(df["Label"].nunique()),
        "dropped_short_runs": len(short), "dropped_short_labels": short,
    }


def assign_splits(labels: np.ndarray, seed: int) -> dict[int, int]:
    labels = labels.copy()
    np.random.default_rng(seed).shuffle(labels)
    chunks = np.array_split(labels, 5)
    return {int(label): split for split, chunk in enumerate(chunks, 1) for label in chunk}


def make_images(
    df: pd.DataFrame, split_map: dict[int, int], step_size: int, augmentations: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample 64 seconds at 1 Hz and repeat 16 sensors four times to width 64."""
    images, targets, splits = [], [], []
    for label, group in df.groupby("Label", sort=False):
        values = group[SENSORS].to_numpy(dtype=np.float32)
        # Faithful to the notebook: MinMax scaling is performed per five-way split.
        # Scaling is applied later so all runs assigned to a split share one scaler.
        for start in range(0, augmentations * step_size, step_size):
            sampled = values[start : 6400 + start : 100]
            if sampled.shape != (64, 16):
                continue
            images.append(sampled)
            targets.append(group[TARGETS].iloc[0].to_numpy(dtype=np.float32))
            splits.append(split_map[int(label)])
    x = np.asarray(images, dtype=np.float32)
    split_array = np.asarray(splits, dtype=np.int8)
    for split in range(1, 6):
        mask = split_array == split
        flat = x[mask].reshape(-1, 16)
        x[mask] = MinMaxScaler().fit_transform(flat).reshape((-1, 64, 16))
    x = np.repeat(x, 4, axis=2)[..., None]
    return x, np.asarray(targets, dtype=np.float32), split_array


def save_prepared(output: Path, x: np.ndarray, y: np.ndarray, splits: np.ndarray, summary: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / "prepared.npz", images=x, targets=y, splits=splits)
    (output / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    # One visual artifact makes the image encoding directly inspectable.
    Image.fromarray(np.uint8(np.clip(x[0, ..., 0] * 255, 0, 255))).save(output / "sample.png")


def build_models():
    local_deps = Path(__file__).with_name(".deps2")
    if local_deps.exists() and str(local_deps) not in sys.path:
        sys.path.insert(0, str(local_deps))
    try:
        import tensorflow as tf
        from tensorflow.keras import layers, Model, Sequential
    except ImportError as exc:
        raise RuntimeError("Full training requires TensorFlow (not installed in this environment).") from exc

    inp = layers.Input((64, 64, 1))
    z = inp
    for filters in (32, 64, 128):
        z = layers.Conv2D(filters, 3, activation="relu", padding="same")(z)
        z = layers.MaxPooling2D(2, padding="same")(z)
    z = layers.Flatten()(z)
    encoded = layers.Dense(256, activation="relu", name="latent")(z)
    z = layers.Dense(8 * 8 * 128, activation="relu")(encoded)
    z = layers.Reshape((8, 8, 128))(z)
    for filters in (128, 64, 32):
        z = layers.Conv2DTranspose(filters, 3, activation="relu", padding="same")(z)
        z = layers.UpSampling2D(2)(z)
    decoded = layers.Conv2DTranspose(1, 3, activation="sigmoid", padding="same")(z)
    autoencoder = Model(inp, decoded, name="autoencoder")
    encoder = Model(inp, encoded, name="encoder")
    autoencoder.compile(optimizer="adam", loss="mse")

    regressor = Sequential([
        layers.Input((16, 16)),
        layers.LSTM(128, return_sequences=True), layers.Dropout(0.2),
        layers.LSTM(64), layers.Dropout(0.2),
        layers.Dense(32, activation="relu"), layers.Dense(2),
    ], name="latent_lstm_regressor")
    regressor.compile(optimizer=tf.keras.optimizers.Adam(0.002), loss="mse", metrics=["mae"])
    return tf, autoencoder, encoder, regressor


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    result = {}
    for i, gas in enumerate(("CO", "Ethylene")):
        mae = mean_absolute_error(y_true[:, i], y_pred[:, i])
        mse = mean_squared_error(y_true[:, i], y_pred[:, i])
        rmse = float(np.sqrt(mse))
        result[gas] = {"MAE": float(mae), "MSE": float(mse), "RMSE": rmse,
                       "R2": float(r2_score(y_true[:, i], y_pred[:, i])),
                       "NRMSE_mean_percent": float(100 * rmse / np.mean(y_true[:, i]))}
    return result


def train(args, x, y, splits, summary) -> None:
    tf, autoencoder, encoder, model = build_models()
    train_mask, test_mask = splits != args.test_split, splits == args.test_split
    x_train_all, x_test = x[train_mask], x[test_mask]
    y_train_all, y_test_raw = y[train_mask], y[test_mask]
    x_train, x_val, y_train_raw, y_val_raw = train_test_split(
        x_train_all, y_train_all, test_size=0.1, random_state=args.seed
    )
    target_scaler = MinMaxScaler().fit(y_train_raw)  # never fit on validation/test
    y_train = target_scaler.transform(y_train_raw)
    y_val = target_scaler.transform(y_val_raw)
    ae_epochs = 2 if args.quick else args.autoencoder_epochs
    lstm_epochs = 3 if args.quick else args.lstm_epochs
    autoencoder.fit(x_train, x_train, validation_data=(x_val, x_val), epochs=ae_epochs,
                    batch_size=args.batch_size, verbose=2)
    train_z = encoder.predict(x_train, verbose=0).reshape(-1, 16, 16)
    val_z = encoder.predict(x_val, verbose=0).reshape(-1, 16, 16)
    test_z = encoder.predict(x_test, verbose=0).reshape(-1, 16, 16)
    stop = tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=50,
                                             restore_best_weights=True)
    model.fit(train_z, y_train, validation_data=(val_z, y_val), epochs=lstm_epochs,
              batch_size=args.batch_size, callbacks=[stop], verbose=2)
    prediction = target_scaler.inverse_transform(model.predict(test_z, verbose=0))
    summary["test_split"] = args.test_split
    summary["test_samples"] = int(test_mask.sum())
    summary["metrics"] = metrics(y_test_raw, prediction)
    (args.output / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    model.save(args.output / "lstm.keras")
    encoder.save(args.output / "encoder.keras")


def main() -> int:
    args = parse_args()
    seed_everything(args.seed)
    if args.stage == "inspect":
        result = inspect_data(args.data)
        print(json.dumps(result, indent=2))
        return 0
    if args.stage == "full":
        local_deps = Path(__file__).with_name(".deps2")
        if local_deps.exists() and str(local_deps) not in sys.path:
            sys.path.insert(0, str(local_deps))
        try:
            import tensorflow  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Full training requires TensorFlow; use --stage prepare to validate preprocessing."
            ) from exc
    df = load_data(args.data)
    processed, summary = preprocess(df)
    summary["seed"] = args.seed
    summary["source"] = str(args.data.resolve())
    split_map = assign_splits(processed["Label"].unique(), args.seed)
    x, y, splits = make_images(processed, split_map, args.step_size, args.augmentations)
    summary["image_shape"] = list(x.shape)
    summary["split_samples"] = {str(i): int((splits == i).sum()) for i in range(1, 6)}
    save_prepared(args.output, x, y, splits, summary)
    print(json.dumps(summary, indent=2))
    if args.stage == "full":
        train(args, x, y, splits, summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
