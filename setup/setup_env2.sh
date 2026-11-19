#!/usr/bin/env bash
set -e
E=/workspace/code/pano_xr/env_cube/bin
$E/pip install -r /workspace/code/pano_xr/logs/req_cube.txt > /workspace/code/pano_xr/logs/env_cube2.txt 2>&1
$E/pip install imageio-ffmpeg opencv-python-headless >> /workspace/code/pano_xr/logs/env_cube2.txt 2>&1
echo ENV_DONE
