"""Assemble the device content folder (pushed with adb) from finished outputs:
  content/manifest.json, content/photos/<name>.jpg (8K app texture), content/videos/<name>.mp4 (8K HEVC), content/thumbs/<name>.jpg
Files are hard-linked (no copies). Only finished items are listed. Also writes a size/count report.
  build_content.py [OUT_CONTENT_DIR]
"""
import json, os, sys
from pathlib import Path
from PIL import Image

ROOT = Path('/workspace/code/pano_xr')
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'deliver/content'
themes = json.loads((ROOT / 'jobs/themes.json').read_text())
for d in ('photos', 'videos', 'thumbs'):
    (OUT / d).mkdir(parents=True, exist_ok=True)


def link(src, dst):
    if dst.exists():
        dst.unlink()
    os.link(src, dst)


man, tot, n_p, n_v = [], 0, 0, 0
for t in themes:
    e = dict(id=t['id'], ko=t['ko'], category=t['category'], photos=[], videos=[])
    for k in (1, 2):
        p = ROOT / 'out/photos/app8k' / f"{t['id']}_p{k}.jpg"; th = ROOT / 'out/photos/thumbs' / f"{t['id']}_p{k}.jpg"
        if p.exists() and th.exists():
            link(p, OUT / 'photos' / p.name); link(th, OUT / 'thumbs' / p.name)
            w, h = Image.open(p).size
            d = dict(file=f'photos/{p.name}', thumb=f'thumbs/{p.name}', width=w, height=h)
            au = ROOT / 'out/photo_audio' / f"{t['id']}_p{k}.m4a"
            if au.exists():
                (OUT / 'audio').mkdir(exist_ok=True); link(au, OUT / 'audio' / au.name); d['audio'] = f'audio/{au.name}'; tot += au.stat().st_size
            e['photos'].append(d); tot += p.stat().st_size; n_p += 1
        v = ROOT / 'out/videos/final' / f"{t['id']}_v{k}.mp4"; vt = v.with_suffix('.thumb.jpg')
        if v.exists() and vt.exists():
            link(v, OUT / 'videos' / v.name); link(vt, OUT / 'thumbs' / (v.stem + '.jpg'))
            e['videos'].append(dict(file=f'videos/{v.name}', thumb=f'thumbs/{v.stem}.jpg', width=7680, height=3840)); tot += v.stat().st_size; n_v += 1
    man.append(e)
(OUT / 'manifest.json').write_text(json.dumps(dict(version=1, themes=man), ensure_ascii=False, indent=1))
print(json.dumps(dict(photos=n_p, videos=n_v, themes=len(man), gigabytes=round(tot / 1e9, 2), out=str(OUT))))
