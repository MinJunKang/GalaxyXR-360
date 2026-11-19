#!/usr/bin/env bash
cd /workspace/code/pano_xr
export HF_HUB_DISABLE_XET=1
while tmux has-session -t pano_queue 2>/dev/null && ! grep -q "OK Wan-AI/Wan2.2-I2V-A14B" logs/download_queue.out; do sleep 30; done
python3 - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download('nomadoor/flux-2-klein-9B-360-erp-outpaint-lora', local_dir='/workspace/code/pano_xr/model-cache/flux-2-klein-9B-360-erp-outpaint-lora', max_workers=4)
print('LORA_OK', flush=True)
snapshot_download('black-forest-labs/FLUX.2-klein-base-9B', local_dir='/workspace/code/pano_xr/model-cache/FLUX.2-klein-base-9B', max_workers=4,
  allow_patterns=['model_index.json','scheduler/*','text_encoder/*','tokenizer/*','transformer/*','vae/*','LICENSE.md','README.md'])
print('F2K9_OK', flush=True)
PY
python3 scripts/verify_hf.py black-forest-labs/FLUX.2-klein-base-9B model-cache/FLUX.2-klein-base-9B 'text_encoder/*' 'transformer/*' 'vae/*'
python3 scripts/verify_hf.py nomadoor/flux-2-klein-9B-360-erp-outpaint-lora model-cache/flux-2-klein-9B-360-erp-outpaint-lora '*.safetensors'
echo F2K9_DONE
