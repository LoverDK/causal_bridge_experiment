"""Reproduce current Figures 5 and 6 from committed CSVs using portable paths."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'current_method/results'
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
 'font.size':8,'axes.titlesize':9,'legend.fontsize':7.5,'axes.spines.top':False,
 'axes.spines.right':False,'legend.frameon':False,'pdf.fonttype':42})
sources=pd.read_csv(DATA/'full/manylabs_sources.csv').sort_values('effect',ascending=False)
fig,axes=plt.subplots(1,2,figsize=(5.5,5.7))
fig.subplots_adjust(left=.20,right=.99,top=.95,bottom=.11,wspace=1.0)
for ax,rows,title in zip(axes,[sources.iloc[:29],sources.iloc[29:]],['Sources 1-29','Sources 30-57']):
    y=np.arange(len(rows))
    ax.errorbar(rows.effect,y,xerr=1.96*np.sqrt(rows.variance),fmt='o',ms=2.5,color='#0F4D92',elinewidth=.6,capsize=0)
    ax.axvline(.17286449173759633,color='#42949E',ls='--',lw=.9)
    ax.axvline(0,color='#767676',ls=':',lw=.6)
    ax.set(yticks=y,yticklabels=rows.source,title=title,xlabel='Source risk difference',xlim=(-.4,.85),ylim=(28.7,-.7),xticks=[-.4,0,.4,.8])
    ax.tick_params(axis='y',labelsize=7,length=0)
fig.savefig(out/'revision_sources.pdf');fig.savefig(out/'revision_sources.png',dpi=180);plt.close(fig)
pooled=pd.read_csv(DATA/'workflow_full/pooled_summary.csv')
methods=[('r2_targeted','Targeted R2','#0F4D92','-','o'),('rinf_targeted','Targeted R-infinity','#9A4D8E','--','s'),
 ('r2_random','Random R2','#B64342','-.','^'),('r2_nearest','Nearest R2','#42949E',':','D'),
 ('r2_static','Archive only R2','#767676','--','x'),('target_only','Target trial','#272727',':','+')]
fig,axes=plt.subplots(2,3,figsize=(5.5,3.8),sharex=True,sharey=True)
fig.subplots_adjust(left=.11,right=.985,bottom=.28,top=.92,hspace=.30,wspace=.19)
for col,scenario in enumerate(['bridgeable','supported','unreachable']):
    for row,tolerance in enumerate([.2,.3]):
        ax=axes[row,col]
        for method,label,color,style,marker in methods:
            g=pooled[pooled.scenario.eq(scenario)&pooled.method.eq(method)&pooled.tolerance.eq(tolerance)].sort_values('budget')
            assert len(g)==4
            x=g.budget.to_numpy()*96
            ax.plot(x,g.released,color=color,ls=style,marker=marker,ms=4,lw=1.1,markerfacecolor='none',label=label)
            ax.fill_between(x,g.released_lower,g.released_upper,color=color,alpha=.07)
        ax.set(xticks=[0,96,192,288],yticks=[0,.5,1],ylim=(-.03,1.04));ax.tick_params(labelsize=7)
        if row==0:ax.set_title(scenario.capitalize(),fontsize=8)
        if col==0:ax.set_ylabel(f'Tolerance {tolerance:g}\nFraction released',fontsize=8)
handles=[Line2D([],[],color=c,ls=s,marker=m,ms=4,markerfacecolor='none',label=l) for _,l,c,s,m in methods]
fig.supxlabel('Available new participants',fontsize=8,y=.16)
fig.legend(handles=handles,loc='lower center',ncol=3,fontsize=7.5,bbox_to_anchor=(.52,.01))
fig.savefig(out/'revision_workflow.pdf');fig.savefig(out/'revision_workflow.png',dpi=180);plt.close(fig)
inputs=[DATA/'full/manylabs_sources.csv',DATA/'workflow_full/pooled_summary.csv']
(out/'provenance.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},indent=2))
print('Rendered Figures 5 and 6 to',out)
