"""Explore full-scene stress images using the repository's SAR/WHOI readers.

Each SAR scene is paired with the nearest WHOI observation using the existing
notebook convention. Training loss is evaluated only at the SAR pixel nearest
the matched observation's latitude and longitude.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = Path("/lustre/storeB/project/IT/geout/machine-ocean/data_raw/sentinel")
DEFAULT_WHOI_REPO = REPO_ROOT / "notebooks" / "MachineOcean_WP1_WHOI"


def import_repository_readers(whoi_repo: str | None):
    """Import the same SAR and WHOI reader modules used by the notebooks."""
    sys.path.insert(0, str(REPO_ROOT))
    if whoi_repo:
        sys.path.insert(0, str(Path(whoi_repo).expanduser().resolve()))
    elif DEFAULT_WHOI_REPO.exists():
        sys.path.insert(0, str(DEFAULT_WHOI_REPO))

    sar = importlib.import_module("sar")
    try:
        from mo_whoi_data.load_data import load_data_xarray
        from mo_whoi_data.residual_learning_time_hist.predictors import predictors
    except ImportError as exc:
        raise ImportError(
            "Could not import the WHOI reader used by the collocation notebooks. "
            "Pass --whoi-repo pointing to MachineOcean_WP1_WHOI."
        ) from exc
    return sar, load_data_xarray, predictors


def buoy_name_from_transfer_key(key: Any) -> str:
    """Apply the Transfer_<buoy>.mat naming convention used in the notebooks."""
    name = Path(str(key)).stem
    if name.startswith("Transfer_"):
        return name[len("Transfer_"):]
    return name


def load_sar_metadata(data_dir: Path, metadata_path: str | None) -> dict:
    """Read the existing Sentinel product metadata pickle."""
    if metadata_path:
        path = Path(metadata_path).expanduser()
    else:
        candidates = [
            data_dir / "in_situ_obs_with_sar_params_old.pickle",
            data_dir / "in_situ_obs_with_sar_params.pickle",
        ]
        path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    if not path.exists():
        raise FileNotFoundError(f"SAR product metadata pickle not found: {path}")
    with path.open("rb") as handle:
        return pickle.load(handle)


def filter_valid_observations(frame: pd.DataFrame, predictors: list[str]) -> pd.DataFrame:
    """Apply the quality checks used in the SAR collocation notebook."""
    valid = np.ones(len(frame), dtype=bool)

    sbytes_column = next((col for col in ("Sbytes", "SBytes") if col in frame), None)
    if sbytes_column is not None:
        valid &= pd.to_numeric(frame[sbytes_column], errors="coerce").to_numpy() == 0

    available_predictors = [col for col in predictors if col in frame]
    if available_predictors:
        predictor_values = frame[available_predictors].apply(
            pd.to_numeric, errors="coerce"
        ).to_numpy(dtype=np.float64)
        real_values = np.real(predictor_values).astype(np.float64)
        valid &= np.all(np.isfinite(real_values), axis=1)
        valid &= ~np.any(real_values > 1.0e8, axis=1)
        valid &= ~np.any(np.abs(real_values - 9999.0) < 1.0, axis=1)

    for column in ("UW", "UWr"):
        if column in frame:
            values = pd.to_numeric(frame[column], errors="coerce").to_numpy()
            valid &= np.isfinite(values) & (values >= -2.0) & (values <= 0.2)

    if any(column not in frame for column in ("datetime", "UWr", "rhoair", "lat", "lon")):
        return frame.iloc[0:0].copy()

    result = frame.loc[valid].copy()
    result["datetime"] = pd.to_datetime(result["datetime"], utc=True, errors="coerce")
    result["UWr"] = pd.to_numeric(result["UWr"], errors="coerce")
    result["rhoair"] = pd.to_numeric(result["rhoair"], errors="coerce")
    result["lat"] = pd.to_numeric(result["lat"], errors="coerce")
    result["lon"] = pd.to_numeric(result["lon"], errors="coerce")
    result = result.dropna(subset=["datetime", "UWr", "rhoair", "lat", "lon"])
    result = result.sort_values("datetime").drop_duplicates("datetime", keep="first")
    return result.set_index("datetime")


def nearest_observation(frame: pd.DataFrame, acquisition_time: Any, max_delta_minutes: float):
    """Return nearest valid WHOI row if within the allowed acquisition-time gap."""
    acquisition = pd.Timestamp(acquisition_time)
    acquisition = acquisition.tz_localize("UTC") if acquisition.tzinfo is None else acquisition.tz_convert("UTC")
    position = frame.index.get_indexer([acquisition], method="nearest")[0]
    if position < 0:
        return None
    observed_time = frame.index[position]
    delta_minutes = abs((observed_time - acquisition).total_seconds()) / 60.0
    if delta_minutes > max_delta_minutes:
        return None
    return frame.iloc[position], observed_time, delta_minutes


def resize_scene(sar, product_path: Path, image_size: int):
    """Read a full SAR scene and resize its feature/geolocation channels."""
    s0, s0_norm, incidence, azimuth, longitudes, latitudes, _ = sar.sar_params(
        sar_fn=str(product_path), normalize=True, vv=True
    )
    if s0_norm is None:
        raise ValueError("sar.sar_params returned no normalized backscatter")

    channels = [
        np.asarray(s0_norm, dtype=np.float32),
        np.asarray(incidence, dtype=np.float32),
        np.asarray(azimuth, dtype=np.float32),
        np.asarray(latitudes, dtype=np.float32),
        np.asarray(longitudes, dtype=np.float32),
    ]
    if len({channel.shape for channel in channels}) != 1 or channels[0].ndim != 2:
        raise ValueError("Full-scene SAR feature and geolocation arrays must share a 2-D shape")

    raw = np.stack(channels, axis=-1)
    pixel_mask = np.all(np.isfinite(raw[..., :3]), axis=-1, keepdims=True).astype(np.float32)
    for channel in range(raw.shape[-1]):
        finite = np.isfinite(raw[..., channel])
        fill_value = float(np.median(raw[..., channel][finite])) if finite.any() else 0.0
        raw[..., channel][~finite] = fill_value

    resized = tf.image.resize_with_pad(raw, image_size, image_size, method="bilinear").numpy()
    resized_mask = tf.image.resize_with_pad(
        pixel_mask, image_size, image_size, method="nearest"
    ).numpy()
    features = np.concatenate([resized, resized_mask], axis=-1).astype(np.float32)

    geo = tf.image.resize_with_pad(raw[..., 3:5], image_size, image_size, method="bilinear").numpy()
    geo[resized_mask[..., 0] < 0.5] = np.nan
    return features, resized_mask.astype(np.float32), geo.astype(np.float32)


def make_point_target(
    geo: np.ndarray,
    valid_mask: np.ndarray,
    buoy_latitude: float,
    buoy_longitude: float,
    stress: float,
) -> tuple[np.ndarray, np.ndarray, tuple[int, int], float]:
    """Place the scalar label and loss weight at the nearest valid SAR pixel."""
    latitudes = geo[..., 0]
    longitudes = geo[..., 1]
    valid = (valid_mask[..., 0] > 0.5) & np.isfinite(latitudes) & np.isfinite(longitudes)
    if not np.any(valid):
        raise ValueError("SAR scene has no valid geolocated pixels")

    latitude_radians = np.deg2rad(latitudes)
    longitude_radians = np.deg2rad(longitudes)
    buoy_latitude_radians = np.deg2rad(buoy_latitude)
    buoy_longitude_radians = np.deg2rad(buoy_longitude)
    delta_latitude = latitude_radians - buoy_latitude_radians
    delta_longitude = (longitude_radians - buoy_longitude_radians + np.pi) % (2 * np.pi) - np.pi
    haversine = (
        np.sin(delta_latitude / 2) ** 2
        + np.cos(latitude_radians) * np.cos(buoy_latitude_radians)
        * np.sin(delta_longitude / 2) ** 2
    )
    haversine[~valid] = np.inf
    y_index, x_index = np.unravel_index(np.argmin(haversine), haversine.shape)
    distance_km = 6371.0 * 2 * np.arcsin(np.sqrt(np.min(haversine)))

    target = np.zeros((*valid.shape, 1), dtype=np.float32)
    point_weights = np.zeros_like(target)
    target[y_index, x_index, 0] = stress
    point_weights[y_index, x_index, 0] = 1.0
    return target, point_weights, (y_index, x_index), float(distance_km)


def build_training_examples(
    data_dir: Path,
    metadata: dict,
    sar,
    load_data_xarray,
    predictors: list[str],
    image_size: int,
    max_delta_minutes: float,
):
    """Load WHOI records, match SAR products by time, and assemble scene samples."""
    transfer_data = load_data_xarray.load_all_into_xarray(run_on_ppi=True)
    images, valid_masks, targets, point_weights = [], [], [], []
    metadata_rows, geolocation, buoy_pixels = [], [], []

    for transfer_key, observations in transfer_data.items():
        buoy = buoy_name_from_transfer_key(transfer_key)
        if buoy not in metadata or not metadata[buoy].get("products"):
            print(f"Skipping {buoy}: no matching Sentinel product metadata")
            continue

        valid_observations = filter_valid_observations(observations, predictors)
        if valid_observations.empty:
            print(f"Skipping {buoy}: no valid WHOI observations")
            continue

        for product_id, product in metadata[buoy]["products"].items():
            filename = product.get("filename")
            acquisition_time = product.get("beginposition")
            if not filename or acquisition_time is None:
                continue

            match = nearest_observation(
                valid_observations, acquisition_time, max_delta_minutes
            )
            if match is None:
                continue
            observation, observed_time, delta_minutes = match
            target_stress = -float(observation["UWr"]) * float(observation["rhoair"])
            if not np.isfinite(target_stress):
                continue

            product_path = data_dir / filename
            if not product_path.exists():
                print(f"Missing SAR product: {product_path}")
                continue

            try:
                image, valid_mask, geo = resize_scene(sar, product_path, image_size)
                target, point_weight, buoy_pixel, distance_km = make_point_target(
                    geo,
                    valid_mask,
                    float(observation["lat"]),
                    float(observation["lon"]),
                    target_stress,
                )
            except Exception as exc:
                print(f"Could not read {product_path}: {exc}")
                continue

            images.append(image)
            valid_masks.append(valid_mask)
            targets.append(target)
            point_weights.append(point_weight)
            geolocation.append(geo)
            buoy_pixels.append(buoy_pixel)
            metadata_rows.append(
                {
                    "buoy": buoy,
                    "product_id": product_id,
                    "filename": filename,
                    "acquisition_time": str(acquisition_time),
                    "observation_time": str(observed_time),
                    "time_difference_minutes": delta_minutes,
                    "stress": target_stress,
                    "buoy_latitude": float(observation["lat"]),
                    "buoy_longitude": float(observation["lon"]),
                    "matched_pixel_y": buoy_pixel[0],
                    "matched_pixel_x": buoy_pixel[1],
                    "buoy_pixel_distance_km": distance_km,
                }
            )

    if len(images) < 2:
        raise ValueError(
            f"Only {len(images)} SAR/WHOI pairs could be loaded. Check the SAR metadata, "
            "product files, WHOI reader paths, and time-difference limit."
        )

    return (
        np.stack(images),
        np.stack(valid_masks),
        np.stack(targets),
        np.stack(point_weights),
        metadata_rows,
        np.stack(geolocation),
        np.asarray(buoy_pixels, dtype=np.int32),
    )


def standardize_images(train_images, other_images, train_masks, other_masks):
    """Normalize channels using only valid pixels in training scenes."""
    means = np.zeros(train_images.shape[-1] - 1, dtype=np.float32)
    stds = np.ones_like(means)
    for channel in range(len(means)):
        pixels = train_images[..., channel][train_masks[..., 0] > 0.5]
        finite = pixels[np.isfinite(pixels)]
        if not finite.size:
            raise ValueError(f"Input channel {channel} has no finite training pixels")
        means[channel] = finite.mean()
        std = finite.std()
        stds[channel] = std if std > 1e-6 else 1.0

    def transform(images):
        result = images.copy()
        for channel in range(len(means)):
            values = result[..., channel]
            values[~np.isfinite(values)] = means[channel]
            result[..., channel] = (values - means[channel]) / stds[channel]
        return result

    train_result = transform(train_images)
    other_result = transform(other_images)
    train_result[..., -1] = train_masks[..., 0]
    other_result[..., -1] = other_masks[..., 0]
    return train_result, other_result, means, stds


def build_unet(input_shape: tuple[int, int, int]) -> keras.Model:
    """Build a compact U-Net that returns one stress value per output pixel."""
    inputs = keras.Input(shape=input_shape)
    first = layers.Conv2D(16, 3, padding="same", activation="relu")(inputs)
    first = layers.Conv2D(16, 3, padding="same", activation="relu")(first)
    down1 = layers.MaxPooling2D()(first)
    second = layers.Conv2D(32, 3, padding="same", activation="relu")(down1)
    second = layers.Conv2D(32, 3, padding="same", activation="relu")(second)
    down2 = layers.MaxPooling2D()(second)
    bridge = layers.Conv2D(64, 3, padding="same", activation="relu")(down2)
    bridge = layers.Conv2D(64, 3, padding="same", activation="relu")(bridge)
    up2 = layers.UpSampling2D(interpolation="bilinear")(bridge)
    up2 = layers.Concatenate()([up2, second])
    up2 = layers.Conv2D(32, 3, padding="same", activation="relu")(up2)
    up2 = layers.Conv2D(32, 3, padding="same", activation="relu")(up2)
    up1 = layers.UpSampling2D(interpolation="bilinear")(up2)
    up1 = layers.Concatenate()([up1, first])
    up1 = layers.Conv2D(16, 3, padding="same", activation="relu")(up1)
    up1 = layers.Conv2D(16, 3, padding="same", activation="relu")(up1)
    output = layers.Conv2D(1, 1, padding="same", activation="linear")(up1)
    model = keras.Model(inputs, output, name="sar_to_stress_image")
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss=sparse_point_mse)
    return model


def sparse_point_mse(y_true: tf.Tensor, y_pred: tf.Tensor) -> tf.Tensor:
    """MSE at observed pixels only; y_true channels are target and point mask."""
    target = y_true[..., :1]
    point_weights = y_true[..., 1:2]
    squared_error = tf.square(y_pred - target) * point_weights
    numerator = tf.reduce_sum(squared_error, axis=(1, 2, 3))
    denominator = tf.maximum(tf.reduce_sum(point_weights, axis=(1, 2, 3)), 1.0)
    return numerator / denominator


def train(args: argparse.Namespace) -> None:
    if args.image_size <= 0 or args.image_size % 4:
        raise ValueError("image-size must be a positive multiple of 4 for this U-Net")
    sar, load_data_xarray, predictors = import_repository_readers(args.whoi_repo)
    data_dir = Path(args.data_dir).expanduser()
    metadata = load_sar_metadata(data_dir, args.sar_metadata)
    images, valid_masks, sparse_targets, point_weights, scene_info, geolocation, buoy_pixels = build_training_examples(
        data_dir,
        metadata,
        sar,
        load_data_xarray,
        list(predictors),
        args.image_size,
        args.max_time_delta_minutes,
    )

    rng = np.random.default_rng(args.seed)
    order = rng.permutation(len(images))
    validation_count = max(1, int(round(len(images) * args.validation_fraction)))
    if validation_count >= len(images):
        raise ValueError("Validation fraction leaves no training scenes")
    valid_indices, train_indices = order[:validation_count], order[validation_count:]

    x_train, x_valid, means, stds = standardize_images(
        images[train_indices], images[valid_indices],
        valid_masks[train_indices], valid_masks[valid_indices]
    )
    y_train = np.concatenate(
        [sparse_targets[train_indices], point_weights[train_indices]], axis=-1
    )
    y_valid = np.concatenate(
        [sparse_targets[valid_indices], point_weights[valid_indices]], axis=-1
    )

    model = build_unet(x_train.shape[1:])
    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_valid, y_valid),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True)],
        verbose=1,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save(output_dir / "sar_to_stress_image.keras")
    np.savez(output_dir / "input_normalization.npz", mean=means, std=stds)
    predictions = model.predict(x_valid, batch_size=args.batch_size, verbose=0)[..., 0]

    summary = []
    for position, index in enumerate(valid_indices):
        prediction = predictions[position]
        prediction[valid_masks[index, ..., 0] < 0.5] = np.nan
        buoy_y, buoy_x = buoy_pixels[index]
        np.savez_compressed(
            output_dir / f"stress_image_{position:04d}.npz",
            stress=prediction,
            latitude=geolocation[index, ..., 0],
            longitude=geolocation[index, ..., 1],
            buoy_pixel=np.asarray([buoy_y, buoy_x]),
        )
        summary.append({
            **scene_info[index],
            "predicted_mean": float(np.nanmean(prediction)),
            "predicted_std": float(np.nanstd(prediction)),
            "predicted_at_buoy_pixel": float(prediction[buoy_y, buoy_x]),
            "point_error_at_buoy": float(prediction[buoy_y, buoy_x] - scene_info[index]["stress"]),
        })

    pd.DataFrame(summary).to_csv(output_dir / "validation_summary.csv", index=False)
    with (output_dir / "training_history.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["epoch", "loss", "val_loss"])
        for epoch, values in enumerate(zip(
            history.history.get("loss", []),
            history.history.get("val_loss", []),
        ), start=1):
            writer.writerow([epoch, *values])

    print(f"Training scenes: {len(train_indices)}; validation scenes: {len(valid_indices)}")
    print(f"Saved model and geolocated stress arrays to {output_dir}")
    print("Loss is applied only at the nearest SAR pixel to each matched buoy observation.")
    print("The rest of each predicted map is not directly supervised.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Sentinel product directory")
    parser.add_argument("--sar-metadata", help="Path to in_situ_obs_with_sar_params[_old].pickle")
    parser.add_argument("--whoi-repo", help="Path to MachineOcean_WP1_WHOI for the existing WHOI loader")
    parser.add_argument("--max-time-delta-minutes", type=float, default=30.0)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="stress_image_output")
    return parser.parse_args()


if __name__ == "__main__":
    train(parse_args())
