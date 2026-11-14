"""Independently verify all recorded Wilson MC intervals against SciPy."""
from pathlib import Path
import csv,json
from scipy.stats import binomtest

root=Path(__file__).resolve().parent
rows=list(csv.DictReader((root/'full'/'summary.csv').open()))
checked=0;max_error=0.
for r in rows:
    n=int(r['worlds']);nr=int(r['releases']);bad=int(r['bad_releases'])
    for name,v,den in [('coverage',int(r['coverage_n']),n),('release',nr,n),('refusal',n-nr,n),
                       ('bad_release_probability',bad,n),('selective_risk',bad,nr),
                       ('conditional_coverage',int(r['conditional_coverage_n']),nr)]:
        if not den:
            assert r[name]==r[name+'_lo']==r[name+'_hi']==''
            continue
        ci=binomtest(v,den).proportion_ci(confidence_level=.95,method='wilson')
        error=max(abs(ci.low-float(r[name+'_lo'])),abs(ci.high-float(r[name+'_hi'])))
        max_error=max(max_error,error);assert error<2e-12
        checked+=1
for r in csv.DictReader((root/'paired_discordance.csv').open()):
    for name in ['left_release_right_refuse','right_release_left_refuse']:
        ci=binomtest(int(r[name+'_n']),int(r['worlds'])).proportion_ci(confidence_level=.95,method='wilson')
        error=max(abs(ci.low-float(r[name+'_lo'])),abs(ci.high-float(r[name+'_hi'])))
        max_error=max(max_error,error);assert error<2e-12
        checked+=1
out=dict(passed=True,wilson_intervals_verified_against_scipy=checked,max_error=max_error)
(root/'interval_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
