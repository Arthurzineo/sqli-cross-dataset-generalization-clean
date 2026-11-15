#!/usr/bin/env python3
"""Summarize saved matched edges and collect validated manuscript PDFs. No fits."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from PIL import Image

OUT=Path(__file__).resolve().parents[1]
ADD=OUT.parent
AN=ADD.parent
ROOT=AN.parent
FINAL=ROOT/'figures/manuscript_final'
PREVIOUS=ROOT/'figures/final'
MODELS=['logistic','catboost','mlp']
LABELS={'logistic':'Logistic Regression','catboost':'CatBoost','mlp':'MLP'}
REPS=['RAW','CANONICALIZED']
METRICS=['f1','mcc','pr_auc']
KEYS=['target','added_source','model','representation','base_sources']
TOL=1e-9
COMMAND=' '.join([sys.executable,*sys.argv])


def js(x):return json.dumps(x,sort_keys=True,ensure_ascii=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(ROOT.parent))
def ids(values):return js(sorted({i for v in values for i in json.loads(v)}))
def sources(s):return frozenset(s.split('+'))


class Task:
    def __init__(self):
        for d in ['tables','derived','figures','evidence']:(OUT/d).mkdir(exist_ok=True)
        self.inputs={};self.tables={};self.recipes=[];self.graphics={};self.copies=[]
        self.edges=self.read(ADD/'tables/marginal_source_additions.parquet')
        csv=self.read(ADD/'tables/marginal_source_additions.csv')
        pd.testing.assert_frame_equal(self.edges,csv,check_dtype=False,check_exact=True)
        self.pairs=self.read(ADD/'derived/matched_source_additions_per_seed.parquet')
        self.lineage=self.read(ADD/'SOURCE_LINEAGE.parquet')
        self.targets=sorted(self.edges.target.unique())
        plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8.5,'axes.titlesize':8.5,
            'xtick.labelsize':7.5,'ytick.labelsize':7.5,'axes.linewidth':.6,'pdf.fonttype':42,'ps.fonttype':42,
            'savefig.facecolor':'white'})

    def read(self,p):
        self.inputs[rel(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
        if p.suffix=='.parquet':return pd.read_parquet(p)
        if p.suffix=='.csv':return pd.read_csv(p,float_precision='round_trip',keep_default_na=False)
        return json.loads(p.read_text())

    def table(self,name,frame,description,source):
        d=frame.copy().reset_index(drop=True)
        d['row_id']=[hashlib.sha256(js([name,i,str(r)]).encode()).hexdigest()[:24] for i,r in enumerate(d.to_dict('records'))]
        for v in d.experiment_ids:assert set(json.loads(v))<=set(self.lineage.experiment_id)
        p=OUT/(name+'.csv');d.to_csv(p,index=False,float_format='%.17g');d.to_parquet(p.with_suffix('.parquet'),index=False)
        self.tables[name]=d
        self.recipes.append(dict(artifact=name,source=source,columns=js(list(d.columns)),filter_aggregation=description,
            script=rel(Path(__file__)),command=COMMAND,lineage=rel(OUT/'SOURCE_LINEAGE.parquet')))
        return d

    def validate(self):
        e=self.edges;p=self.pairs
        assert not e.duplicated(KEYS).any() and not p.duplicated(KEYS+['seed']).any()
        for d in [e,p]:
            for r in d.itertuples():
                before=sources(r.base_sources);after=sources(r.sources_after)
                assert r.added_source not in before and after==before|{r.added_source}
                assert r.target not in after and r.n_sources_before==len(before) and r.n_sources_after==len(after)
        known=self.read(AN/'_global/master_results.parquet').set_index('experiment_id')
        # Metadata only: make sure each before/after original ID resolves to the same matching condition/seed.
        for r in p.itertuples():
            for column,pool in [('experiment_ids_before',r.base_sources),('experiment_ids_after',r.sources_after)]:
                for eid in json.loads(getattr(r,column)):
                    original=known.loc[eid]
                    assert (original.target_dataset,original.model,original.representation,int(original.seed))==(r.target,r.model,r.representation,int(r.seed))
                    assert sources(original.effective_development_datasets)==sources(pool)
                    assert original.usable and original.experiment_type=='contribution'
        indexed=e.set_index(KEYS);checks=[]
        for key,g in p.groupby(KEYS,sort=False):
            row=indexed.loc[key]
            assert len(g)==row.n_seed_pairs and sorted(g.seed.tolist())==json.loads(row.seeds)
            assert ids(g.experiment_ids_before)==row.experiment_ids_before
            assert ids(g.experiment_ids_after)==row.experiment_ids_after
            for metric in METRICS:
                saved=float(row['delta_'+metric]);verification=float(g['delta_'+metric].mean())
                assert np.isclose(saved,verification,atol=1e-15,rtol=0)
            checks.append(dict(zip(KEYS,key))|dict(n_seed_pairs=len(g),seed_and_coalition_match=True,existing_seed_mean_matches=True,experiment_ids=row.experiment_ids))
        self.table('derived/input_pair_verification',pd.DataFrame(checks),
            'All existing edges checked against saved per-seed matching and master metadata; validate existing seed means, do not replace them.',rel(ADD/'tables/marginal_source_additions.parquet'))
        self.lineage[self.lineage.experiment_id.isin({i for v in e.experiment_ids for i in json.loads(v)})].to_parquet(OUT/'SOURCE_LINEAGE.parquet',index=False)

    def aggregate(self):
        rows=[]
        for key,g in self.edges.groupby(['target','added_source','model','representation','n_sources_before']):
            r=dict(zip(['target','added_source','model','representation','n_sources_before'],key))
            r.update(n_sources_after=int(r['n_sources_before'])+1,n_coalition_contexts=len(g),n_seed_pairs=int(g.n_seed_pairs.sum()),
                context_row_ids=js(g.row_id.tolist()),experiment_ids=ids(g.experiment_ids))
            for m in METRICS:r['mean_delta_'+m]=g['delta_'+m].mean()
            rows.append(r)
        self.by_target_size=self.table('derived/marginal_gain_target_source_pool_size',pd.DataFrame(rows),
            'Seeds already averaged within exact matched edge in input. Equal mean over distinct eligible coalition contexts within target/source/model/view/k.',rel(ADD/'tables/marginal_source_additions.parquet'))
        rows=[]
        for key,g in self.by_target_size.groupby(['added_source','model','representation','n_sources_before']):
            r=dict(zip(['added_source','model','representation','n_sources_before'],key))
            r.update(n_sources_after=int(r['n_sources_before'])+1,n_targets=len(g),n_coalition_contexts=int(g.n_coalition_contexts.sum()),
                n_seed_pairs=int(g.n_seed_pairs.sum()),targets=js(sorted(g.target)),experiment_ids=ids(g.experiment_ids))
            for metric in METRICS:
                v=g['mean_delta_'+metric]
                for name,value in [('mean',v.mean()),('median',v.median()),('std',v.std(ddof=1)),('min',v.min()),('max',v.max())]:r[name+'_target_delta_'+metric]=value
            rows.append(r)
        self.a=self.table('tables/marginal_gain_by_added_source_and_pool_size',pd.DataFrame(rows),
            'Equal-weight macro of target-level coalition means. Median/SD/min/max over target means, SD ddof=1. Count contexts and matched seed-pairs separately. No zero imputation.', 'derived/marginal_gain_target_source_pool_size.parquet')
        rows=[]
        for key,g in self.edges.groupby(['added_source','target','model','representation']):
            r=dict(zip(['added_source','target','model','representation'],key))
            r.update(n_valid_coalition_contexts=len(g),n_seed_pairs=int(g.n_seed_pairs.sum()),
                n_seeds=int(len({s for v in g.seeds for s in json.loads(v)})),context_row_ids=js(g.row_id.tolist()),experiment_ids=ids(g.experiment_ids))
            for m in METRICS:
                v=g['delta_'+m]
                for name,value in [('mean',v.mean()),('median',v.median()),('std',v.std(ddof=1)),('min',v.min()),('max',v.max())]:r[name+'_delta_'+m]=value
            r.update(n_positive_contexts=int((g.delta_f1>TOL).sum()),n_negative_contexts=int((g.delta_f1< -TOL).sum()),
                fraction_positive=float((g.delta_f1>TOL).mean()),fraction_negative=float((g.delta_f1< -TOL).mean()))
            rows.append(r)
        self.b=self.table('tables/marginal_gain_by_added_source_target',pd.DataFrame(rows),
            'Each cell: mean marginal change when this source was added across ALL valid nonempty coalition contexts for the same target/model/view. Contexts equally weighted after saved matched-seed means; no arbitrary addition order. n_seed_pairs sums context-specific pair counts; repeated seed labels are not independent targets.',rel(ADD/'tables/marginal_source_additions.parquet'))
        # Verify shared summary columns against the previous validated source×target table.
        old=self.read(ADD/'tables/marginal_gain_by_added_source_target.parquet')
        keys=['target','added_source','model','representation']
        match=self.b.merge(old,on=keys,suffixes=('_new','_old'),validate='one_to_one')
        for m in METRICS:
            for stat in ['mean','median','std']:
                np.testing.assert_allclose(match[stat+'_delta_'+m+'_new'],match[stat+'_delta_'+m+'_old'],rtol=0,atol=1e-15)
        rows=[]
        for key,g in self.b.groupby(['added_source','model','representation']):
            high=g.loc[g.mean_delta_f1.idxmax()];low=g.loc[g.mean_delta_f1.idxmin()]
            rows.append(dict(zip(['added_source','model','representation'],key))|dict(n_targets=len(g),
                mean_target_delta_f1=g.mean_delta_f1.mean(),std_target_delta_f1=g.mean_delta_f1.std(ddof=1),
                target_range_delta_f1=g.mean_delta_f1.max()-g.mean_delta_f1.min(),
                n_coalition_contexts=int(g.n_valid_coalition_contexts.sum()),n_seed_pairs=int(g.n_seed_pairs.sum()),
                targets_positive=int((g.mean_delta_f1>TOL).sum()),targets_negative=int((g.mean_delta_f1< -TOL).sum()),
                mean_target_fraction_positive=g.fraction_positive.mean(),
                best_target=high.target,best_target_delta_f1=high.mean_delta_f1,best_target_contexts=int(high.n_valid_coalition_contexts),best_row_id=high.row_id,
                lowest_target=low.target,lowest_target_delta_f1=low.mean_delta_f1,lowest_target_contexts=int(low.n_valid_coalition_contexts),lowest_row_id=low.row_id,
                experiment_ids=ids(g.experiment_ids)))
        self.overall=self.table('tables/source_identity_overview',pd.DataFrame(rows),
            'Equal-target mean of source×target means; target dependence=range and sample SD of target means. Targets positive/negative classify mean at tolerance1e-9. Positive-context fractions macro-averaged by target. Extremes may both be positive: lowest is not necessarily harmful.', 'tables/marginal_gain_by_added_source_target.parquet')
        rows=[]
        for key,g in self.a[self.a.n_sources_before<=4].groupby(['added_source','model','representation']):
            g=g.sort_values('n_sources_before')
            for (_,a),(_,b) in zip(g.iloc[:-1].iterrows(),g.iloc[1:].iterrows()):
                assert a.targets==b.targets
                x,y=a.mean_target_delta_f1,b.mean_target_delta_f1
                if x>TOL and y< -TOL or x< -TOL and y>TOL:
                    rows.append(dict(zip(['added_source','model','representation'],key))|dict(k_before=int(a.n_sources_before),k_after=int(b.n_sources_before),
                        delta_at_smaller_pool=x,delta_at_larger_pool=y,direction='positive_to_negative' if x>0 else 'negative_to_positive',
                        n_targets=int(a.n_targets),contexts_smaller=int(a.n_coalition_contexts),contexts_larger=int(b.n_coalition_contexts),
                        smaller_row_id=a.row_id,larger_row_id=b.row_id,experiment_ids=ids([a.experiment_ids,b.experiment_ids])))
        self.switches=self.table('tables/source_pool_sign_changes',pd.DataFrame(rows),
            'Adjacent k among 1..4 only, identical eligible-target set; mean target delta crosses ±1e-9. k=5 deliberately excluded from cross-k sign claims because target eligibility changes.', 'tables/marginal_gain_by_added_source_and_pool_size.parquet')
        rows=[]
        for key,g in self.edges.groupby(['target','added_source','model','representation','n_sources_before']):
            low=g.loc[g.delta_f1.idxmin()];high=g.loc[g.delta_f1.idxmax()]
            if low.delta_f1< -TOL and high.delta_f1>TOL:
                rows.append(dict(zip(['target','added_source','model','representation','n_sources_before'],key))|
                    dict(n_contexts=len(g),negative_base_sources=low.base_sources,negative_delta_f1=low.delta_f1,
                        positive_base_sources=high.base_sources,positive_delta_f1=high.delta_f1,
                        spread=high.delta_f1-low.delta_f1,negative_context_id=low.row_id,positive_context_id=high.row_id,
                        n_seed_pairs_per_context=int(low.n_seed_pairs),experiment_ids=ids([low.experiment_ids,high.experiment_ids])))
        self.reversals=self.table('tables/context_sign_reversals_same_target_and_size',pd.DataFrame(rows),
            'Existing most positive and negative edge within identical target/source/model/view/pool size. Shows conditional context dependence, not causal effect or population frequency; extrema selected automatically.', rel(ADD/'tables/marginal_source_additions.parquet'))
        coverage=[]
        for model in MODELS:
            for rep in REPS:
                for source in self.targets:
                    for target in self.targets:
                        g=self.b[(self.b.model==model)&(self.b.representation==rep)&(self.b.added_source==source)&(self.b.target==target)]
                        coverage.append(dict(model=model,representation=rep,added_source=source,target=target,
                            present=bool(len(g)),n_contexts=int(g.n_valid_coalition_contexts.iloc[0]) if len(g) else 0,
                            reason='eligible' if len(g) else ('source_is_target' if source==target else 'same_family_target_exclusion'),
                            experiment_ids=ids(g.experiment_ids)))
        self.table('tables/source_target_cell_coverage',pd.DataFrame(coverage),
            'Coverage metadata only: context count0 denotes absence; missing DELTA cells remain NaN, never0. Exclusion follows the already-audited historical family policy.', 'tables/marginal_gain_by_added_source_target.parquet')

    def figures(self):
        bound=max(self.a.mean_target_delta_f1.abs().max(),self.b.mean_delta_f1.abs().max())
        self.color_bound=float(bound)
        for name,frame,column,xcol,xorder in [
            ('marginal_gain_by_source_and_pool_size',self.a,'mean_target_delta_f1','n_sources_before',list(range(1,6))),
            ('marginal_gain_by_source_and_target',self.b,'mean_delta_f1','target',self.targets)]:
            fig,axes=plt.subplots(2,3,figsize=(174/25.4,6.05 if xcol=='target' else 5.25),sharex=True,sharey=True,layout='constrained')
            norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound)
            for i,rep in enumerate(REPS):
                for j,model in enumerate(MODELS):
                    ax=axes[i,j];g=frame[(frame.model==model)&(frame.representation==rep)]
                    wide=g.pivot(index='added_source',columns=xcol,values=column).reindex(index=self.targets,columns=xorder)
                    array=wide.to_numpy();cmap=plt.get_cmap('RdBu').copy();cmap.set_bad('#D9D9D9')
                    image=ax.pcolormesh(np.ma.masked_invalid(array),norm=norm,cmap=cmap,edgecolors='white',linewidth=.4,rasterized=False)
                    np.testing.assert_array_equal(np.ma.filled(image.get_array(),np.nan).reshape(array.shape),array)
                    ax.set_ylim(len(self.targets),0);ax.set_aspect('auto')
                    ax.set_title(LABELS[model]+'\n'+rep,pad=6)
                    ax.set_yticks(np.arange(len(self.targets))+.5,self.targets)
                    ax.set_xticks(np.arange(len(xorder))+.5,([str(k)+'→'+str(k+1) for k in xorder] if xcol!='target' else xorder),
                        rotation=55 if xcol=='target' else 0,ha='right' if xcol=='target' else 'center',rotation_mode='anchor')
                    ax.tick_params(length=0,pad=4)
                    if j==0:ax.set_ylabel('Added source')
                    if i==1:ax.set_xlabel('Unseen target' if xcol=='target' else 'Pool size before → after')
                    for spine in ax.spines.values():spine.set_visible(False)
            bar=fig.colorbar(image,ax=axes,orientation='horizontal',fraction=.06,pad=.03,shrink=.8,aspect=35)
            bar.set_label('Mean ΔF1: after adding source minus before')
            bar.ax.set_title('Gray: missing / ineligible',fontsize=7.5,pad=4)
            bar.solids.set_rasterized(False)
            fig.canvas.draw()
            renderer=fig.canvas.get_renderer()
            for ax in fig.axes:
                for text in [ax.title,ax.xaxis.label,ax.yaxis.label,*ax.get_xticklabels(),*ax.get_yticklabels()]:
                    if not text.get_visible() or not text.get_text():continue
                    box=text.get_window_extent(renderer)
                    # Ignore auto-colorbar tick labels beyond its own numeric limits.
                    if text in bar.ax.get_xticklabels() and not -bound<=text.get_position()[0]<=bound:continue
                    assert box.x0>=-1 and box.y0>=-1 and box.x1<=fig.bbox.width+1 and box.y1<=fig.bbox.height+1,(name,text.get_text())
            pdf=OUT/'figures'/(name+'.pdf');png=pdf.with_suffix('.png')
            fig.savefig(pdf,metadata={'CreationDate':None,'ModDate':None});fig.savefig(png,dpi=300);plt.close(fig)
            assert len(subprocess.check_output(['pdfimages','-list',str(pdf)],text=True).strip().splitlines())==2
            with Image.open(png) as im:assert all(abs(d-300)<.01 for d in im.info['dpi'])
            self.graphics[name]=dict(pdf=rel(pdf),png=rel(png),shared_symmetric_bound=float(bound),zero_center=0,
                values_equal_source=True,vector_pdf=True,png_dpi=300,text_in_bounds=True)

    @staticmethod
    def markdown(d,columns):
        def fmt(x):return f'{x:.6f}' if isinstance(x,(float,np.floating)) else str(x)
        return '\n'.join(['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']+
            ['| '+' | '.join(fmt(r[c]) for c in columns)+' |' for _,r in d.iterrows()])

    def provenance(self):
        return f'''\n## Data Sources and Traceability

Script: `{rel(Path(__file__))}`. Command: `{COMMAND}`.
Inputs: existing `ADDITIONAL_MANUSCRIPT_ANALYSES/tables/marginal_source_additions.csv` and .parquet, existing `derived/matched_source_additions_per_seed.parquet`, historical `_global/master_results.parquet` (metadata validation), and existing source lineage. No prediction, checkpoint, dataset payload or model file was read.
Per-table columns/filters/formulas: `SOURCE_INTERACTIONS/TRACEABILITY.csv` (relative to ADDITIONAL_MANUSCRIPT_ANALYSES). Full input/output SHA-256 and report revision: `SOURCE_INTERACTIONS/ARTIFACT_MANIFEST.json`. Each row carries experiment_ids; resolve them through `SOURCE_INTERACTIONS/SOURCE_LINEAGE.parquet`. The new derived target/source/pool table carries original context row IDs. Existing edge table supplies before/after experiment IDs; existing per-seed table supplies exact seed matches.
Seeds are already averaged inside exact nested coalition edges; these existing deltas were reused unchanged, validated against their saved seed-pair means. Analysis A: equal coalition-context means within each target/source/model/view/k, then equal targets. Analysis B: equal context means for each source/target/model/view across all eligible sizes, not equal weighting of size levels and not one addition order. n_seed_pairs counts context-specific pairs, not independent targets. SD is ddof=1. Sign tolerance1e-9 is numerical, not practical equivalence. No hypothesis tests.
Missing cells remain missing. Context counts differ combinatorially; related site sources and target-family exclusion limit independent diversity. k=5→6 has fewer eligible targets; sign-switch claims use k≤4 with identical target sets. Source pools mean effective training+validation files, not necessarily optimizer-only files. Validation changes are inherited from the historical procedure. Contributions are conditional/descriptive, not causal or intrinsic source quality.
'''

    def report(self):
        prefix='SOURCE_INTERACTIONS/tables/'
        lines=['## Source Identity and Coalition Context','',
            f'The following analyses reuse **{len(self.edges)}** valid nested coalition contexts and **{len(self.pairs)}** saved matched-seed pairs; all contexts have five seed pairs. The requested seed means already exist and were not replaced. Sources: `tables/marginal_source_additions.parquet` and `derived/matched_source_additions_per_seed.parquet`; row keys target/model/representation/base_sources/added_source. Verification: `SOURCE_INTERACTIONS/derived/input_pair_verification.parquet`. Each target receives equal macro weight in Analysis A.',
            'All numeric rows below identify model and representation and carry n_contexts (or n_coalition_contexts/n_valid_coalition_contexts), row_id and experiment_ids in their named CSV/Parquet. Script and all IDs resolve through the provenance section and SOURCE_INTERACTIONS/SOURCE_LINEAGE.parquet. RAW/CAN are historical views, not a newly established identical-payload causal comparison.', '',
            '### 1. Largest average marginal gains','',
            'Compare only as descriptive averages over eligible targets; eligibility differs by added source. These are not intrinsic dataset-quality ranks. Full source/model/view results, including negative means, are in `'+prefix+'source_identity_overview.csv`.',
            self.markdown(self.overall.sort_values('mean_target_delta_f1',ascending=False).groupby(['model','representation'],sort=False).head(1),
                ['added_source','model','representation','mean_target_delta_f1','n_targets','n_coalition_contexts','row_id']), '',
            '### 2. Same source, different pool sizes','',
            'The complete table below reports target-macro ΔF1 at each eligible size; these values describe all matching coalition contexts, not an arbitrary addition order. Source: `'+prefix+'marginal_gain_by_added_source_and_pool_size.csv`, filter each displayed added_source/model/representation/n_sources_before. k=1..4 has a stable target set for each source; k=5 may change it.',
            self.markdown(self.a,['added_source','model','representation','n_sources_before','n_targets','n_coalition_contexts','mean_target_delta_f1']), '',
            '### 3. Sign changes as the pool grows','',
            'Adjacent sign reversals below preserve identical eligible target sets (base sizes 1..4 only). Positive-to-negative transitions directly answer the requested reversal question; reverse transitions are retained rather than hidden. Source: `'+prefix+'source_pool_sign_changes.csv`; linked smaller_row_id/larger_row_id resolve the original A cells and IDs.',
            self.markdown(self.switches,['added_source','model','representation','k_before','k_after','direction','delta_at_smaller_pool','delta_at_larger_pool','n_targets','contexts_smaller','contexts_larger']), '',
            '### 4–5. Targets helped most and hurt most by each source','',
            'Extrema of mean context effects for every source/model/view. A positive lowest value means **no negative target-average effect was observed**, not that the source never hurt an individual context. Negative contexts can coexist with a positive mean. Source: `'+prefix+'source_identity_overview.csv`; best_row_id/lowest_row_id point into `'+prefix+'marginal_gain_by_added_source_target.csv`.',
            self.markdown(self.overall,['added_source','model','representation','best_target','best_target_delta_f1','best_target_contexts','lowest_target','lowest_target_delta_f1','lowest_target_contexts']), '',
            '### 6. Strongest target-dependent behavior','',
            'Descriptive operational definition: largest max–min range of target-mean effects within a model/view; sample SD is also shown. Not a significance test. Full context counts and endpoints are retained. Source: `'+prefix+'source_identity_overview.csv`.',
            self.markdown(self.overall.sort_values('target_range_delta_f1',ascending=False).groupby(['model','representation'],sort=False).head(1),
                ['added_source','model','representation','target_range_delta_f1','std_target_delta_f1','n_targets','n_coalition_contexts','row_id']), '',
            '### 7. Positive effects across many contexts','',
            'The following lists every source, including weak or inconsistent ones. mean_target_fraction_positive first computes the proportion of positive contexts within each target, then weights targets equally. targets_positive/negative classify target MEANS; neither is a guarantee for every coalition. Numerical sign tolerance is 1e-9, not a scientific equivalence margin. Source: `'+prefix+'source_identity_overview.csv`.',
            self.markdown(self.overall,['added_source','model','representation','mean_target_fraction_positive','targets_positive','targets_negative','n_targets','n_coalition_contexts']), '',
            '### 8. Direct evidence of coalition-conditional contribution','',
            'Below are automatically selected largest-spread examples per model/view where the SAME source has positive and negative existing marginal effects for the SAME target AND pool size, but different base coalitions. Every displayed context has five matched seeds. These extrema illustrate conditionality, not population frequency or causality. The full qualifying table is `'+prefix+'context_sign_reversals_same_target_and_size.csv`; negative_context_id/positive_context_id resolve original marginal_source_additions rows and before/after IDs.',
            self.markdown(self.reversals.sort_values('spread',ascending=False).groupby(['model','representation'],sort=False).head(1),
                ['target','added_source','model','representation','n_sources_before','n_contexts','negative_base_sources','negative_delta_f1','positive_base_sources','positive_delta_f1','row_id']), '',
            '### Interpretation limits and preservation','',
            'Adding a source may also change validation domains, early stopping and thresholds; the historical comparisons are not interventions that isolate only optimizer training data. Larger pools do not make a source intrinsically useful. No new statistical inference was performed. Causal source effects, universal source rankings, and sign-change claims comparing unmatched target cohorts are **NOT VERIFIED FOR PAPER**.',
            'The existing source-count, marginal-distribution and stable-feature PDFs remain unchanged and are retained alongside the two new interaction views. The new tables live under SOURCE_INTERACTIONS/ to avoid modifying earlier validated analytical tables. No approved final experimental-design PDF was found in the existing figure/analysis directories; no such figure was invented.']
        text='\n\n'.join(lines)
        (OUT/'SOURCE_IDENTITY_RESULTS.md').write_text('# Source-interaction manuscript results\n\n'+text+self.provenance())
        main=ADD/'ADDITIONAL_RESULTS_FOR_PAPER.md';backup=OUT/'evidence/ADDITIONAL_RESULTS_BEFORE_SOURCE_INTERACTIONS.md'
        if not backup.exists():shutil.copy2(main,backup)
        old=backup.read_text();head,tail=old.rsplit('## Data Sources and Traceability',1)
        main.write_text(head+'\n'+text+'\n\n## Data Sources and Traceability'+tail+'\n\nSource-interaction extension: `SOURCE_INTERACTIONS/SOURCE_IDENTITY_RESULTS.md`, `SOURCE_INTERACTIONS/TRACEABILITY.csv` and `SOURCE_INTERACTIONS/ARTIFACT_MANIFEST.json`. Original pre-extension report preserved in SOURCE_INTERACTIONS/evidence/. The parent ARTIFACT_MANIFEST.json remains the historical pre-extension snapshot; its report hash is superseded only by the revision entry in the extension manifest.\n')
        self.report_revision={'original_sha256':sha(backup),'updated_sha256':sha(main),'backup':rel(backup),'updated':rel(main)}

    def collect(self):
        finalaudit=self.read(PREVIOUS/'FIGURE_VALIDATION.json')
        addmanifest=self.read(ADD/'ARTIFACT_MANIFEST.json')
        # Exact source table keys for previously validated figures; no rerendering here.
        descriptions=[
            ('01','lodo_by_target',PREVIOUS,'5.3 Cross-Dataset Generalization','Controlled LODO performance across unseen targets.',
             AN/'SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/lodo_by_target.parquet','target, model, representation, test_f1_mean','All targets/models/views; saved seed means; no pooled test samples.'),
            ('02','id_ood_common_test_gap',PREVIOUS,'5.3 Cross-Dataset Generalization','ID minus OOD F1 evaluated on exactly the same holdout.',
             AN/'SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/id_ood_same_test.parquet','target, model, representation, gap_f1_mean','All saved target/model/view means over paired seeds; identical evaluated holdout.'),
            ('03','generalization_vs_source_count',ADD/'figures','5.4 Source-Dataset Contribution','Historical OOD F1 versus effective source-pool size. Each target receives equal weight after seed and coalition aggregation. Bands show target IQR; the detached six-source point uses fewer eligible targets.',
             ADD/'tables/performance_by_source_count_macro.parquet','model, representation, n_sources, n_targets, f1_mean, f1_q25, f1_q75','All historical usable effective coalitions; seed mean then coalition mean inside target, then equal targets. Seven targets for1..5, five for6; no connection across cohort change.'),
            ('04','marginal_gain_per_added_source',ADD/'figures','5.4 Source-Dataset Contribution','Historical distributions of marginal F1 after adding one source to nested pools. Boxes show context-level quartiles after matched-seed aggregation; coalition contexts are not independent targets.',
             ADD/'tables/marginal_source_additions.parquet','model, representation, n_sources_before, delta_f1, n_seed_pairs','All valid nested edges; saved matched-seed means; boxes median/IQR,1.5IQR whiskers,all fliers. After minus before; zero reference.'),
            ('05','marginal_gain_by_source_and_pool_size',OUT/'figures','5.4 Source-Dataset Contribution','Marginal source effects conditional on existing pool size. Each target has equal weight after matched-seed and within-target context aggregation. Positive values indicate higher F1 after adding the source; gray denotes missing/ineligible cells.',
             OUT/'tables/marginal_gain_by_added_source_and_pool_size.parquet','added_source, model, representation, n_sources_before, n_targets, n_coalition_contexts, mean_target_delta_f1','All eligible added sources/models/views/sizes. Existing matched seeds within exact S→S∪{D}; then contexts within target/source/k; then equal targets. k5→6 has reduced eligible targets.'),
            ('06','marginal_gain_by_source_and_target',OUT/'figures','5.4 Source-Dataset Contribution','Mean marginal target F1 change when a source was added across all valid existing coalition contexts—not one dataset-addition order. Positive means improvement after addition; gray denotes missing/ineligible pairs.',
             OUT/'tables/marginal_gain_by_added_source_target.parquet','added_source, target, model, representation, n_valid_coalition_contexts, n_seed_pairs, mean_delta_f1','All eligible source/target pairs and all nonempty S excluding D; same target/model/view and matched seeds. Equal contexts after seed means; NOT equal size-level means, no cross-target aggregation per cell.'),
            ('07','source_contribution',PREVIOUS,'5.4 Source-Dataset Contribution','Controlled full-pool F1 minus source-removed F1. Validation/test are fixed; eligible seed means are shown, and gray combinations remain ineligible.',
             AN/'SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/source_contribution_by_target.parquet','target, removed_source, model, representation, delta_f1_mean','Controlled supplement, not the historical all-coalition analysis. Same eligible matched seeds; full minus removed. Shared symmetric zero-centered scale.'),
            ('08','selected_score_shift',PREVIOUS,'5.5 Decision Behavior','Saved score distributions for the previously selected representative largest-oracle-gap condition. Oracle selection is diagnostic; source-validation and target-test histograms are stratified by class.',
             AN/'SUPPLEMENTAL_CONTROLLED_ANALYSIS/derived/selected_score_histograms.parquet','role, label, left, right, fraction, experiment_ids','Existing selected_runs/cases first largest_oracle_gap ID; exact singleton experiment_ids filter. Plot existing fraction at (left+right)/2. No scores or predictions recomputed.'),
            ('09','cross_dataset_stable_features',ADD/'figures','5.6 Feature Stability','Most stable engineered features across unseen targets in historical CatBoost LODO. Top-10 frequency is the proportion of eligible target/seed models containing the feature among their ten highest-ranked engineered features. This is recurrence, not causal transferability.',
             ADD/'tables/top10_cross_dataset_stable_features.parquet','representation, feature, top_k_frequency, rank_mean, importance_mean','Historical CatBoost lex64 LODO C. Exactly10/view ordered frequency descending,mean rank ascending,importance descending; saved importance/frequency unchanged.'),
            ('10','canonicalization_effect',PREVIOUS,'5.7 Canonicalization and Dataset Separability','Controlled paired F1 difference CANONICALIZED minus RAW on identical samples and partitions, summarized over seeds.',
             AN/'SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/canonicalization_by_target.parquet','target, model, delta_test_f1_mean','Exact existing RAW/CAN pairs; mean paired seed deltas. Zero-centered symmetric scale; losses retained.'),
            ('11','controlled_separability',PREVIOUS,'5.7 Canonicalization and Dataset Separability','Balanced dataset-origin macro-F1 for all classes, benign-only and malicious-only conditions. Bars are saved seed means ±SD; dashed line is the uniform balanced asymptotic reference.',
             AN/'SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/separability.parquet','condition, representation, origin_macro_f1_mean, origin_macro_f1_std, origin_chance_accuracy_uniform_mean','Order all,benign,malicious; RAW/CAN. Preserved balanced-source conditions, saved seed SD and chance reference (not a confidence interval).'),
        ]
        FINAL.mkdir(exist_ok=True)
        expected={number+'_'+name+'.pdf' for number,name,*_ in descriptions}|{'LATEX_FIGURE_INDEX.md','MANUSCRIPT_FIGURE_TRACEABILITY.md'}
        assert not (set(p.name for p in FINAL.iterdir())-expected),'Unexpected files in final manuscript directory; do not delete them automatically.'
        index=['# LaTeX manuscript figure index','',
            'The clean inclusion directory contains final PDFs plus the two explicitly requested index/traceability documents; PNGs, analytical tables and scripts remain outside it. All figures are intended for full two-column width (174 mm); use figure* in a two-column manuscript. Proposed order follows the Results narrative. No approved final experimental-design PDF was found; 00 is deliberately omitted.','']
        trace=['# Manuscript figure traceability','',
            'All earlier PDFs were copied byte-for-byte after checking their existing validation-manifest hashes. New source-interaction figures use saved historical matched edges only. No originals were moved, deleted or rerendered. Model labels: Logistic Regression, CatBoost, MLP; representations: RAW, CANONICALIZED. Original analytical figures and metrics remain unchanged; only the explicitly requested Results-report extension was applied, with a preserved pre-extension copy.', '',
            f'Collection script: `{rel(Path(__file__))}`. Command: `{COMMAND}`.',
            f'New interaction evidence: `{rel(OUT)}`. Pair checks: `derived/input_pair_verification.parquet`. Total valid contexts={len(self.edges)}; matched seed pairs={len(self.pairs)}; five matched seeds/context. Both analyses cover this same set; counting an edge in multiple summaries does not create independent observations.',
            'Analysis A: seed-matched nested edge means → equal coalition contexts within each target/source/model/view/k → equal targets. Analysis B: seed-matched nested edge means → equal contexts within source/target/model/view across all eligible sizes. Ineligible cells remain absent and plot gray; never zero-filled. No inference treats contexts or seeds as independent targets.', '']
        for number,name,folder,section,purpose,table,cols,aggregation in descriptions:
            source=folder/(name+'.pdf');target=FINAL/(number+'_'+name+'.pdf')
            expectedhash=(finalaudit['output_sha256'][name+'.pdf'] if folder==PREVIOUS else
                          addmanifest['outputs']['figures/'+name+'.pdf']['sha256'] if folder==ADD/'figures' else sha(source))
            assert sha(source)==expectedhash,(source,'validation hash mismatch')
            if target.exists():assert sha(target)==expectedhash,'Different final PDF already exists; needs explicit version resolution.'
            else:shutil.copy2(source,target)
            assert sha(target)==sha(source)
            self.copies.append(dict(filename=target.name,original_pdf=rel(source),source_table=rel(table),sha256=sha(target)))
            label='fig:'+name.replace('_','-')
            index += [f'## {number} — {name.replace("_"," ")}','',f'Filename: `{target.name}`. Section: {section}.',
                f'Purpose: {purpose}',f'Source analytical table: `{rel(table)}`.',f'Label: `{label}`. Suggested width: `\\textwidth`.',
                '```latex\n\\includegraphics[width=\\textwidth]{figures/manuscript_final/'+target.name+'}\n```',
                'Suggested caption: '+purpose,'']
            supplementary=folder==PREVIOUS
            script=ROOT/'scripts/render_final_manuscript_figures.py' if supplementary else ADD/'scripts/additional_analyses.py' if folder==ADD/'figures' else Path(__file__)
            lineage=AN/'SUPPLEMENTAL_CONTROLLED_ANALYSIS/SOURCE_FILES.parquet' if supplementary else OUT/'SOURCE_LINEAGE.parquet' if folder==OUT/'figures' else ADD/'SOURCE_LINEAGE.parquet'
            command=sys.executable+' '+rel(script)
            if supplementary:command+=' --overwrite  # backups preserved by renderer; NOT executed in this task'
            trace += [f'## {target.name}','',f'- Final PDF: `{rel(target)}`.',f'- Original PDF (copied): `{rel(source)}`.',
                f'- Source Parquet: `{rel(table)}`; corresponding CSV: `{rel(table.with_suffix(".csv"))}`.',
                f'- Columns: {cols}; experiment_ids and row_id for lineage.',f'- Filters / aggregation: {aggregation}',
                f'- Experiment IDs: in source analytical rows; original artifact mapping: `{rel(lineage)}`.',
                f'- Rendering script: `{rel(script)}`.',f'- Rendering command: `{command}`.',
                f'- Collection command: `{COMMAND}`.',f'- Final PDF SHA-256: `{sha(target)}`.']
            if number in ['05','06']:
                trace += ['- Matched contexts: '+str(len(self.edges))+' (sum n_coalition_contexts for A; sum n_valid_coalition_contexts for B), '+str(len(self.pairs))+' context-specific seed pairs. Every edge matches the same outer target/model/view/seed and exactly one added source.',
                    '- Missing policy: reindex visualization only; NaN/masked cells remain gray. See tables/source_target_cell_coverage.csv; no generated or imputed experiments.',
                    '- Scale: shared with the other new interaction figure, exactly zero-centered with symmetric bound '+repr(self.color_bound)+'. No rounding before plotting. Existing validation changes remain a methodological limitation.']
            if number=='08':
                trace += ['- Selection source: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/selected_runs/cases.parquet` (criterion,experiment_ids); selected ID: `'+finalaudit['selected_experiment_id']+'`.']
            trace.append('')
        suffix=f'''\n## Data Sources and Traceability

Per-figure sources, filters, aggregation, rendering scripts and original PDF paths are documented in MANUSCRIPT_FIGURE_TRACEABILITY.md in this directory. The collection and new analysis were performed by `{rel(Path(__file__))}`, command `{COMMAND}`. Full copy manifest and input/output hashes are in `{rel(OUT/'ARTIFACT_MANIFEST.json')}`. Each figure’s analytical source carries experiment_ids; follow the listed lineage file to original experimental artifacts. Historical source-count/coalition and feature-stability results remain separate from the controlled supplement. No models, predictions, importance metrics or validated source tables were altered.
'''
        (FINAL/'LATEX_FIGURE_INDEX.md').write_text('\n\n'.join(index)+suffix)
        (FINAL/'MANUSCRIPT_FIGURE_TRACEABILITY.md').write_text('\n\n'.join(trace)+suffix)

    def finish(self):
        pd.DataFrame(self.recipes).to_csv(OUT/'TRACEABILITY.csv',index=False)
        for p,info in self.inputs.items():assert sha(ROOT.parent/p)==info['sha256']
        assert len(list(FINAL.glob('*.pdf')))==11
        assert all(name in (FINAL/'LATEX_FIGURE_INDEX.md').read_text() for name in [c['filename'] for c in self.copies])
        for c in self.copies:assert sha(ROOT.parent/c['original_pdf'])==c['sha256']
        checks=dict(no_training=True,no_predictions=True,existing_metrics_unchanged=True,matched_nested_coalitions=True,
            matched_seeds=True,missing_not_zero_filled=True,equal_target_macro_weight=True,conditional_interpretation=True,
            all_11_pdfs_exist=True,index_matches=True,all_figures_have_sources=True,original_pdfs_unchanged=True,
            contexts=len(self.edges),seed_pairs=len(self.pairs),new_A_rows=len(self.a),new_B_rows=len(self.b),figures=self.graphics)
        (OUT/'FINAL_CHECK.json').write_text(json.dumps(checks,indent=2)+'\n')
        manifest={'generated_at':datetime.now(timezone.utc).isoformat(),'script':rel(Path(__file__)),'script_sha256':sha(__file__),
            'command':COMMAND,'inputs':self.inputs,'pdf_copies':self.copies,'report_revision':self.report_revision,
            'outputs':{rel(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in list(OUT.rglob('*'))+list(FINAL.iterdir())
                if p.is_file() and p.name!='ARTIFACT_MANIFEST.json' and '__pycache__' not in p.parts}}
        (OUT/'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(checks,indent=2))


if __name__=='__main__':
    task=Task()
    for step in ['validate','aggregate','figures','report','collect','finish']:
        print(datetime.now(timezone.utc).isoformat(),step,flush=True);getattr(task,step)()
