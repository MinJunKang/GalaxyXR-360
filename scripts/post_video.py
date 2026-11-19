"""360 ERP frames (CubeComposer PNGs, any source fps) -> Galaxy XR deliverable.
  1. retime to --fps (30) with RIFE 4.25 (Practical-RIFE, official weights), horizontally wrap-padded so the 0/360 seam
     is interpolated with real neighbours
  2. seamless loop: the last X output frames cross-fade into the first X (length N - X)
  3. upscale to 7680x3840: Real-ESRGAN x2plus (tiled, wrap-padded), then Lanczos to the exact size (3K input) — or lanczos only
  4. HEVC Main, high tier, level 6.0, VBR --bitrate (100 Mb/s, max 150), 1 s closed GOP, BT.709 (hevc_nvenc), optional audio
  5. Spherical Video V1 metadata (google spatial-media), equirectangular mono (+ spatial audio flag when --audio is ambiX FOA)
  6. thumbnail 1024x512
  post_video.py FRAMES_DIR OUT.mp4 --src_fps 12 [--fps 30] [--xfade 15] [--upscale esrgan|lanczos] [--bitrate 100] [--audio foa.wav]
"""
import argparse, json, subprocess, sys, time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

W8, H8 = 7680, 3840
ROOT = Path('/workspace/code/pano_xr')


def load_esrgan():
    from spandrel import ModelLoader
    return ModelLoader().load_from_file(str(ROOT / 'weights/RealESRGAN_x2plus.pth')).model.cuda().eval().half()


def load_rife():
    sys.path.insert(0, str(ROOT / 'Practical-RIFE')); sys.path.insert(0, str(ROOT / 'weights/rife425'))
    from train_log.RIFE_HDv3 import Model
    m = Model(); m.load_model(str(ROOT / 'weights/rife425/train_log'), -1); m.eval(); m.device()
    return m


@torch.no_grad()
def rife_mid(model, a, b, t, scale, pad=64):
    """a, b: 3,H,W float cuda in [0,1] -> frame at time t in (0,1); wrap-pad horizontally, pad to a multiple of 128/scale."""
    x0 = torch.cat([a[..., -pad:], a, a[..., :pad]], -1)[None]; x1 = torch.cat([b[..., -pad:], b, b[..., :pad]], -1)[None]
    h, w = x0.shape[-2:]; m = max(128, int(128 / scale)); ph, pw = (h - 1) // m * m + m, (w - 1) // m * m + m
    x0 = F.pad(x0, (0, pw - w, 0, ph - h)); x1 = F.pad(x1, (0, pw - w, 0, ph - h))
    out = model.inference(x0, x1, timestep=t, scale=scale)
    return out[0, :, :h, pad:w - pad].clamp(0, 1)


