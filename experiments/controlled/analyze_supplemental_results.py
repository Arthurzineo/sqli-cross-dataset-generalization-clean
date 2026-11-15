#!/usr/bin/env python3
"""Post-hoc controlled-experiment analysis. Never fits models or reads checkpoints."""
import os
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '2'
import argparse
import itertools
import json
from pathlib import Path
import sys
import time
import resource
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.provenance import atomic_json, sha256, stable_hash, now

BASE = ROOT/'complementos_generalizacao_v1'
INPUT = BASE/'full/analysis'
OUTPUT = ROOT/'analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS'
MODELS = ['logistic', 'catboost', 'mlp']
REPS = ['RAW', 'CANONICALIZED']
METRICS = ['f1', 'mcc', 'pr_auc', 'precision', 'recall', 'fpr', 'fnr', 'roc_auc', 'balanced_accuracy', 'brier', 'ece_10']
COMMAND = f'{sys.executable} {Path(__file__).resolve()}'


def ids(frame):
    return json.dumps(sorted({i for value in frame.experiment_ids for i in json.loads(value)}))


def summarize(frame, keys, metrics):
    rows = []
    for key, group in frame.groupby(keys, dropna=False, sort=True):
        if not isinstance(key, tuple): key = (key,)
        row = dict(zip(keys, key)); row['experiment_ids'] = ids(group)
        row['n_observations'] = len(group)
        if 'seed' in group: row['n_seeds'] = group.seed.nunique()
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors='coerce').dropna()
            for suffix, value in [('mean', values.mean()), ('std', values.std(ddof=1)), ('median', values.median()),
                                  ('min', values.min()), ('max', values.max()), ('n', len(values))]:
                row[metric+'_'+suffix] = value
        rows.append(row)
    return pd.DataFrame(rows)


