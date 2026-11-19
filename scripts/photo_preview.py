"""Preview a 360 photo with its ambience as a small 360 mp4: ERP 2K -> Real-ESRGAN x2 (wrap-padded) 4096x2048 ->
20 s still video (H.264, 30 fps) + looped ambience (2 loops) + spherical metadata.  photo_preview.py NAME SEED OUT.mp4"""
import subprocess, sys
from pathlib import Path
import numpy as np, torch
from PIL import Image
ROOT = Path('/workspace/code/pano_xr'); sys.path.insert(0, str(ROOT / 'scripts'))
from post_video import esrgan_wrap, load_esrgan
name, seed, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]).resolve()
img = torch.from_numpy(np.array(Image.open(ROOT / f'out/photo360/{name}__s{seed}.png').convert('RGB'))).cuda().permute(2, 0, 1).float() / 255
up = esrgan_wrap(load_esrgan(), img)
png = out.with_suffix('.png'); Image.fromarray((up * 255 + 0.5).byte().permute(1, 2, 0).cpu().numpy()).save(png)
tmp = out.with_suffix('.noMeta.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-i', str(png), '-stream_loop', '1', '-i', str(ROOT / f'out/photo_audio/{name}.m4a'),
                '-t', '20', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'stillimage', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
                '-movflags', '+faststart', str(tmp)], check=True)
subprocess.run([sys.executable, '-m', 'spatialmedia', '-i', str(tmp), str(out)], cwd=ROOT / 'spatial-media', check=True, stdout=subprocess.DEVNULL)
assert out.exists(); tmp.unlink(); png.unlink()
print('OK', out, out.stat().st_size)
