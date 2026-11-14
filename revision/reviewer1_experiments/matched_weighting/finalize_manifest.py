"""Finalize hashes after independent verification and report authoring."""
from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent
m=json.loads((W/'manifest.json').read_text())
m['output_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in W.iterdir() if p.is_file() and p.name!='manifest.json'}
m['finalized_after_independent_verification']=True
(W/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print('Finalized manifest for',len(m['output_sha256']),'artifacts')
