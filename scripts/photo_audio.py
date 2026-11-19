"""Ambience for 360 photos: still clip of the photo's source image (12 s) -> HunyuanVideo-Foley with the theme sound prompt
-> seamless loop (last 1 s cross-faded into the start, 11 s) -> stereo 48 kHz, -20 LUFS -> AAC .m4a for the app.
  photo_audio.py NAME[,NAME...] OUT_DIR   (source image: out/photo_src/<name>_1280x720.png unless --src_dir)"""
import os, subprocess, sys
from pathlib import Path
ROOT = Path('/workspace/code/pano_xr'); sys.path.insert(0, str(ROOT / 'content'))
import sounds, photo_sounds, json
names, out = sys.argv[1].split(','), Path(sys.argv[2]).resolve(); out.mkdir(parents=True, exist_ok=True)
src_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / 'out/photo_src'
py = str(ROOT / 'env_foley/bin/python')
for n in names:
    final = out / f'{n}.m4a'
    if final.exists():
        continue
    still = out / f'{n}_still.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', str(src_dir / f'{n}_1280x720.png'), '-t', '12', '-r', '16',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(still)], check=True)
    main, forbid = photo_sounds.P[n]
    p, neg = main + sounds.QUAL, sounds.NEG + ', ' + forbid
    best = None
    for seed in (1, 7, 23, 51):                 # regenerate until CLAP finds no forbidden sound class (> 15 %)
        subprocess.run([py, str(ROOT / 'scripts/run_foley.py'), str(still), p, str(out), '--neg_prompt', neg, '--audio_length', '12',
                        '--guidance_scale', '6.0'], check=True, env=dict(os.environ, HF_HUB_OFFLINE='1', FOLEY_SEED=str(seed)),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        gen = out / f'{n}_still_generated.wav'
        if not gen.exists(): raise SystemExit('foley produced no audio for ' + n)
        r = json.loads(subprocess.run([py, str(ROOT / 'scripts/clap_check.py'), str(gen), forbid], capture_output=True, text=True,
                                      env=dict(os.environ, CUDA_VISIBLE_DEVICES='')).stdout.strip().splitlines()[-1])
        cand = out / f'{n}_seed{seed}.wav'; gen.rename(cand)
        print('TRY', n, seed, json.dumps(r), flush=True)
        if best is None or r['worst_p'] < best[1]['worst_p']: best = (cand, r)
        if r['ok']: break
    (out / f'{n}.clap.json').write_text(json.dumps(dict(prompt=p, negative=neg, chosen=best[0].name, **best[1])))
    wav = out / f'{n}_still_generated.wav'; best[0].rename(wav)
    # seamless loop: out = a[1:12] with its first second cross-faded with a[0:1] taken from the tail mix
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-filter_complex',
                    "[0:a]asplit=3[s1][s2][s3];[s1]atrim=0:1,asetpts=PTS-STARTPTS[head];[s2]atrim=1:11,asetpts=PTS-STARTPTS[b0];[s3]atrim=11:12,asetpts=PTS-STARTPTS[tail];[tail][head]acrossfade=d=1:c1=tri:c2=tri[x];[x][b0]concat=n=2:v=0:a=1,pan=stereo|c0=c0|c1=c0,aecho=0.8:0.7:18|23:0.15|0.12,loudnorm=I=-20:TP=-2,aresample=48000",
                    '-c:a', 'aac', '-b:a', '256k', str(final)], check=True)
    still.unlink(missing_ok=True)
    print('AUDIO', n, flush=True)
