"""Audit and describe the frozen historical-evidence experiment; no sampling."""
import os
for _name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[_name]='1'
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd

METHODS=('target_radius','logdet','frozen_random','direct_target')
REFERENCE='direct_reference'
LABELS=dict(target_radius='Target-radius',logdet='Logdet',frozen_random='Fixed random',direct_target='Direct target')
COLORS=dict(target_radius='#0F4D92',logdet='#42949E',frozen_random='#B64342',direct_target='#767676')

def read_json(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_json(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8',newline='\n')
def save_csv(p,frame):frame.to_csv(p,index=False,float_format='%.17g',lineterminator='\n')
def sign(lower,upper):return np.where(np.asarray(lower)>0,1,np.where(np.asarray(upper)<0,-1,0))
def wilson(k,n):
    if not n:return None,None
    z=1.959963984540054;p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,float(mid-half)),min(1.,float(mid+half))


def audit(raw):
    manifest=read_json(raw/'run_manifest.json');assert manifest['status']=='complete'
    cfg=manifest['config'];profile=cfg['profiles'][manifest['profile']]
    source=raw/'source_snapshot'/cfg['archive_path'];assert digest(source)==cfg['archive_sha256']
    archive=read_json(source);used=read_json(raw/'archive_designs_used.json')
    assert used==[archive[i] for i in profile['design_indices']]
    for name,h in manifest['source_sha256'].items():assert digest(raw/'source_snapshot'/name)==h,name
    for name,h in manifest['artifact_sha256'].items():assert digest(raw/name)==h,name
    records=pd.read_csv(raw/'budget_records.csv',dtype={'method':'category','role':'category','future_stream':'category'})
    history=pd.read_csv(raw/'history_observations.csv')
    stats=pd.read_csv(raw/'prefix_type_stats.csv',dtype={'stream':'category'})
    nw=profile['worlds_per_design'];expected_rows=len(used)*nw*(len(METHODS)*len(cfg['budgets'])+1)
    assert len(records)==expected_rows and not records.duplicated(['design_id','replicate','method','new_budget']).any()
    assert records.groupby(['design_id','method','new_budget'],observed=True).size().eq(nw).all()
    assert len(history)==len(used)*nw*cfg['history_studies']
    assert not history.duplicated(['design_id','replicate','candidate_type']).any()
    diffs=dict(W=0.,q=0.,weights=0.,next_W=0.,estimate=0.,reference_estimate=0.,trace_estimate=0.)
    widths=[];states=0;choices=0;plan_cache={}
    rg=records.groupby('design_id',observed=True);hg=history.groupby('design_id');sg=stats.groupby('design_id',observed=True)
    for d in used:
        did=d['replicate'];P=np.asarray(d['prior']);pinv=np.linalg.solve(P,np.eye(len(P)));t=np.asarray(d['target'])
        x=np.vstack([d['design'],t]);v=np.r_[np.asarray(d['sigma'])**2,cfg['direct_noise_sd']**2]
        expected_types=np.random.default_rng(np.random.SeedSequence([cfg['history_selection_seed'],did])).permutation(12)[:cfg['history_studies']]
        hcounts=np.bincount(expected_types,minlength=13)
        plans=read_json(raw/f'design_{did:03d}_plans.json');plan_cache[did]=plans
        historical=hg.get_group(did)
        assert set(historical.candidate_type)==set(expected_types)
        assert historical.groupby('replicate').size().eq(cfg['history_studies']).all()
        hmatrix=historical.pivot(index='replicate',columns='candidate_type',values='observed_y').reindex(index=range(nw),columns=range(13)).fillna(0).to_numpy()
        future=sg.get_group(did).pivot(index='replicate',columns=['stream','candidate_type','future_observations'],values='sum_future_y').reindex(range(nw))
        rec=rg.get_group(did);reference=rec[rec.method==REFERENCE].sort_values('replicate')
        assert reference.new_budget.eq(cfg['reference_direct_observations']).all()
        assert reference.future_stream.eq('reference_future').all()
        assert np.max(reference.width)<=2*np.sqrt(cfg['direct_noise_sd']**2/(cfg['reference_direct_observations']*cfg['failure_probability']))+1e-12
        for method,plan in plans.items():
            assert np.array_equal(plan['history_types'],expected_types)
            assert np.array_equal(plan['history_counts'],hcounts)
            path=plan['path'];horizon=cfg['reference_direct_observations'] if method==REFERENCE else max(cfg['budgets'])
            assert len(path)==horizon+1
            c=np.asarray([s['total_counts'] for s in path]);f=np.asarray([s['future_counts'] for s in path]);states+=len(path)
            assert np.array_equal(c,hcounts+f) and np.array_equal(f.sum(axis=1),np.arange(len(path)))
            V=np.linalg.inv(pinv+np.einsum('ni,ij,ik->njk',c/v,x,x));u=V@t;w=(u@x.T)/v
            residual=(c*w)@x-t;parameter=np.einsum('ni,ij,nj->n',residual,P,residual)
            noise=np.sum(c*w*w*v,axis=1);W=parameter+noise;q=u@t
            diffs['W']=max(diffs['W'],float(np.max(np.abs(W-[s['W'] for s in path]))))
            diffs['q']=max(diffs['q'],float(np.max(np.abs(W-q))))
            diffs['weights']=max(diffs['weights'],float(np.max(np.abs(w-[s['weights'] for s in path]))))
            assert np.all(np.diff(W)<=1e-11)
            selected=np.array([s['selected'] for s in path[1:]],int)
            assert np.array_equal(np.diff(f,axis=0),np.eye(13,dtype=int)[selected])
            assert all(s['visit']==f[j-1,s['selected']] for j,s in enumerate(path[1:],1))
            if method in ('direct_target',REFERENCE):assert np.all(selected==12)
            else:
                vx=V[:-1]@x[:12].T;quadratic=np.einsum('ik,nki->ni',x[:12],vx)
                nextW=W[:-1,None]-(u[:-1]@x[:12].T)**2/(v[:12]+quadratic)
                chosen=nextW[np.arange(len(selected)),selected]
                diffs['next_W']=max(diffs['next_W'],float(np.max(np.abs(chosen-W[1:]))))
                if method=='target_radius':assert np.all(chosen<=nextW.min(axis=1)+1e-11)
                elif method=='logdet':
                    score=.5*np.log1p(quadratic/v[:12]);assert np.all(score[np.arange(len(selected)),selected]>=score.max(axis=1)-1e-11)
                else:assert np.array_equal(selected,np.asarray(plan['random_order'])[np.arange(horizon)%12])
                choices+=horizon
            budgets=[horizon] if method==REFERENCE else cfg['budgets']
            for b in budgets:
                stream='reference_future' if method==REFERENCE else 'policy_future'
                fm=np.zeros((nw,13))
                for k,count in enumerate(f[b]):
                    if count:fm[:,k]=future[(stream,k,count)].to_numpy()
                estimated=(hmatrix+fm)@w[b]
                rows=rec[(rec.method==method)&(rec.new_budget==b)].sort_values('replicate')
                assert np.array_equal(rows.replicate,np.arange(nw))
                assert rows.total_observations.eq(cfg['history_studies']+b).all()
                assert np.allclose(rows.width,2*np.sqrt(W[b]/cfg['failure_probability']),atol=1e-11,rtol=0)
                assert np.allclose(rows.W,W[b],atol=1e-11,rtol=0)
                assert np.allclose(rows.parameter_component,parameter[b],atol=1e-11,rtol=0)
                assert np.allclose(rows.noise_component,noise[b],atol=1e-11,rtol=0)
                diffs['estimate']=max(diffs['estimate'],float(np.max(np.abs(estimated-rows.estimate))))
                diffs['reference_estimate']=max(diffs['reference_estimate'],float(np.max(np.abs(rows.reference_estimate.to_numpy()-reference.estimate.to_numpy()))))
                assert np.allclose(rows.truth,reference.truth,atol=0,rtol=0)
                assert np.array_equal(rows.reference_ci_sign,reference.ci_sign)
                widths.append(dict(design_id=did,method=method,new_budget=b,history_width=float(2*np.sqrt(W[0]/cfg['failure_probability'])),
                    width=float(2*np.sqrt(W[b]/cfg['failure_probability'])),width_ratio=float(np.sqrt(W[b]/W[0])),
                    width_reduction_fraction=float(1-np.sqrt(W[b]/W[0])),
                    absolute_width_reduction=float(2*(np.sqrt(W[0])-np.sqrt(W[b]))/np.sqrt(cfg['failure_probability'])),W=float(W[b])))
    assert np.allclose(records.error,records.estimate-records.truth)
    assert np.allclose(records.absolute_error,np.abs(records.error))
    assert np.allclose(records.squared_error,records.error**2)
    assert np.allclose(records.radius,records.width/2)
    assert np.allclose(records.radius**2*cfg['failure_probability'],records.W)
    assert np.allclose(records.lower,records.estimate-records.radius)
    assert np.allclose(records.upper,records.estimate+records.radius)
    assert np.allclose(records.absolute_point_difference,np.abs(records.point_difference))
    assert np.allclose(records.squared_point_difference,records.point_difference**2)
    assert records.covered.eq(records.truth.between(records.lower,records.upper)).all()
    assert records.ci_sign.eq(sign(records.lower,records.upper)).all()
    assert records.ci_direction_wrong.eq(records.ci_sign.ne(0)&records.ci_sign.ne(np.sign(records.truth))).all()
    assert records.within_reference_threshold.eq(records.absolute_point_difference.le(cfg['point_difference_threshold'])).all()
    assert np.allclose(records.point_difference,records.estimate-records.reference_estimate)
    assert records.ci_sign_agreement.eq(records.ci_sign.eq(records.reference_ci_sign)).all()
    assert records.decisive_same_direction.eq(records.ci_sign.ne(0)&records.reference_ci_sign.ne(0)&records.ci_sign.eq(records.reference_ci_sign)).all()
    assert records.decisive_opposite_direction.eq(records.ci_sign.ne(0)&records.reference_ci_sign.ne(0)&records.ci_sign.ne(records.reference_ci_sign)).all()
    trace=pd.read_csv(raw/'single_world_trace.csv');ledger=pd.read_csv(raw/'single_world_observations.csv')
    trace_did=cfg['trace_design_id'];trace_rep=cfg['trace_world'];d=archive[trace_did]
    P=np.array(d['prior']);t=np.array(d['target']);x=np.vstack([d['design'],t]);v=np.r_[np.array(d['sigma'])**2,.25]
    hh=history[(history.design_id==trace_did)&(history.replicate==trace_rep)]
    initial_precision=np.linalg.inv(P);initial_z=np.zeros(len(t))
    for h in hh.itertuples():initial_precision+=np.outer(x[h.candidate_type],x[h.candidate_type])/v[h.candidate_type];initial_z+=x[h.candidate_type]*h.observed_y/v[h.candidate_type]
    paired={}
    for method in (*METHODS,REFERENCE):
        precision=initial_precision.copy();z=initial_z.copy();estimates=[float(t@np.linalg.solve(precision,z))]
        obs=ledger[ledger.method==method].sort_values('stage')
        for row in obs.itertuples():
            k=row.candidate_type;precision+=np.outer(x[k],x[k])/v[k];z+=x[k]*row.observed_y/v[k]
            estimates.append(float(t@np.linalg.solve(precision,z)))
            key=(row.stream,k,row.visit)
            if key in paired:assert paired[key]==row.observed_y
            paired[key]=row.observed_y
        rows=trace[trace.method==method].sort_values('stage')
        diffs['trace_estimate']=max(diffs['trace_estimate'],float(np.max(np.abs(rows.estimate-estimates))))
    for visit in range(max(cfg['budgets'])):assert paired['policy_future',12,visit]!=paired['reference_future',12,visit]
    assert max(diffs.values())<1e-9,diffs
    evidence=dict(status='passed',profile=manifest['profile'],designs=len(used),worlds=len(used)*nw,evaluation_rows=len(records),
        audited_path_states=states,audited_bridge_choices=choices,max_absolute_differences=diffs,
        source_archive_sha256=digest(source),sampling_performed=False,
        scope=['Independent matrix and outcome reconstruction; experiment implementation not imported.',
               'History enters both precision and center; history/future/reference sources remain distinct.',
               'Reference independence is established by disjoint source RNG streams; unequal samples alone are not proof of independence.',
               'All coverage is pointwise joint marginal, not conditional on observed history or simultaneous over budgets.'])
    return manifest,records,pd.DataFrame(widths),history,trace,ledger,evidence


def summarize(records,widths):
    design_rows=[]
    for (method,b),g in widths.groupby(['method','new_budget'],observed=True):
        design_rows.append(dict(method=method,new_budget=b,designs=len(g),median_width=float(g.width.median()),q10_width=float(g.width.quantile(.1)),q90_width=float(g.width.quantile(.9)),
            median_absolute_width_reduction=float(g.absolute_width_reduction.median()),q10_absolute_width_reduction=float(g.absolute_width_reduction.quantile(.1)),q90_absolute_width_reduction=float(g.absolute_width_reduction.quantile(.9)),
            median_width_reduction=float(g.width_reduction_fraction.median()),q10_width_reduction=float(g.width_reduction_fraction.quantile(.1)),q90_width_reduction=float(g.width_reduction_fraction.quantile(.9))))
    def stochastic_row(g):
        decisive=g.ci_sign.ne(0);ref=g.reference_ci_sign.ne(0);both_undecided=g.ci_sign.eq(0)&~ref
        same=g.ci_sign.eq(g.reference_ci_sign);same_decisive=decisive&ref&same;opposite=decisive&ref&~same
        k=int(g.covered.sum());lo,hi=wilson(k,len(g));nref=int(ref.sum())
        return dict(n_worlds=len(g),mae=float(g.absolute_error.mean()),rmse=float(np.sqrt(g.squared_error.mean())),covered_count=k,coverage=k/len(g),coverage_wilson_low=lo,coverage_wilson_high=hi,
            decisive_count=int(decisive.sum()),decisive_rate=float(decisive.mean()),wrong_direction_count=int(g.ci_direction_wrong.sum()),wrong_direction_rate=float(g.ci_direction_wrong.mean()),
            median_absolute_point_difference=float(g.absolute_point_difference.median()),q90_absolute_point_difference=float(g.absolute_point_difference.quantile(.9)),
            mean_absolute_point_difference=float(g.absolute_point_difference.mean()),point_difference_rmse=float(np.sqrt(g.squared_point_difference.mean())),
            point_difference_le_030_count=int(g.within_reference_threshold.sum()),point_difference_le_030_rate=float(g.within_reference_threshold.mean()),
            three_class_agreement_count=int(same.sum()),three_class_agreement_rate=float(same.mean()),both_undecided_count=int(both_undecided.sum()),both_undecided_rate=float(both_undecided.mean()),
            same_decisive_count=int(same_decisive.sum()),same_decisive_rate=float(same_decisive.mean()),opposite_decisive_count=int(opposite.sum()),opposite_decisive_rate=float(opposite.mean()),
            reference_decisive_count=nref,reference_decisive_same_count=int(same_decisive.sum()),reference_decisive_undecided_count=int((ref&~decisive).sum()),reference_decisive_opposite_count=int(opposite.sum()),
            reference_decisive_same_rate=float(same_decisive.sum()/nref) if nref else None,
            reference_decisive_undecided_rate=float((ref&~decisive).sum()/nref) if nref else None,
            reference_decisive_opposite_rate=float(opposite.sum()/nref) if nref else None)
    per_design=[];pooled=[];confusion=[]
    policies=records[records.method!=REFERENCE]
    for (did,method,b),g in policies.groupby(['design_id','method','new_budget'],observed=True):per_design.append(dict(design_id=did,method=method,new_budget=b,**stochastic_row(g)))
    for (method,b),g in policies.groupby(['method','new_budget'],observed=True):
        descriptive={k:v for k,v in stochastic_row(g).items() if not k.startswith('coverage_wilson_')}
        pooled.append(dict(method=method,new_budget=b,**descriptive))
        for rs in (-1,0,1):
            for ps in (-1,0,1):confusion.append(dict(method=method,new_budget=b,reference_direction=rs,policy_direction=ps,count=int((g.reference_ci_sign.eq(rs)&g.ci_sign.eq(ps)).sum()),all_worlds=len(g)))
    ref_rows=[]
    for did,g in records[records.method==REFERENCE].groupby('design_id',observed=True):
        k=int(g.covered.sum());lo,hi=wilson(k,len(g))
        ref_rows.append(dict(design_id=did,n_worlds=len(g),width=float(g.width.iloc[0]),mae=float(g.absolute_error.mean()),rmse=float(np.sqrt(g.squared_error.mean())),
            covered_count=k,coverage=k/len(g),coverage_wilson_low=lo,coverage_wilson_high=hi,decisive_count=int(g.ci_decisive.sum()),decisive_rate=float(g.ci_decisive.mean()),wrong_direction_count=int(g.ci_direction_wrong.sum())))
    paired=[]
    for b in sorted(policies.new_budget.unique()):
        p=widths[(widths.new_budget==b)&(widths.method!=REFERENCE)].pivot(index='design_id',columns='method',values='width')
        for comparator in METHODS[1:]:
            diff=p.target_radius-p[comparator];ratio=p.target_radius/p[comparator]
            paired.append(dict(new_budget=int(b),comparator=comparator,designs=len(p),target_narrower=int((diff<-1e-11).sum()),equal_width=int((np.abs(diff)<=1e-11).sum()),target_wider=int((diff>1e-11).sum()),median_target_minus_comparator_width=float(diff.median()),median_target_over_comparator_width=float(ratio.median())))
    return dict(width_summary=pd.DataFrame(design_rows),pooled_descriptive_metrics=pd.DataFrame(pooled),per_design_metrics=pd.DataFrame(per_design),
        direction_confusion=pd.DataFrame(confusion),reference_per_design=pd.DataFrame(ref_rows),paired_width_comparisons=pd.DataFrame(paired))


def figures(out,tables,primary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import NullFormatter
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':10,
        'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.facecolor':'white'})
    fig,axs=plt.subplots(1,3,figsize=(13.4,3.8),layout='constrained')
    for method in METHODS:
        w=tables['width_summary'].query('method == @method').sort_values('new_budget')
        g=tables['pooled_descriptive_metrics'].query('method == @method').sort_values('new_budget')
        axs[0].plot(w.new_budget,w.median_width,marker='o',ms=3,color=COLORS[method],label=LABELS[method])
        axs[0].fill_between(w.new_budget,w.q10_width,w.q90_width,color=COLORS[method],alpha=.07)
        axs[1].plot(g.new_budget,g.decisive_rate,marker='o',ms=3,color=COLORS[method])
        axs[2].plot(g.new_budget,g.median_absolute_point_difference,marker='o',ms=3,color=COLORS[method])
        axs[2].plot(g.new_budget,g.q90_absolute_point_difference,color=COLORS[method],ls=':',lw=1)
    ref=tables['reference_per_design']
    axs[0].axhline(float(ref.width.median()),color='#222222',ls='--',lw=1,label='64 direct reference (median)')
    axs[1].axhline(float(ref.decisive_count.sum()/ref.n_worlds.sum()),color='#222222',ls='--',lw=1)
    axs[2].axhline(.3,color='#222222',ls='--',lw=1)
    for ax in axs:
        ax.axvline(primary,color='#aaaaaa',lw=.7,ls='--');ax.set_xticks([0,1,2,4,8]);ax.set_xlabel('New study observations (4 historical studies shared)')
    axs[0].set(title='A  Interval width',ylabel='Median width; shading: design q10–q90',yscale='log')
    axs[0].set_yticks([.6,1,2,4,8],labels=['0.6','1','2','4','8'])
    axs[0].yaxis.set_minor_formatter(NullFormatter())
    axs[0].legend(frameon=False,fontsize=7.5,loc='lower left',bbox_to_anchor=(.01,.08))
    axs[1].set(title='B  Intervals that establish a direction',ylabel='Fraction of worlds with CI excluding zero',ylim=(0,1))
    axs[2].set(title='C  Difference from the 64-study reference',ylabel='Absolute point difference; solid median / dotted q90',ylim=(0,None))
    fig.savefig(out/'historical_budget_results.png',dpi=300,bbox_inches='tight');fig.savefig(out/'historical_budget_results.pdf',bbox_inches='tight');plt.close(fig)


