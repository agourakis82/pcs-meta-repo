#!/bin/bash
# Script to run KEC GPU-enabled processing with multi-core support

# Load config values from zuco_performance.yaml using yq (assumes yq is installed)
GPU_ENABLED=$(yq e '.zuco_processing.gpu.enabled' config/zuco_performance.yaml)
GPU_DEVICE=$(yq e '.zuco_processing.gpu.device' config/zuco_performance.yaml)
MAX_WORKERS=$(yq e '.zuco_processing.memory.max_workers' config/zuco_performance.yaml)

if [ "$GPU_ENABLED" = "true" ]; then
  export CUDA_VISIBLE_DEVICES=${GPU_DEVICE#cuda:}
  echo "GPU enabled on device $CUDA_VISIBLE_DEVICES"
else
  echo "GPU disabled"
fi

echo "Using max workers: $MAX_WORKERS"

# Run the GPU-enabled Python script with max workers
python3 scripts/run_kec_gpu.py --jobs $MAX_WORKERS
