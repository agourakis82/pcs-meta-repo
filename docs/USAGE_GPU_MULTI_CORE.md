# Enabling Multi-Core and GPU Usage

This document explains how to enable and configure multi-core parallelism and GPU acceleration for the processing scripts.

## Configuration

The main configuration file is `config/zuco_performance.yaml`.

- `gpu.enabled`: Set to `true` to enable GPU acceleration (requires CUDA-compatible GPU and CuPy installed).
- `gpu.device`: GPU device identifier, e.g., `"cuda:0"`.
- `memory.max_workers`: Number of parallel workers for multi-core processing.

## Running GPU-Enabled Processing

Use the provided shell script `run_kec_gpu.sh` to run GPU-enabled processing with multi-core support.

```bash
bash run_kec_gpu.sh
```

This script reads the configuration and sets environment variables accordingly.

## Running GPU-Enabled Semantic Analysis

Alternatively, run the Python script directly with options:

```bash
python3 scripts/run_kec_gpu.py --jobs 4
```

Use `--no-gpu` to disable GPU:

```bash
python3 scripts/run_kec_gpu.py --no-gpu
```

Use `--config` to specify a different config file:

```bash
python3 scripts/run_kec_gpu.py --config path/to/config.yaml
```

## Requirements

- CUDA-compatible GPU and drivers installed
- CuPy installed for GPU acceleration
- Python dependencies installed (see `requirements.txt`)

## Notes

- Multi-core parallelism uses the number of workers specified in the config or via `--jobs` argument.
- GPU acceleration is enabled by default if available and not disabled by `--no-gpu`.
- Adjust `max_workers` and `gpu.device` in the config file to tune performance.
