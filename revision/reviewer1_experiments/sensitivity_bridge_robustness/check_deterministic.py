"""Independent direct-solve audit; does not import run_deterministic."""
import ast
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "deterministic_reanalysis01"

def read(name):
    with (OUT/name).open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    start=time.perf_counter()
    protocol=json.loads((ROOT/"deterministic_protocol.json").read_text())
    run=json.loads((OUT/"run_manifest.json").read_text())
    assert sha(ROOT/"deterministic_protocol.json")==run["protocol_sha256"]
    assert sha(protocol["input_designs"])==protocol["input_designs_sha256"]==sha(OUT/"input_designs.json")
    assert sha(protocol["archived_records"])==protocol["archived_records_sha256"]
    for name,digest in run["output_sha256"].items():
        assert sha(OUT/name)==digest
    designs=json.loads((OUT/"input_designs.json").read_text())
    assert [d["replicate"] for d in designs]==list(range(200))
    subsets=read("subset_scores.csv")
    methods=read("method_results.csv")
    steps=read("greedy_steps.csv")
    candidates=read("greedy_candidate_scores.csv")
    assert len(subsets)==200*(12+66+495) and len(methods)==200*3*4
    subset_groups={}
    for r in subsets:
        subset_groups.setdefault((int(r["replicate"]),int(r["budget"])),[]).append(r)
    method_groups={(int(r["replicate"]),int(r["budget"]),r["method"]):r for r in methods}
    candidate_groups={}
    for r in candidates:
        candidate_groups.setdefault((int(r["replicate"]),r["method"],int(r["stage"])),[]).append(r)
    errors={k:0.0 for k in ["subset_variance","subset_information","subset_condition","greedy_covariance","rank_one_variance_gain","candidate_target_gain","candidate_information_gain","method_variance","archived_metric"]}
    def check(label,actual,expected,tol=1e-8):
        err=float(np.max(np.abs(np.asarray(actual)-np.asarray(expected))))
        errors[label]=max(errors[label],err)
        assert np.allclose(actual,expected,rtol=tol,atol=tol),(label,actual,expected,err)
    checked_extrema=0
    for d in designs:
        rid=d["replicate"]
        P=np.array(d["prior"]); X=np.array(d["design"]); sig=np.array(d["sigma"]); t=np.array(d["target"])
        I=np.eye(len(t))
        Pprec=np.linalg.solve(P,I)
        logdet0=np.linalg.slogdet(P)[1]
        def cov(selected):
            if not selected:
                return P.copy()
            A=X[list(selected)]/sig[list(selected),None]
            return np.linalg.solve(Pprec+A.T@A,I)
        for B in [1,2,4]:
            group=subset_groups[(rid,B)]
            got=[tuple(json.loads(r["selected"])) for r in group]
            expected=list(itertools.combinations(range(12),B))
            assert got==expected and len(set(got))==math.comb(12,B)
            variance=[]; information=[]; conditions=[]
            for r,selected in zip(group,expected):
                V=cov(selected)
                W=float(t@V@t)
                info=.5*(logdet0-np.linalg.slogdet(V)[1])
                condition=float(np.linalg.eigvalsh(V)[-1]/np.linalg.eigvalsh(V)[0])
                check("subset_variance",float(r["target_variance"]),W)
                check("subset_information",float(r["information"]),info)
                check("subset_condition",float(r["condition"]),condition)
                variance.append(W); information.append(info); conditions.append(condition)
            target=method_groups[(rid,B,"target_variance_exhaustive")]
            infoopt=method_groups[(rid,B,"logdet_exhaustive")]
            assert tuple(json.loads(target["selected"]))==expected[int(np.argmin(variance))]
            assert tuple(json.loads(infoopt["selected"]))==expected[int(np.argmax(information))]
            checked_extrema+=2
            for method in protocol["comparators"]:
                r=method_groups[(rid,B,method)]
                V=cov(json.loads(r["selected"]))
                check("method_variance",float(r["target_variance"]),float(t@V@t))
                assert abs(float(r["all_subset_kappa"])-max(conditions))<1e-6
                assert float(r["radius_over_target_optimum"])>=1-1e-9
            if B==1:
                assert abs(float(method_groups[(rid,B,"target_variance_greedy")]["radius_over_target_optimum"])-1)<1e-9
    for r in steps:
        rid=int(r["replicate"]); d=designs[rid]
        P=np.array(d["prior"]); X=np.array(d["design"]); sig=np.array(d["sigma"]); t=np.array(d["target"])
        I=np.eye(len(t)); p0=np.linalg.solve(P,I)
        chosen=json.loads(r["selected"]); prefix=chosen[:-1]; b=chosen[-1]
        def direct(selected):
            if not selected: return P.copy()
            A=X[selected]/sig[selected,None]
            return np.linalg.solve(p0+A.T@A,I)
        Vprev=direct(prefix); Vnext=direct(chosen)
        check("greedy_covariance",np.array(json.loads(r["covariance"])),Vnext)
        check("rank_one_variance_gain",float(r["rank_one_gain"]),float(t@Vprev@t-t@Vnext@t))
        group=candidate_groups[(rid,r["method"],int(r["stage"]))]
        assert sorted(int(s["candidate"]) for s in group)==[i for i in range(12) if i not in prefix]
        scores={}
        for s in group:
            b2=int(s["candidate"])
            assert json.loads(s["prefix"])==prefix
            Vcandidate=direct(prefix+[b2])
            target_gain=float(t@Vprev@t-t@Vcandidate@t)
            info_gain=.5*(np.linalg.slogdet(Vprev)[1]-np.linalg.slogdet(Vcandidate)[1])
            check("candidate_target_gain",float(s["target_variance_gain"]),target_gain)
            check("candidate_information_gain",float(s["information_gain"]),info_gain)
            scores[b2]=target_gain if r["method"]=="target_variance_greedy" else info_gain
        assert scores[b]>=max(scores.values())-1e-10
    with Path(protocol["archived_records"]).open(newline="",encoding="utf-8") as f:
        archived=list(csv.DictReader(f))
    mapping={"greedy":"logdet_greedy","logdet_optimum":"logdet_exhaustive","target_optimum":"target_variance_exhaustive"}
    n_old=0
    for old in archived:
        if old["method"] not in mapping: continue
        r=method_groups[(int(old["replicate"]),4,mapping[old["method"]])]
        assert set(ast.literal_eval(old["selected"]))==set(json.loads(r["selected"]))
        for key in ["information","target_radius","condition","all_subset_kappa"]:
            check("archived_metric",float(r[key]),float(old[key]))
        n_old+=1
    assert n_old==600
    result=dict(status="passed",code_sha256=sha(__file__),protocol_sha256=sha(ROOT/"deterministic_protocol.json"),run_manifest_sha256=sha(OUT/"run_manifest.json"),elapsed_seconds=time.perf_counter()-start,designs=200,subsets_checked=len(subsets),method_rows_checked=len(methods),greedy_steps_checked=len(steps),candidate_scores_checked=len(candidates),exhaustive_extrema_checked=checked_extrema,archived_rows_reproduced=n_old,max_absolute_discrepancies=errors,no_sampling=True,notes="No experiment implementation imported. Independent solve-based covariance and direct objective differences audit rank-one implementation and exhaustive extrema. Numeric tolerance1e-8 absolute/relative; choice tolerance1e-10. All200 designs retained; no scientific theorem follows from this audit.")
    (OUT/"independent_audit.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
