"""Static-camera perspective clip with Wan2.2-I2V-A14B (MoE: high-noise + low-noise expert), first frame from FLUX 3.
Official i2v_A14B settings: 16 fps, 81 frames/segment, 40 steps, shift 5.0, boundary 0.900, guidance 3.5.
Segment 1 starts from the FLUX 3 image; segment k>1 starts from the previous segment's last frame (1 + 80*N frames;
2 segments = 161 frames = 10.06 s @ 16 fps). On a 48 GB A6000 both experts do not fit: diffsynth VRAM management keeps
weights in CPU RAM and streams them (vram_limit), so expect ~60-70 GB host RAM per process.
  pers_gen_a14b.py --image first.png --prompt "..." --out OUT.mp4 [--segments 2] [--seed 0] [--steps 40] [--vram_gb 40]
"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np
import torch

CC = Path('/workspace/code/pano_xr/CubeComposer'); sys.path.insert(0, str(CC))
from diffsynth.pipelines.wan_video_new import WanVideoPipeline  # noqa: E402
from diffsynth.utils import ModelConfig  # noqa: E402
from diffsynth.models.wan_video_dit import WanModel  # noqa: E402
from PIL import Image  # noqa: E402

_patchify = WanModel.patchify
def _plain_patchify(self, x, control_camera_latents_input=None, perspective_latents=None, **kw):
    assert perspective_latents is None   # CubeComposer-only argument; plain Wan ignores it
    return _patchify(self, x, control_camera_latents_input)
WanModel.patchify = _plain_patchify

BASE = '/workspace/code/pano_xr/model-cache'
NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，"
       "多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走，"
       "镜头移动，镜头晃动，摇镜头，变焦，文字，水印")
STYLE = 'Static tripod shot, the camera does not move at all. Photorealistic, highly detailed, natural colors, calm and peaceful atmosphere. '


def load(vram_gb):
    mid = 'Wan-AI/Wan2.2-I2V-A14B'
    cfgs = [ModelConfig(model_id=mid, origin_file_pattern=p, local_model_path=BASE, skip_download=True, offload_device='cpu') for p in
            ('high_noise_model/diffusion_pytorch_model*.safetensors', 'low_noise_model/diffusion_pytorch_model*.safetensors',
             'models_t5_umt5-xxl-enc-bf16.pth', 'Wan2.1_VAE.pth')]
    tok = ModelConfig(model_id=mid, origin_file_pattern='google/*', local_model_path=BASE, skip_download=True)
    pipe = WanVideoPipeline.from_pretrained(torch_dtype=torch.bfloat16, device='cuda', model_configs=cfgs, tokenizer_config=tok,
                                            redirect_common_files=False)
    pipe.enable_vram_management(vram_limit=vram_gb)
    return pipe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', required=True); ap.add_argument('--prompt', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--segments', type=int, default=2); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--steps', type=int, default=40); ap.add_argument('--cfg', type=float, default=3.5)
    ap.add_argument('--width', type=int, default=1280); ap.add_argument('--height', type=int, default=720)
    ap.add_argument('--vram_gb', type=float, default=40.0)
    a = ap.parse_args()
    t0 = time.time(); pipe = load(a.vram_gb); load_s = time.time() - t0
    first = Image.open(a.image).convert('RGB').resize((a.width, a.height), Image.LANCZOS)
    prompt = STYLE + a.prompt
    frames, segs = [], []
    for k in range(a.segments):
        ts = time.time()
        v = pipe(prompt=prompt, negative_prompt=NEG, input_image=first if not frames else frames[-1], seed=a.seed + k,
                 height=a.height, width=a.width, num_frames=81, num_inference_steps=a.steps, cfg_scale=a.cfg,
                 sigma_shift=5.0, switch_DiT_boundary=0.900, tiled=True)
        segs.append(round(time.time() - ts, 1))
        frames += v if not frames else v[1:]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    import imageio
    w = imageio.get_writer(str(out), fps=16, codec='libx264', ffmpeg_params=['-crf', '10', '-pix_fmt', 'yuv420p'])
    for f in frames:
        w.append_data(np.asarray(f))
    w.close()
    info = dict(prompt=prompt, image=a.image, seed=a.seed, segments=a.segments, frames=len(frames), fps=16, size=[a.width, a.height],
                steps=a.steps, cfg=a.cfg, load_seconds=round(load_s, 1), seg_seconds=segs,
                peak_gpu_gb=round(torch.cuda.max_memory_allocated() / 2**30, 1))
    out.with_suffix('.json').write_text(json.dumps(info, indent=1))
    print('DONE', json.dumps(info), flush=True)


if __name__ == '__main__':
    main()
