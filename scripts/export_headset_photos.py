"""All 360 photo candidates as headset-ready 8K GPano JPEGs + matching sound, in ONE folder:
  <name>_A.jpg / <name>_A.m4a  (candidate s0),  <name>_B.jpg / <name>_B.m4a  (candidate s1)
The app pairs a photo with the sound of the same file name. usage: export_headset_photos.py OUT_DIR [--jobs 8]"""
import argparse, io, os, shutil, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from PIL import Image
ROOT = Path('/workspace/code/pano_xr')
src = open(ROOT / 'scripts/photo_gen.py').read(); ns = {}; exec(src[src.index('def xmp_gpano'):src.index('def save_jpeg_gpano')], ns)

def one(args):
    png, out = args
    if out.exists() and out.stat().st_size > 0: return out.name, 'skip'
    img = Image.open(png).convert('RGB'); b = io.BytesIO(); img.save(b, 'JPEG', quality=92, optimize=True); j = b.getvalue()
    seg = ns['xmp_gpano'](*img.size); seg = seg if isinstance(seg, bytes) else seg.encode()
    tmp = out.with_suffix('.tmp'); tmp.write_bytes(j[:2] + b'\xff\xe1' + (len(seg) + 2).to_bytes(2, 'big') + seg + j[2:]); tmp.rename(out)
    return out.name, round(out.stat().st_size / 1e6, 1)

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--jobs', type=int, default=8); a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
work = []
for png in sorted((ROOT / 'out/photo360_8k').glob('*__s[01].png')):
    name, s = png.stem.split('__s'); tag = 'AB'[int(s)]
    aud = ROOT / 'out/photo_audio' / f'{name}.m4a'
    if not aud.exists(): print('NO_AUDIO', name); continue
    shutil.copy(aud, out / f'{name}_{tag}.m4a')
    work.append((png, out / f'{name}_{tag}.jpg'))
with ProcessPoolExecutor(a.jobs) as ex:
    for i, r in enumerate(ex.map(one, work)):
        if i % 20 == 0: print(i, r, flush=True)
print('EXPORT_DONE', len(work))
