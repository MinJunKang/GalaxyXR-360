"""Static-camera perspective clip with Wan2.2-TI2V-5B (720p, 24 fps), used as CubeComposer input.
Segment 1: text-to-video, 121 frames. Further segments: image-to-video continued from the previous segment's last frame,
so N segments give 1 + 120*N frames (2 segments = 241 frames = 10.0 s @ 24 fps).
  pers_gen.py --prompt "..." --out OUT.mp4 [--segments 2] [--seed 0] [--steps 50]
"""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np
import torch

CC = Path('/workspace/code/pano_xr/CubeComposer'); sys.path.insert(0, str(CC))
from diffsynth.pipelines.wan_video_new import WanVideoPipeline  # noqa: E402
from diffsynth.utils import ModelConfig  # noqa: E402
from PIL import Image  # noqa: E402
from diffsynth.models.wan_video_dit import WanModel  # noqa: E402

_patchify = WanModel.patchify
def _plain_patchify(self, x, control_camera_latents_input=None, perspective_latents=None, **kw):
    # CubeComposer's model_fn passes perspective_latents (used only by its panorama DiT); plain Wan T2V/I2V ignores it
    assert perspective_latents is None
    return _patchify(self, x, control_camera_latents_input)
WanModel.patchify = _plain_patchify

BASE = '/workspace/code/pano_xr/model-cache'
NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，"
       "多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走，"
       "镜头移动，镜头晃动，摇镜头，变焦，文字，水印")   # + camera motion, pan, zoom, text, watermark
STYLE = ('Static tripod shot, the camera does not move. Wide-angle, photorealistic, highly detailed, natural colors, calm and peaceful atmosphere. ')


def load():
    mid = 'Wan-AI/Wan2.2-TI2V-5B'
    cfgs = [ModelConfig(model_id=mid, origin_file_pattern=p, local_model_path=BASE, skip_download=True) for p in
            ('diffusion_pytorch_model*.safetensors', 'models_t5_umt5-xxl-enc-bf16.pth', 'Wan2.2_VAE.pth')]
    tok = ModelConfig(model_id=mid, origin_file_pattern='google/*', local_model_path=BASE, skip_download=True)
    return WanVideoPipeline.from_pretrained(torch_dtype=torch.bfloat16, device='cuda', model_configs=cfgs, tokenizer_config=tok,
                                            redirect_common_files=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prompt', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--segments', type=int, default=2); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--steps', type=int, default=50); ap.add_argument('--cfg', type=float, default=5.0)
    ap.add_argument('--width', type=int, default=1280); ap.add_argument('--height', type=int, default=704)
    a = ap.parse_args()
    t0 = time.time(); pipe = load(); load_s = time.time() - t0
    prompt = STYLE + a.prompt
    frames, segs = [], []
    t0 = time.time()
    for k in range(a.segments):
        kw = dict(prompt=prompt, negative_prompt=NEG, seed=a.seed + k, height=a.height, width=a.width, num_frames=121,
                  num_inference_steps=a.steps, cfg_scale=a.cfg, tiled=True)
        if frames:
            kw['input_image'] = frames[-1]
        ts = time.time(); v = pipe(**kw); segs.append(round(time.time() - ts, 1))
        frames += v if not frames else v[1:]          # the I2V first frame repeats the previous last frame
    gen_s = time.time() - t0
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    import imageio
    w = imageio.get_writer(str(out), fps=24, codec='libx264', quality=None, ffmpeg_params=['-crf', '10', '-pix_fmt', 'yuv420p'])
    for f in frames:
        w.append_data(np.asarray(f))
    w.close()
    info = dict(prompt=prompt, seed=a.seed, segments=a.segments, frames=len(frames), fps=24, size=[a.width, a.height], steps=a.steps, cfg=a.cfg,
                load_seconds=round(load_s, 1), gen_seconds=round(gen_s, 1), seg_seconds=segs, peak_gb=round(torch.cuda.max_memory_allocated() / 2**30, 1))
    out.with_suffix('.json').write_text(json.dumps(info, indent=1))
    print('DONE', json.dumps(info), flush=True)


if __name__ == '__main__':
    main()