@torch.no_grad()
def esrgan_wrap(model, img, tile=960, pad=32):
    x = torch.cat([img[..., -pad:], img, img[..., :pad]], -1)[None].half()
    _, _, h, w = x.shape
    out = torch.zeros((1, 3, h * 2, w * 2), device='cuda', dtype=torch.half)
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            ya, yb = max(0, y0 - pad), min(h, y0 + tile + pad); xa, xb = max(0, x0 - pad), min(w, x0 + tile + pad)
            r = model(x[..., ya:yb, xa:xb])
            oy, ox = (y0 - ya) * 2, (x0 - xa) * 2
            hh, ww = (min(h, y0 + tile) - y0) * 2, (min(w, x0 + tile) - x0) * 2
            out[..., y0 * 2:y0 * 2 + hh, x0 * 2:x0 * 2 + ww] = r[..., oy:oy + hh, ox:ox + ww]
    return out[0, :, :, pad * 2:-pad * 2].float().clamp(0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('frames'); ap.add_argument('out'); ap.add_argument('--src_fps', type=float, required=True)
    ap.add_argument('--fps', type=int, default=30); ap.add_argument('--xfade', type=int, default=15)
    ap.add_argument('--upscale', default='esrgan', choices=['esrgan', 'lanczos']); ap.add_argument('--bitrate', type=int, default=100)
    ap.add_argument('--audio', default=''); ap.add_argument('--rife_scale', type=float, default=0.5)
    a = ap.parse_args()
    fr = sorted(Path(a.frames).glob('*.png')); N = len(fr)
    dur = (N - 1) / a.src_fps                                   # seconds spanned by the source frames
    M = int(round(dur * a.fps)) + 1                             # output frames before looping
    X = a.xfade; assert M > 2 * X, (M, X)
    out = Path(a.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True); tmp = out.with_suffix('.noMeta.mp4')
    load = lambda i: torch.from_numpy(np.array(Image.open(fr[i]).convert('RGB'))).cuda().permute(2, 0, 1).float() / 255  # noqa: E731
    rife = load_rife() if abs(a.src_fps - a.fps) > 1e-6 else None
    sr = load_esrgan() if a.upscale == 'esrgan' else None
    cache = {}
    def src(i):
        if i not in cache:
            if len(cache) > 4: cache.pop(min(cache))
            cache[i] = load(i)
        return cache[i]
    def frame(k):                                               # output frame k (0..M-1) at time k / fps
        s = k / a.fps * a.src_fps; i = int(np.floor(s)); t = s - i
        if i >= N - 1: return src(N - 1)
        if t < 1e-3 or rife is None: return src(i)
        if t > 1 - 1e-3: return src(i + 1)
        return rife_mid(rife, src(i), src(i + 1), float(t), a.rife_scale)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W8}x{H8}', '-r', str(a.fps), '-i', '-']
    if a.audio: cmd += ['-i', a.audio]
    cmd += ['-map', '0:v'] + (['-map', '1:a', '-c:a', 'aac', '-b:a', '384k', '-shortest'] if a.audio else [])
    xp = (f'level-idc=6.0:high-tier=1:vbv-maxrate={int(a.bitrate * 1500)}:vbv-bufsize={a.bitrate * 2000}:keyint={a.fps}:min-keyint={a.fps}:'
          'bframes=0:open-gop=0:colorprim=bt709:transfer=bt709:colormatrix=bt709:range=limited:pools=24')
    cmd += ['-c:v', 'libx265', '-preset', 'medium', '-b:v', f'{a.bitrate}M', '-x265-params', xp, '-profile:v', 'main',
            '-pix_fmt', 'yuv420p', '-tag:v', 'hvc1', '-movflags', '+faststart', str(tmp)]   # no NVENC library in this container
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time(); thumb = None
    with torch.no_grad():
        for k in range(M - X):
            img = frame(k)
            if k < X:
                w = (k + 1) / (X + 1); img = w * img + (1 - w) * frame(M - X + k)
            up = esrgan_wrap(sr, img) if sr is not None else img
            if up.shape[-2:] != (H8, W8):
                up = F.interpolate(up[None], size=(H8, W8), mode='bicubic', align_corners=False, antialias=True)[0].clamp(0, 1)
            arr = (up * 255 + 0.5).byte().permute(1, 2, 0).contiguous().cpu().numpy()
            enc.stdin.write(arr.tobytes())
            if k == (M - X) // 2: thumb = Image.fromarray(arr).resize((1024, 512), Image.LANCZOS)
    enc.stdin.close(); assert enc.wait() == 0
    inj = [sys.executable, '-m', 'spatialmedia', '-i'] + (['--spatial-audio'] if a.audio else []) + [str(tmp), str(out)]
    subprocess.run(inj, cwd=ROOT / 'spatial-media', check=True, stdout=subprocess.DEVNULL)
    assert out.exists() and out.stat().st_size > 0.9 * tmp.stat().st_size, 'spatial metadata injection did not write the output; keeping ' + str(tmp)
    tmp.unlink(); thumb.save(out.with_suffix('.thumb.jpg'), quality=88)
    info = dict(src=str(a.frames), frames_in=N, src_fps=a.src_fps, frames_out=M - X, fps=a.fps, seconds=round((M - X) / a.fps, 2),
                size=[W8, H8], upscale=a.upscale, interp='rife4.25' if rife else None, bitrate_mbps=a.bitrate, audio=a.audio or None,
                bytes=out.stat().st_size, wall_s=round(time.time() - t0, 1))
    out.with_suffix('.post.json').write_text(json.dumps(info, indent=1)); print('DONE', json.dumps(info), flush=True)


if __name__ == '__main__':
    main()