def mdtable(frame,formats=None):
    formats=formats or {};cols=list(frame.columns)
    def cell(k,v):
        if k in formats:return formats[k](v)
        if pd.isna(v):return '—'
        if isinstance(v,(float,np.floating)):return f'{v:.4g}'
        return str(v)
    return '\n'.join(['| '+' | '.join(cols)+' |','| '+' | '.join('---' for _ in cols)+' |']+['| '+' | '.join(cell(k,row[k]) for k in cols)+' |' for _,row in frame.iterrows()])


def report(out,manifest,records,widths,history,trace,ledger,tables,evidence):
    cfg=manifest['config'];b=cfg['primary_budget'];p=tables['pooled_descriptive_metrics'];w=tables['width_summary'];nd=widths.design_id.nunique()
    primary=w[w.new_budget==b].merge(p[p.new_budget==b],on=['method','new_budget'])
    primary=primary.set_index('method').loc[list(METHODS)].reset_index()
    reference=records[records.method==REFERENCE];target=primary[primary.method=='target_radius'].iloc[0]
    direct=primary[primary.method=='direct_target'].iloc[0]
    compact=primary[['method','median_width','median_width_reduction','point_difference_le_030_rate','reference_decisive_same_rate','reference_decisive_undecided_rate','mae']].rename(columns={
        'method':'方法','median_width':'区间宽度中位数','median_width_reduction':'相对历史缩短','point_difference_le_030_rate':'点差≤.30',
        'reference_decisive_same_rate':'参考定向时同向','reference_decisive_undecided_rate':'参考定向时仍不足','mae':'真值MAE'})
    direction=primary[['method','three_class_agreement_rate','both_undecided_rate','same_decisive_rate','opposite_decisive_rate']].rename(columns={
        'method':'方法','three_class_agreement_rate':'三分类一致','both_undecided_rate':'双方不足','same_decisive_rate':'双方定向且同向','opposite_decisive_rate':'双方定向但反向'})
    direction['双方定向但反向']=[f'{int(row.opposite_decisive_count)} ({row.opposite_decisive_rate:.4%})' for row in primary.itertuples()]
    conditional=primary[['method','reference_decisive_count','reference_decisive_same_rate','reference_decisive_undecided_rate','reference_decisive_opposite_rate']].rename(columns={
        'method':'方法','reference_decisive_count':'参考定向分母','reference_decisive_same_rate':'同向','reference_decisive_undecided_rate':'策略不足','reference_decisive_opposite_rate':'反向'})
    conditional['反向']=[f'{int(row.reference_decisive_opposite_count)} ({row.reference_decisive_opposite_rate:.6%})' for row in primary.itertuples()]
    reliability=primary[['method','n_worlds','mae','rmse','covered_count','coverage','wrong_direction_count']]
    all_budgets=w[w.method!=REFERENCE][['method','new_budget','median_width','median_width_reduction']].merge(p[['method','new_budget','median_absolute_point_difference','point_difference_le_030_rate','decisive_rate']],on=['method','new_budget'])
    hh=history[(history.design_id==cfg['trace_design_id'])&(history.replicate==cfg['trace_world'])]
    example=records[(records.design_id==cfg['trace_design_id'])&(records.replicate==cfg['trace_world'])]
    target_trace=trace[trace.method=='target_radius'];selected=target_trace[target_trace.stage.isin(cfg['budgets'])][['stage','selected','estimate','lower','upper','width','ci_sign','point_difference']]
    elapsed=manifest['elapsed_seconds'];checks=len(manifest.get('checks',{}))
    text=rf'''# 历史证据与有限桥接预算

本轮使用全部 {nd} 个原存档设计，每设计 {cfg['profiles'][manifest['profile']]['worlds_per_design']} 个世界。每世界先实际生成4项历史研究结果，所有策略共享；新增预算0、1、2、4、8均实际采集。**主预算为4，8仅为预定补充。**另有共享历史、未来噪声独立的64次直接目标观测参考，它不是模拟真值。

## 主预算4：实际回答了什么

目标选桥的区间宽度中位数为 {target.median_width:.4g}，各设计绝对缩短量的中位数为 {target.median_absolute_width_reduction:.4g}，相对各自历史区间缩短比例的中位数为 {target.median_width_reduction:.2%}。与64次直接参考的绝对点差中位数为 {target.median_absolute_point_difference:.4g}，90%分位为 {target.q90_absolute_point_difference:.4g}；差不超过.30的比例为 {target.point_difference_le_030_rate:.2%}。

但在参考已经给出方向的 {int(target.reference_decisive_count):,} 个世界里，目标选桥同向 {int(target.reference_decisive_same_count):,} 个（{target.reference_decisive_same_rate:.2%}），仍证据不足 {int(target.reference_decisive_undecided_count):,} 个（{target.reference_decisive_undecided_rate:.2%}），反向 {int(target.reference_decisive_opposite_count)} 个（{target.reference_decisive_opposite_rate:.6%}）。真实目标MAE为 {target.mae:.4g}；同预算direct的对应MAE为 {direct.mae:.4g}。本轮主预算4的结果支持定向选桥相对其他选桥规则的改善，尚不支持它已与64次direct得到相近的方向结论；同预算direct的点差和方向能力更好。区间单调缩短本身只是当前公式的保证。

{mdtable(compact,{name:lambda value:f'{value:.2%}' for name in ['相对历史缩短','点差≤.30','参考定向时同向','参考定向时仍不足']})}

宽度及其缩短按 **{nd} 个设计**统计；随机世界不会增加成本/宽度的有效样本数。点差和方向率是各设计等量世界的描述汇总，每设计的完整统计在 `per_design_metrics.csv`。没有把多个预算或四种方法当成新增独立世界，没有使用结果挑预算，也没有做未声明的总体显著性检验。

同预算的配对宽度比较如下。target更窄/更宽都完整保留，不能用与历史比较替代与强对照比较。

{mdtable(tables['paired_width_comparisons'].query('new_budget == @b'))}

![预算、区间、定向率与点差](historical_budget_results.png)

图A阴影为200个设计的10%–90%分位，不是置信带。图B按区间是否排除0判断方向。图C实线为点差中位数、点线为90%分位，横虚线为预定.30尺度。预算4竖线只标记预定主预算。参考64的宽度和方向能力另作水平参照，没有把它放进相同费用的位置。

## 方向一致不等于结论正确

区间下界>0记正，区间上界<0记负，其余记证据不足。下表分母均为全部世界；“双方不足”单独列出，不能把这部分当作成功发现方向。

{mdtable(direction,{name:lambda value:f'{value:.2%}' for name in ['三分类一致','双方不足','双方定向且同向']})}

仅在参考有方向的世界中，分成同向、策略不足、反向三个互斥结果。这是描述性条件比例，不是条件覆盖保证：

{mdtable(conditional,{name:lambda value:f'{value:.2%}' for name in ['同向','策略不足']})}

完整3×3混淆表位于 `direction_confusion.csv`：每方法每预算都保留参考负/不足/正 × 策略负/不足/正的九个格子。所有策略与参考共享真实参数及历史噪声，因此一致性带有关联；参考未来噪声独立于所有低预算策略，包括低预算direct，避免额外嵌套共享造成对direct的特殊优待。

## 独立真值评分与参考质量

{mdtable(reliability,{'coverage':lambda value:f'{value:.6f}'})}

参考共 {len(reference):,} 个世界，覆盖 {int(reference.covered.sum()):,}/{len(reference):,}（{reference.covered.mean():.6f}），MAE={reference.absolute_error.mean():.5g}，RMSE={np.sqrt(reference.squared_error.mean()):.5g}；能给方向的比例为 {reference.ci_decisive.mean():.2%}，错误定向 {int(reference.ci_direction_wrong.sum())} 次。其实际全宽范围为 [{reference.width.min():.6g}, {reference.width.max():.6g}]。64来自运行前确定的设计上界：$q\le .25/64$，所以全宽不超过 $2\sqrt{{.25/(64\times.05)}}=.559017$。这保证一个精度尺度，不保证目标远离0，也不保证每个世界的参考值准确。

错误定向是已给正/负方向却与模拟真目标符号相反，以上数量分母是全部世界。覆盖和真实误差独立评分，绝不以参考当真值。逐设计覆盖的Wilson区间基于每设计{cfg['profiles'][manifest['profile']]['worlds_per_design']}世界，未作跨设计多重比较校正；没有声称所有预算同时覆盖或观察历史后的条件覆盖。

## 全部预定预算

{mdtable(all_budgets)}

预算0是同一历史起点，四策略结果相同；所有后续区间中心实际使用历史与新增Y。研究成本仅计新增次数，既有4项单列；不是参与者人数、货币或现实跨研究成本。固定预算策略实际采到8次，不在达到某阈值时提前停止。

## 固定示例：设计0、世界0

四个历史观测（候选编号从0起）：

{mdtable(hh[['history_position','candidate_type','observed_y','noise_sd']])}

目标选桥在预定预算的更新：

{mdtable(selected)}

该世界真实目标为 {example.truth.iloc[0]:.6g}，参考点估计为 {example[example.method==REFERENCE].estimate.iloc[0]:.6g}，两者分开保存。逐次的选择、新Y和更新见 `single_world_steps.csv` 与原始ledger；不是根据结果挑选的示例。

## 定理与实现接口

原先验P仍为假定已知的二阶矩。历史四项不是重新命名的先验：它们的真实Y和设计均显式进入下面的求和，其中每次重复采集都是新的独立观测索引。

$$A=P^{{-1}}+\sum_{{i\in H\cup S}}x_ix_i^\top/v_i,\quad V=A^{{-1}},\quad a_i=t^\top Vx_i/v_i,\quad\widehat\theta=\sum_{{i\in H\cup S}}a_iY_i.$$

$$d=\sum_i a_ix_i-t,\quad W=d^\top Pd+\sum_i a_i^2v_i=t^\top Vt,\quad R=\sqrt{{W/.05}}.$$

每一步枚举候选更新后的W并选择最小者，同时核对 $W_{{next}}=W-(t^\top Vx_b)^2/(v_b+x_b^\top Vx_b)$。logdet和固定随机只替换选择规则，估计器与半径相同。下一步最优不等于整个预算全局最优。

beta和所有研究噪声实际抽取标准化Student-t5，保留原P和sigma。设计和矩信息在观察Y之前固定，Y仅用于更新中心。保证联合覆盖随机beta、历史噪声和新噪声；V不是非高斯条件后验协方差。这里仍是已知矩的线性结构化分支，没有运行一般U/L/H校准、simplex权重与sharp拒绝集流程。

## 核验、时长与来源

原 full 运行耗时 {elapsed:.1f} 秒，10项实现测试、{checks} 项运行检查通过；测试记录见原目录 `test_log.txt`。代码提交 `{manifest['git_revision']}`，源档案哈希 `{cfg['archive_sha256']}`。运行前预告full约1–3分钟，smoke后对一个200世界设计的生成/写入/检查实测为0.285秒，据此更新为60–120秒；该计时子集不作为额外独立世界合入结果。分析绘图耗时在 `analysis_manifest.json` 单独记录，本报告没有重新采样。

独立分析不导入实验实现，从原档案重算 {evidence['audited_path_states']:,} 个路径状态、{evidence['audited_bridge_choices']:,} 次选桥，并从历史Y及未来前缀观测和重建全部 {evidence['evaluation_rows']:,} 个端点。固定示例也从逐次观测重建。最大差为 `{json.dumps(evidence['max_absolute_differences'])}`。来源与产物哈希均核对，详见 `independent_audit.json`。

## 审稿问题完整回顾

| 问题 | 本轮证据与边界 |
| --- | --- |
| REV-01 | 有真实历史起点和逐次例子，支持解释；正文可读性仍需作者审阅 |
| REV-02 | 仍为设计型权重/选择，未提供R∞结果适应性效用 |
| REV-03 | 新数字只绑定此历史线性分支，不自动更新摘要 |
| REV-04 | 已知P/x/v与合成历史不等于真实U、L、H校准 |
| REV-05 | 合成历史复用闭环，不是真实应用闭环 |
| REV-06 | 未新增Many Labs噪声证据 |
| REV-07 | 同历史、同新增预算、强direct对照与独立未来参考；未验证现实经济成本 |
| REV-08 | 运行结果不证明新颖性，相关文献仍需独立比较 |
| REV-09 | 线性矩估计器可有负权重，不验证一般simplex类最优 |
| REV-10 | 实际非高斯抽样、W与单步选桥一致；线性、已知矩和单步范围保留 |
| REV-11 | 版本、原档案、历史与未来流明确，不能混同一般U模型或旧压力测试 |
| REV-12 | 点差、三分类方向、参考不确定性和真值风险分开；固定预算不声明全路径保证 |

没有因跑通而关闭任何审稿问题。是否足以支持作者想要的有限预算效用，应依据上述与对照、参考及真值的完整结果判断。
'''
    (out/'RESULTS.md').write_text(text,encoding='utf-8',newline='\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();raw=args.raw.resolve();out=args.output.resolve()
    if out.exists():raise FileExistsError('Use a fresh report directory.')
    start=time.perf_counter();manifest,records,widths,history,trace,ledger,evidence=audit(raw)
    tables=summarize(records,widths);out.mkdir(parents=True)
    for name,frame in tables.items():save_csv(out/(name+'.csv'),frame)
    save_csv(out/'design_widths.csv',widths)
    save_csv(out/'single_world_steps.csv',trace.merge(ledger[['method','stage','observed_y']],on=['method','stage'],how='left'))
    save_json(out/'independent_audit.json',evidence)
    figures(out,tables,manifest['config']['primary_budget']);report(out,manifest,records,widths,history,trace,ledger,tables,evidence)
    save_json(out/'analysis_manifest.json',dict(raw_directory=str(raw),raw_manifest_sha256=digest(raw/'run_manifest.json'),analysis_script_sha256=digest(Path(__file__)),
        analysis_elapsed_seconds=time.perf_counter()-start,sampling_performed=False,output_sha256={p.name:digest(p) for p in out.iterdir() if p.is_file()}))
    primary=tables['pooled_descriptive_metrics'][tables['pooled_descriptive_metrics'].new_budget.eq(manifest['config']['primary_budget'])]
    print(json.dumps(dict(audit=evidence,primary=primary.to_dict('records'),width_summary=tables['width_summary'][tables['width_summary'].new_budget.eq(manifest['config']['primary_budget'])].to_dict('records'),analysis_elapsed_seconds=time.perf_counter()-start),ensure_ascii=False))

if __name__=='__main__':main()
