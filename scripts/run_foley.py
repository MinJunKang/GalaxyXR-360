"""Run HunyuanVideo-Foley (video + text -> 48 kHz audio) with local weights, no network.
  run_foley.py VIDEO TEXT OUT_DIR [extra infer.py args...]"""
import os, sys
from pathlib import Path
ROOT = Path('/workspace/code/pano_xr'); MC = ROOT / 'model-cache'
LOCAL = {'google/siglip2-base-patch16-512': str(MC / 'siglip2-base-patch16-512'), 'laion/larger_clap_general': str(MC / 'larger_clap_general')}
import transformers
for cls in (transformers.AutoModel, transformers.AutoTokenizer, transformers.AutoProcessor, transformers.ClapTextModelWithProjection):
    orig = cls.from_pretrained.__func__
    def patched(c, name, *a, _o=orig, **k):
        return _o(c, LOCAL.get(name, name), *a, **k)
    cls.from_pretrained = classmethod(patched)
video, text, out = os.path.abspath(sys.argv[1]), sys.argv[2], os.path.abspath(sys.argv[3])
os.chdir(ROOT / 'HunyuanVideo-Foley'); sys.path.insert(0, str(ROOT / 'HunyuanVideo-Foley'))
sys.argv = ['infer.py', '--model_path', str(MC / 'HunyuanVideo-Foley'), '--single_video', video, '--single_prompt', text,
            '--output_dir', out] + sys.argv[4:]
seed = int(os.environ.get('FOLEY_SEED', '1'))
src = open('infer.py').read().replace('set_manual_seed(1)', f'set_manual_seed({seed})')
code = compile(src, str(ROOT / 'HunyuanVideo-Foley' / 'infer.py'), 'exec')
exec(code, {'__name__': '__main__', '__file__': str(ROOT / 'HunyuanVideo-Foley' / 'infer.py')})
