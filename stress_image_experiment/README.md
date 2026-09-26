# SAR-to-stress-image experiment

This exploratory prototype uses the same SAR and WHOI readers as the repository collocation notebooks. It does not read zarr or require a CSV manifest.

## Data and collocation

1. WHOI observations are loaded with `mo_whoi_data.load_data.load_data_xarray.load_all_into_xarray(run_on_ppi=True)`.
2. Sentinel product metadata are read from `in_situ_obs_with_sar_params_old.pickle` (or `in_situ_obs_with_sar_params.pickle`) in the Sentinel data directory.
3. The buoy name is derived from each `Transfer_<buoy>.mat` key.
4. Each SAR product's `beginposition` is matched to the nearest valid WHOI `datetime`, with a 30-minute maximum separation by default.
5. Stress is computed as `-UWr * rhoair`.
6. The full Sentinel scene is read through `sar.sar_params(...)`, with no station coordinates so it is not cropped around the buoy.
7. The WHOI row's latitude/longitude is matched to the nearest valid pixel using the SAR scene's geolocation grids.

## Supervision limitation

The U-Net outputs a stress value for every pixel, but its training loss is applied **only at the SAR pixel nearest the buoy observation**. That pixel is recalculated for every scene. Other output pixels are not treated as zero and receive no direct loss. Their predictions are exploratory spatial extrapolations, not measured or validated stress values.

Latitude and longitude grids are included as SAR input channels. The buoy coordinates locate the supervised output pixel; they are not broadcast as inputs to every pixel. The model is not currently given acquisition-time channels.

## Run

Use the same Python environment as the collocation notebooks, with TensorFlow, Nansat, the WHOI reader package, NumPy, and pandas installed. From the repository root:

```bash
python3 stress_image_experiment/train_stress_image.py \
  --data-dir /lustre/storeB/project/IT/geout/machine-ocean/data_raw/sentinel \
  --whoi-repo notebooks/MachineOcean_WP1_WHOI \
  --image-size 256 \
  --output-dir stress_image_output
```

If the WHOI package is installed elsewhere, pass its path with `--whoi-repo`. Use `--sar-metadata` to specify the metadata pickle and `--max-time-delta-minutes` to change the observation matching tolerance. `--image-size` must be a positive multiple of four.

## Output

- `sar_to_stress_image.keras`: trained model
- `stress_image_*.npz`: predicted stress arrays, corresponding latitude/longitude arrays, and buoy pixel indices
- `validation_summary.csv`: scene information and predicted stress/error at the supervised buoy pixel
- `training_history.csv`: sparse point loss history
- `input_normalization.npz`: training-set input channel means and standard deviations

The input channels are normalized backscatter, incidence angle, look direction, latitude, longitude, and a valid-pixel mask. Full scenes are resized with padding to a common square size, preserving aspect ratio. The matching SAR pixel is found on the resized geolocation grid so it aligns with the model output.

The current train/validation split is random by scene. For a reliable estimate of generalization, hold out buoy stations or time periods as groups; scenes from the same buoy can otherwise appear in both splits.
