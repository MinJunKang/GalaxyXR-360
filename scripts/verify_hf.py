"""Verify local snapshot files against HF LFS sha256; print BAD files. verify_hf.py REPO LOCAL_DIR [pattern...]"""
import hashlib, sys, fnmatch
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from huggingface_hub import HfApi
repo, d, pats = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
info = HfApi().model_info(repo, files_metadata=True)
todo = [(s.rfilename, s.lfs.sha256) for s in info.siblings if s.lfs and (not pats or any(fnmatch.fnmatch(s.rfilename, p) for p in pats))]
def chk(x):
    f, want = x; p = d / f
    if not p.exists(): return f, 'MISSING'
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 24), b''): h.update(b)
    return f, 'OK' if h.hexdigest() == want else 'BAD'
with ThreadPoolExecutor(6) as ex:
    for f, r in ex.map(chk, todo): print(r, f, flush=True)
