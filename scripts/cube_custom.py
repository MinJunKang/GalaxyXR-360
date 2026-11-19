"""CubeComposer on our own perspective clip (not ODVista360).
The perspective clip (static camera, known horizontal FOV) is placed at yaw/pitch/roll = 0 in the sphere, remapped to ERP
with its coverage mask, split into cubemap faces, and CubeComposer generates the unobserved parts face-window by face-window.
Output: lossless PNG frames of the generated equirectangular video + generation_info.json.

  cube_custom.py --video pers.mp4 --caption "..." --out OUT [--fov 90] [--mode 4k] [--frames N] [--stride S] [--steps 15] [--cfg 5]
"""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np
import torch

CC = Path('/workspace/code/pano_xr/CubeComposer')
ORIG = Path.cwd()
sys.path.insert(0, str(CC)); os.chdir(CC)
from run import load_args_from_json, create_pipeline_from_args  # noqa: E402
from models.panorama import PanoVideoProcessor  # noqa: E402
from equilib import Equi2Pers  # noqa: E402
import torchvision  # noqa: E402

NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，"
       "多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走")
HF = Path('/workspace/code/pano_xr/hf/CubeComposer')
BASE = '/workspace/code/pano_xr/model-cache'


def read_video(path, frames, stride):
    import av
    out = []
    with av.open(str(path)) as c:
        for i, f in enumerate(c.decode(video=0)):
            if i % stride == 0:
                out.append(f.to_ndarray(format='rgb24'))
            if frames and len(out) >= frames:
                break
    return np.stack(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', default=''); ap.add_argument('--image', default='', help='still image -> static clip of --frames (default 5) frames'); ap.add_argument('--caption', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--fov', type=float, default=90.0); ap.add_argument('--pitch', type=float, default=0.0)
    ap.add_argument('--mode', default='4k', choices=['3k', '4k']); ap.add_argument('--frames', type=int, default=0)
    ap.add_argument('--stride', type=int, default=1); ap.add_argument('--steps', type=int, default=15); ap.add_argument('--cfg', type=float, default=5.0)
    ap.add_argument('--seed', type=int, default=0); ap.add_argument('--face_prompts', default='')
    ap.add_argument('--history', type=int, default=0, help='max_history_windows override (trained: 2)')
    ap.add_argument('--full_context', action='store_true', help='always_full_context: condition on the whole perspective clip')
    a = ap.parse_args()
    a.out = str((ORIG / a.out).resolve())
    if a.video: a.video = str((ORIG / a.video).resolve())
    if a.image: a.image = str((ORIG / a.image).resolve())
    out = Path(a.out); (out / 'frames').mkdir(parents=True, exist_ok=True)
    torch.manual_seed(a.seed); np.random.seed(a.seed)

    sub = 'cubecomposer-4k' if a.mode == '4k' else 'cubecomposer-3k'
    targs = load_args_from_json(str(HF / sub / 'args.json')); targs.base_model_path = BASE
    if a.mode == '3k':
        targs.height, targs.width = 1536, 3072  # cube 768
    if a.history: targs.max_history_windows = a.history
    if a.full_context: targs.always_full_context = True
    H, W, cube = targs.height, targs.width, targs.cube_map_size
    t0 = time.time(); pipe = create_pipeline_from_args(targs, checkpoint_path=str(HF / sub / 'model.safetensors')); load_s = time.time() - t0

    if a.image:
        from PIL import Image as _I
        im = np.asarray(_I.open(a.image).convert('RGB').resize((1280, 720), _I.LANCZOS))
        pers = np.stack([im] * (a.frames or 5))
    else:
        pers = read_video(a.video, a.frames, a.stride)                               # T,h,w,3 uint8
    wl = int(targs.window_length)
    if pers.shape[0] % wl:                     # the pipeline fails on a short last window (seen at 121 frames, window 9)
        keep = pers.shape[0] // wl * wl
        print(f'trimming {pers.shape[0]} -> {keep} frames (window_length {wl})', flush=True); pers = pers[:keep]
    T = pers.shape[0]
    pv = torch.from_numpy(pers).permute(0, 3, 1, 2).float().div(255).cuda()     # T,3,h,w
    rots = np.tile(np.array([[0.0, a.pitch, 0.0]]), (T, 1))                    # roll, pitch, yaw (deg)
    # Coverage mask built the way training builds it (equi2pers sample mask, blur 31/1.0, > 0.05); the repo's
    # remap_perspective_to_equirectangular mask is all ones for this use (checked), so it is not used.
    e2p = Equi2Pers(height=pers.shape[1] * 2, width=pers.shape[2] * 2, fov_x=a.fov, mode='bilinear')
    _, m0 = e2p(equi=torch.zeros(3, H, W, device='cuda'), rots={'roll': 0.0, 'pitch': np.radians(a.pitch), 'yaw': 0.0})
    m0 = m0.float().reshape(1, 1, H, W)
    m0 = (torchvision.transforms.functional.gaussian_blur(m0, kernel_size=31, sigma=1.0) > 0.05).float()   # 1,1,H,W
    cm0 = PanoVideoProcessor.extract_cube_maps(m0, cube_map_size=cube)
    cm0 = {f: (v > 0.5).to(torch.bfloat16).cpu() for f, v in cm0.items()}
    # content: perspective -> ERP, chunked on GPU, kept on CPU in bf16 (241 frames of 1920x3840 do not fit next to the model)
    # fixed camera -> one ERP->perspective sampling grid on GPU (same convention as equilib, checked: image centre at
    # ERP centre, +x right, +y up); the repo's pers2equi rebuilds a CPU grid every frame and takes ~20 min for 241 frames
    hp, wp = pers.shape[1], pers.shape[2]
    v_, u_ = torch.meshgrid((torch.arange(H, device='cuda') + 0.5) / H, (torch.arange(W, device='cuda') + 0.5) / W, indexing='ij')
    lon, lat = u_ * 2 * np.pi - np.pi, np.pi / 2 - v_ * np.pi
    x, y, z = torch.cos(lat) * torch.sin(lon), torch.sin(lat), torch.cos(lat) * torch.cos(lon)
    pr = np.radians(a.pitch); y, z = y * np.cos(pr) - z * np.sin(pr), y * np.sin(pr) + z * np.cos(pr)   # camera pitched up by a.pitch
    fpx = (wp / 2) / np.tan(np.radians(a.fov) / 2)
    zs = z.clamp(min=1e-6)
    gx, gy = (fpx * x / zs) / (wp / 2), (-fpx * y / zs) / (hp / 2)                  # normalized [-1, 1]
    inside = ((z > 0) & (gx.abs() <= 1) & (gy.abs() <= 1)).float()[None, None]
    grid = torch.stack([gx, gy], -1)[None].clamp(-2, 2)
    m0 = m0 * inside
    gt = {}
    for s0 in range(0, T, 8):
        ch = pv[s0:s0 + 8]
        e = torch.nn.functional.grid_sample(ch, grid.expand(ch.shape[0], -1, -1, -1), mode='bilinear', align_corners=False) * m0
        ce = PanoVideoProcessor.extract_cube_maps(e, cube_map_size=cube)
        for f in ce:
            gt.setdefault(f, []).append(ce[f].clamp(0, 1).to(torch.bfloat16).cpu())
        del e, ce
    gt = {f: torch.cat(v) for f, v in gt.items()}
    mk = {f: cm0[f].expand(T, -1, -1, -1).contiguous() for f in gt}
    del pv; torch.cuda.empty_cache()
    cond = {f: gt[f] * mk[f] for f in gt}
    coverage = {f: round(float(v.mean()), 4) for f, v in mk.items()}
    print('coverage per face', coverage, flush=True)
    fc = json.loads(a.face_prompts) if a.face_prompts else None

    t0 = time.time()
    with torch.no_grad():
        equi, faces, order = pipe(prompt=a.caption, negative_prompt=NEG, gt_cubemap=gt, cond_cubemap=cond, mask_cubemap=mk,
                                  num_inference_steps=a.steps, denoising_strength=1.0, sigma_shift=5.0, cfg_scale=a.cfg,
                                  face_captions=fc, use_face_prompts=bool(fc), tiled=False)
    gen_s = time.time() - t0
    from PIL import Image
    v = (equi.clamp(0, 1) * 255).to(torch.uint8).permute(0, 2, 3, 1).cpu().numpy()
    for t in range(v.shape[0]):
        Image.fromarray(v[t]).save(out / 'frames' / f'{t:04d}.png', compress_level=1)
    info = dict(video=str(a.video), caption=a.caption, fov=a.fov, pitch=a.pitch, mode=a.mode, frames=int(T), stride=a.stride, steps=a.steps, cfg=a.cfg,
                seed=a.seed, history=getattr(targs, 'max_history_windows', 2), full_context=bool(getattr(targs, 'always_full_context', False)), erp=[int(v.shape[2]), int(v.shape[1])], cube=cube, coverage=coverage, windows=len(order),
                load_seconds=round(load_s, 1), gen_seconds=round(gen_s, 1), peak_gb=round(torch.cuda.max_memory_allocated() / 2**30, 1))
    (out / 'generation_info.json').write_text(json.dumps(info, indent=1))
    print('DONE', json.dumps(info), flush=True)


if __name__ == '__main__':
    main()
