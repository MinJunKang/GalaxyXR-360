#!/usr/bin/env bash
cd /workspace/code/pano_xr
export HF_HUB_DISABLE_XET=1
python3 - <<'PY'
from huggingface_hub import snapshot_download
for r,d in [('google/siglip2-base-patch16-512','siglip2-base-patch16-512'),('laion/larger_clap_general','larger_clap_general'),('tencent/HunyuanVideo-Foley','HunyuanVideo-Foley')]:
    snapshot_download(r, local_dir=f'/workspace/code/pano_xr/model-cache/{d}', max_workers=4); print('OK',r,flush=True)
PY
python3 scripts/verify_hf.py tencent/HunyuanVideo-Foley model-cache/HunyuanVideo-Foley | grep -v '^OK'
echo FOLEY_DONE
