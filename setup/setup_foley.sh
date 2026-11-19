#!/usr/bin/env bash
set -e
cd /workspace/code/pano_xr
/opt/conda/bin/conda create -y -p /workspace/code/pano_xr/env_foley python=3.10 > logs/env_foley.txt 2>&1
E=/workspace/code/pano_xr/env_foley/bin
$E/pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124 >> logs/env_foley.txt 2>&1
$E/pip install -r HunyuanVideo-Foley/requirements.txt >> logs/env_foley.txt 2>&1
echo FOLEY_ENV_DONE
