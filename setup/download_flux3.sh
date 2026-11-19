#!/usr/bin/env bash
cd /workspace/code/pano_xr
export HF_HUB_DISABLE_XET=1
python3 - <<'PY'
from huggingface_hub import snapshot_download
pat=["model.safetensors","config.json","manifest.json","modular_model_index.json","ae.safetensors","text_encoder/*","README.md","LICENSE.md","NOTICE.md"]
for r in ['flux-3-image-klein','flux-3-image-klein-base']:
    snapshot_download('black-forest-labs/'+r, local_dir='/workspace/code/pano_xr/model-cache/'+r, allow_patterns=pat, max_workers=4); print('OK',r,flush=True)
snapshot_download('black-forest-labs/flux-3-image-klein-pup', local_dir='/workspace/code/pano_xr/model-cache/flux-3-image-klein-pup', max_workers=4); print('OK pup',flush=True)
PY
for r in flux-3-image-klein flux-3-image-klein-base flux-3-image-klein-pup; do python3 scripts/verify_hf.py black-forest-labs/$r model-cache/$r | grep -v "^OK\|MISSING variants"; done
echo FLUX3_DONE
