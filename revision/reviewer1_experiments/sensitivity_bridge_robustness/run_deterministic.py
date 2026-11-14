"""Frozen deterministic saved-design optimization; no stochastic draws."""
import csv
import hashlib
import itertools
import json
from pathlib import Path
import platform
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
PROTO = ROOT / "deterministic_protocol.json"
OUT = ROOT / "deterministic_reanalysis01"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def metrics(P, V, t):
    W = float(t @ V @ t)
    return W, 1.96*np.sqrt(W), .5*(np.linalg.slogdet(P)[1]-np.linalg.slogdet(V)[1]), float(np.linalg.cond(V))

def main():
    start = time.perf_counter()
    protocol = json.loads(PROTO.read_text())
    for field in ["input_designs", "archived_records"]:
        assert sha(protocol[field]) == protocol[field + "_sha256"]
    designs = json.loads(Path(protocol["input_designs"]).read_text())
    assert [d["replicate"] for d in designs] == list(range(200))
    OUT.mkdir(exist_ok=False)
    (OUT / "input_designs.json").write_bytes(Path(protocol["input_designs"]).read_bytes())
    subset_rows, method_rows, candidate_rows, step_rows = [], [], [], []
    for d in designs:
        rid = d["replicate"]
        P, X, sig, t = (np.asarray(d[k], float) for k in ["prior", "design", "sigma", "target"])
        assert P.shape == (6, 6) and X.shape == (12, 6)
        prec0 = np.linalg.inv(P)
        paths = {}
        relevance = np.abs(X @ P @ t) / np.sqrt((t@P@t)*np.einsum("ij,jk,ik->i",X,P,X))
        for method in ["target_variance_greedy", "logdet_greedy"]:
            V = P.copy()
            chosen = []
            paths[method] = {}
            for stage in range(1,5):
                scores = []
                for b,x in enumerate(X):
                    if b in chosen:
                        scores.append(-np.inf)
                        continue
                    den = float(sig[b]**2+x@V@x)
                    target_gain = float((t@V@x)**2/den)
                    info_gain = float(.5*np.log1p((x@V@x)/sig[b]**2))
                    score = target_gain if method == "target_variance_greedy" else info_gain
                    scores.append(score)
                    candidate_rows.append(dict(replicate=rid,method=method,stage=stage,prefix=json.dumps(chosen),candidate=b,target_variance_gain=target_gain,information_gain=info_gain,prior_target_correlation=float(relevance[b])))
                best = int(np.argmax(scores))
                x = X[best]
                before = float(t@V@t)
                den = float(sig[best]**2+x@V@x)
                gain = float((t@V@x)**2/den)
                V = V-np.outer(V@x,V@x)/den
                chosen.append(best)
                step_rows.append(dict(replicate=rid,method=method,stage=stage,selected=json.dumps(chosen),chosen=best,variance_before=before,rank_one_gain=gain,variance_after=float(t@V@t),covariance=json.dumps(V.tolist())))
                if stage in protocol["budgets"]:
                    paths[method][stage] = (tuple(chosen),V.copy())
        for B in protocol["budgets"]:
            cases = []
            for subset in itertools.combinations(range(12),B):
                precision = prec0.copy()
                for b in subset:
                    precision += np.outer(X[b],X[b])/sig[b]**2
                V = np.linalg.inv(precision)
                W,radius,information,condition = metrics(P,V,t)
                cases.append((subset,V,W,radius,information,condition))
                subset_rows.append(dict(replicate=rid,budget=B,selected=json.dumps(subset),target_variance=W,target_radius=radius,information=information,condition=condition))
            best_target = min(cases,key=lambda row:row[2])
            best_info = max(cases,key=lambda row:row[4])
            kappa = max(row[5] for row in cases)
            selected_methods = [(method,*paths[method][B]) for method in paths]
            selected_methods.extend([("target_variance_exhaustive",best_target[0],best_target[1]),("logdet_exhaustive",best_info[0],best_info[1])])
            for method,chosen,V in selected_methods:
                W,radius,information,condition = metrics(P,V,t)
                method_rows.append(dict(replicate=rid,budget=B,method=method,selected=json.dumps(chosen),target_variance=W,target_radius=radius,information=information,condition=condition,all_subset_kappa=kappa,prior_condition=float(np.linalg.cond(P)),radius_over_target_optimum=radius/best_target[3],variance_over_target_optimum=W/best_target[2],information_over_logdet_optimum=information/best_info[4],max_prior_target_correlation=float(np.max(relevance)),first_choice_prior_target_correlation=float(relevance[chosen[0]]) if "greedy" in method else ""))
    write_csv(OUT / "subset_scores.csv",subset_rows)
    write_csv(OUT / "method_results.csv",method_rows)
    write_csv(OUT / "greedy_candidate_scores.csv",candidate_rows)
    write_csv(OUT / "greedy_steps.csv",step_rows)
    summaries = []
    for B in protocol["budgets"]:
        for method in protocol["comparators"]:
            rs = [r for r in method_rows if r["budget"] == B and r["method"] == method]
            for stratum in ["all","[0,25)","[25,50)","[50,100)","[100,inf)"]:
                edges = {"[0,25)":(0,25),"[25,50)":(25,50),"[50,100)":(50,100),"[100,inf)":(100,np.inf)}
                sr = rs if stratum == "all" else [r for r in rs if edges[stratum][0]<=r["all_subset_kappa"]<edges[stratum][1]]
                if not sr:
                    continue
                a = np.array([r["radius_over_target_optimum"] for r in sr])
                summaries.append(dict(budget=B,method=method,condition_stratum=stratum,n_designs=len(sr),mean_radius_ratio=float(a.mean()),min_radius_ratio=float(a.min()),q10_radius_ratio=float(np.quantile(a,.1)),median_radius_ratio=float(np.median(a)),q90_radius_ratio=float(np.quantile(a,.9)),max_radius_ratio=float(a.max()),target_optimal_count=int(np.sum(a<=1+1e-9)),mean_information_ratio=float(np.mean([r["information_over_logdet_optimum"] for r in sr]))))
    write_csv(OUT / "summary.csv",summaries)
    paired = []
    for B in protocol["budgets"]:
        for comparator in ["logdet_greedy","logdet_exhaustive"]:
            g = [r for r in method_rows if r["budget"]==B and r["method"]=="target_variance_greedy"]
            c = [r for r in method_rows if r["budget"]==B and r["method"]==comparator]
            diffs=np.array([x["target_radius"]-y["target_radius"] for x,y in zip(g,c)])
            ratios=np.array([x["target_radius"]/y["target_radius"] for x,y in zip(g,c)])
            paired.append(dict(budget=B,comparator=comparator,n_designs=200,target_greedy_narrower=int(np.sum(diffs < -1e-9)),tied=int(np.sum(np.abs(diffs)<=1e-9)),target_greedy_wider=int(np.sum(diffs>1e-9)),median_target_greedy_over_comparator=float(np.median(ratios)),worst_target_greedy_over_comparator=float(ratios.max())))
    write_csv(OUT / "paired_comparisons.csv",paired)
    manifest=dict(protocol_sha256=sha(PROTO),code_sha256=sha(__file__),input_designs_sha256=sha(protocol["input_designs"]),archived_records_sha256=sha(protocol["archived_records"]),command="python run_deterministic.py",python=platform.python_version(),numpy=np.__version__,elapsed_seconds=time.perf_counter()-start,n_designs=200,n_subsets=len(subset_rows),n_method_results=len(method_rows),new_sampling=False,new_dgp=False,source_archive_modified=False,output_sha256={p.name:sha(p) for p in OUT.iterdir() if p.is_file()})
    (OUT / "run_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps({"elapsed_seconds":manifest["elapsed_seconds"],"subsets":len(subset_rows),"main_budget4":[r for r in summaries if r["budget"]==4 and r["condition_stratum"]=="all"],"paired":paired},indent=2))

if __name__ == "__main__":
    main()
