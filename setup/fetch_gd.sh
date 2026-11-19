#!/usr/bin/env bash
# fetch_gd.sh <gdrive folder> <hf repo id> : wait for COMPLETE, copy into model-cache/<folder>-gd, verify against HF
F=$1; R=$2; D=/workspace/code/pano_xr/model-cache/$F-gd
cd /workspace/code/pano_xr
until rclone lsf gdrive:pano_xr_models-20261119/$F/ 2>/dev/null | grep -q '^COMPLETE'; do sleep 60; done
echo "$(date -u +%T) COMPLETE seen for $F"
t0=$(date +%s); rclone copy gdrive:pano_xr_models-20261119/$F $D --transfers 8 --checkers 16 --drive-chunk-size 128M 2>&1 | tail -3
t1=$(date +%s); echo "$(date -u +%T) copied $(du -sm $D | cut -f1) MB in $((t1-t0)) s"
python3 scripts/verify_hf.py $R $D | grep -v '^OK' ; echo "VERIFY_DONE $F (non-OK lines above, if any)"
