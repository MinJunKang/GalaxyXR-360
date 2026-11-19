#!/usr/bin/env bash
set -e
cd /workspace/code/pano_xr
/opt/conda/bin/conda create -y -p /workspace/code/pano_xr/env_flux3 python=3.11 > logs/env_flux3.txt 2>&1
E=/workspace/code/pano_xr/env_flux3/bin
$E/pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu126 >> logs/env_flux3.txt 2>&1
$E/pip install git+https://github.com/huggingface/diffusers.git transformers accelerate safetensors sentencepiece protobuf peft opencv-python-headless spandrel pillow >> logs/env_flux3.txt 2>&1
$E/python -c "import diffusers,transformers,torch;print('diffusers',diffusers.__version__,'transformers',transformers.__version__,'torch',torch.__version__, torch.cuda.is_available())"
echo FLUX3_ENV_DONE
