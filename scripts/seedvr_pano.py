"""8K 360 photo with SeedVR2 (diffusion super-resolution, x4): 2048x1024 ERP -> 8192x4096 ERP.
The ERP is wrap-padded left/right before upscaling so the 0/360 deg seam gets real neighbours, then cropped back.
  seedvr_pano.py IN.png OUT.png [--model seedvr2_ema_7b_sharp_fp16.safetensors] [--pad 128] [--seed 42]
"""
import argparse, glob, os, subprocess, sys, tempfile, time
from pathlib import Path
from PIL import Image

ROOT = Path('/workspace/code/pano_xr')
ap = argparse.ArgumentParser()
ap.add_argument('inp'); ap.add_argument('out')
ap.add_argument('--model', default='seedvr2_ema_7b_sharp_fp16.safetensors'); ap.add_argument('--pad', type=int, default=128)
ap.add_argument('--seed', type=int, default=42); ap.add_argument('--scale', type=int, default=4)
a = ap.parse_args()
src = Image.open(a.inp).convert('RGB'); w, h = src.size; P = a.pad
padded = Image.new('RGB', (w + 2 * P, h)); padded.paste(src.crop((w - P, 0, w, h)), (0, 0)); padded.paste(src, (P, 0)); padded.paste(src.crop((0, 0, P, h)), (P + w, 0))
with tempfile.TemporaryDirectory(dir=str(ROOT / 'out')) as td:
    pin = Path(td) / 'in.png'; padded.save(pin); odir = Path(td) / 'out'; odir.mkdir()
    t0 = time.time()
    cmd = [str(ROOT / 'env_flux3/bin/python'), str(ROOT / 'SeedVR2_upscaler/inference_cli.py'), str(pin), '--output', str(odir), '--output_format', 'png',
           '--model_dir', str(ROOT / 'model-cache/SeedVR2'), '--dit_model', a.model, '--resolution', str(h * a.scale), '--seed', str(a.seed),
           '--batch_size', '1', '--color_correction', 'lab', '--vae_encode_tiled', '--vae_decode_tiled',
           '--vae_encode_tile_size', '1024', '--vae_decode_tile_size', '1024', '--attention_mode', 'sdpa']
    subprocess.run(cmd, check=True, cwd=str(ROOT / 'SeedVR2_upscaler'))
    res = [f for f in glob.glob(str(odir / '**/*.png'), recursive=True)]
    assert res, 'SeedVR2 wrote no image'
    up = Image.open(res[0]).convert('RGB'); s = up.size[1] / h
    up = up.crop((round(P * s), 0, round((P + w) * s), up.size[1]))
    if up.size != (w * a.scale, h * a.scale):
        up = up.resize((w * a.scale, h * a.scale), Image.LANCZOS)
    up.save(a.out, compress_level=3)
print('DONE', a.out, up.size, round(time.time() - t0, 1), 's', flush=True)
