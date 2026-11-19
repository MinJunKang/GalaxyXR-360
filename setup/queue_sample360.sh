#!/usr/bin/env bash
# when an A14B sample clip is written, convert it to 360 with CubeComposer 3K, 30 steps, full 16 fps (frames trimmed to a multiple of 9)
cd /workspace/code/pano_xr
name=$1; gpu=$2; clip=$3
until [ -f "$clip" ] && grep -q "^DONE" logs/sample/a14b_$4.log 2>/dev/null; do sleep 60; done
C="$(python3 -c "import json;print([x for x in json.load(open('jobs/videos_v2.json')) if x['name']=='$name'][0]['caption'])")"
CUDA_VISIBLE_DEVICES=$gpu PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONUNBUFFERED=1 env_cube/bin/python scripts/cube_custom.py --video "$clip" --caption "$C" --out out/sample/${name}_cube3k_s30 --mode 3k --steps 30 > logs/sample/cube3k_$name.log 2>&1
echo CUBE_DONE >> logs/sample/cube3k_$name.log
