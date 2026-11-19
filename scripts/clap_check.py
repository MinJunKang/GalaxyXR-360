"""CLAP class check of a generated sound against a fixed set of everyday sound classes.
Fails when any forbidden class (mapped from the item's negative words) gets > LIMIT of the probability mass.
  clap_check.py AUDIO.wav "forbidden words, comma separated"  -> JSON {top, forbidden, worst, worst_p, ok}"""
import json, sys
import torch, torchaudio
from transformers import ClapModel, ClapProcessor
M = '/workspace/code/pano_xr/model-cache/larger_clap_general'; LIMIT = 0.15
CLASSES = ['birds chirping', 'flowing water stream', 'rain', 'wind blowing', 'leaves rustling', 'bamboo knocking', 'insects buzzing',
           'fire crackling', 'ocean waves', 'bell ringing', 'people talking', 'traffic noise', 'thunder', 'music', 'underwater bubbles',
           'animal calls', 'electronic hum', 'silence']
MAP = {'water': 'flowing water stream', 'stream': 'flowing water stream', 'river': 'flowing water stream', 'rain': 'rain',
       'birds': 'birds chirping', 'birdsong': 'birds chirping', 'traffic': 'traffic noise', 'cars': 'traffic noise', 'thunder': 'thunder',
       'music': 'music', 'speech': 'people talking', 'voices': 'people talking', 'waves': 'ocean waves', 'waves crashing': 'ocean waves', 'wind': 'wind blowing'}
wav, forb_words = sys.argv[1], [w.strip() for w in sys.argv[2].split(',')]
forb = sorted({MAP[w] for w in forb_words if w in MAP})
a, sr = torchaudio.load(wav); a = a.mean(0)
if sr != 48000: a = torchaudio.functional.resample(a, sr, 48000)
model = ClapModel.from_pretrained(M).eval(); proc = ClapProcessor.from_pretrained(M)
with torch.no_grad():
    p = model(**proc(text=CLASSES, audios=[a.numpy()], sampling_rate=48000, return_tensors='pt', padding=True)).logits_per_audio.softmax(-1)[0].tolist()
d = dict(zip(CLASSES, p))
worst = max(forb, key=lambda c: d[c]) if forb else None
res = dict(top=[(c, round(v, 2)) for c, v in sorted(d.items(), key=lambda x: -x[1])[:3]], forbidden=forb, worst=worst,
           worst_p=round(d[worst], 3) if worst else 0.0)
res['ok'] = res['worst_p'] <= LIMIT
print(json.dumps(res))
