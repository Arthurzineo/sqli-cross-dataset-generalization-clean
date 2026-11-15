#!/usr/bin/env python3
"""Descriptive manuscript summaries of completed historical experiments only."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
from pathlib import Path
import hashlib
import itertools
import json
import math
import sys
import subprocess
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

OUT=Path(__file__).resolve().parents[1]
AN=OUT.parent
ROOT=AN.parent
FEATURE=AN/'M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability'
MODELS=['logistic','catboost','mlp']
REPS=['RAW','CANONICALIZED']
LABELS={'logistic':'Logistic Regression','catboost':'CatBoost','mlp':'MLP'}
COLORS={'RAW':'#0072B2','CANONICALIZED':'#D55E00'}
METRICS=['f1','mcc','pr_auc']
TOL=1e-9
COMMAND=' '.join([sys.executable,*sys.argv])


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def js(value):return json.dumps(value,sort_keys=True,ensure_ascii=False)
def members(value):return frozenset(filter(None,str(value).split('+')))
def pool(value):return '+'.join(sorted(value))
def ids(values):return js(sorted({eid for value in values for eid in json.loads(value)}))
def relative(path):return str(Path(path).relative_to(ROOT.parent))


class Analysis:
    def __init__(self):
        self.inputs={};self.recipes=[];self.frames={};self.used=set();self.notes=[]
        self.master=self.read(AN/'_global/master_results.parquet')
        self.lineage=self.read(AN/'_global/SOURCE_LINEAGE.parquet')
        datasets=self.read(AN/'M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_characterization.csv')
        self.family=datasets.drop_duplicates('dataset').set_index('dataset').family.to_dict()
        self.targets=sorted(datasets[datasets.primary].dataset.unique())
        self.seeds=sorted(self.master[(self.master.usable)&(self.master.experiment_type=='contribution')].seed.unique().astype(int))
        for name in ['tables','derived','figures']: (OUT/name).mkdir(exist_ok=True)
        plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8.5,
            'axes.titlesize':9,'xtick.labelsize':7.5,'ytick.labelsize':8,'legend.fontsize':8,
            'axes.linewidth':.6,'pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white'})

    def read(self,path):
        path=Path(path);self.inputs[relative(path)]={'sha256':sha(path),'bytes':path.stat().st_size}
        frame=pd.read_parquet(path) if path.suffix=='.parquet' else pd.read_csv(path,float_precision='round_trip')
        self.inputs[relative(path)]['rows']=len(frame)
        return frame

    def save(self,name,frame,recipe):
        frame=frame.copy().reset_index(drop=True)
        if 'experiment_ids' not in frame:frame['experiment_ids']='[]'
        for value in frame.experiment_ids:self.used.update(json.loads(value))
        if 'row_id' in frame:frame=frame.rename(columns={'row_id':'input_row_id'})
        frame['row_id']=[hashlib.sha256(js([name,i,str(row)]).encode()).hexdigest()[:24] for i,row in enumerate(frame.to_dict('records'))]
        path=OUT/(name+'.csv');frame.to_csv(path,index=False,float_format='%.17g')
        frame.to_parquet(path.with_suffix('.parquet'),index=False)
        pd.testing.assert_frame_equal(frame,pd.read_parquet(path.with_suffix('.parquet')))
        self.frames[name]=frame
        self.recipes.append(dict(artifact=name,source_files=js(list(self.inputs)),columns=js(list(frame.columns)),
            filter_aggregation=recipe,script=relative(Path(__file__)),command=COMMAND,lineage='SOURCE_LINEAGE.parquet'))
        return frame

    def features(self):
        csv=FEATURE/'tables/stable_features.csv';parquet=csv.with_suffix('.parquet')
        stable=self.read(csv)
        self.feature_parquet_exists=parquet.exists()
        if parquet.exists():pd.testing.assert_frame_equal(stable,self.read(parquet),check_dtype=False)
        # This snapshot is only a format conversion, NOT a claimed pre-existing counterpart.
        self.save('derived/historical_stable_features_snapshot',stable,
            'Exact values copied from historical stable_features.csv; original Parquet absent unless reported otherwise; no importance/rank/frequency recomputation.')
        stable=stable[stable.representation.isin(REPS)].copy()
        stable=stable.sort_values(['representation','top_k_frequency','rank_mean','importance_mean','feature'],
            ascending=[True,False,True,False,True],kind='stable')
        selected=stable.groupby('representation',sort=False).head(10)
        assert selected.groupby('representation').size().eq(10).all()
        wanted={eid for v in stable.experiment_ids for eid in json.loads(v)}
        run=self.master[self.master.experiment_id.isin(wanted)]
        assert run.usable.all() and run.experiment_type.eq('lodo_C_complete').all()
        assert run.model.eq('catboost').all() and run.feature_set.eq('lex64').all()
        # Validate only existing saved ranks; never compute an importance or rerank a model.
        ranks=self.read(FEATURE/'derived/selected_feature_importances.parquet')
        ranks=ranks[ranks.experiment_id.isin(wanted)]
        counts=ranks.assign(in_top10=ranks['rank']<=10).groupby('experiment_id').in_top10.sum()
        assert counts.eq(10).all() and set(counts.index)==wanted
        columns=['representation','feature','top_k_frequency','rank_mean','rank_std','importance_mean','importance_std','n_runs','n_seeds','seeds','experiment_ids','row_id']
        self.top=self.save('tables/top10_cross_dataset_stable_features',selected[columns],
            'Historical CatBoost lex64 LODO C only; order frequency descending, mean rank ascending, mean importance descending, feature name deterministic last tie-break. Exactly 10/view. All statistics copied unchanged; no combined score.')
        self.feature_runs=run

    def coalitions(self):
        d=self.master
        contribution=d[d.experiment_type.eq('contribution')].copy()
        mask=(contribution.usable & contribution.pilot.eq(0) & contribution.feature_set.eq('lex64') &
              contribution.model.isin(MODELS) & contribution.representation.isin(REPS))
        excluded=contribution[~mask][['experiment_id','target_dataset','model','representation','status','exclusion_reason']].copy()
        excluded['experiment_ids']=excluded.experiment_id.map(lambda x:js([x]))
        self.save('tables/excluded_historical_runs',excluded,'All historical contribution records outside usable/nonpilot/lex64/RAW-CAN/three-model filter; preserve existing exclusion reason.')
        c=contribution[mask].copy();self.raw=c;assert c.experiment_id.is_unique
        assert c[METRICS].notna().all().all()
        assert np.isfinite(c[METRICS].to_numpy()).all()
        assert not c.duplicated(['target_dataset','model','representation','training_datasets','seed']).any()
        rows=[];dup=[]
        keys=['target_dataset','model','representation','effective_development_datasets','seed']
        for key,g in c.groupby(keys,sort=True):
            target,model,rep,sources,seed=key;actual=members(sources)
            assert target not in actual and actual
            assert all(self.family[s]!=self.family[target] for s in actual)
            assert all(members(x)|members(y)==actual for x,y in zip(g.actual_train_datasets,g.validation_datasets))
            # Requested aliases collapse only when all saved metrics and partition metadata agree exactly.
            for col in METRICS+['actual_train_datasets','validation_datasets','split_counts','configuration_id','test_n','threshold_source']:
                assert g[col].nunique(dropna=False)==1,(key,col,'nonidentical aliases need manual adjudication')
            r=g.iloc[0]
            record=dict(target=target,model=model,representation=rep,sources=pool(actual),seed=int(seed),
                n_sources=len(actual),n_source_families=len({self.family[s] for s in actual}),
                actual_training_sources=r.actual_train_datasets,validation_sources=r.validation_datasets,
                n_actual_training_sources=len(members(r.actual_train_datasets)),configuration_id=r.configuration_id,
                requested_coalitions=js(sorted(g.training_datasets.unique())),n_requested_aliases=len(g),
                experiment_ids=js(sorted(g.experiment_id)),test_n=r.test_n)
            record.update({m:float(r[m]) for m in METRICS});rows.append(record)
            if len(g)>1:dup.append(record)
        self.effective=self.save('derived/effective_coalition_seed_results',pd.DataFrame(rows),
            'Only completed usable historical contribution lex64. Sources=effective union of training and validation datasets, after target-family purge. Collapse same-seed requested aliases ONLY after exact equality of F1/MCC/AP, threshold, configuration and saved split counts; retain ALL IDs. No metric recomputation.')
        self.save('tables/collapsed_requested_aliases',pd.DataFrame(dup),'Same exact duplicate-alias policy; these are not extra distinct source coalitions.')
        rows=[]
        for key,g in self.effective.groupby(['target','model','representation','sources'],sort=True):
            row=dict(zip(['target','model','representation','sources'],key));row.update(n_sources=int(g.n_sources.iloc[0]),
                n_source_families=int(g.n_source_families.iloc[0]),n_seeds=g.seed.nunique(),seeds=js(sorted(g.seed.astype(int))),
                n_actual_training_sources_min=int(g.n_actual_training_sources.min()),n_actual_training_sources_max=int(g.n_actual_training_sources.max()),
                experiment_ids=ids(g.experiment_ids))
            for m in METRICS:row[m+'_mean']=g[m].mean();row[m+'_seed_std']=g[m].std(ddof=1)
            rows.append(row)
        self.coal=self.save('derived/seed_aggregated_coalitions',pd.DataFrame(rows),
            'First equal-weight seed means inside exact target/model/view/effective source coalition; seed SD ddof=1. No pooling of coalitions or targets.')
        rows=[]
        for key,g in self.coal.groupby(['target','model','representation','n_sources'],sort=True):
            row=dict(zip(['target','model','representation','n_sources'],key));row.update(n_coalitions=len(g),n_seeds_min=g.n_seeds.min(),n_seeds_max=g.n_seeds.max(),experiment_ids=ids(g.experiment_ids))
            for m in METRICS:self.distribution(row,m,g[m+'_mean'])
            rows.append(row)
        self.bycount=self.save('tables/performance_by_source_count',pd.DataFrame(rows),
            'Each coalition contributes its seed mean once. Distribution across distinct effective coalitions of given size inside target/model/view: mean, median, sample SD, linear-interpolation q25/q75, min,max. All three metrics complete.')
        self.coverage()
        self.macro=self.make_macro(self.bycount,'tables/performance_by_source_count_macro','Available-target macro; n_targets explicitly changes at k=6.')
        common=sorted(set.intersection(*[set(g.target) for _,g in self.bycount.groupby('n_sources')]))
        self.common=common
        self.fixedmacro=self.make_macro(self.bycount[self.bycount.target.isin(common)],'tables/performance_by_source_count_macro_common_targets',
            'Fixed common target cohort across ALL observed source-count levels. Equal targets; sensitivity, not replacement of seven-target results.')

    @staticmethod
    def distribution(row,prefix,values):
        row.update({prefix+'_mean':values.mean(),prefix+'_median':values.median(),prefix+'_std':values.std(ddof=1),
            prefix+'_q25':values.quantile(.25),prefix+'_q75':values.quantile(.75),prefix+'_min':values.min(),prefix+'_max':values.max()})

    def make_macro(self,frame,name,note):
        rows=[]
        for key,g in frame.groupby(['model','representation','n_sources'],sort=True):
            row=dict(zip(['model','representation','n_sources'],key));row.update(n_targets=g.target.nunique(),targets=js(sorted(g.target)),
                n_coalitions_total=int(g.n_coalitions.sum()),experiment_ids=ids(g.experiment_ids))
            for m in METRICS:self.distribution(row,m,g[m+'_mean'])
            rows.append(row)
        return self.save(name,pd.DataFrame(rows),note+' Mean/median/SD/IQR/min/max across TARGET-level coalition means, never individual runs. Each target receives equal weight after seed and coalition aggregation.')

    def coverage(self):
        rows=[];missing=[]
        for target,model,rep in itertools.product(self.targets,MODELS,REPS):
            eligible={s for s in self.targets if self.family[s]!=self.family[target]}
            g=self.effective[(self.effective.target==target)&(self.effective.model==model)&(self.effective.representation==rep)]
            for k in range(1,7):
                q=g[g.n_sources==k];expected={pool(s) for s in itertools.combinations(sorted(eligible),k)}
                observed=set(q.sources)
                absent=[(s,seed) for s in sorted(expected) for seed in self.seeds if not ((q.sources==s)&(q.seed==seed)).any()]
                row=dict(target=target,model=model,representation=rep,n_sources=k,n_eligible_source_files=len(eligible),
                    n_eligible_source_families=len({self.family[s] for s in eligible}),expected_coalitions=len(expected),observed_coalitions=len(observed),
                    expected_seed_models=len(expected)*len(self.seeds),observed_seed_models=len(q),missing_seed_models=len(absent),
                    status='structurally_unavailable' if not expected else ('complete' if not absent and expected==observed else 'incomplete'),experiment_ids=ids(q.experiment_ids))
                rows.append(row)
                for sources,seed in absent:missing.append(dict(target=target,model=model,representation=rep,n_sources=k,sources=sources,seed=seed))
        self.cover=self.save('tables/coalition_coverage',pd.DataFrame(rows),'Combinatorial coverage of eligible effective source sets per target/model/view and saved expected seed set; absent levels never imputed.')
        self.save('tables/missing_coalition_seed_conditions',pd.DataFrame(missing,columns=['target','model','representation','n_sources','sources','seed']),
            'Expected eligible source coalition × observed design seed grid minus completed conditions. Structural impossibility is in coalition_coverage, not a failed run.')

    def additions(self):
        pairrows=[];edges=[]
        for (target,model,rep),g in self.effective.groupby(['target','model','representation'],sort=True):
            coalitions={members(s):q.set_index('seed') for s,q in g.groupby('sources')}
            eligible={s for s in self.targets if self.family[s]!=self.family[target]}
            for base,a in sorted(coalitions.items(),key=lambda item:pool(item[0])):
                for added in sorted(eligible-base):
                    after=base|{added}
                    if after not in coalitions:continue
                    b=coalitions[after];shared=sorted(set(a.index)&set(b.index))
                    if not shared:continue
                    selected=[]
                    for seed in shared:
                        before=a.loc[seed];later=b.loc[seed]
                        assert before.configuration_id==later.configuration_id
                        assert before.test_n==later.test_n
                        r=dict(target=target,model=model,representation=rep,base_sources=pool(base),added_source=added,
                            sources_after=pool(after),n_sources_before=len(base),n_sources_after=len(after),seed=int(seed),
                            validation_changed=before.validation_sources!=later.validation_sources,
                            validation_before=before.validation_sources,validation_after=later.validation_sources,
                            actual_training_sources_before=before.actual_training_sources,actual_training_sources_after=later.actual_training_sources,
                            added_source_in_actual_training=added in members(later.actual_training_sources),
                            configuration_id=before.configuration_id,
                            experiment_ids_before=before.experiment_ids,experiment_ids_after=later.experiment_ids,
                            experiment_ids=ids([before.experiment_ids,later.experiment_ids]))
                        for metric in METRICS:
                            r[metric+'_before']=before[metric];r[metric+'_after']=later[metric];r['delta_'+metric]=later[metric]-before[metric]
                        selected.append(r);pairrows.append(r)
                    q=pd.DataFrame(selected)
                    row={k:q[k].iloc[0] for k in ['target','model','representation','base_sources','added_source','sources_after','n_sources_before','n_sources_after']}
                    row.update(n_seed_pairs=len(q),seeds=js(shared),n_seed_before=len(a),n_seed_after=len(b),
                        unmatched_seeds_before=js(sorted(set(a.index)-set(shared))),unmatched_seeds_after=js(sorted(set(b.index)-set(shared))),
                        validation_changed_fraction=q.validation_changed.mean(),added_source_in_actual_training_fraction=q.added_source_in_actual_training.mean(),
                        experiment_ids_before=ids(q.experiment_ids_before),experiment_ids_after=ids(q.experiment_ids_after),experiment_ids=ids(q.experiment_ids))
                    for metric in METRICS:
                        for col in [metric+'_before',metric+'_after','delta_'+metric]:row[col]=q[col].mean()
                    edges.append(row)
        self.pairs=self.save('derived/matched_source_additions_per_seed',pd.DataFrame(pairrows),
            'Exact nested effective S to S∪{Di}, same outer target/model/view and seed. Delta=after-before of SAVED metrics. Target sample counts and saved config IDs equal. Config is not immutable per-run historical provenance. Validation switch explicitly recorded.')
        self.edges=self.save('tables/marginal_source_additions',pd.DataFrame(edges),
            'Mean of exactly matched-seed deltas per nested coalition edge; before and after averaged on identical seeds. All alias IDs retained. No unpaired fallback, unrelated coalitions, or no-op family-filtered sources.')
        self.gains=self.summarize_edges(self.edges,['model','representation','n_sources_before'],'tables/marginal_gain_by_pool_size')
        self.targetgains=self.summarize_edges(self.edges,['target','model','representation','n_sources_before'],'tables/marginal_gain_by_pool_size_target')
        rows=[]
        for key,g in self.targetgains.groupby(['model','representation','n_sources_before']):
            row=dict(zip(['model','representation','n_sources_before'],key));row.update(n_targets=len(g),experiment_ids=ids(g.experiment_ids))
            for m in METRICS:
                row['target_macro_mean_delta_'+m]=g['mean_delta_'+m].mean()
            for col in ['fraction_positive','fraction_negative','fraction_zero']:row['target_macro_'+col]=g[col].mean()
            rows.append(row)
        self.gainmacro=self.save('tables/marginal_gain_by_pool_size_target_macro',pd.DataFrame(rows),
            'First average nested edges inside outer target, then equal target means. Available target set shown; supplementary to descriptive edge-distribution table.')
        rows=[]
        for target,model,rep in itertools.product(self.targets,MODELS,REPS):
            n=len([s for s in self.targets if self.family[s]!=self.family[target]])
            for k in range(1,6):
                g=self.edges[(self.edges.target==target)&(self.edges.model==model)&(self.edges.representation==rep)&(self.edges.n_sources_before==k)]
                expected=math.comb(n,k)*(n-k) if k<n else 0
                rows.append(dict(target=target,model=model,representation=rep,n_sources_before=k,
                    expected_edges=expected,observed_edges=len(g),n_seed_pairs_min=g.n_seed_pairs.min(),n_seed_pairs_max=g.n_seed_pairs.max(),
                    status='structurally_unavailable' if expected==0 else ('complete' if len(g)==expected else 'incomplete'),experiment_ids=ids(g.experiment_ids)))
        self.edgecoverage=self.save('tables/marginal_edge_coverage',pd.DataFrame(rows),'Expected nested edges C(m,k)*(m-k), excluding empty coalition; observed matched-seed edges. Descriptive coverage only.')
        pertarget=self.summarize_edges(self.edges,['target','added_source','model','representation'],'tables/marginal_gain_by_added_source_target')
        rows=[]
        for key,g in self.edges.groupby(['added_source','model','representation']):
            source,model,rep=key;t=pertarget[(pertarget.added_source==source)&(pertarget.model==model)&(pertarget.representation==rep)]
            means=t.mean_delta_f1
            rows.append(dict(added_source=source,model=model,representation=rep,
                mean_delta_f1=means.mean(),median_delta_f1=g.delta_f1.median(),median_target_mean_delta_f1=means.median(),
                targets_helped=int((means>TOL).sum()),targets_harmed=int((means< -TOL).sum()),targets_neutral=int((means.abs()<=TOL).sum()),n_targets=len(t),
                fraction_positive=float((g.delta_f1>TOL).mean()),fraction_negative=float((g.delta_f1< -TOL).mean()),
                target_macro_fraction_positive=t.fraction_positive.mean(),target_macro_fraction_negative=t.fraction_negative.mean(),
                number_of_valid_additions=len(g),target_mean_std=means.std(ddof=1),target_mean_min=means.min(),target_mean_max=means.max(),
                experiment_ids=ids(g.experiment_ids)))
        self.sources=self.save('tables/marginal_gain_by_added_source',pd.DataFrame(rows),
            'mean_delta_f1 is equal-target macro of per-target edge means. median_delta_f1 and fraction_positive/negative describe edges; target_macro fractions provided separately. targets_helped/harmed classify TARGET mean at numerical tolerance1e-9; not universal quality, no independence of edges.')
        # End-to-end audit of selected derived deltas against the existing master, never raw predictions.
        rows=[];master=self.master.set_index('experiment_id')
        for r in self.pairs.sample(n=min(24,len(self.pairs)),random_state=2026).itertuples():
            a=json.loads(r.experiment_ids_before);b=json.loads(r.experiment_ids_after)
            for m in METRICS:
                recalculated=float(master.loc[b[0],m]-master.loc[a[0],m]);value=getattr(r,'delta_'+m)
                assert recalculated==value
                rows.append(dict(pair_row_id=r.row_id,metric=m,reported=value,reconstructed_from_master=recalculated,match=True,experiment_ids=r.experiment_ids))
        self.save('tables/derivation_audit',pd.DataFrame(rows),'24 reproducibly sampled seed-pairs ×3 saved metrics; exact arithmetic audit against master only. No predictions or original metrics reopened.')

    def summarize_edges(self,frame,keys,name):
        rows=[]
        for key,g in frame.groupby(keys,sort=True):
            if not isinstance(key,tuple):key=(key,)
            r=dict(zip(keys,key));r.update(n_additions=len(g),n_targets=g.target.nunique(),experiment_ids=ids(g.experiment_ids))
            for m in METRICS:
                v=g['delta_'+m]
                for label,value in [('mean',v.mean()),('median',v.median()),('std',v.std(ddof=1)),('q25',v.quantile(.25)),('q75',v.quantile(.75))]:r[label+'_delta_'+m]=value
                for label,value in [('positive',(v>TOL).mean()),('negative',(v< -TOL).mean()),('zero',(v.abs()<=TOL).mean())]:
                    r['fraction_'+label+('' if m=='f1' else '_'+m)]=value
            rows.append(r)
        return self.save(name,pd.DataFrame(rows),
            'Distribution of seed-aggregated nested edges, not independent targets. Means/median/sampleSD/linear quartiles; sign tolerance |delta|≤1e-9 numerical zero, NOT practical equivalence. No inference.')

    def figsave(self,name,fig,source,caption):
        fig.canvas.draw()
        fig.savefig(OUT/'figures'/f'{name}.pdf',metadata={'CreationDate':None,'ModDate':None})
        fig.savefig(OUT/'figures'/f'{name}.png',dpi=300)
        plt.close(fig)
        images=subprocess.check_output(['pdfimages','-list',str(OUT/'figures'/f'{name}.pdf')],text=True)
        assert len(images.strip().splitlines())==2
        self.recipes.append(dict(artifact='figures/'+name,source_files=js(source),columns='See source table',
            filter_aggregation=caption,script=relative(Path(__file__)),command=COMMAND,lineage='SOURCE_LINEAGE.parquet'))

    def figures(self):
        width=174/25.4
        fig,axes=plt.subplots(1,2,figsize=(width,4.3),layout='constrained')
        for ax,rep in zip(axes,REPS):
            g=self.top[self.top.representation==rep]
            ax.barh(np.arange(len(g)),g.top_k_frequency,color=COLORS[rep],height=.72)
            ax.set_yticks(range(len(g)),g.feature);ax.invert_yaxis();ax.set_xlim(0,1.05)
            ax.set_title(rep);ax.set_xlabel('Top-10 frequency');ax.set_xticks([0,.25,.5,.75,1])
            ax.spines[['top','right']].set_visible(False)
        fig.supxlabel('Proportion of LODO CatBoost models containing the feature in their Top-10',fontsize=7.5)
        self.figsave('cross_dataset_stable_features',fig,['tables/top10_cross_dataset_stable_features.csv'],
            'Most stable engineered features across unseen targets; CatBoost historical LODO C. Top-10 frequency = proportion of eligible LODO CatBoost models in which the feature appears among the ten highest-ranked engineered features. Ranking by frequency, then mean rank, then importance; bars only frequency; no causal claim.')
        fig,axes=plt.subplots(1,3,figsize=(width,3.5),sharey=True,layout='constrained')
        for ax,model in zip(axes,MODELS):
            for rep in REPS:
                g=self.macro[(self.macro.model==model)&(self.macro.representation==rep)].sort_values('n_sources')
                full=g[g.n_targets==len(self.targets)];partial=g[g.n_targets<len(self.targets)]
                ax.plot(full.n_sources,full.f1_mean,color=COLORS[rep],marker='o',ms=3,label=rep)
                ax.fill_between(full.n_sources,full.f1_q25,full.f1_q75,color=COLORS[rep],alpha=.15)
                ax.vlines(partial.n_sources,partial.f1_q25,partial.f1_q75,color=COLORS[rep],linewidth=1.4)
                ax.plot(partial.n_sources,partial.f1_mean,'o',ms=4,mfc='white',color=COLORS[rep])
            ax.set_title(LABELS[model]);ax.set_xticks(range(1,7));ax.set_ylim(0,1);ax.grid(axis='y',alpha=.15)
            ax.spines[['top','right']].set_visible(False)
        axes[0].set_ylabel('OOD F1')
        fig.supxlabel('Number of source datasets (training + validation pool)\nk ≤ 5: seven targets; k = 6: five targets (unconnected)',fontsize=7.5)
        fig.legend(*axes[0].get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
        self.figsave('generalization_vs_source_count',fig,['tables/performance_by_source_count_macro.csv'],
            'Each target receives equal weight after seed and coalition aggregation. Lines/bands: seven-target macro mean and IQR of target means at k=1..5. Detached hollow k=6: five-target macro mean with IQR across those targets; not connected because target cohort changes. Source count is effective train+validation pool, not optimizer-only files nor independent family count.')
        fig,axes=plt.subplots(1,3,figsize=(width,3.6),sharey=True,layout='constrained')
        for ax,model in zip(axes,MODELS):
            for offset,rep in [(-.18,'RAW'),(.18,'CANONICALIZED')]:
                g=self.edges[(self.edges.model==model)&(self.edges.representation==rep)]
                values=[g[g.n_sources_before==k].delta_f1.to_numpy() for k in range(1,6)]
                boxes=ax.boxplot(values,positions=np.arange(1,6)+offset,widths=.30,patch_artist=True,manage_ticks=False,
                    showfliers=True,flierprops={'markersize':1.6,'markeredgewidth':.3,'markeredgecolor':COLORS[rep]},
                    medianprops={'color':'black','linewidth':.8},whiskerprops={'linewidth':.6},capprops={'linewidth':.6})
                for box in boxes['boxes']:box.set(facecolor=COLORS[rep],alpha=.65,linewidth=.6)
                ax.plot([],[],color=COLORS[rep],lw=5,label=rep)
            ax.axhline(0,color='#333333',lw=.8,ls='--');ax.set_title(LABELS[model])
            ax.set_xticks(range(1,6),[f'{k}→{k+1}' for k in range(1,6)],rotation=45)
            ax.spines[['top','right']].set_visible(False)
        axes[0].set_ylabel('ΔF1 after adding one source')
        fig.supxlabel('Source-pool size before → after',fontsize=8)
        fig.legend(*axes[0].get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
        self.figsave('marginal_gain_per_added_source',fig,['tables/marginal_source_additions.csv'],
            'Distribution across nested effective coalition edges after matched-seed averaging; same target/model/view before/after. Boxes q25/median/q75, whiskers 1.5 IQR, all fliers shown. Edges are not independent targets. Changes may include validation/early-stopping/threshold selection; 5→6 lacks the two site targets. Zero line explicit; numerical sign tolerance1e-9 is not practical equivalence.')

    @staticmethod
    def mdtable(frame,columns):
        def fmt(x):return f'{x:.6f}' if isinstance(x,(float,np.floating)) else str(x)
        return '\n'.join(['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']+
            ['| '+' | '.join(fmt(r[c]) for c in columns)+' |' for _,r in frame.iterrows()])

    def provenance(self):
        return f'''\n## Data Sources and Traceability

Script: `{relative(Path(__file__))}`. Command: `{COMMAND}`.
Inputs and output SHA-256: `ARTIFACT_MANIFEST.json`. Exact filters, columns and aggregation recipes: `TRACEABILITY.csv`.
Primary analytical input: `{relative(AN/'_global/master_results.parquet')}`; only usable historical contribution/lex64/nonpilot models and RAW/CANONICALIZED, plus historical LODO C CatBoost IDs for features. No supplemental results are mixed in.
Every output table has row_id and experiment_ids. Resolve IDs with `SOURCE_LINEAGE.parquet`, which preserves original metric, feature-importance, manifest, predictions and score paths without opening those files. Nested-edge tables also expose before/after IDs; per-seed matches are in `derived/matched_source_additions_per_seed.parquet`. Formatting-only feature snapshot and original input-row IDs are preserved.
Seeds: equal weight within exact effective coalition; nested edges use only identical seeds. Coalition distribution: equal distinct effective pools after verified duplicate alias collapse. Target macro: equal outer-target means, not weighting by number of coalitions. Marginal effects: after minus before of saved F1/MCC/AP; sample SD uses ddof=1; quartiles use linear interpolation; |delta|≤1e-9 is numerical zero, not practical equivalence. No hypothesis tests, predictions, training or importance recomputation.
Generated tables/figures, source paths/row filters and formulas are listed in TRACEABILITY.csv. Exact source-value audits are in tables/derivation_audit.csv. Scientific coverage checks: tables/coalition_coverage.csv and tables/marginal_edge_coverage.csv. Unavailable or unsupported conclusions are explicitly NOT VERIFIED FOR PAPER.
'''

    def reports(self):
        self.lineage[self.lineage.experiment_id.isin(self.used)].to_parquet(OUT/'SOURCE_LINEAGE.parquet',index=False)
        assert self.used<=set(self.lineage.experiment_id)
        featuretext=['# Cross-dataset stable features — traceability','',
            f'Source CSV: `{relative(FEATURE/"tables/stable_features.csv")}`. Requested historical Parquet counterpart exists: **{self.feature_parquet_exists}**.',
            'The absent historical Parquet was not replaced by the supplemental table with the same basename. `derived/historical_stable_features_snapshot.parquet` is an explicitly new format-only copy of the historical CSV, not an original counterpart.',
            'Filter: historical lodo_C_complete, CatBoost, lex64, RAW/CANONICALIZED, eligible completed runs. Saved source table already contains aggregation. The selected statistics are copied exactly, not recalculated. Ranking: Top-10 frequency descending; mean rank ascending; mean importance descending; feature-name last tie-break. Exactly ten features per view.',
            'Top-10 frequency = proportion of eligible LODO CatBoost models in which the feature appears among the ten highest-ranked engineered features. The original routine used saved average rank ≤10; its saved ranks were checked to select exactly ten in all eligible models (no boundary-tie ambiguity here).',
            f'Eligibility: {len(self.feature_runs)} models total, {self.feature_runs.seed.nunique()} seeds, {self.feature_runs.target_dataset.nunique()} targets. Each view has 35 models. Source importance units are CatBoost native importance points, not causal effects. See copied n_runs/n_seeds in the output table.',
            'Output table: `tables/top10_cross_dataset_stable_features.csv` and .parquet. Figure: `figures/cross_dataset_stable_features.pdf` and 300-dpi .png. All experiment IDs are in the table; original sources resolve through SOURCE_LINEAGE.parquet. Output hashes are in ARTIFACT_MANIFEST.json.',
            'Terminology: **most stable features across unseen targets**. These are not demonstrated best transferable features, and no causal ranking is claimed.']
        (OUT/'FEATURE_STABILITY_TRACEABILITY.md').write_text('\n\n'.join(featuretext)+self.provenance())
        lines=['# Additional manuscript results','',
            'Descriptive re-use of completed historical results only. No fit, importance, model prediction or statistical test was recomputed. F1/MCC/AP originals remain unchanged; this analysis computes only requested summaries and nested differences.', '',
            '## Scope and scientific checks','',
            f'Eligible completed historical source-composition runs: **{len(self.raw)}**. After collapsing identical requested aliases at the same seed: **{len(self.effective)}** effective coalition/seed conditions; **{len(self.coal)}** seed-aggregated target/model/view/coalition conditions. Source: `derived/effective_coalition_seed_results.csv` and `derived/seed_aggregated_coalitions.csv` (all rows).',
            f'Targets: {", ".join(self.targets)}; models: Logistic Regression, CatBoost, MLP; RAW/CANONICALIZED; seeds: {self.seeds}. Seed coverage and absence are recorded, never filled.',
            '**Meaning of S:** the effective development pool (union of training and validation sources), after the historical target-family exclusion. This is the coalition specified to the training procedure, NOT necessarily the files seen by the optimizer. `n_actual_training_sources_min/max` and per-seed validation/training lists expose the distinction. A literal optimizer-only source-diversity effect independent of validation: NOT VERIFIED FOR PAPER.',
            'site_cooking and site_sqli share site_lab. When either is the target, the other is purged, so only five source files are eligible. For the other targets six source files include these two related sources; six files do not mean six independent families. Requested aliases have exactly identical saved metrics, threshold and split-count metadata; they are counted once with all IDs preserved. Seven outer targets include only six provenance families. No inferential p-values are produced.',
            'Coverage per source-count level (take each target/model/view separately; counts vary combinatorially):',
            self.mdtable(self.cover[(self.cover.model=='catboost')&(self.cover.representation=='RAW')],['target','n_sources','expected_coalitions','observed_coalitions','missing_seed_models','status']),
            'Source: `tables/coalition_coverage.csv`, filter model=catboost, representation=RAW; all model/view checks in full table. Structural absence at k=6 for site targets is NOT an execution failure. `tables/missing_coalition_seed_conditions.csv` enumerates any genuine missing seeds.',
            f'Nested edges: **{len(self.edges)}**, using **{len(self.pairs)}** matched-seed pairs. All edges match target/model/representation and saved configuration ID; no unpaired fallback. Historical config IDs were derived from current configuration, not immutable per-run snapshots. `tables/marginal_edge_coverage.csv` gives exact expected/observed counts.',
            f'Validation source changes in **{int(self.pairs.validation_changed.sum())}/{len(self.pairs)}** seed pairs; the added source is in optimizer training in **{int(self.pairs.added_source_in_actual_training.sum())}/{len(self.pairs)}** pairs. These counts are read from `derived/matched_source_additions_per_seed.csv` (boolean filters). Marginal gains measure the whole historical procedure, not a causal isolated addition of training examples.', '',
            '## 1. How does OOD F1 change as source-pool size increases?','',
            self.mdtable(self.macro,['model','representation','n_sources','n_targets','f1_mean','f1_q25','f1_q75']),
            'Source: `tables/performance_by_source_count_macro.csv`; each displayed row identifies its filter. **Each target receives equal weight after seed and coalition aggregation.** Band: IQR across target coalition-means, not confidence interval. Use seven-target results for k=1..5. At k=6 only five targets remain; never attribute the cross-cohort difference between k=5 and k=6 solely to source count.',
            'Fixed common-target sensitivity uses '+', '.join(self.common)+':',
            self.mdtable(self.fixedmacro[self.fixedmacro.n_sources.isin([1,6])],['model','representation','n_sources','n_targets','f1_mean']),
            'Source: `tables/performance_by_source_count_macro_common_targets.csv`, n_sources in {1,6}. Intermediate levels are also available. This preserves identical targets across the whole range, without dropping any result from the main available-target tables.', '',
            '## 2–3. Diminishing marginal benefit and frequency of negative additions','',
            self.mdtable(self.gains,['model','representation','n_sources_before','n_additions','mean_delta_f1','median_delta_f1','fraction_negative','fraction_positive','fraction_zero']),
            'Source: `tables/marginal_gain_by_pool_size.csv`; rows match model/view/k. These means and fractions describe nested EDGES after matched-seed aggregation, not independent target observations. Equal-target counterparts are in `tables/marginal_gain_by_pool_size_target_macro.csv`.',
            self.mdtable(self.gainmacro,['model','representation','n_sources_before','n_targets','target_macro_mean_delta_f1','target_macro_fraction_negative']),
            'Source: `tables/marginal_gain_by_pool_size_target_macro.csv`; row filters are the displayed keys. Compare k=1..4 within seven targets; k=5 involves five targets. There is no fitted diminishing-returns law or inferential test.', '']
        for (model,rep),g in self.gains.groupby(['model','representation']):
            r=g.loc[g.fraction_negative.idxmax()]
            v=self.gainmacro[(self.gainmacro.model==model)&(self.gainmacro.representation==rep)&(self.gainmacro.n_sources_before<=4)].sort_values('n_sources_before')
            decreasing=bool((np.diff(v.target_macro_mean_delta_f1)<=0).all())
            lines.append(f'{LABELS[model]} / {rep}: highest negative-addition fraction at {int(r.n_sources_before)}→{int(r.n_sources_before)+1}: **{r.fraction_negative:.6f}** ({int(r.n_additions)} edges; marginal_gain_by_pool_size.csv row_id `{r.row_id}`). Across the fixed seven-target transitions 1→2 through 4→5, macro mean benefit decreases at every step: **{decreasing}** (target_macro table, same model/view, n_sources_before≤4). This is descriptive, not a universal diminishing-returns claim.')
        lines+=['','## 4–5. Representations and model-dependent behavior','',
            'Use the complete model/view curves above, not only the best line. The RAW/CANONICALIZED historical datasets came from separate files; identical payload populations across views are not established by these coalition summaries. A causal canonicalization effect from these curves is **NOT VERIFIED FOR PAPER**. Within each view, nested comparisons preserve the target and matched seed; dataset size, validation selection and source composition can all change.',
            'Numeric end-point differences on the SAME seven targets (k=1 vs k=5):']
        for model,rep in itertools.product(MODELS,REPS):
            g=self.macro[(self.macro.model==model)&(self.macro.representation==rep)].set_index('n_sources')
            lines.append(f'- {LABELS[model]} / {rep}: F1 {g.loc[1,"f1_mean"]:.6f} → {g.loc[5,"f1_mean"]:.6f}; delta **{g.loc[5,"f1_mean"]-g.loc[1,"f1_mean"]:+.6f}**. Source: performance_by_source_count_macro.csv, model={model}, representation={rep}, n_sources∈{{1,5}}; IDs are the union of those two rows.')
        lines+=['','## 6–7. Sources with consistent positive versus target-dependent effects','',
            'The full table includes every source, model and view. mean_delta_f1 is TARGET-MACRO (each target first averages its nested edges); median/fractions are edge descriptive and labeled accordingly. targets_helped/harmed use the sign of each target’s mean effect. Do not describe any source as universally good or bad.',
            self.mdtable(self.sources,['added_source','model','representation','mean_delta_f1','targets_helped','targets_harmed','n_targets','fraction_positive','fraction_negative','number_of_valid_additions','target_mean_std']),
            'Source: `tables/marginal_gain_by_added_source.csv`, all rows. Target dependence is described by SD and min/max of TARGET mean gains, not a new stability score. Exact target-specific signs and values are in `tables/marginal_gain_by_added_source_target.csv`.']
        for (model,rep),g in self.sources.groupby(['model','representation']):
            ranked=g.assign(helped_fraction=g.targets_helped/g.n_targets).sort_values(['helped_fraction','target_macro_fraction_positive','mean_delta_f1'],ascending=False)
            best=ranked.iloc[0];var=g.loc[g.target_mean_std.idxmax()]
            lines.append(f'{LABELS[model]} / {rep}: most consistently positive by helped-target fraction, then target-macro positive-edge fraction: **{best.added_source}**, {int(best.targets_helped)}/{int(best.n_targets)} targets, macro ΔF1={best.mean_delta_f1:+.6f}; row_id `{best.row_id}`. Largest between-target SD: **{var.added_source}**, SD={var.target_mean_std:.6f}, target-mean range [{var.target_mean_min:+.6f}, {var.target_mean_max:+.6f}]; row_id `{var.row_id}`. Ties follow the declared order; this is not an intrinsic dataset-quality rank.')
        lines+=['','## 8. Which ten engineered features are most stable?','',
            self.mdtable(self.top,['representation','feature','top_k_frequency','rank_mean','rank_std','importance_mean','importance_std','n_runs','n_seeds']),
            'Source: `tables/top10_cross_dataset_stable_features.csv`, representation/feature keys; original stable_features.csv input_row_id and experiment_ids preserved. These are **most stable features across unseen targets**, not proven best transferable features. Importances are model-specific descriptive support, not causal contribution.', '',
            '## 9. How do stable-feature sets differ after canonicalization?','']
        raw=set(self.top[self.top.representation=='RAW'].feature);can=set(self.top[self.top.representation=='CANONICALIZED'].feature)
        lines += [f'Overlap: **{len(raw&can)}/10**. Shared: {", ".join(sorted(raw&can))}. RAW-only: {", ".join(sorted(raw-can))}. CANONICALIZED-only: {", ".join(sorted(can-raw))}. Source: top10_cross_dataset_stable_features.csv, set intersection/differences by representation, all selected rows; no new importance computation.',
            'A representation-dependent top-ten set does not demonstrate invariant features or causal improvement. Historical RAW/CAN population differences remain a limitation.', '',
            '## Negative findings, limitations and manuscript use','',
            'Negative additions remain in all distributions and summaries, including boxplot fliers. Numerical zero is not practical equivalence. Coalition sizes have different numbers of combinations; full pools have one coalition, so within-level sample SD is undefined, not zero. The targets are not all independent provenance families. Repeated coalitions share runs and targets, so no p-values are computed from edges.',
            'Figure captions and exact figure-source mappings: TRACEABILITY.csv. Main figures: cross_dataset_stable_features, generalization_vs_source_count, marginal_gain_per_added_source (vector PDF plus 300-dpi PNG). Figure B1 uses a detached k=6 point to avoid presenting a target-cohort change as an extra-source gain. Its detached vertical interval is the IQR across five targets; earlier bands are IQR across seven target means.',
            'NOT VERIFIED FOR PAPER: causal feature effects; universally beneficial sources; a guaranteed monotonic/diminishing law; causal RAW/CAN gain on identical historical samples; optimizer-only diversity independent of validation; significance or generality beyond these targets. All reported numbers are descriptive and traceable, not inferential guarantees.']
        # Ensure CommonMark heading/list spacing.
        text='\n\n'.join(lines)+self.provenance()
        (OUT/'ADDITIONAL_RESULTS_FOR_PAPER.md').write_text(text)
        captions=['# Manuscript figure captions','']
        for recipe in self.recipes:
            if not recipe['artifact'].startswith('figures/'):continue
            captions.extend(['## '+recipe['artifact'],'',recipe['filter_aggregation'],'',
                'Data: '+recipe['source_files']+'. Output: '+recipe['artifact']+'.pdf and .png.',''])
        (OUT/'FIGURE_CAPTIONS.md').write_text('\n'.join(captions)+self.provenance())

    def finish(self):
        pd.DataFrame(self.recipes).to_csv(OUT/'TRACEABILITY.csv',index=False)
        for path,info in self.inputs.items():assert sha(ROOT.parent/path)==info['sha256']
        summary={'historical_runs':len(self.raw),'effective_seed_conditions':len(self.effective),'coalitions':len(self.coal),
            'nested_edges':len(self.edges),'matched_seed_pairs':len(self.pairs),
            'matched_seed_counts':sorted(self.edges.n_seed_pairs.unique().astype(int).tolist()),
            'missing_coalition_seed_conditions':len(self.frames['tables/missing_coalition_seed_conditions']),
            'incomplete_edge_conditions':int(self.edgecoverage.status.eq('incomplete').sum()),
            'feature_original_parquet_exists':self.feature_parquet_exists,'features_per_representation':self.top.groupby('representation').size().to_dict(),
            'training_runs_executed':0,'model_predictions_computed':0,'feature_importances_computed':0,'hypothesis_tests':0,
            'validation_switch_seed_pairs':int(self.pairs.validation_changed.sum()),'input_files_unchanged':True}
        (OUT/'VALIDATION.json').write_text(json.dumps(summary,indent=2)+'\n')
        manifest={'generated_at':datetime.now(timezone.utc).isoformat(),'script':relative(Path(__file__)),
            'command':COMMAND,'inputs':self.inputs,'outputs':{str(p.relative_to(OUT)):{'sha256':sha(p),'bytes':p.stat().st_size}
            for p in OUT.rglob('*') if p.is_file() and p.name!='ARTIFACT_MANIFEST.json' and '__pycache__' not in p.parts}}
        (OUT/'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(summary,indent=2))


if __name__=='__main__':
    analysis=Analysis()
    for step in ['features','coalitions','additions','figures','reports','finish']:
        print(datetime.now(timezone.utc).isoformat(),step,flush=True);getattr(analysis,step)()
