#!/usr/bin/env bash
cd /workspace/code/pano_xr
export HF_HUB_DISABLE_XET=1
python3 - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download('Wan-AI/Wan2.2-I2V-A14B',local_dir='/workspace/code/pano_xr/model-cache/Wan-AI/Wan2.2-I2V-A14B',max_workers=6)
print('A14B_OK', flush=True)
PY
python3 scripts/verify_hf.py Wan-AI/Wan2.2-I2V-A14B model-cache/Wan-AI/Wan2.2-I2V-A14B
echo A14B_DONE
