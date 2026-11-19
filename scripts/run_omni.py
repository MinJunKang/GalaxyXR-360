"""Run OmniAudio (360 video -> first-order ambisonics, 44.1 kHz, 10 s) with local weights.
  run_omni.py VIDEO.mp4 OUT_DIR [--seed 42]
Maps the HF ids used inside OmniAudio to the verified local copies (no network)."""
import os, sys, runpy
from pathlib import Path
ROOT = Path('/workspace/code/pano_xr'); MC = ROOT / 'model-cache'
LOCAL = {'facebook/metaclip-h14-fullcc2.5b': str(MC / 'metaclip-h14-fullcc2.5b')}
import transformers
for cls in (transformers.AutoProcessor, transformers.AutoModel, transformers.AutoTokenizer, transformers.AutoImageProcessor):
    orig = cls.from_pretrained.__func__
    def patched(c, name, *a, _o=orig, **k):
        name = LOCAL.get(name, name)
        if isinstance(name, str) and name.startswith('useful_ckpts/'):
            name = LOCAL.get('facebook/' + name.split('/', 1)[1], name)
        return _o(c, name, *a, **k)
    cls.from_pretrained = classmethod(patched)
video, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.chdir(ROOT / 'OmniAudio'); sys.path.insert(0, str(ROOT / 'OmniAudio'))
sys.argv = ['inference.py', '--base-dir', video, '--infer-type', 'v2a', '--model-config', 'configs/v2a_foa.json',
            '--ckpt-path', str(MC / 'OmniAudio360V2SA' / 'model.ckpt'), '--dirname', out, '--mode', 'eqfov'] + sys.argv[3:]
runpy.run_path('inference.py', run_name='__main__')