class Analysis:
    def __init__(self):
        self.reads = {}; self.trace = []; self.tables = {}; self.started = time.perf_counter()
        OUTPUT.mkdir(parents=True, exist_ok=True)
        self.master = self.read(INPUT/'master_results.parquet')
        self.lineage = self.read(INPUT/'SOURCE_LINEAGE.parquet').drop(columns='row_id', errors='ignore')
        assert self.master.experiment_id.is_unique
        assert self.master.execution_context.nunique() == 1, 'Separate distinct experimental contexts before analysis'
        assert (self.master.pilot_cap == 0).all()
        self.valid_ids = set(self.master.experiment_id)
        self.by_id = self.master.set_index('experiment_id')
        self.sources = self.lineage.set_index('experiment_id')
        first=self.read(self.master.original_metric_file.iloc[0])
        family=self.read(Path(first['cache'])/'cohort.parquet',columns=['dataset','family']).drop_duplicates()
        assert family.dataset.is_unique
        self.family=family.set_index('dataset').family.to_dict()
        self.lineage.to_parquet(OUTPUT/'SOURCE_FILES.parquet', index=False)
        self.tests = []

    def read(self, path, columns=None):
        path = Path(path)
        old=self.reads.get(str(path))
        projection='*' if columns is None else json.dumps(sorted(columns))
        if old:
            projection='*' if old['columns']=='*' or columns is None else json.dumps(sorted(set(json.loads(old['columns']))|set(columns)))
        self.reads[str(path)] = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha256(path),
                                 'columns': projection}
        if path.suffix == '.parquet': return pd.read_parquet(path, columns=columns)
        return json.loads(path.read_text())

    def table(self, name, frame, description, formula, section='5.8', rq='Cross-RQ'):
        frame = frame.copy().reset_index(drop=True)
        if 'experiment_ids' not in frame: raise ValueError('No row lineage: '+name)
        for value in frame.experiment_ids:
            assert set(json.loads(value)) <= self.valid_ids, name
        frame['row_id'] = [stable_hash([name, i, row])[:24] for i, row in enumerate(frame.astype(str).to_dict('records'))]
        path = OUTPUT/(name+'.csv'); path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False); frame.to_parquet(path.with_suffix('.parquet'), index=False)
        self.tables[name] = frame
        self.trace.append(dict(artifact_id=name, artifact_path=str(path), methodology_section='4.'+{'5.1':'3','5.2':'4','5.3':'6','5.4':'7','5.5':'8','5.6':'9','5.7':'10','5.8':'11','5.9':'12'}.get(section,'11'),
            tcc_section=section, research_question=rq, analysis_description=description,
            master_table_filter=description, source_file_manifest=str(OUTPUT/'SOURCE_FILES.parquet'),
            source_columns=json.dumps(list(frame.columns)), aggregation=formula,
            script=str(Path(__file__).resolve()), command=COMMAND, generated_at=now(),
            experiment_id_manifest=str(path.with_suffix('.parquet'))))
        return frame

    def figure(self, name, fig, table_name, caption):
        path = OUTPUT/'figures'/name; path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path.with_suffix('.png'), dpi=170, bbox_inches='tight')
        fig.savefig(path.with_suffix('.pdf'), bbox_inches='tight'); plt.close(fig)
        row = dict(next(x for x in self.trace if x['artifact_id']==table_name))
        row.update(artifact_id='figure_'+name, artifact_path=str(path.with_suffix('.png')),
                   analysis_description=caption, aggregation='Plot exact values from '+table_name,
                   experiment_id_manifest=str(OUTPUT/(table_name+'.parquet')))
        self.trace.append(row)
        self.trace.append(row|dict(artifact_id='figure_'+name+'_pdf',artifact_path=str(path.with_suffix('.pdf'))))

    def core(self):
        m = self.master; lodo=m[m.kind=='lodo'].copy()
        self.table('tables/coverage', summarize(m,['kind','model','representation'],['runtime_seconds']),
                   'All completed non-pilot supplemental runs', 'Count runs; runtime per run', '5.1','Integrity')
        self.table('tables/lodo_per_run', lodo, 'kind=lodo; full target test', 'No aggregation', '5.3','RQ1')
        self.lodo_summary = self.table('tables/lodo_by_target', summarize(lodo,['target','model','representation'],['test_'+x for x in METRICS]+['threshold_drift','oracle_gap_f1','threshold_source']),
            'kind=lodo; same target/model/view', 'Mean/std/median/min/max over seeds inside target; AP not trapezoidal PR area', '5.3','RQ1')
        self.table('tables/lodo_macro_summary',summarize(self.lodo_summary,['model','representation'],['test_f1_mean','test_mcc_mean','test_pr_auc_mean']),
            'LODO target-level seed means', 'Unweighted mean and extrema over targets, never pooled test examples', '5.3','RQ1')
        self.gap = self.read(INPUT/'id_vs_ood_same_test.parquet')
        self.gap['ratio_f1'] = self.gap.f1_ood/self.gap.f1_id.replace(0,np.nan)
        self.gap_summary = self.table('tables/id_ood_same_test',summarize(self.gap,['target','model','representation'],['f1_id','f1_ood','gap_f1','ratio_f1']),
            'Matched ID/LODO with identical common-test sample IDs', 'gap=F1_ID-F1_OOD; ratio=OOD/ID per seed then summarize seeds', '5.3','RQ1')
        self.canonical = self.read(INPUT/'raw_vs_canonicalized_pairs.parquet')
        paired=self.canonical[self.canonical.kind=='lodo'].copy()
        self.canonical_summary=self.table('tables/canonicalization_by_target',summarize(paired,['target','model'],[c for c in paired if c.startswith('delta_') and not c.startswith('delta_origin')]),
            'kind=lodo; RAW/CANONICALIZED identical split within target/model/seed', 'CANONICALIZED-RAW per seed; summarize seeds', '5.7','RQ4')
        wins=[]
        for model,g in self.canonical_summary.groupby('model'):
            d=g.delta_test_f1_mean
            wins.append(dict(model=model,improved=int((d>1e-9).sum()),neutral=int((abs(d)<=1e-9).sum()),worsened=int((d< -1e-9).sum()),n_targets=len(g),experiment_ids=ids(g)))
        self.table('tables/canonicalization_win_tie_loss',pd.DataFrame(wins),'LODO; one seed-mean effect per target/model','Tolerance 1e-9; count target signs, not seed signs','5.7','RQ4')
        c=self.read(INPUT/'fixed_validation_contribution.parquet').copy()
        for idx,row in c.iterrows():
            full,removed=json.loads(row.experiment_ids); f=self.by_id.loc[full]; r=self.by_id.loc[removed]
            assert f.target==r.target and f.seed==r.seed and f.model==r.model and f.representation==r.representation
            for metric in METRICS:
                c.loc[idx,'full_'+metric]=f['test_'+metric]; c.loc[idx,'removed_'+metric]=r['test_'+metric]
                c.loc[idx,'delta_'+metric]=f['test_'+metric]-r['test_'+metric]
            c.loc[idx,'benefit_fpr']=r.test_fpr-f.test_fpr; c.loc[idx,'benefit_fnr']=r.test_fnr-f.test_fnr
            c.loc[idx,'full_train_n']=f.train_n; c.loc[idx,'removed_train_n']=r.train_n
        self.contribution=self.table('derived/source_contribution_per_seed',c,'kind=contribution_fixed_validation, matched full LODO','Full-removed for higher-is-better; benefit error rates=removed-full; same val/test IDs','5.4','RQ2')
        self.contribution_summary=self.table('tables/source_contribution_by_target',summarize(c,['target','removed_source','model','representation'],['delta_'+x for x in METRICS]+['benefit_fpr','benefit_fnr','delta_threshold']),
            'Full vs removed training source; frozen validation/test; eligible seeds only', 'Average seeds inside target/source/model/view; report n_seeds (validation-source eligibility varies)','5.4','RQ2')
        source_rows=[]
        for key,g in self.contribution_summary.groupby(['removed_source','model','representation']):
            delta=g.delta_f1_mean
            source_rows.append(dict(zip(['removed_source','model','representation'],key))|dict(n_targets=len(g),n_seeds_min=int(g.n_seeds.min()),n_seeds_max=int(g.n_seeds.max()),
                contribution_mean=delta.mean(),contribution_median=delta.median(),targets_helped=int((delta>1e-9).sum()),targets_harmed=int((delta< -1e-9).sum()),targets_neutral=int((abs(delta)<=1e-9).sum()),experiment_ids=ids(g)))
        self.source_summary=self.table('tables/source_summary',pd.DataFrame(source_rows),'Eligible target/source cells; not a universal source ranking','First seeds within target/source; then equal weight per observed target','5.4','RQ2')
        self.table('tables/negative_transfer',self.contribution_summary[self.contribution_summary.delta_f1_mean< -1e-9].sort_values('delta_f1_mean'),
            'All target/source/model/view cells with seed-mean full-minus-removed F1 < -1e-9','Removing this source improved F1; not causal or size-matched','5.4','RQ2')
        self.table('tables/positive_transfer',self.contribution_summary[self.contribution_summary.delta_f1_mean>1e-9].sort_values('delta_f1_mean',ascending=False),
            'All target/source/model/view cells with seed-mean contribution > 1e-9','Positive contribution: full exceeds removed','5.4','RQ2')
        self.decision=self.table('tables/decision_by_target',summarize(lodo,['target','model','representation'],['test_pr_auc','test_roc_auc','test_f1','threshold_source','threshold_drift','oracle_gap_f1','oracle_f1_diagnostic','test_fpr','test_fnr','test_brier','test_ece_10','validation_f1']),
            'LODO scores/threshold diagnostics; oracle never deployable','Source threshold from validation; drift=abs(source-oracle); oracle gap=F1_oracle-F1_source; seeds summarized','5.5','RQ3')

    def origin(self):
        m=self.master[self.master.kind=='separability']; rows=[]; controls=[]
        for r in m.itertuples():
            original=self.read(r.original_metric_file); v=original['metrics_origin']; cm=np.asarray(v['confusion_matrix'],dtype=float)
            assert len(set(cm.sum(axis=1)))==1,'Unequal test origin sizes'
            split=self.read(Path(original['split_file']).with_suffix('.json')); counts=pd.DataFrame(split['counts'])
            for part,g in counts.groupby('split'): assert g.n.nunique()==1, 'Unequal per-origin/class counts'
            a=split['audit']
            controls.append(dict(condition=r.condition,representation=r.representation,seed=r.seed,n_per_dataset_class=a['n_per_dataset_class'],
                removed_cross_origin_rows=a['removed_cross_origin_rows'],n_before=a['n_before'],n_after=a['n_after'],
                train_per_origin_class=int(counts[counts.split=='train'].n.iloc[0]),test_per_origin_class=int(counts[counts.split=='test'].n.iloc[0]),
                experiment_ids=json.dumps([r.experiment_id])))
            for i,target in enumerate(v['origin_order']):
                tp=cm[i,i]; precision=tp/cm[:,i].sum() if cm[:,i].sum() else 0; recall=tp/cm[i,:].sum()
                f1=2*tp/(cm[:,i].sum()+cm[i,:].sum())
                rows.append(dict(target=target,condition=r.condition,representation=r.representation,seed=r.seed,origin_f1=f1,origin_precision=precision,origin_recall=recall,experiment_ids=json.dumps([r.experiment_id])))
            assert np.isclose(np.mean([x['origin_f1'] for x in rows[-len(cm):]]),v['macro_f1'])
        self.origin_summary=self.table('tables/separability',summarize(m,['condition','representation'],['origin_macro_f1','origin_accuracy','origin_chance_accuracy_uniform']),
            'Balanced origins/classes; all/benign/malicious; multiclass logistic','Seeds summarized within condition/view; chance 1/K accuracy (macro-F1 only asymptotic balanced reference)','5.7','RQ4')
        self.origin_targets=self.table('tables/separability_by_origin',summarize(pd.DataFrame(rows),['target','condition','representation'],['origin_f1','origin_precision','origin_recall']),
            'Per-origin class F1 from saved multiclass confusion matrices','2*TP/(predicted support+true support); seed summaries','5.7','RQ4')
        self.table('tables/separability_controls',pd.DataFrame(controls),'Origin-classifier split manifests','Explicit shared-hash purge and equal per-origin/class partition sizes; no fit','5.7','RQ4')
        sep=self.canonical[self.canonical.kind=='separability']
        self.origin_deltas=self.table('tables/separability_paired_deltas',summarize(sep,['condition'],['delta_origin_macro_f1','delta_origin_accuracy']),
            'Paired origin classification on identical samples','CANONICALIZED-RAW within seed; only descriptive repeated-split variation','5.7','RQ4')

    def features(self):
        fm=self.master[(self.master.model=='catboost') & self.master.kind.isin(['lodo','contribution_fixed_validation'])]
        by_id={}; rows=[]
        for r in fm.itertuples():
            f=self.read(self.sources.loc[r.experiment_id,'feature_file']).sort_values('feature')
            assert len(f)==64 and f.feature.is_unique and np.isfinite(f.importance).all()
            total=f.importance.sum(); assert total>0
            f['importance_pct']=100*f.importance/total; f['rank']=stats.rankdata(-f.importance,method='average')
            f['top10']=f.feature.isin(f.sort_values(['importance_pct','feature'],ascending=[False,True]).head(10).feature)
            by_id[r.experiment_id]=f.set_index('feature')
            for z in f.itertuples(): rows.append(dict(target=r.target,representation=r.representation,seed=r.seed,kind=r.kind,removed_source=r.removed_source,
                feature=z.feature,importance_pct=z.importance_pct,rank=z.rank,top10=float(z.top10),experiment_ids=json.dumps([r.experiment_id])))
        feature_rows=self.table('derived/feature_importance_per_run',pd.DataFrame(rows),'CatBoost LODO + fixed-validation removals; engineered lexical features only',
            'Normalize built-in importance to 100%; average ranks for ties; top10 ties broken by feature name','5.6','RQ3')
        base=feature_rows[feature_rows.kind=='lodo']
        feature_target=summarize(base,['target','representation','feature'],['importance_pct','rank','top10'])
        self.table('tables/features_by_target',feature_target,'Full LODO CatBoost; 64 engineered features','Seed means within target','5.6','RQ3')
        self.feature_stable=self.table('tables/stable_features',summarize(feature_target,['representation','feature'],['importance_pct_mean','rank_mean','top10_mean']),
            'Full LODO CatBoost only; excludes removals to avoid unequal composition weights','First seeds within target; then equal target weights. Importance is model reliance, not causal or semantic invariance','5.6','RQ3')
        pairs=[]; deltas=[]
        def compare(a,b,kind,context):
            x=by_id[a]; y=by_id[b]; assert x.index.equals(y.index)
            topa=set(x[x.top10].index); topb=set(y[y.top10].index)
            result=context|dict(comparison=kind,spearman=stats.spearmanr(x['rank'],y['rank']).statistic,
                kendall=stats.kendalltau(x['rank'],y['rank']).statistic,jaccard_top10=len(topa&topb)/len(topa|topb),experiment_ids=json.dumps([a,b]))
            pairs.append(result)
            if kind=='source_removal':
                f=self.by_id.loc[a]; r=self.by_id.loc[b]
                for name in x.index:
                    deltas.append(context|dict(feature=name,delta_importance_pct=x.loc[name,'importance_pct']-y.loc[name,'importance_pct'],
                        delta_rank=x.loc[name,'rank']-y.loc[name,'rank'],delta_f1=f.test_f1-r.test_f1,delta_mcc=f.test_mcc-r.test_mcc,
                        delta_threshold=f.threshold_source-r.threshold_source,delta_fpr=f.test_fpr-r.test_fpr,delta_recall=f.test_recall-r.test_recall,experiment_ids=json.dumps([a,b])))
        for r in self.contribution[self.contribution.model=='catboost'].itertuples():
            a,b=json.loads(r.experiment_ids); compare(a,b,'source_removal',dict(target=r.target,representation=r.representation,seed=r.seed,removed_source=r.removed_source))
        for r in self.canonical[(self.canonical.model=='catboost') & self.canonical.kind.isin(['lodo','contribution_fixed_validation'])].itertuples():
            a,b=json.loads(r.experiment_ids); compare(a,b,'raw_vs_canonicalized',dict(target=r.target,representation='PAIRED',seed=r.seed,removed_source=r.removed_source,kind=r.kind))
        for (rep,seed),g in fm[fm.kind=='lodo'].groupby(['representation','seed']):
            for a,b in itertools.combinations(g.itertuples(),2):
                compare(a.experiment_id,b.experiment_id,'cross_target',dict(target=a.target,other_target=b.target,representation=rep,seed=seed))
        self.feature_pairs=self.table('derived/feature_rank_pairs',pd.DataFrame(pairs),'CatBoost lexical only; full-vs-removed, RAW/CANONICALIZED and target pairs',
            'Spearman and Kendall over tied 64-feature ranks; Jaccard on deterministic top10 sets; correlations not significance tests','5.6','RQ3')
        self.feature_effects=self.table('tables/source_removal_feature_effects',summarize(pd.DataFrame(deltas),['target','removed_source','representation','feature'],['delta_importance_pct','delta_rank','delta_f1','delta_mcc','delta_threshold','delta_fpr','delta_recall']),
            'Same-target full vs removed CatBoost; frozen val/test','Full-minus-removed importance/rank/performance; seeds averaged within source/target; not causal','5.6','RQ3')
        self.table('tables/feature_stability',summarize(self.feature_pairs,['comparison','representation'],['spearman','kendall','jaccard_top10']),
            'Descriptive rank-comparison pairs; pairs are dependent','Distribution across listed dependent pairs; no independence claim or inferential p-values','5.6','RQ3')

    def statistics(self):
        def wilcoxon_test(family,label,frame,column,minimum=5):
            values=frame[column].dropna().to_numpy(); p=np.nan; statistic=np.nan; reason='too few distinct targets'
            if len(values)>=minimum:
                if np.all(abs(values)<1e-12): statistic=0.;p=1.;reason='all differences zero'
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore'); result=stats.wilcoxon(values,alternative='two-sided',zero_method='wilcox',method='auto')
                    p=float(result.pvalue);statistic=float(result.statistic);reason='exploratory; targets share training pools'
            self.tests.append(dict(family=family,comparison=label,test='Wilcoxon signed-rank',unit='target seed-mean',n_units=len(values),
                statistic=statistic,p_value=p,effect_mean=float(np.mean(values)) if len(values) else np.nan,reason=reason,experiment_ids=ids(frame)))
        for model,g in self.canonical_summary.groupby('model'): wilcoxon_test('canonicalization','CAN-RAW '+model,g,'delta_test_f1_mean')
        for (model,rep),g in self.gap_summary.groupby(['model','representation']): wilcoxon_test('id_ood_gap',model+' '+rep,g,'gap_f1_mean')
        for (source,model,rep),g in self.contribution_summary.groupby(['removed_source','model','representation']):
            wilcoxon_test('source_contribution',source+' '+model+' '+rep,g,'delta_f1_mean')
        for rep,g in self.lodo_summary.groupby('representation'):
            wide=g.pivot(index='target',columns='model',values='test_f1_mean').dropna()
            result=stats.friedmanchisquare(*[wide[model] for model in MODELS])
            self.tests.append(dict(family='model_comparison',comparison=rep,test='Friedman',unit='target seed-mean',n_units=len(wide),statistic=result.statistic,
                p_value=result.pvalue,effect_mean=np.nan,reason='exploratory omnibus; no automatic post-hoc ranking',experiment_ids=ids(g)))
        def correlate(label,g,x,y):
            g=g.dropna(subset=[x,y]); n=len(g); p=stat=np.nan; reason='insufficient or constant target-level observations'
            if n>=5 and g[x].nunique()>1 and g[y].nunique()>1:
                result=stats.spearmanr(g[x],g[y]);stat=float(result.statistic);p=float(result.pvalue);reason='exploratory association, not causation'
            self.tests.append(dict(family='cross_rq_associations',comparison=label,test='Spearman',unit='target seed-mean',n_units=n,statistic=stat,p_value=p,
                effect_mean=np.nan,reason=reason,experiment_ids=ids(g)))
        decision=self.decision.merge(self.gap_summary,on=['target','model','representation'],suffixes=('','_gap'),validate='one_to_one')
        decision['experiment_ids']=[json.dumps(sorted(set(json.loads(a)+json.loads(b)))) for a,b in zip(decision.experiment_ids,decision.experiment_ids_gap)]
        for (model,rep),g in decision.groupby(['model','representation']):
            correlate('threshold drift vs common gap '+model+' '+rep,g,'threshold_drift_mean','gap_f1_mean')
            correlate('oracle gap vs OOD F1 '+model+' '+rep,g,'oracle_gap_f1_mean','test_f1_mean')
        # Origin-specific F1 can be associated with target-specific OOD, unlike a global macro score replicated over targets.
        rel=self.origin_targets[self.origin_targets.condition=='all'].merge(self.lodo_summary,on=['target','representation'],suffixes=('','_ood'),validate='one_to_many')
        rel['experiment_ids']=[json.dumps(sorted(set(json.loads(a)+json.loads(b)))) for a,b in zip(rel.experiment_ids,rel.experiment_ids_ood)]
        self.table('tables/separability_vs_generalization',rel,'Origin-specific F1, all-class controlled origin task, paired with OOD target F1','Separate tasks and splits; seeds averaged first; not a causal test','5.7','RQ4')
        for (model,rep),g in rel.groupby(['model','representation']): correlate('origin F1 vs OOD F1 '+model+' '+rep,g,'origin_f1_mean','test_f1_mean')
        rank=self.feature_pairs[self.feature_pairs.comparison=='source_removal'].copy()
        rank['instability']=1-rank.spearman
        rank=rank.merge(self.contribution[self.contribution.model=='catboost'][['target','removed_source','representation','seed','delta_f1']],
            on=['target','removed_source','representation','seed'],validate='one_to_one')
        rank['absolute_f1_change']=abs(rank.delta_f1)
        first=summarize(rank,['target','removed_source','representation'],['instability','delta_f1','absolute_f1_change'])
        second=summarize(first,['target','representation'],['instability_mean','delta_f1_mean','absolute_f1_change_mean'])
        related=second.merge(self.lodo_summary[self.lodo_summary.model=='catboost'],on=['target','representation'],suffixes=('','_ood'),validate='one_to_one')
        related['experiment_ids']=[json.dumps(sorted(set(json.loads(a)+json.loads(b)))) for a,b in zip(related.experiment_ids,related.experiment_ids_ood)]
        self.table('tables/feature_instability_relationships',related,'CatBoost removal rank instability; seeds then equal eligible source weights inside target',
            'Instability=1-Spearman; target aggregates paired with full OOD F1; exploratory associations only','5.6','RQ3')
        for rep,g in related.groupby('representation'):
            correlate('feature instability vs OOD F1 '+rep,g,'instability_mean_mean','test_f1_mean')
            correlate('feature instability vs absolute removal F1 change '+rep,g,'instability_mean_mean','absolute_f1_change_mean_mean')
        t=pd.DataFrame(self.tests); t['p_holm']=np.nan
        for family,g in t.groupby('family'):
            order=g[g.p_value.notna()].sort_values('p_value').index; adjusted=np.maximum.accumulate([min(1.,t.loc[ix,'p_value']*(len(order)-i)) for i,ix in enumerate(order)])
            t.loc[order,'p_holm']=adjusted
        self.stat_table=self.table('statistics/tests_holm',t,'Requested exploratory contrasts; fixed targets; no seeds as independent targets',
            'Seed means first; two-sided Wilcoxon/Friedman/Spearman; Holm separately within listed comparison family; no origin-only seed significance tests','5.8','Cross-RQ')
        posthoc=[]
        for rep in REPS:
            gate=t[(t.family=='model_comparison')&(t.comparison==rep)].iloc[0]
            if gate.p_holm>=.05:continue
            g=self.lodo_summary[self.lodo_summary.representation==rep]
            wide=g.pivot(index='target',columns='model',values='test_f1_mean').dropna()
            for a,b in itertools.combinations(MODELS,2):
                d=wide[a]-wide[b];result=stats.wilcoxon(d,alternative='two-sided',zero_method='wilcox',method='auto')
                posthoc.append(dict(representation=rep,model_a=a,model_b=b,n_targets=len(d),delta_f1_mean=float(d.mean()),p_value=float(result.pvalue),
                    omnibus_p_holm=gate.p_holm,experiment_ids=ids(g[g.model.isin([a,b])]),family='model_posthoc_'+rep))
        post=pd.DataFrame(posthoc);post['p_holm']=np.nan
        for _,g in post.groupby('family'):
            order=g.sort_values('p_value').index
            post.loc[order,'p_holm']=np.maximum.accumulate([min(1.,post.loc[ix,'p_value']*(len(order)-i)) for i,ix in enumerate(order)])
        self.table('statistics/model_posthoc',post,'Only representations passing Holm-adjusted Friedman omnibus at 0.05','Pairwise target-level Wilcoxon; Holm across three model pairs within representation; exploratory','5.8','RQ1')
        # Sensitivity: related site files cannot automatically be treated as independent targets.
        family=self.canonical_summary.copy();family['source_family']=family.target.map(self.family)
        family=summarize(family,['source_family','model'],['delta_test_f1_mean'])
        self.table('tables/canonicalization_family_sensitivity',family,'Sensitivity only: average related target files within recorded origin family','Seeds -> target means -> equal target weight within family; does not replace file-level main analysis','5.8','RQ4')
        sensitivity=[]
        for model,g in family.groupby('model'):
            delta=g.delta_test_f1_mean_mean; result=stats.wilcoxon(delta,alternative='two-sided',zero_method='wilcox',method='auto')
            sensitivity.append(dict(model=model,n_families=len(g),p_value=result.pvalue,effect_mean=delta.mean(),experiment_ids=ids(g)))
        sensitivity=pd.DataFrame(sensitivity);order=sensitivity.sort_values('p_value').index
        sensitivity.loc[order,'p_holm']=np.maximum.accumulate([min(1.,sensitivity.loc[ix,'p_value']*(len(order)-i)) for i,ix in enumerate(order)])
        self.family_sensitivity=self.table('statistics/canonicalization_family_sensitivity',sensitivity,'Related-target sensitivity, not new training or a replacement for file-level results',
            'Two-sided Wilcoxon on family-level means; Holm over models; shared source pools still limit independence','5.8','RQ4')

    def diagnostics(self):
        selections=[]
        def pair_case(name,summary,per_seed,metric,mode,keys):
            ordered=summary.sort_values(metric)
            chosen=ordered.iloc[0 if mode=='min' else -1 if mode=='max' else len(ordered)//2]
            g=per_seed.copy()
            for key in keys:g=g[g[key]==chosen[key]]
            base_metric=metric.removesuffix('_mean')
            r=g.iloc[np.argmin(abs(g[base_metric].to_numpy()-chosen[metric]))]
            selections.append(dict(criterion=name,target=r.target,model=r.model,representation=r.get('representation','PAIRED'),seed=r.seed,
                selection_value=float(chosen[metric]),selection_unit='condition seed-mean extreme/median; seed closest to condition mean',
                experiment_ids=r.experiment_ids))
        canonical=self.canonical[self.canonical.kind=='lodo']
        for name,mode in [('canonicalization_largest_gain','max'),('canonicalization_largest_loss','min'),('canonicalization_median','median')]:
            pair_case(name,self.canonical_summary,canonical,'delta_test_f1_mean',mode,['target','model'])
        for name,mode in [('negative_transfer','min'),('positive_transfer','max')]:
            pair_case(name,self.contribution_summary,self.contribution,'delta_f1_mean',mode,['target','model','representation','removed_source'])
        pair_case('largest_common_test_gap',self.gap_summary,self.gap,'gap_f1_mean','max',['target','model','representation'])
        for name,metric in [('largest_threshold_drift','threshold_drift'),('largest_oracle_gap','oracle_gap_f1')]:
            chosen=self.decision.sort_values(metric+'_mean').iloc[-1]
            g=self.master[(self.master.kind=='lodo')&(self.master.target==chosen.target)&(self.master.model==chosen.model)&(self.master.representation==chosen.representation)]
            r=g.iloc[np.argmin(abs(g[metric].to_numpy()-chosen[metric+'_mean']))]
            selections.append(dict(criterion=name,target=r.target,model=r.model,representation=r.representation,seed=r.seed,selection_value=chosen[metric+'_mean'],
                selection_unit='condition seed mean; representative seed closest to mean',experiment_ids=json.dumps([r.experiment_id])))
        selected=self.table('selected_runs/cases',pd.DataFrame(selections),'Algorithmic extreme/median cases; no manual cherry picking','Representative seed nearest seed mean; not a population estimate','5.5','RQ1/RQ2/RQ3/RQ4')
        cache={}; examples=[]; distributions=[]; histograms=[]; checks=[]
        for eid in sorted({i for value in selected.experiment_ids for i in json.loads(value)}):
            path=self.sources.loc[eid,'prediction_file']; f=self.read(path,columns=['sample_id','dataset','y','is_common_test','role','score','predicted_label'])
            cache[eid]=f; test=f[f.role=='test']; tn=int(((test.y==0)&(test.predicted_label==0)).sum());fp=int(((test.y==0)&(test.predicted_label==1)).sum())
            fn=int(((test.y==1)&(test.predicted_label==0)).sum());tp=int(((test.y==1)&(test.predicted_label==1)).sum()); f1=2*tp/(2*tp+fp+fn)
            checks.append(dict(experiment_ids=json.dumps([eid]),reported_value=self.by_id.loc[eid,'test_f1'],recalculated_value=f1,match=bool(np.isclose(f1,self.by_id.loc[eid,'test_f1'],atol=1e-12)),
                final_table='tables/lodo_per_run or derived/source_contribution_per_seed',source_prediction_file=path,calculation='2TP/(2TP+FP+FN) from selected predictions'))
            for (role,y),g in f.groupby(['role','y']):
                distributions.append(dict(role=role,label=y,n=len(g),score_mean=g.score.mean(),score_q10=g.score.quantile(.1),score_median=g.score.median(),score_q90=g.score.quantile(.9),experiment_ids=json.dumps([eid])))
                n,edges=np.histogram(g.score,bins=np.linspace(0,1,21))
                for i,count in enumerate(n):histograms.append(dict(role=role,label=y,left=edges[i],right=edges[i+1],count=int(count),fraction=count/len(g),experiment_ids=json.dumps([eid])))
            for label,mask in [('FP',(test.y==0)&(test.predicted_label==1)),('FN',(test.y==1)&(test.predicted_label==0))]:
                g=test[mask]; chosen=g.sample(min(5,len(g)),random_state=2026)
                for r in chosen.itertuples():examples.append(dict(criterion=label,sample_id=r.sample_id,dataset=r.dataset,y=r.y,score=r.score,
                    predicted_label=r.predicted_label,source_prediction_file=path,selection='uniform sample without replacement; seed2026; at most5 per error class/run',experiment_ids=json.dumps([eid])))
        transitions=[]
        for r in selected.itertuples():
            eids=json.loads(r.experiment_ids)
            if len(eids)!=2:continue
            a,b=eids; x=cache[a];y=cache[b];x=x[x.role=='test'];y=y[y.role=='test']
            if r.criterion=='largest_common_test_gap':x=x[x.is_common_test];y=y[y.is_common_test]
            assert set(x.sample_id)==set(y.sample_id), 'Selected pair test IDs differ'
            merged=x.merge(y,on='sample_id',suffixes=('_a','_b'),validate='one_to_one');assert (merged.y_a==merged.y_b).all()
            correct_a=merged.predicted_label_a==merged.y_a;correct_b=merged.predicted_label_b==merged.y_b
            for direction,mask in [('correct_to_incorrect',correct_a&~correct_b),('incorrect_to_correct',~correct_a&correct_b)]:
                g=merged[mask]
                for z in g.sample(min(10,len(g)),random_state=2026).itertuples():
                    transitions.append(dict(criterion=r.criterion,direction=direction,sample_id=z.sample_id,y=z.y_a,score_a=z.score_a,score_b=z.score_b,
                        total_available_transitions=len(g),source_prediction_a=self.sources.loc[a,'prediction_file'],source_prediction_b=self.sources.loc[b,'prediction_file'],
                        interpretation='A/B follow experiment_ids order (RAW/CAN, full/removed, or ID/OOD)',experiment_ids=r.experiment_ids))
        self.table('tables/selected_score_distributions',pd.DataFrame(distributions),'Only automatically selected runs; validation vs test stratified by label','Descriptive score quantiles; validation is held-out source, not fitted train','5.5','RQ3')
        self.hist=self.table('derived/selected_score_histograms',pd.DataFrame(histograms),'Same selected runs only','20 fixed bins on [0,1]; within-role/class fractions','5.5','RQ3')
        self.table('tables/error_examples',pd.DataFrame(examples),'Selected runs only; FP/FN','Reproducible seed2026 sampling, at most5 per class/run; sample IDs not manually selected payloads','5.5','RQ3')
        self.table('tables/error_transitions',pd.DataFrame(transitions),'Selected paired runs; identical test IDs (common holdout for ID/OOD)','At most10 random transitions/direction/selected pair; seed2026; full transition count retained','5.7','Cross-RQ')
        self.prediction_checks=checks

    def audit_and_resources(self):
        checks=list(self.prediction_checks)
        for table_name,column,mode in [('tables/lodo_by_target','test_f1_mean','mean'),('tables/canonicalization_by_target','delta_test_f1_mean','canonical'),
                                        ('tables/id_ood_same_test','gap_f1_mean','gap'),('tables/source_contribution_by_target','delta_f1_mean','contribution')]:
            table=self.tables[table_name]
            for _,r in table.sample(min(3,len(table)),random_state=2026).iterrows():
                eids=json.loads(r.experiment_ids); metrics=[self.read(self.sources.loc[e,'metric_file']) for e in eids]
                if mode=='mean': value=np.mean([d['metrics_test']['f1'] for d in metrics])
                else:
                    by_seed={}
                    for d in metrics: by_seed.setdefault(d['seed'],[]).append(d)
                    deltas=[]
                    for seed,items in by_seed.items():
                        assert len(items)==2
                        if mode=='canonical':
                            lookup={d['representation']:d['metrics_test']['f1'] for d in items}; deltas.append(lookup['CANONICALIZED']-lookup['RAW'])
                        elif mode=='gap':
                            lookup={d['kind']:d['metrics_common']['f1'] for d in items}; deltas.append(lookup['id']-lookup['lodo'])
                        else:
                            lookup={d['kind']:d['metrics_test']['f1'] for d in items}; deltas.append(lookup['lodo']-lookup['contribution_fixed_validation'])
                    value=np.mean(deltas)
                checks.append(dict(final_table=table_name+'.csv',final_row_id=r.row_id,column=column,reported_value=r[column],recalculated_value=value,
                    match=bool(np.isclose(r[column],value,atol=1e-12)),experiment_ids=r.experiment_ids,
                    original_source_files=json.dumps([self.sources.loc[e,'metric_file'] for e in eids]),calculation=mode+' from original metrics.json, not master'))
        audit=self.table('tables/reproducibility_audit',pd.DataFrame(checks),'Random seed2026 table cells plus selected-run predictions','Recalculate original JSON or predictions; tolerance1e-12; no checkpoints','5.9','Integrity')
        assert audit.match.all(), 'Reproducibility mismatch'
        self.table('tables/runtime_summary',summarize(self.master,['kind','model'],['runtime_seconds','training_seconds','inference_seconds','rss_peak_mib']),
            'Saved per-worker resource metrics for completed supplemental runs','Descriptive per-fit time/RSS; sum worker runtimes is not wall time','5.9','Reproducibility')
        audit_summary=self.read(BASE/'existing_analysis/split_audit/SUMMARY.json')
        assert audit_summary['full_audit_complete'] and audit_summary['critical_issues']==0
        self.historical_audit=audit_summary
        self.sequence=self.read(BASE/'sequence/STATE.json'); assert self.sequence['status']=='COMPLETED'
        first=self.read(self.master.original_metric_file.iloc[0]); cache=Path(first['cache'])
        self.cache_audit=self.read(cache/'input_audit.parquet')
        self.cache_marker=self.read(cache/'READY.json')
        cohort=self.read(cache/'cohort.parquet',columns=['dataset','y','canonical_hash'])
        dataset_rows=[]
        for r in self.cache_audit.itertuples():
            group=cohort[cohort.dataset==r.dataset]
            eids=self.master[self.master.target==r.dataset].experiment_ids
            dataset_rows.append(dict(dataset=r.dataset,n=r.n,n_benign=int((group.y==0).sum()),n_attack=int((group.y==1).sum()),unique_canonical=group.canonical_hash.nunique(),
                n_changed=r.n_changed,changed_fraction=r.changed_fraction,original_source_file=r.source_file,original_source_sha256=r.source_sha256,experiment_ids=ids(self.master[self.master.target==r.dataset])))
        self.table('tables/paired_dataset_characterization',pd.DataFrame(dataset_rows),'Shared RAW-derived cohort; no new sampling outside explicit origin balancing','Canonical changed-row counts from frozen cache; labels/IDs identical across views','5.2','RQ4')

    def plots(self):
        targets=sorted(self.lodo_summary.target.unique())
        wide=self.lodo_summary.pivot(index='target',columns=['model','representation'],values='test_f1_mean').reindex(targets)
        wide=wide.reindex(columns=pd.MultiIndex.from_product([MODELS,REPS]))
        fig,ax=plt.subplots(figsize=(10,4.5));im=ax.imshow(wide.to_numpy(),vmin=.5,vmax=1,cmap='viridis');ax.set_yticks(range(len(wide)),wide.index)
        ax.set_xticks(range(len(wide.columns)),[m+'\n'+r for m,r in wide.columns],fontsize=8)
        for i in range(len(wide)):
            for j in range(len(wide.columns)):ax.text(j,i,f'{wide.iloc[i,j]:.3f}',ha='center',va='center',color='white' if wide.iloc[i,j]<.8 else 'black',fontsize=9)
        fig.colorbar(im,ax=ax,label='Attack F1; mean of seeds');ax.set_title('Controlled LODO: full unseen target')
        self.figure('lodo_by_target',fig,'tables/lodo_by_target','Per-target F1; seed means; no pooled test samples')
        wide=self.canonical_summary.pivot(index='target',columns='model',values='delta_test_f1_mean').reindex(index=targets,columns=MODELS)
        bound=max(abs(wide.to_numpy().min()),abs(wide.to_numpy().max()))
        fig,ax=plt.subplots(figsize=(6,4.5));im=ax.imshow(wide,vmin=-bound,vmax=bound,cmap='RdBu');ax.set_yticks(range(len(wide)),wide.index);ax.set_xticks(range(3),MODELS)
        for i in range(len(wide)):
            for j in range(3):ax.text(j,i,f'{wide.iloc[i,j]:+.3f}',ha='center',va='center',fontsize=9)
        fig.colorbar(im,ax=ax,label='F1 CANONICALIZED − RAW');ax.set_title('Identical samples and partitions')
        self.figure('canonicalization_effect',fig,'tables/canonicalization_by_target','Paired transformation effect, including losses')
        fig,axes=plt.subplots(1,3,figsize=(13,4),sharey=True)
        for ax,model in zip(axes,MODELS):
            for offset,rep,color in [(-.17,'RAW','#d95f02'),(.17,'CANONICALIZED','#1b9e77')]:
                g=self.gap_summary[(self.gap_summary.model==model)&(self.gap_summary.representation==rep)].set_index('target').loc[targets]
                ax.barh(np.arange(len(targets))+offset,g.gap_f1_mean,height=.32,label=rep,color=color)
            ax.set_yticks(range(len(targets)),targets);ax.axvline(0,color='black',lw=.7);ax.set_title(model);ax.set_xlabel('F1 ID − OOD (same test)')
        axes[0].legend(fontsize=7);self.figure('id_ood_common_test_gap',fig,'tables/id_ood_same_test','ID minus OOD on exactly the same evaluated holdout')
        fig,axes=plt.subplots(2,3,figsize=(13,9),sharex=True,sharey=True)
        bound=abs(self.contribution_summary.delta_f1_mean).max()
        for i,rep in enumerate(REPS):
            for j,model in enumerate(MODELS):
                g=self.contribution_summary[(self.contribution_summary.model==model)&(self.contribution_summary.representation==rep)]
                wide=g.pivot(index='removed_source',columns='target',values='delta_f1_mean').reindex(index=targets,columns=targets)
                colors=plt.get_cmap('RdBu').copy();colors.set_bad('#c5c5c5')
                ax=axes[i,j];im=ax.imshow(np.ma.masked_invalid(wide.to_numpy()),vmin=-bound,vmax=bound,cmap=colors)
                ax.set_xticks(range(len(targets)),targets,rotation=70,ha='right',fontsize=7);ax.set_yticks(range(len(targets)),targets,fontsize=8);ax.set_title(model+' / '+rep)
        fig.subplots_adjust(right=.88,bottom=.18,hspace=.25);fig.colorbar(im,cax=fig.add_axes([.9,.2,.015,.6]),label='F1 full − removed; source rows, target columns')
        fig.suptitle('Gray: source/target combination not eligible',fontsize=10,y=.96)
        self.figure('source_contribution',fig,'tables/source_contribution_by_target','Missing cells remain blank; eligible seeds averaged within target/source')
        fig,ax=plt.subplots(figsize=(7,4));conditions=['all','benign','malicious']
        for offset,rep in [(-.18,'RAW'),(.18,'CANONICALIZED')]:
            g=self.origin_summary[self.origin_summary.representation==rep].set_index('condition').loc[conditions]
            ax.bar(np.arange(3)+offset,g.origin_macro_f1_mean,width=.35,yerr=g.origin_macro_f1_std,label=rep,capsize=3)
        ax.axhline(float(self.origin_summary.origin_chance_accuracy_uniform_mean.iloc[0]),ls='--',color='gray',label='Uniform balanced asymptotic reference')
        ax.set_xticks(range(3),conditions);ax.set_ylim(0,1);ax.set_ylabel('Origin macro-F1; seed mean ± SD');ax.legend(fontsize=7)
        self.figure('controlled_separability',fig,'tables/separability','Balanced source discrimination; seed SD, not confidence interval')
        selected=self.tables['selected_runs/cases'];eid=json.loads(selected[selected.criterion=='largest_oracle_gap'].experiment_ids.iloc[0])[0]
        h=self.hist[self.hist.experiment_ids==json.dumps([eid])];fig,ax=plt.subplots(figsize=(7,4))
        for (role,y),g in h.groupby(['role','label']):ax.plot((g.left+g.right)/2,g.fraction,label=role+' / '+('attack' if y else 'benign'),ls='-' if role=='test' else '--')
        ax.set_xlabel('Attack score');ax.set_ylabel('Fraction within role/class');ax.legend(fontsize=8);ax.set_title('Representative largest oracle-gap condition')
        self.figure('selected_score_shift',fig,'derived/selected_score_histograms','Automatically selected largest condition-mean oracle gap; representative seed, not all runs')

    def documentation(self):
        run_counts=self.master.groupby('kind').size().to_dict()
        wins=self.tables['tables/canonicalization_win_tie_loss'];neg=self.tables['tables/negative_transfer'];pos=self.tables['tables/positive_transfer']
        overall_gap=self.table('tables/generalization_gap_macro',summarize(self.gap_summary,['model','representation'],['gap_f1_mean']),
            'Same-test ID/OOD gap, already seed-averaged inside target','Unweighted target mean of ID-OOD gaps; dispersion across targets','5.3','RQ1')
        mincase=self.canonical_summary.sort_values('delta_test_f1_mean').iloc[0]
        maxcase=self.canonical_summary.sort_values('delta_test_f1_mean').iloc[-1]
        strong=neg.iloc[0];stable=self.feature_stable.sort_values(['representation','importance_pct_mean_mean'],ascending=[True,False])
        lines=['# Análise científica complementar — controles pareados', '',
            'Escopo: novos experimentos lexicais controlados, separados do histórico. Nenhum treinamento foi executado por esta análise.', '',
            '## 5.1 Cobertura e integridade', '',
            f'Foram analisados {len(self.master)} runs não piloto: '+', '.join(f'{k}={v}' for k,v in sorted(run_counts.items()))+'. Fonte: `tables/coverage.csv` e `SOURCE_FILES.parquet`.',
            'A auditoria histórica terminou para todos os manifests previstos, sem inconsistências nos controles de hash, origem do alvo e contagens. Isso não prova o comportamento de cada operação interna histórica. Fonte original: `../../complementos_generalizacao_v1/existing_analysis/split_audit/SUMMARY.json` (caminho absoluto em `FILES_READ.csv`).', '',
            '## 5.2 Representações e modelos', '',
            'As duas vistas vêm das mesmas linhas RAW, não dos arquivos decoded históricos. A canonicalização atua também em URL/body e pode alterar enc_pct/path_depth. Esta é uma nova condição experimental; não juntar suas médias às antigas. CatBoost, logística e MLP tabular usam 64 features lexicais; não há embeddings nesta bateria. Fontes: `tables/paired_dataset_characterization.csv`, `SOURCE_FILES.parquet` e protocolo `artigo/scripts/supplemental/ANALYSIS_METHOD.md`.', '',
            '## 5.3 RQ1 — generalização para alvos não vistos', '',
            'O resultado principal por alvo/modelo/vista está em `tables/lodo_by_target.csv` (todas as seeds em `tables/lodo_per_run.csv`). O gap usa somente o teste comum ID/OOD, não mistura o holdout ID com o alvo inteiro. Fonte: `tables/id_ood_same_test.csv`.', '',
            '| Modelo | Vista | Gap F1 médio entre alvos (ID−OOD) |','|---|---|---:|']
        for r in overall_gap.itertuples():lines.append(f'| {r.model} | {r.representation} | {r.gap_f1_mean_mean:.4f} |')
        lines+=['','Esses gaps são médias não ponderadas de alvos, após resumir seeds; fonte: `tables/generalization_gap_macro.csv`. A tabela por alvo preserva as falhas locais. PR-AUC significa average precision. Desempenho OOD não estabelece transferência universal nem independência de fontes.', '',
            '## 5.4 RQ2 — contribuição e transferência negativa', '',
            f'Há {len(neg)} condições alvo/fonte/modelo/vista com contribuição média negativa e {len(pos)} positiva; não são {len(neg)} alvos independentes. Zero usa tolerância 1e-9. Fontes: `tables/negative_transfer.csv`, `tables/positive_transfer.csv`, `tables/source_contribution_by_target.csv`.',
            f'Um caso extremo é target={strong.target}, source={strong.removed_source}, model={strong.model}, view={strong.representation}: full−removed F1={strong.delta_f1_mean:.4f}, em {strong.n_seeds} seeds elegíveis. Fonte: `tables/negative_transfer.csv`, row_id `{strong.row_id}`.',
            'Mais fontes não ajudam sempre. Validação e teste ficam fixos, mas tamanho do treino, early stopping e threshold resultante podem variar. A fonte reservada para validação não é removível; n_seeds varia por fonte. Médias por fonte dão peso igual aos alvos elegíveis, não às seeds disponíveis. Fonte: `tables/source_summary.csv`.', '',
            '## 5.5 RQ3 — scores e thresholds', '',
            'Separar discriminação (AP/ROC-AUC), decisão operacional (F1/FPR/FNR) e diagnóstico oracle. `tables/decision_by_target.csv` contém drift, oracle gap, Brier/ECE e métricas source. Um oracle alto não autoriza usar o alvo para escolher threshold.',
            'Casos de análise de erro foram selecionados automaticamente por extremos/média representativa: `selected_runs/cases.csv`. Scores só foram abertos para esses IDs. `tables/error_examples.csv` e `tables/error_transitions.csv` preservam sample_id, caminho e critério. Não se inferem causas sem olhar o conteúdo das entradas.', '',
            '## 5.6 RQ3 — estabilidade de features', '',
            'As importâncias são nativas do CatBoost, normalizadas em percentual; não são SHAP nem prova causal. `tables/stable_features.csv` resume primeiro seeds e depois alvos. `derived/feature_rank_pairs.csv` preserva Spearman/Kendall/Jaccard por comparação, incluindo empates. Não são dimensões de embeddings.', '']
        for rep in REPS:
            top=stable[stable.representation==rep].head(5)
            lines.append(rep+': maiores importâncias médias: '+', '.join(f'{r.feature} ({r.importance_pct_mean_mean:.2f}%)' for r in top.itertuples())+'. Fonte: `tables/stable_features.csv`, filtro representation='+rep+'.')
        stability=self.tables['tables/feature_stability']
        for comparison in ['cross_target','source_removal']:
            v=stability[stability.comparison==comparison].set_index('representation')
            lines.append(f'Estabilidade {comparison}: Spearman médio RAW={v.loc["RAW","spearman_mean"]:.4f}, CANONICALIZED={v.loc["CANONICALIZED","spearman_mean"]:.4f}. Fonte: `tables/feature_stability.csv`. São comparações dependentes e descritivas; pares site_cooking/site_sqli podem compartilhar pools efetivos, não são origens independentes.')
        lines+=['','Alterações full/removed estão em `tables/source_removal_feature_effects.csv`. Dependência de composição é uma interpretação possível, não equivalência entre importância e capacidade transferível.', '',
            '## 5.7 RQ4 — canonicalização e separabilidade', '',
            '| Modelo | Alvos com ganho | Empate | Piora |','|---|---:|---:|---:|']
        for r in wins.itertuples():lines.append(f'| {r.model} | {r.improved} | {r.neutral} | {r.worsened} |')
        lines += ['', 'Fonte: `tables/canonicalization_win_tie_loss.csv`; sinal do delta médio das seeds de cada alvo, tolerância 1e-9.',
            f'Maior ganho médio: {maxcase.target}/{maxcase.model}, ΔF1={maxcase.delta_test_f1_mean:+.4f}; menor efeito: {mincase.target}/{mincase.model}, ΔF1={mincase.delta_test_f1_mean:+.4f}. Fonte: `tables/canonicalization_by_target.csv`, row_ids `{maxcase.row_id}` e `{mincase.row_id}`.', '',
            '| Condição origem | RAW macro-F1 | CANONICALIZED macro-F1 |','|---|---:|---:|']
        for condition in ['all','benign','malicious']:
            g=self.origin_summary[self.origin_summary.condition==condition].set_index('representation')
            lines.append(f'| {condition} | {g.loc["RAW","origin_macro_f1_mean"]:.4f} | {g.loc["CANONICALIZED","origin_macro_f1_mean"]:.4f} |')
        lines+=['','Fonte: `tables/separability.csv`; médias de seeds. Menor separabilidade não significa invariância: a origem permanece previsível. `tables/separability_controls.csv` registra tamanhos iguais, composição e purge. Não usar seeds de reamostragens sobrepostas como novos domínios independentes. Relações com OOD estão em `tables/separability_vs_generalization.csv` e são apenas exploratórias.', '',
            '## 5.8 Síntese estatística', '',
            'Unidade das comparações: alvo após agregação das seeds. Wilcoxon para duas condições, Friedman para modelos, Spearman para associações; Holm dentro das famílias indicadas. Fontes: `statistics/tests_holm.csv`. Com sete alvos e fontes compartilhadas entre as composições, os testes têm poder limitado; site_cooking e site_sqli pertencem à mesma família. Não interpretar p>0,05 como equivalência.', '',
            '## Negative and Null Findings', '',
            'A piora de canonicalização e todos os casos de transferência negativa estão preservados nas tabelas. Testes sem diferença detectável constam com p_holm e razão em `statistics/tests_holm.csv`; teste não aplicável por poucos alvos não é resultado nulo. Não executar teste de significância da separabilidade usando suas seeds como datasets independentes.', '',
            '## 5.9 Reprodutibilidade', '',
            'Células aleatórias das tabelas finais foram reconstruídas diretamente de métricas originais; runs selecionados também foram recalculados das predictions. Fonte: `tables/reproducibility_audit.csv`. Recursos por fit: `tables/runtime_summary.csv`; tempo somado dos workers não é tempo de parede. Todas as tabelas têm row_id e experiment_ids. Figuras têm arquivo-fonte em `TRACEABILITY.csv`.', '',
            '## Limitações e conclusões que não são justificadas', '',
            'Não concluir generalização universal, ausência de quase-duplicatas semânticas, causalidade, melhoria garantida ao decodificar, equivalência entre origens ou validade dos encoders a partir desta bateria lexical. Não usar o novo Shapley como se a referência vazia fosse recuperada de um treinamento ausente. O recálculo Shapley está separado em `artigo/complementos_generalizacao_v1/existing_analysis/` e depende da referência declarada; não mede o mesmo protocolo de validação fixa desta análise. Não misturar resultados pairwise/ID/LODO ou antigos decoded/novos CANONICALIZED.', '']
        # Insert concrete threshold and statistical findings beside their supporting sections.
        diagnostic=self.decision.sort_values('oracle_gap_f1_mean').iloc[-1]
        at=lines.index('## 5.6 RQ3 — estabilidade de features')
        lines[at:at]=[f'Exemplo diagnóstico: {diagnostic.target}/{diagnostic.model}/{diagnostic.representation} tem AP={diagnostic.test_pr_auc_mean:.4f}, F1 source={diagnostic.test_f1_mean:.4f} e F1 oracle={diagnostic.oracle_f1_diagnostic_mean:.4f}. Isso sugere margem de recuperação por threshold nesta condição, não garante que ela possa ser escolhida sem acesso ao alvo. Fonte: `tables/decision_by_target.csv`, row_id `{diagnostic.row_id}`.', '']
        at=lines.index('## Negative and Null Findings')
        detail=[]
        for r in self.stat_table[self.stat_table.family=='canonicalization'].itertuples():
            detail.append(f'Comparação {r.comparison}: p bruto={r.p_value:.6f}, p Holm={r.p_holm:.6f}, {r.n_units} alvos. Resultado exploratório sensível à dependência e ao pequeno conjunto de fontes; não confirmação populacional. Fonte: `statistics/tests_holm.csv`, row_id `{r.row_id}`.')
        detail+=['Comparações entre modelos após omnibus significativo estão em `statistics/model_posthoc.csv`; não interpretar Friedman sozinho como vitória de um modelo específico.','']
        for r in self.family_sensitivity.itertuples():
            detail.append(f'Sensibilidade agrupando arquivos de alvos relacionados pela família de origem: {r.model}, {r.n_families} famílias, p Holm={r.p_holm:.5f}. Fonte: `statistics/canonicalization_family_sensitivity.csv`, row_id `{r.row_id}`. Essa análise não altera os testes por arquivo e mostra a sensibilidade da inferência à unidade considerada independente.')
        lines[at:at]=detail
        at=lines.index('## 5.9 Reprodutibilidade')
        nulls=[]
        for family in ['source_contribution','cross_rq_associations','id_ood_gap']:
            g=self.stat_table[self.stat_table.family==family];finite=g[g.p_holm.notna()]
            nulls.append(f'Família {family}: {int((finite.p_holm>=.05).sum())} de {len(finite)} testes aplicáveis não passaram o limiar exploratório de 0,05 após Holm; {len(g)-len(finite)} não aplicáveis. Fonte: `statistics/tests_holm.csv`, filtro family={family}. Isso não apaga os efeitos descritivos nem demonstra ausência de efeito.')
        nulls+=['OracleGap contém −F1_source por definição; sua associação com F1 pode ter acoplamento matemático. Correlações entre esses valores não são mecanismo causal.','']
        lines[at:at]=nulls
        self.write_md('RESULTS.md','\n'.join(lines),metric=True)
        method='''# Método da análise complementar

O que/por quê: analisar somente a bateria controlada concluída para sanar comparações não pareadas e confundimento por validação na remoção de fontes. Não treinar, não carregar checkpoints, não reabrir todo o corpus. O protocolo dos fits está congelado nos source_snapshots da sequência e em cada metrics.json.

Entradas: master e lineage consolidadas; tabelas pareadas; importâncias CatBoost pequenas; matrizes de confusão dos classificadores de origem; apenas predictions dos casos selecionados; métricas originais selecionadas para reconstrução. Filtros: pilot_cap=0, contexto único, IDs únicos. Nenhum run válido dessa bateria é omitido; pilotos e histórico não são combinados. Todos os IDs elegíveis estão em SOURCE_FILES.parquet. FILES_READ.csv registra cada arquivo efetivamente lido, hash, bytes e projeção de colunas.

Unidade: seeds são repetições. Média/std/mediana/mínimo/máximo dentro de target/model/view (e fonte removida quando pertinente). Média macro usa peso igual para cada alvo, não cada linha ou seed. Algumas fontes não são removíveis quando reservadas à validação; a tabela informa n_seeds e não inventa condições. Para separabilidade, seeds são apenas variação descritiva sobre reamostragens sobrepostas, sem teste inferencial sobre elas.

Fórmulas: gap=F1_ID−F1_OOD no MESMO teste; razão=F1_OOD/F1_ID se denominador não zero. Canonicalização=CAN−RAW em cada par/seed. Contribuição=full−removed para higher-is-better; benefício FPR/FNR=removed−full. ThresholdDrift=abs(source−oracle); OracleGap=F1_oracle−F1_source. Oracle não seleciona modelo nem decisão operacional. PR-AUC=average precision. Origem F1=2TP/(suporte previsto+suporte verdadeiro) da confusão multiclasse. Chance 1/K é accuracy uniforme e referência macro-F1 assintótica balanceada.

Features: somente as 64 lexicais CatBoost; normalize importância nativa para somar100. Empates de rank usam média; empates do top10 usam nome da feature. Comparações Spearman/Kendall/Jaccard são descritivas, com pares dependentes; não p-values sobre features como observações independentes. Ranking estável: média das seeds dentro do alvo, depois igual peso por alvo. Importância não é SHAP nem causalidade.

Estatística: Wilcoxon signed-rank bilateral de diferenças pareadas das médias por alvo; mínimo5 alvos. Zeros completos recebem p=1; menos alvos ficam não aplicáveis. Friedman sobre os três modelos nos mesmos alvos. Post-hoc somente se omnibus Friedman ajustado por Holm<0,05: Wilcoxon pareado com Holm nas três comparações de modelos dentro de cada vista. Spearman usa alvos agregados, não replicações target×seed. Holm separadamente por família registrada, incluindo associações exploratórias. Instabilidade de features=1−Spearman full/removal, resumida primeiro em seeds por fonte/target, depois igual peso por fonte elegível dentro do target; correlação final tem unidade target. Sensibilidade de canonicalização: agrupar médias de targets relacionados pela família registrada no cohort.parquet congelado (site_cooking/site_sqli), dar igual peso por target dentro da família e testar as médias das famílias com Holm entre modelos. Isso não executa novos testes de treinamento por família; evidencia dependência da inferência à unidade. Pools de treino compartilhados continuam limitando independência. Sem intervalos de confiança nem alegações de equivalência ou de validade para outras populações, dado o número de alvos. OracleGap vs F1 contém acoplamento matemático por construção. Todas as hipóteses são exploratórias pós-experimento, não pré-registro independente dos dados.

Análise dirigida: extremos/mediana calculados nas médias de condições, escolhendo a seed mais próxima daquela média. Só então abrir scores; exemplos FP/FN até5 por run/classe, transições até10 por direção/par, amostragem seed2026. Não consultar payloads nem selecionar manualmente casos convenientes. Distribuições de scores separam classe e validation/test. Validação é fonte retida, não dados ajustados pelo modelo.

Reprodutibilidade: selecionar células de quatro tabelas por seed2026 e recalcular dos JSONs originais; recalcular F1 dos scores/predições dos casos dirigidos. Tolerância1e-12. Não reutilizar master como verdade da reconstrução. Rastrear cada linha via row_id→experiment_ids→SOURCE_FILES.parquet→originais. TRACEABILITY.csv liga figuras às tabelas e documenta filtros, agregação, script e comando. ANALYSIS_AUDIT.json registra escopo, recursos e verificações.
'''
        self.write_md('ANALYSIS_METHOD.md',method,metric=True)
        self.write_md('README.md','''# Análise complementar controlada

Methodology sections: 4.3, 4.6–4.12. TCC Results sections: 5.1–5.9. Research questions: RQ1–RQ4.

Purpose: analisar os controles novos sem confundi-los com protocolos históricos. Status: análise pós-treinamento concluída para os dados disponíveis; limitações científicas descritas em RESULTS.md.

Começar por RESULTS.md e FINAL_TCC_RESULTS_GUIDE.md. Método: ANALYSIS_METHOD.md. Tabelas CSV e Parquet: tables/; intermediários por seed e feature: derived/; casos dirigidos: selected_runs/; estatísticas: statistics/; figuras PNG/PDF: figures/. Cada tabela tem row_id e experiment_ids; consultar SOURCE_FILES.parquet para os originais. O índice histórico e suas tabelas foram preservados.

Para consultar uma célula, usar `python artigo/scripts/trace_supplemental_value.py --table tables/lodo_by_target.csv --row-id ID_DA_LINHA --column test_f1_mean`. O script resolve a tabela relativa a esta pasta e mostra valor, condições, IDs, arquivos originais e receita de agregação; não executa treinamento. Escolher o row_id diretamente na tabela. `FINAL_TRACEABILITY_AUDIT.json` registra a verificação final de cobertura dos artefatos e concordância CSV/Parquet.
''')
        guide=['# Chapter 5 — Controlled supplemental results guide','','Este é um complemento, não uma substituição das contagens e populações históricas. Consulte RESULTS.md para os valores e ressalvas.']
        sections=[('5.1 Experimental Coverage and Integrity','tables/coverage.csv','none','A auditoria dos manifests agora é completa; não prova cada operação interna nem quase-duplicatas semânticas.'),
                  ('5.2 Dataset, Representation, and Model Characterization','tables/paired_dataset_characterization.csv','none','Explicar que CAN deriva das mesmas linhas RAW e inclui URL/body; 64 features, sem embeddings.'),
                  ('5.3 Cross-Dataset Generalization — RQ1','tables/lodo_by_target.csv; tables/id_ood_same_test.csv','figures/lodo_by_target.pdf; figures/id_ood_common_test_gap.pdf','Resultado principal: F1 por alvo e gap em teste idêntico; média global somente secundária.'),
                  ('5.4 Source-Dataset Contribution — RQ2','tables/source_contribution_by_target.csv; tables/negative_transfer.csv','figures/source_contribution.pdf','Resultado principal: efeitos com validação fixa; número de seeds elegíveis varia. Não é comparação size-matched nem causal.'),
                  ('5.5 Decision Behavior — RQ3','tables/decision_by_target.csv','figures/selected_score_shift.pdf','Oracle só diagnóstico; separar ranking de scores e threshold. Casos extremos não estimam população.'),
                  ('5.6 Feature Stability — RQ3','tables/stable_features.csv; tables/source_removal_feature_effects.csv','none','Importância nativa CatBoost; não invariância causal, não dimensões de embedding.'),
                  ('5.7 Canonicalization and Dataset Separability — RQ4','tables/canonicalization_by_target.csv; tables/separability.csv','figures/canonicalization_effect.pdf; figures/controlled_separability.pdf','Resultado principal: efeito pareado e origem ainda discriminável. Não omitir perdas; não inferir causa por correlação.'),
                  ('5.8 Statistical Synthesis','statistics/tests_holm.csv','none','Seeds agregadas dentro do alvo; Holm por família; conservar não significativos e não aplicáveis separadamente.'),
                  ('5.9 Reproducibility','tables/reproducibility_audit.csv; tables/runtime_summary.csv','none','Reconstrução dos originais; não confundir runtime somado e parede; não juntar novos IDs aos antigos sem rótulo de protocolo.')]
        for title,tables,figures,warning in sections:
            guide+=['','## '+title,'','Main result and safe interpretation: '+warning,'','Tables to include: '+tables,'','Figures to include: '+figures,
                    '','Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.',
                    '','Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.']
        self.write_md('FINAL_TCC_RESULTS_GUIDE.md','\n'.join(guide))

    def write_md(self,name,body,metric=False):
        provenance='''\n## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| LODO F1/MCC/AP | tables/lodo_by_target.csv | SOURCE_FILES.parquet | kind=lodo, pilot=0 | seeds inside target/model/view | analyze_supplemental_results.py |
| ID/OOD gap | tables/id_ood_same_test.csv | SOURCE_FILES.parquet | identical common-test IDs | ID−OOD per seed then seed summary | analyze_supplemental_results.py |
| Source contribution | tables/source_contribution_by_target.csv | SOURCE_FILES.parquet | frozen validation/test | full−removed then eligible seeds | analyze_supplemental_results.py |
| Canonicalization | tables/canonicalization_by_target.csv | SOURCE_FILES.parquet | identical RAW/CAN splits | CAN−RAW then seeds | analyze_supplemental_results.py |
| Separability | tables/separability.csv | SOURCE_FILES.parquet | balanced origins/classes | seed descriptive summaries | analyze_supplemental_results.py |
| Features | tables/stable_features.csv | SOURCE_FILES.parquet, feature_file | lexical CatBoost LODO | seeds then equally weighted targets | analyze_supplemental_results.py |
| Threshold/score behavior | tables/decision_by_target.csv; selected_runs/cases.csv | SOURCE_FILES.parquet | source-threshold LODO; oracle diagnostic | seeds inside target | analyze_supplemental_results.py |
| Statistical tests | statistics/tests_holm.csv | SOURCE_FILES.parquet | target-level seed means | two-sided, Holm per family | analyze_supplemental_results.py |
| Reproducibility | tables/reproducibility_audit.csv | original_source_files / source_prediction_file in table | seed2026 selected cells and diagnostic runs | reconstruct originals, tolerance1e-12 | analyze_supplemental_results.py |
'''
        trace=f'''\n## Data Sources and Traceability

Original-file mapping: `SOURCE_FILES.parquet`, one row per supplemental experiment_id; all eligible IDs are included. Primary analytical inputs: `{INPUT}/master_results.parquet`, `SOURCE_LINEAGE.parquet`, `raw_vs_canonicalized_pairs.parquet`, `id_vs_ood_same_test.parquet`, `fixed_validation_contribution.parquet`. Globs for underlying artifacts: `{BASE}/full/runs/SUPP_*/metrics.json`, `feature_importance.parquet`, `predictions.parquet`; these are not all opened indiscriminately. Selected prediction IDs/criteria: `selected_runs/cases.csv`. Exact unique files read, counts by extension, projected columns, hashes and sizes: `FILES_READ.csv`, `ANALYSIS_AUDIT.json`. No checkpoint contents read, no training, no raw payload reads. Historical audit uses only `{BASE}/existing_analysis/split_audit/SUMMARY.json`; individual historical results remain separate.

Filters: completed consolidated runs, pilot_cap=0, one execution context, unique IDs; specific kind/target/model/view/source filters and formulas in `TRACEABILITY.csv` and `ANALYSIS_METHOD.md`. All scientific table rows contain row_id and experiment_ids. Seeds are summarized inside target/condition, never independent targets; absent comparisons remain absent. `TRACEABILITY.csv` records source columns, grouping/formula, command, figure source table, and each derived artifact. Original arrays for controlled cohorts remain in cache paths referenced by metrics.json; `tables/paired_dataset_characterization.csv` links dataset hashes. All tables: `tables/`, per-seed intermediates: `derived/`, statistics: `statistics/`, figures PNG/PDF: `figures/`. Figure/table relationships are explicit in TRACEABILITY.csv.

Script: `{Path(__file__).resolve()}`. Command: `{COMMAND}`. Code hash, run counts, actual file counts, generation timestamp, runtime, peak RAM and reproducibility checks: `ANALYSIS_AUDIT.json`. Complete cell-to-source reconstruction example: table row → experiment_ids → SOURCE_FILES.parquet metric_file → original metrics.json. Random reconstructed values are in `tables/reproducibility_audit.csv`. This report keeps the historical protocol and new RAW-derived paired protocol separate.
'''
        (OUTPUT/name).write_text(body+(provenance if metric else '')+trace)

    def finish(self):
        pd.DataFrame(self.trace).to_csv(OUTPUT/'TRACEABILITY.csv',index=False)
        pd.DataFrame(self.reads.values()).to_csv(OUTPUT/'FILES_READ.csv',index=False)
        unmatched=[t['artifact_path'] for t in self.trace if not Path(t['artifact_path']).exists()]
        assert not unmatched
        for name,frame in self.tables.items():
            assert frame.row_id.is_unique and frame.row_id.notna().all()
            assert frame.experiment_ids.map(lambda v:len(json.loads(v))>0).all()
            csv=pd.read_csv(OUTPUT/(name+'.csv'));parquet=pd.read_parquet(OUTPUT/(name+'.parquet'))
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',FutureWarning)
                pd.testing.assert_frame_equal(csv,parquet,check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-12)
        for path in OUTPUT.glob('*.md'):
            text=path.read_text();assert '## Data Sources and Traceability' in text
            if path.name in ['ANALYSIS_METHOD.md','RESULTS.md']:assert '## Metric Provenance' in text
        atomic_json(OUTPUT/'FINAL_TRACEABILITY_AUDIT.json',{
            'generated_at':now(),'source_ids_exactly_match_master':set(self.lineage.experiment_id)==self.valid_ids,
            'all_table_rows_have_unique_nonempty_row_id_and_experiment_ids':True,
            'csv_parquet_agree':True,'n_tables_checked':len(self.tables),'every_figure_has_source_table_manifest':True,
            'all_declared_artifacts_exist':True,'markdown_provenance_sections_present':True,
            'sampled_original_metric_and_prediction_reconstruction_passed':bool(self.tables['tables/reproducibility_audit'].match.all()),
            'related_target_sensitivity_reported':True,'historical_protocol_not_pooled_with_supplemental':True,
            'limitations':'Sampled numerical reconstruction, not recomputation of every cell from raw scores; hashes/manifests cannot prove every historical internal operation.'})
        audit=dict(generated_at=now(),completed=True,script=str(Path(__file__).resolve()),script_sha256=sha256(Path(__file__).resolve()),command=COMMAND,
            supplemental_runs=len(self.master),n_tables=len(self.tables),n_figure_files=sum(x['artifact_id'].startswith('figure_') for x in self.trace),
            unique_files_read=len(self.reads),files_read_by_extension=pd.Series([Path(p).suffix for p in self.reads]).value_counts().to_dict(),
            bytes_in_files_read=sum(x['bytes'] for x in self.reads.values()),checkpoints_read=0,new_trainings=0,
            source_mapping_complete=set(self.lineage.experiment_id)==self.valid_ids,all_table_rows_have_ids=True,
            reproducibility_rows=len(self.tables['tables/reproducibility_audit']),reproducibility_all_match=bool(self.tables['tables/reproducibility_audit'].match.all()),
            runtime_seconds=time.perf_counter()-self.started,rss_peak_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            statistical_unit='target after seed aggregation; origin seeds descriptive only',historical_results_overwritten=False)
        atomic_json(OUTPUT/'ANALYSIS_AUDIT.json',audit);print(json.dumps(audit,indent=2))


def main():
    a=Analysis()
    for name in ['core','origin','features','statistics','diagnostics','audit_and_resources','plots','documentation','finish']:
        print(now(),name,flush=True);getattr(a,name)()


if __name__=='__main__': main()
