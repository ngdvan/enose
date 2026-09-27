#!/usr/bin/env python3
"""Controlled sensor-order sensitivity tests for the trained AE-LSTM."""
from __future__ import annotations

import json
import sys
import time
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ec_sensor_order"
SEED = 42


def load_converter():
    spec = spec_from_file_location("ec_converter", ROOT / "split-to-5-lstm-co-ethy.py")
    module = module_from_spec(spec); assert spec.loader; spec.loader.exec_module(module)
    return module


def permute_blocks(x: np.ndarray, order: np.ndarray) -> np.ndarray:
    """Reorder the 16 four-column sensor blocks in a 64x64 notebook image."""
    blocks = x.reshape(len(x), 64, 16, 4, 1)
    return blocks[:, :, order, :, :].reshape(len(x), 64, 64, 1)


def random_per_sample(x: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed); out = np.empty_like(x)
    for i in range(len(x)): out[i] = permute_blocks(x[i:i+1], rng.permutation(16))[0]
    return out


def evaluate(encoder, model, x, y_raw, scaler, converter) -> dict:
    z = encoder.predict(x, batch_size=32, verbose=0).reshape(-1, 16, 16)
    pred = scaler.inverse_transform(model.predict(z, batch_size=32, verbose=0))
    return converter.metrics(y_raw, pred)


def retrain(converter, tf, x_train, y_train, x_val, y_val, x_test, y_test, scaler,
            name: str, ae_epochs=30, lstm_epochs=300) -> dict:
    tf.keras.backend.clear_session(); tf.keras.utils.set_random_seed(SEED)
    ae, encoder, model = converter.build_models()[1:]
    started = time.perf_counter()
    ae_hist = ae.fit(x_train, x_train, validation_data=(x_val, x_val), epochs=ae_epochs,
                     batch_size=32, verbose=0)
    train_z = encoder.predict(x_train, batch_size=32, verbose=0).reshape(-1,16,16)
    val_z = encoder.predict(x_val, batch_size=32, verbose=0).reshape(-1,16,16)
    test_z = encoder.predict(x_test, batch_size=32, verbose=0).reshape(-1,16,16)
    stop = tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=50,
                                             restore_best_weights=True)
    hist = model.fit(train_z, y_train, validation_data=(val_z, y_val), epochs=lstm_epochs,
                     batch_size=32, callbacks=[stop], verbose=0)
    pred = scaler.inverse_transform(model.predict(test_z, batch_size=32, verbose=0))
    encoder.save(OUT / f"{name}_encoder.keras"); model.save(OUT / f"{name}_lstm.keras")
    return {"metrics": converter.metrics(y_test, pred), "seconds": time.perf_counter()-started,
            "ae_epochs": len(ae_hist.history["loss"]), "lstm_epochs": len(hist.history["loss"]),
            "final_ae_val_loss": float(ae_hist.history["val_loss"][-1]),
            "best_lstm_val_loss": float(min(hist.history["val_loss"]))}


def main():
    OUT.mkdir(exist_ok=True)
    converter = load_converter()
    local_deps = ROOT / ".deps2"
    if str(local_deps) not in sys.path: sys.path.insert(0, str(local_deps))
    import tensorflow as tf
    tf.keras.utils.set_random_seed(SEED)

    d = dict(np.load(ROOT / "ec_run_improved_full" / "prepared.npz"))
    x, y, splits = d["images"], d["targets"], d["splits"]
    train_mask, test_mask = splits != 4, splits == 4
    x_all, x_test, y_all, y_test = x[train_mask], x[test_mask], y[train_mask], y[test_mask]
    x_train, x_val, y_train_raw, y_val_raw = train_test_split(
        x_all, y_all, test_size=.1, random_state=SEED)
    scaler = MinMaxScaler().fit(y_train_raw)
    y_train, y_val = scaler.transform(y_train_raw), scaler.transform(y_val_raw)

    encoder = tf.keras.models.load_model(ROOT / "ec_run_improved_full" / "encoder.keras")
    model = tf.keras.models.load_model(ROOT / "ec_run_improved_full" / "lstm.keras")
    random_order = np.random.default_rng(SEED).permutation(16)

    # Correlation order is derived only from outer-training raw sequences.
    raw = dict(np.load(ROOT / "ec_improvements" / "raw_sequences.npz"))
    mask = (raw["folds"] != 4) & (raw["offsets"] == 0)
    values = raw["sequences"][mask].reshape(-1,16)
    corr = np.corrcoef(values, rowvar=False)
    distance = np.clip(1 - np.abs(corr), 0, 1); np.fill_diagonal(distance, 0)
    corr_order = leaves_list(linkage(squareform(distance, checks=False), method="average"))

    results = {"seed": SEED, "test_split": 4, "test_samples": int(test_mask.sum()),
               "random_order_zero_based": random_order.tolist(),
               "random_order_sensor_names": [f"Sensor{i+1}" for i in random_order],
               "correlation_order_zero_based": corr_order.tolist(),
               "correlation_order_sensor_names": [f"Sensor{i+1}" for i in corr_order], "tests": {}}
    results["tests"]["existing_original"] = {
        "metrics": evaluate(encoder, model, x_test, y_test, scaler, converter)}
    results["tests"]["existing_fixed_random_order"] = {
        "metrics": evaluate(encoder, model, permute_blocks(x_test, random_order), y_test, scaler, converter)}
    results["tests"]["existing_random_order_per_sample"] = {
        "metrics": evaluate(encoder, model, random_per_sample(x_test, SEED+1), y_test, scaler, converter)}
    results["tests"]["retrained_fixed_random_order"] = retrain(
        converter, tf, permute_blocks(x_train,random_order), y_train,
        permute_blocks(x_val,random_order), y_val, permute_blocks(x_test,random_order), y_test,
        scaler, "fixed_random")
    results["tests"]["retrained_correlation_order"] = retrain(
        converter, tf, permute_blocks(x_train,corr_order), y_train,
        permute_blocks(x_val,corr_order), y_val, permute_blocks(x_test,corr_order), y_test,
        scaler, "correlation")
    (OUT / "sensor_order_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__": main()
