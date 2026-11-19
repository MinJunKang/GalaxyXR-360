"""8K 360 photo + its looping ambience -> 8192x4096 HEVC still video with sound and spherical metadata (for viewing in
360 players and on the headset outside the app). Audio loops to fill the clip.
  photo8k_sound.py PHOTO_8K.png AUDIO.m4a OUT.mp4 [--seconds 30]"""
import argparse, subprocess, sys
from pathlib import Path
ROOT = Path('/workspace/code/pano_xr')
ap = argparse.ArgumentParser(); ap.add_argument('photo'); ap.add_argument('audio'); ap.add_argument('out'); ap.add_argument('--seconds', type=int, default=30)
a = ap.parse_args()
out = Path(a.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True); tmp = out.with_suffix('.noMeta.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '2', '-i', str(Path(a.photo).resolve()),
                '-stream_loop', '-1', '-i', str(Path(a.audio).resolve()), '-t', str(a.seconds), '-map', '0:v', '-map', '1:a',
                '-c:v', 'libx265', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-tag:v', 'hvc1',
                '-x265-params', 'keyint=2:min-keyint=1:level-idc=6.0:high-tier=1:log-level=error',
                '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(tmp)], check=True)
subprocess.run([sys.executable, '-m', 'spatialmedia', '-i', str(tmp), str(out)], cwd=ROOT / 'spatial-media', check=True, stdout=subprocess.DEVNULL)
assert out.exists() and out.stat().st_size > 0.9 * tmp.stat().st_size; tmp.unlink()
print('OK', out, round(out.stat().st_size / 1e6, 1), 'MB')
