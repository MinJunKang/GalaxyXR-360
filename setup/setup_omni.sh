#!/usr/bin/env bash
set -e
cd /workspace/code/pano_xr
[ -x /workspace/code/pano_xr/env_omni/bin/python ] || /opt/conda/bin/conda create -y -p /workspace/code/pano_xr/env_omni python=3.10 > logs/env_omni.txt 2>&1
E=/workspace/code/pano_xr/env_omni/bin
$E/pip install torch==2.4.1 torchaudio==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu121 >> logs/env_omni.txt 2>&1
grep -vE "^(torch|torchaudio|torchvision|av|cupy|SoundFile|soundfile)==" OmniAudio/requirements.txt > logs/req_omni.txt; printf "av==12.0.0\ncupy-cuda12x==12.3.0\nSoundFile==0.12.1\n" >> logs/req_omni.txt
$E/pip install -r logs/req_omni.txt >> logs/env_omni.txt 2>&1 || $E/pip install -r logs/req_omni.txt --no-deps >> logs/env_omni.txt 2>&1
$E/python -c "import torch, torchaudio, transformers; print('omni env ok', torch.__version__, transformers.__version__)"
echo OMNI_ENV_DONE
