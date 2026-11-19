"""360 photos: DiT360 (FLUX.1-dev + DiT360 LoRA) at its trained 2048x1024, then
  8192x4096 app texture (Real-ESRGAN x4plus, wrap-padded tiles) and 12288x6144 GPano JPEG (Lanczos from the 8K) + thumbnail.
  photo_gen.py JOBS.json OUT_DIR   (JOBS: [{"name":..., "prompt":..., "seed":...}, ...]; skips names already done)
"""
import json, sys, time
from pathlib import Path
import numpy as np
import torch
from PIL import Image

ROOT = Path('/workspace/code/pano_xr'); sys.path.insert(0, str(ROOT / 'DiT360'))
STYLE = 'This is a panorama. The image shows '
SUFFIX = ', photorealistic, highly detailed, natural lighting, peaceful atmosphere.'


def xmp_gpano(w, h):
    x = (f'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
         f'<rdf:Description rdf:about="" xmlns:GPano="http://ns.google.com/photos/1.0/panorama/" GPano:UsePanoramaViewer="True" '
         f'GPano:ProjectionType="equirectangular" GPano:PoseHeadingDegrees="0" GPano:CroppedAreaLeftPixels="0" GPano:CroppedAreaTopPixels="0" '
         f'GPano:CroppedAreaImageWidthPixels="{w}" GPano:CroppedAreaImageHeightPixels="{h}" GPano:FullPanoWidthPixels="{w}" '
         f'GPano:FullPanoHeightPixels="{h}"/></rdf:RDF></x:xmpmeta>')
    return b'http://ns.adobe.com/xap/1.0/\x00' + x.encode()


def save_jpeg_gpano(img, path, quality):
    import io
    b = io.BytesIO(); img.save(b, 'JPEG', quality=quality, subsampling=0 if quality >= 95 else 2, optimize=True); j = b.getvalue()
    seg = xmp_gpano(*img.size); app1 = b'\xff\xe1' + (len(seg) + 2).to_bytes(2, 'big') + seg
    i = 2
    if j[2:4] == b'\xff\xe0':                                   # keep JFIF APP0 first
        i = 4 + int.from_bytes(j[4:6], 'big')
    Path(path).write_bytes(j[:i] + app1 + j[i:])


@torch.no_grad()
def esrgan_wrap(model, img, scale, tile=512, pad=32):
    x = torch.cat([img[..., -pad:], img, img[..., :pad]], -1)[None].half()
    _, _, h, w = x.shape
    out = torch.zeros((1, 3, h * scale, w * scale), device='cuda', dtype=torch.half)
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            ya, yb = max(0, y0 - pad), min(h, y0 + tile + pad); xa, xb = max(0, x0 - pad), min(w, x0 + tile + pad)
            r = model(x[..., ya:yb, xa:xb]); oy, ox = (y0 - ya) * scale, (x0 - xa) * scale
            hh, ww = (min(h, y0 + tile) - y0) * scale, (min(w, x0 + tile) - x0) * scale
            out[..., y0 * scale:y0 * scale + hh, x0 * scale:x0 * scale + ww] = r[..., oy:oy + hh, ox:ox + ww]
    return out[0, :, :, pad * scale:-pad * scale].float().clamp(0, 1)


def main():
    jobs, out = json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2])
    for d in ('raw', 'app8k', 'gpano12k', 'thumbs'):
        (out / d).mkdir(parents=True, exist_ok=True)
    todo = [j for j in jobs if not (out / 'gpano12k' / f"{j['name']}.jpg").exists()]
    if not todo:
        return print('NOTHING_TO_DO')
    from src.pipeline import DiT360Pipeline
    pipe = DiT360Pipeline.from_pretrained(str(ROOT / 'model-cache/FLUX.1-dev'), torch_dtype=torch.float16).to('cuda')
    pipe.load_lora_weights(str(ROOT / 'model-cache/DiT360'))
    from spandrel import ModelLoader
    sr = ModelLoader().load_from_file(str(ROOT / 'weights/RealESRGAN_x4plus.pth')).model.cuda().eval().half()
    for j in todo:
        t0 = time.time()
        img = pipe(STYLE + j['prompt'] + SUFFIX, width=2048, height=1024, num_inference_steps=j.get('steps', 28), guidance_scale=2.8,
                   generator=torch.Generator(device='cuda').manual_seed(j['seed'])).images[0]
        img.save(out / 'raw' / f"{j['name']}.png")
        t1 = time.time()
        x = torch.from_numpy(np.asarray(img.convert('RGB'))).cuda().permute(2, 0, 1).float() / 255
        up = esrgan_wrap(sr, x, 4)                                                       # 8192x4096
        a8 = Image.fromarray((up * 255 + 0.5).byte().permute(1, 2, 0).cpu().numpy())
        save_jpeg_gpano(a8, out / 'app8k' / f"{j['name']}.jpg", 92)
        save_jpeg_gpano(a8.resize((12288, 6144), Image.LANCZOS), out / 'gpano12k' / f"{j['name']}.jpg", 95)
        a8.resize((1024, 512), Image.LANCZOS).save(out / 'thumbs' / f"{j['name']}.jpg", quality=88)
        print('DONE', json.dumps(dict(name=j['name'], gen_s=round(t1 - t0, 1), post_s=round(time.time() - t1, 1))), flush=True)


if __name__ == '__main__':
    main()
