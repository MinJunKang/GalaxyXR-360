"""First frames with FLUX 3 Image Klein (distilled by default) via diffusers ModularPipeline.
Two passes so each fits a 48 GB A6000 (upsampler ~28 GB, image model ~31 GB):
  upsample : flux3_gen.py upsample JOBS.json CAPTIONS.json   -> full scene captions from the official prompt upsampler (pup)
  generate : flux3_gen.py generate CAPTIONS.json OUT_DIR [--model klein|klein-base] [--width 2048 --height 1152]
The camera is described as a level, static, wide-angle (90 degree horizontal FOV) view so it matches the CubeComposer
placement (fov 90, yaw/pitch 0). Images are saved at full size and as a 1280x720 copy for Wan2.2 I2V.
"""
import argparse, json, sys, time
from pathlib import Path
import torch

ROOT = Path('/workspace/code/pano_xr'); MC = ROOT / 'model-cache'
CAMERA = ('Eye-level view looking straight ahead at the horizon, rectilinear perspective with a 90 degree horizontal field of view, '
          'no lens distortion, no fisheye, vertical lines stay perfectly straight and vertical, level horizon in the vertical middle of the frame, '
          'deep focus, natural light, photorealistic, ultra detailed, sharp. No camera, no tripod, no photographer, no people unless described, '
          'no text, no watermark, no frame. Scene: ')


def pipe_for(model, with_upsampler):
    from diffusers import ModularPipeline
    repo = str(MC / ('flux-3-image-klein-diffusers' if model == 'klein' else 'flux-3-image-klein-base-diffusers'))
    if with_upsampler:
        p = ModularPipeline.from_pretrained(repo)
    else:
        blocks = ModularPipeline.from_pretrained(repo).blocks
        blocks.sub_blocks.pop('prompt_upsampler')
        p = blocks.init_pipeline(repo)
    p.load_components(dtype={'vae': torch.float32, 'default': torch.bfloat16})
    return p.to('cuda')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['upsample', 'generate']); ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--model', default='klein', choices=['klein', 'klein-base'])
    ap.add_argument('--width', type=int, default=2048); ap.add_argument('--height', type=int, default=1152)
    ap.add_argument('--only', default='', help='comma separated job names')
    a = ap.parse_args()
    only = set(filter(None, a.only.split(',')))
    if a.mode == 'upsample':
        jobs = [j for j in json.loads(Path(a.src).read_text()) if not only or j['name'] in only]
        out = json.loads(Path(a.dst).read_text()) if Path(a.dst).exists() else {}
        p = pipe_for(a.model, True)
        for j in jobs:
            if j['name'] in out:
                continue
            front = j['prompt']
            t = time.time()
            r = p(prompt=CAMERA + front, width=a.width, height=a.height, generator=torch.Generator().manual_seed(j['seed']),
                  output=['prompt'], num_inference_steps=1)        # only the caption is used; image steps kept minimal
            out[j['name']] = dict(seed=j['seed'], request=CAMERA + front, caption=r['prompt'] if isinstance(r, dict) else r)
            Path(a.dst).write_text(json.dumps(out, indent=1, ensure_ascii=False))
            print('CAPTION', j['name'], round(time.time() - t, 1), flush=True)
        return
    caps = json.loads(Path(a.src).read_text()); outd = Path(a.dst); outd.mkdir(parents=True, exist_ok=True)
    p = pipe_for(a.model, False)
    from PIL import Image
    for name, c in caps.items():
        if only and name not in only:
            continue
        f = outd / f'{name}.png'
        if f.exists():
            continue
        t = time.time()
        img = p(prompt=c['caption'], width=a.width, height=a.height, generator=torch.Generator().manual_seed(c['seed']), output='images')[0]
        img.save(f); img.resize((1280, 720), Image.LANCZOS).save(outd / f'{name}_1280x720.png')
        print('IMAGE', name, round(time.time() - t, 1), 'peak_gb', round(torch.cuda.max_memory_allocated() / 2**30, 1), flush=True)


if __name__ == '__main__':
    main()
