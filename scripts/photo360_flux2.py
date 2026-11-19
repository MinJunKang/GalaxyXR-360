"""360 photos: FLUX 3 perspective image -> ERP control (green canvas, image projected at yaw 0 / pitch 0 with a 90 deg
rectilinear FOV) -> FLUX.2 klein base 9B + nomadoor 360 ERP outpaint LoRA (2048x1024, base model as the LoRA card requires).
  photo360_flux2.py JOBS.json OUT_DIR [--only a,b] [--steps 50] [--guidance 4.0] [--seeds 2]
JOBS: {name: {"image": path, "caption": scene text, "seed": int}}. Writes OUT_DIR/<name>__s<k>.png and the control image.
"""
import argparse, json, time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

ROOT = Path('/workspace/code/pano_xr'); MC = ROOT / 'model-cache'
TRIGGER = ('Fill the green spaces according to the image. Outpaint as a seamless 360 equirectangular panorama (2:1). '
           'Keep the horizon level. Match left and right edges.')


def control_image(img, W=2048, H=1024, fov=90.0):
    """project a pinhole image (any aspect) onto a green ERP canvas, centred at yaw 0 / pitch 0."""
    pv = torch.from_numpy(np.asarray(img.convert('RGB'))).permute(2, 0, 1).float()[None] / 255
    hp, wp = pv.shape[-2:]
    v_, u_ = torch.meshgrid((torch.arange(H) + 0.5) / H, (torch.arange(W) + 0.5) / W, indexing='ij')
    lon, lat = u_ * 2 * np.pi - np.pi, np.pi / 2 - v_ * np.pi
    x, y, z = torch.cos(lat) * torch.sin(lon), torch.sin(lat), torch.cos(lat) * torch.cos(lon)
    f = (wp / 2) / np.tan(np.radians(fov) / 2); zs = z.clamp(min=1e-6)
    gx, gy = (f * x / zs) / (wp / 2), (-f * y / zs) / (hp / 2)
    inside = (z > 0) & (gx.abs() <= 1) & (gy.abs() <= 1)
    e = F.grid_sample(pv, torch.stack([gx, gy], -1)[None].clamp(-2, 2), mode='bicubic', align_corners=False)[0].clamp(0, 1)
    green = torch.tensor([0.0, 1.0, 0.0])[:, None, None].expand(3, H, W)
    out = torch.where(inside[None], e, green)
    return Image.fromarray((out.permute(1, 2, 0).numpy() * 255 + 0.5).astype(np.uint8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jobs'); ap.add_argument('out'); ap.add_argument('--only', default='')
    ap.add_argument('--steps', type=int, default=50); ap.add_argument('--guidance', type=float, default=4.0)
    ap.add_argument('--seeds', type=int, default=2); ap.add_argument('--fov', type=float, default=90.0)
    ap.add_argument('--offload', action='store_true', help='CPU offload (uses ~35 GB host RAM); default keeps all on the GPU')
    a = ap.parse_args()
    jobs = json.loads(Path(a.jobs).read_text()); only = set(filter(None, a.only.split(',')))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    from diffusers import Flux2KleinPipeline
    pipe = Flux2KleinPipeline.from_pretrained(str(MC / 'FLUX.2-klein-base-9B'), torch_dtype=torch.bfloat16)
    pipe.load_lora_weights(str(MC / 'flux-2-klein-9B-360-erp-outpaint-lora'), weight_name='flux-2-klein-9B-360-erp-outpaint-lora_V1.safetensors')
    if a.offload: pipe.enable_model_cpu_offload()
    else: pipe.to('cuda')
    for name, j in jobs.items():
        if only and name not in only:
            continue
        ctrl = control_image(Image.open(ROOT / j['image']), fov=a.fov); ctrl.save(out / f'{name}__control.png')
        for k in range(a.seeds):
            f = out / f'{name}__s{k}.png'
            if f.exists():
                continue
            t = time.time()
            img = pipe(image=ctrl, prompt=TRIGGER + ' ' + j['caption'], height=1024, width=2048, num_inference_steps=a.steps,
                       guidance_scale=a.guidance, generator=torch.Generator('cuda').manual_seed(j['seed'] + k)).images[0]
            img.save(f)
            print('PANO', name, k, round(time.time() - t, 1), 'peak_gb', round(torch.cuda.max_memory_allocated() / 2**30, 1), flush=True)


if __name__ == '__main__':
    main()
