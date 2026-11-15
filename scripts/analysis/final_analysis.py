#!/usr/bin/env python3
"""Read-only analysis of original experiments. Writes only to analise_resultados_tcc.

No fitting, checkpoint loading, or bulk prediction loading is performed.
All table rows carry row_id and experiment_ids; external summaries carry source_file.
"""
import os
for _var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_var] = '2'
import argparse
import collections
import hashlib
import itertools
import json
import math
import resource
import time
import importlib.metadata
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'analise_resultados_tcc'
GLOBAL = OUT / '_global'
SCRIPT = Path(__file__).resolve()
CFG = json.loads((SCRIPT.parent / 'config.json').read_text())
COMMAND = f'{sys.executable} {SCRIPT} --config {SCRIPT.parent / "config.json"}'
METRICS = ['precision','recall','f1','mcc','pr_auc','roc_auc','balanced_accuracy','specificity','fpr','fnr','brier','ece_10']
SECTIONS = {
1: ('M04_01_Experimental_Design__C05_01_Experimental_Coverage','5.1','All','Cobertura experimental'),
2: ('M04_02_Datasets_Provenance__C05_02_Dataset_Characterization','5.2','All','Datasets e procedência'),
3: ('M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity','5.1','All','Integridade e isolamento'),
4: ('M04_04_Input_Feature_Representations__C05_02_Representation_Characterization','5.2','All','Representações'),
5: ('M04_05_Models_Training__C05_02_Model_Characterization','5.2','All','Modelos e treinamento'),
6: ('M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization','5.3','RQ1','Generalização'),
7: ('M04_07_Source_Contribution__C05_04_RQ2_Contribution','5.4','RQ2','Contribuição das fontes'),
8: ('M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration','5.5','RQ3','Decisão e thresholds'),
9: ('M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability','5.6','RQ3','Estabilidade de features'),
10: ('M04_10_Canonicalization_Separability__C05_07_RQ4','5.7','RQ4','Canonicalização e separabilidade'),
11: ('M04_11_Statistics__C05_08_Statistical_Synthesis','5.8','All','Síntese estatística'),
12: ('M04_12_Reproducibility__C05_09_Reproducibility','5.9','All','Reprodutibilidade'),
13: ('M04_13_AI_Use__NO_EXPERIMENTAL_RESULTS',None,None,'Declaração de uso de IA')}
GENERATED = datetime.now(timezone.utc).isoformat()
ANALYSIS_STARTED=time.perf_counter()
READS = {}
ISSUES = []
ARTIFACTS = []
DOCS = {}

def rel(p):
    p=Path(p)
    try:return str(p.resolve().relative_to(ROOT.parent))
    except ValueError:return str(p)

def digest(value):
    return hashlib.sha256(str(value).encode()).hexdigest()

def track(p):
    p=Path(p)
    if p.exists():
        st=p.stat(); READS[str(p.resolve())]={'path':rel(p),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
    return p

def read_json(p):return json.loads(track(p).read_text())
def read_csv(p, **kw):return pd.read_csv(track(p), **kw)
def read_parquet(p, **kw):return pd.read_parquet(track(p), **kw)
def master():return read_parquet(GLOBAL/'master_results.parquet')
def valid():
    d=master();return d[d.usable].copy()
def directory(i):return OUT / SECTIONS[i][0]
def issue(code, severity, message, evidence):
    if not any(v['code']==code for v in ISSUES):
        ISSUES.append(dict(code=code,severity=severity,message=message,evidence=evidence))

def ids(values):
    result=set()
    for v in values:
        if isinstance(v,(list,tuple,set,np.ndarray)):result.update(map(str,v))
        elif isinstance(v,str):
            if v.startswith('['):result.update(json.loads(v))
            elif v:result.add(v)
    return json.dumps(sorted(result))

def save_table(i, name, frame, description='', source='', aggregation='none; one row per observation'):
    if aggregation=='none; one row per observation':aggregation=frame.attrs.get('aggregation',aggregation)
    d=frame.copy();p=(GLOBAL if i==0 else directory(i))/name;p.parent.mkdir(parents=True,exist_ok=True)
    if 'experiment_ids' not in d:
        cols=[c for c in d if c=='experiment_id' or c.startswith('experiment_id_') or c.endswith('_experiment_id')]
        d['experiment_ids']=[ids(row) for row in d[cols].itertuples(index=False,name=None)] if cols else '[]'
    if 'source_file' not in d:d['source_file']=source or rel(GLOBAL/'master_results.parquet')
    if 'row_id' not in d:d.insert(0,'row_id',[digest(rel(p)+':'+str(j))[:20] for j in range(len(d))])
    if p.suffix=='.parquet':d.to_parquet(p,index=False)
    else:d.to_csv(p,index=False)
    ARTIFACTS[:]=[a for a in ARTIFACTS if a['artifact_path']!=rel(p)]
    ARTIFACTS.append(dict(section=i,artifact_id=digest(rel(p))[:20],artifact_path=rel(p),
        methodology_section=f'4.{i}' if i else 'global',tcc_section=SECTIONS[i][1] if i else 'global',
        research_question=SECTIONS[i][2] if i else 'All',analysis_description=description or name,
        master_table_filter='Exact IDs per row: experiment_ids; selection documented in ANALYSIS_METHOD.md',
        source_file_manifest=rel((directory(i) if i else GLOBAL)/'SOURCE_FILES.parquet'),
        source_columns=json.dumps(list(d.columns)),aggregation=aggregation,script=rel(SCRIPT),command=COMMAND,
        generated_at=GENERATED,experiment_id_manifest=rel(p)))
    return d

def summary(d, keys, metrics=METRICS):
    rows=[]
    for key,g in d.groupby(keys,dropna=False,sort=True):
        if not isinstance(key,tuple):key=(key,)
        r=dict(zip(keys,key));r['experiment_ids']=ids(g.experiment_ids if 'experiment_ids' in g else g.experiment_id)
        r['n_runs']=len(g)
        if 'seed' in g:r['n_seeds']=g.seed.nunique();r['seeds']=json.dumps(sorted(map(int,g.seed.dropna().unique())))
        for metric in metrics:
            if metric not in g:continue
            v=pd.to_numeric(g[metric],errors='coerce').dropna()
            for stat,fn in [('mean','mean'),('std','std'),('median','median'),('min','min'),('max','max')]:r[f'{metric}_{stat}']=getattr(v,fn)() if len(v) else np.nan
        rows.append(r)
    result=pd.DataFrame(rows)
    result.attrs['aggregation']='groupby('+', '.join(keys)+'); '+', '.join(metrics)+' summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned'
    return result

def doc(i, findings, method, status='Complete'):
    DOCS[str(i)]={'findings':findings,'method':method,'status':status}

def phase0():
    GLOBAL.mkdir(parents=True,exist_ok=True)
    inventory=[]
    for folder in ['results/raw','runs/status','runs/manifests','runs/predictions','runs/probabilities','runs/checkpoints','runs/feature_importance','runs/thresholds','runs/logs']:
        for p in (ROOT/folder).iterdir():
            if p.is_file():
                st=p.stat();inventory.append({'path':rel(p),'category':folder,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'empty':st.st_size==0})
    pd.DataFrame(inventory).to_parquet(GLOBAL/'file_inventory.parquet',index=False)
    for p in [*ROOT.glob('config/*.yaml'),*ROOT.glob('src/**/*.py'),*ROOT.glob('scripts/**/*.py')]:
        track(p)
    issue('NO_NEW_TRAINING','CONTROL','Esta análise não treina modelos nem abre checkpoints.',rel(SCRIPT))

def phase1():
    registry=read_csv(ROOT/'docs/experiment_registry/experiments.csv',dtype=str).fillna('')
    dup=registry[registry.experiment_id.duplicated(False)]
    save_table(0,'duplicate_registry_ids.csv',dup,source=rel(ROOT/'docs/experiment_registry/experiments.csv'))
    status={}
    for p in (ROOT/'runs/status').glob('*.json'):
        try:status[p.stem]=read_json(p)
        except Exception as e:issue('STATUS_'+p.stem,'CRITICAL ISSUE',str(e),rel(p))
    registry=registry.drop_duplicates('experiment_id',keep='last')
    absent=set(status)-set(registry.experiment_id)
    if absent:registry=pd.concat([registry,pd.DataFrame([{'experiment_id':x} for x in sorted(absent)])],ignore_index=True).fillna('')
    registry['status_file_status']=registry.experiment_id.map(lambda x:status.get(x,{}).get('status','MISSING'))
    registry.to_parquet(GLOBAL/'run_registry.parquet',index=False)
    rows=[]
    for eid in registry.experiment_id:
        r={'experiment_id':eid}
        for col,loc in {'manifest_file':f'runs/manifests/{eid}.json','metric_file':f'results/raw/{eid}.json',
            'prediction_file':f'runs/predictions/{eid}.csv','score_file':f'runs/probabilities/{eid}.npz',
            'threshold_file':f'runs/thresholds/{eid}.json','feature_importance_file':f'runs/feature_importance/{eid}.csv',
            'checkpoint_file':f'runs/checkpoints/{eid}.joblib','log_file':f'runs/logs/{eid}.log','status_file':f'runs/status/{eid}.json',
            'split_file':f'runs/manifests/{eid}_split.csv'}.items():
            p=ROOT/loc
            if col=='split_file' and not p.exists():p=Path(str(p)+'.gz')
            r[col]=rel(p) if p.exists() else None
        r['calibration_file']=r['metric_file'] # metrics_source.brier and ece_10
        rows.append(r)
    lineage=pd.DataFrame(rows);lineage.to_parquet(GLOBAL/'SOURCE_LINEAGE.parquet',index=False)
    lineage.rename(columns={'metric_file':'source_metric_file','prediction_file':'source_prediction_file','score_file':'source_score_file',
        'threshold_file':'source_threshold_file','feature_importance_file':'source_feature_file','manifest_file':'source_manifest'}).to_parquet(GLOBAL/'SOURCE_FILES.parquet',index=False)

def phase2():
    reg=read_parquet(GLOBAL/'run_registry.parquet');line=read_parquet(GLOBAL/'SOURCE_LINEAGE.parquet').set_index('experiment_id')
    rows=[];checks=[];manmeta=[]
    config=read_json(SCRIPT.parent/'config.json')
    modelcfg=yaml.safe_load(track(ROOT/'config/models.yaml').read_text())['models']
    for rr in reg.to_dict('records'):
        eid=rr['experiment_id'];ln=line.loc[eid];metric={};man={}
        if ln.metric_file:
            try:metric=read_json(ROOT.parent/ln.metric_file)
            except Exception as e:checks.append(dict(experiment_id=eid,issue='invalid_metric_file',detail=str(e)))
        if ln.manifest_file:
            try:man=read_json(ROOT.parent/ln.manifest_file)
            except Exception as e:checks.append(dict(experiment_id=eid,issue='invalid_manifest',detail=str(e)))
        spec={}
        try:spec=json.loads(rr.get('config') or '{}')
        except Exception:pass
        v=spec|metric;chapter=v.get('chapter',rr.get('chapter'));model=v.get('model',rr.get('model'));rep=v.get('representation',rr.get('representation'))
        sources=sorted(v.get('train_datasets') or [x for x in rr.get('training_pool','').split('+') if x])
        audit=v.get('split_audit',{});counts=audit.get('counts',{})
        partsets={k:sorted(set(x['dataset'] for x in counts.get(k,[]))) for k in ['train','validation','test']}
        met=v.get('metrics_source',{});th=v.get('thresholds',{})
        row=dict(experiment_id=eid,experiment_type=chapter,target_dataset=v.get('target',rr.get('target')),training_datasets='+'.join(sources),
            n_training_datasets=len(sources),removed_source=None,model=model,model_family={'logistic':'linear','catboost':'boosted_trees','mlp':'neural_mlp'}.get(model),
            configuration_id=digest(json.dumps(modelcfg.get(model,{}),sort_keys=True))[:16],configuration_evidence='current_config_not_per_run_snapshot',
            representation={'raw':'RAW','decoded':'CANONICALIZED','embedding':'CODEBERT_CANONICALIZED','early_fusion':'EARLY_FUSION_CANONICALIZED'}.get(rep,rep),
            original_representation=rep,feature_set=v.get('feature_set') or rr.get('feature_set') or 'unknown',seed=int(v.get('seed') or rr.get('seed') or 0),
            family_aware=v.get('family_aware',True if chapter=='embedding_lodo' else None),pilot=int(v.get('pilot',0)),
            threshold_strategy='validation_f1',threshold_source=th.get('threshold_source'),threshold_oracle=th.get('threshold_oracle'),
            threshold_drift=th.get('threshold_drift'),oracle_gap=th.get('oracle_gap'),f1_oracle=v.get('metrics_oracle_diagnostic',{}).get('f1'),
            f1_fixed=v.get('metrics_fixed',{}).get('f1'),status=rr['status_file_status'],status_reason=rr.get('notes',''),runtime=v.get('runtime'),
            train_n=v.get('train_n'),validation_n=v.get('validation_n'),test_n=v.get('test_n'),
            training_seconds=v.get('training_seconds'),extraction_seconds=v.get('extraction_seconds'),inference_seconds=v.get('inference_seconds'),
            selected_iterations=v.get('selected_iterations'),rss_peak_mib=v.get('rss_peak_mib'),
            started_at=v.get('started_at',rr.get('started_at')),finished_at=v.get('finished_at',rr.get('finished_at')),
            actual_train_datasets='+'.join(partsets['train']),validation_datasets='+'.join(partsets['validation']),
            effective_development_datasets='+'.join(sorted(set(partsets['train']+partsets['validation']))),
            split_counts=json.dumps(counts,sort_keys=True),same_family_removed=json.dumps(audit.get('same_family_removed',{})),
            target_overlap_removed=json.dumps(audit.get('target_overlap_removed',{})),label_conflicts_removed=json.dumps(audit.get('development_label_conflicts_removed',{})),
            original_metric_file=ln.metric_file,original_manifest_file=ln.manifest_file,experiment_key=v.get('experiment_key',rr.get('experiment_key')))
        row['n_effective_sources']=len(set(partsets['train']+partsets['validation']))
        for m in METRICS+['macro_f1','tp','tn','fp','fn','n_attack']:row[m]=met.get(m)
        reasons=[]
        if row['status']!='COMPLETED':reasons.append('status_'+str(row['status']))
        if row['pilot']:reasons.append('pilot')
        if not met:reasons.append('missing_metrics')
        for field in ['target_dataset','model','representation']:
            if not row[field]:reasons.append('missing_'+field)
        for m in METRICS:
            val=row[m]
            if val is not None and (not np.isfinite(val) or not (-1 if m=='mcc' else 0)<=val<=1):
                reasons.append('invalid_'+m);checks.append(dict(experiment_id=eid,issue='invalid_'+m,detail=str(val)))
        if met:
            cm=sum(met.get(k,0) for k in ['tp','tn','fp','fn'])
            if cm!=row['test_n']:reasons.append('confusion_count_mismatch')
            if met.get('n_attack',0)==0:
                for m in ['precision','recall','f1','fnr']:row[m]=None
            if met.get('n_attack') in (0,cm):
                for m in ['macro_f1','balanced_accuracy','mcc','pr_auc','roc_auc']:row[m]=None
        if chapter!='baseline_id' and row['target_dataset'] in partsets['train']+partsets['validation']:
            reasons.append('outer_target_leakage');issue('LEAK_'+eid,'CRITICAL ISSUE','Outer target encontrado no desenvolvimento.',ln.metric_file)
        row['usable']=not reasons;row['exclusion_reason']=';'.join(reasons);rows.append(row)
        manmeta.append(dict(experiment_id=eid,has_git_commit=bool(man.get('git_commit')),has_hardware=bool(man.get('hardware')),
            has_software_versions=bool(man.get('software_versions')),has_config_snapshot='model_config' in man,
            has_dataset_hashes=bool(man.get('dataset_files')),source_file=ln.manifest_file))
    df=pd.DataFrame(rows)
    dupe=df.usable & df.experiment_key.duplicated(keep='last')
    df.loc[dupe,'usable']=False;df.loc[dupe,'exclusion_reason']='duplicate_experiment_key'
    df.to_parquet(GLOBAL/'master_results.parquet',index=False)
    save_table(0,'metric_integrity_issues.csv',pd.DataFrame(checks,columns=['experiment_id','issue','detail']))
    save_table(0,'manifest_metadata.parquet',pd.DataFrame(manmeta))
    issue('CONFIG_HISTORY','LIMITATION','Hyperparameters reconstruídos do código/config atuais; manifests não preservam snapshot completo nem commit Git. Não equivalem a prova imutável da configuração histórica.',rel(ROOT/'config/models.yaml'))
    issue('SHAPLEY_NAME','MAJOR','dataset_shapley.csv contém média uniforme de marginais disponíveis, não Shapley clássico; coalizão vazia ausente e pesos fatoriais não aplicados. Não usar como Shapley no TCC.',rel(ROOT/'scripts/07_shapley/compute_shapley.py'))

def phase3():
    d=master();cfg=yaml.safe_load(track(ROOT/'config/experiments.yaml').read_text());pool=cfg['dataset_policy']['primary_datasets']
    expected=[]
    def add(ch,t,src,features=('lex64',),reps=('RAW','CANONICALIZED')):
        for m,r,f,s in itertools.product(cfg['models'],reps,features,CFG['expected_seeds']):
            expected.append(dict(experiment_type=ch,target_dataset=t,training_datasets='+'.join(sorted(src)),model=m,representation=r,feature_set=f,seed=s))
    for t in pool:
        others=[x for x in pool if x!=t];add('baseline_id',t,[])
        for x in others:add('pairwise',t,[x])
        for n in range(1,len(others)+1):
            for ss in itertools.combinations(others,n):add('contribution',t,ss)
        add('ablation',t,others,('lex64','no_encoding','no_sql_keywords','no_length','no_special_chars','char_rates'))
        add('embedding_lodo',t,others,('codebert_frozen',),('CODEBERT_CANONICALIZED',))
        add('embedding_lodo',t,others,('lex64+codebert',),('EARLY_FUSION_CANONICALIZED',))
    for sc,ss in cfg['dataset_policy']['scenarios'].items():
        for t in ss:add('lodo_'+sc,t,[x for x in ss if x!=t])
    keys=['experiment_type','target_dataset','training_datasets','model','representation','feature_set','seed']
    e=pd.DataFrame(expected);actual=d[d.usable | d.status.eq('SKIPPED')].copy()
    # SKIPPED registry includes the original configuration, including feature set.
    cov=e.merge(actual[keys+['experiment_id','status','usable']],on=keys,how='left')
    save_table(0,'run_coverage.csv',cov)
    save_table(1,'tables/coverage_matrix.csv',cov)
    save_table(1,'tables/missing_runs.csv',cov[cov.experiment_id.isna()])
    save_table(1,'tables/excluded_runs.csv',d[~d.usable])
    counts=[('total_previsto',len(e)),('total_encontrado',len(d)),('total_concluido_status',int(d.status.eq('COMPLETED').sum())),
            ('total_utilizavel',int(d.usable.sum())),('total_incompleto',int(d.status.isin(['RUNNING','MISSING']).sum())),
            ('total_falho',int(d.status.eq('FAILED').sum())),('total_excluido',int((~d.usable).sum())),
            ('contribution_utilizavel',int((d.usable & d.experiment_type.eq('contribution')).sum()))]
    countframe=pd.DataFrame(counts,columns=['category','n'])
    countids={'total_previsto':ids(cov.experiment_id.dropna()),'total_encontrado':ids(d.experiment_id),
        'total_concluido_status':ids(d.loc[d.status.eq('COMPLETED'),'experiment_id']),'total_utilizavel':ids(d.loc[d.usable,'experiment_id']),
        'total_incompleto':ids(d.loc[d.status.isin(['RUNNING','MISSING']),'experiment_id']),'total_falho':ids(d.loc[d.status.eq('FAILED'),'experiment_id']),
        'total_excluido':ids(d.loc[~d.usable,'experiment_id']),'contribution_utilizavel':ids(d.loc[d.usable & d.experiment_type.eq('contribution'),'experiment_id'])}
    countframe['experiment_ids']=countframe.category.map(countids)
    save_table(1,'tables/run_counts.csv',countframe,aggregation='count of IDs matching category; previsto is enumeration of design coverage including SKIPPED')
    for name,col in [('type','experiment_type'),('target','target_dataset'),('model','model'),('representation','representation'),('source_composition','training_datasets'),('seed','seed')]:
        rows=[]
        for key,g in d.groupby([col,'status','usable'],dropna=False):rows.append(dict(zip([col,'status','usable'],key))|{'n':len(g),'experiment_ids':ids(g.experiment_id)})
        save_table(1,f'tables/run_coverage_by_{name}.csv',pd.DataFrame(rows))
    seeds=summary(d[d.usable],keys[:-1],metrics=[]);seeds['missing_seeds']=seeds.seeds.map(lambda x:json.dumps(sorted(set(CFG['expected_seeds'])-set(json.loads(x)))))
    save_table(1,'tables/seed_coverage.csv',seeds)
    rq={'RQ1':d.experiment_type.str.startswith(('baseline','pairwise','lodo','embedding')),
        'RQ2':d.experiment_type.eq('contribution'),'RQ3':d.usable,'RQ4':d.representation.isin(['RAW','CANONICALIZED'])}
    save_table(1,'tables/rq_counts.csv',pd.DataFrame([{'rq':k,'n_runs':int((v&d.usable).sum()),'experiment_ids':ids(d.loc[v&d.usable,'experiment_id'])} for k,v in rq.items()]))
    doc(1,[f'Inventário completo e contribuição são populações distintas. Contagens verificadas em `tables/run_counts.csv`; distribuição em `tables/run_coverage_by_type.csv`.',
        'As exclusões incluem pilotos, falhas históricas e coalizões removidas pelo controle de família; nenhuma exclusão é apagada (`tables/excluded_runs.csv`).'],
        'Grade esperada reconstruída dos scripts de execução, cenários, seis ablações efetivamente solicitadas e cinco seeds. Métricas exigem status COMPLETED, pilot=0 e campos válidos. Falhas não são substituídas por zeros. RQs se sobrepõem; suas contagens não devem ser somadas.')

def phase4():
    from src.data.loader import load_dataset, decode_until_stable, canonical
    specs=yaml.safe_load(track(ROOT/'config/datasets.yaml').read_text())['datasets']
    manifest=read_csv(ROOT/'datasets/metadata/dataset_manifest.csv');character=read_csv(ROOT/'results/tables/dataset_characterization.csv')
    rows=[];dups=[];effects=[]
    for name,sp in specs.items():
        for rep in ['raw','decoded']:
            path=ROOT/'datasets/original_copies'/rep/sp[f'{rep}_file'];track(path)
            f=load_dataset(name,rep);txt=f.text.astype(str)
            r=dict(dataset=name,representation='RAW' if rep=='raw' else 'CANONICALIZED',total_samples=len(f),benign_samples=int(f.y.eq(0).sum()),
                malicious_samples=int(f.y.eq(1).sum()),positive_prevalence=float(f.y.mean()),unique_samples=f.text_hash.nunique(),
                unique_canonical_samples=f.canonical_hash.nunique(),input_type='URL path/query/fragment + body',source_provenance=sp.get('notes'),family=sp['family'],
                primary=name!='artificial',source_file=rel(path));rows.append(r)
            forms={'exact':txt,'lowercase':txt.str.lower(),'whitespace':txt.str.replace(r'\s+',' ',regex=True).str.strip(),'canonical_key':txt.map(canonical)}
            for form,s in forms.items():
                u=pd.DataFrame({'text':s,'y':f.y});conflicts=int((u.groupby('text').y.nunique()>1).sum())
                dups.append(dict(dataset=name,representation=r['representation'],normalization=form,n=len(s),unique=s.nunique(),
                    duplicate_rows_all=int(s.duplicated(False).sum()),duplicate_excess=int(s.duplicated().sum()),label_conflict_keys=conflicts,source_file=rel(path)))
            if rep=='raw':
                decoded=txt.map(decode_until_stable)
                effects.append(dict(dataset=name,n=len(txt),changed_n=int(txt.ne(decoded).sum()),changed_fraction=float(txt.ne(decoded).mean()),
                    length_before=txt.str.len().mean(),length_after=decoded.str.len().mean(),
                    encoding_before=txt.str.contains(r'%[0-9a-fA-F]{2}').mean(),encoding_after=decoded.str.contains(r'%[0-9a-fA-F]{2}').mean(),
                    unique_before=txt.nunique(),unique_after=decoded.nunique(),duplicates_created=txt.nunique()-decoded.nunique(),
                    scope='in-memory URL-decoding of RAW rows; not equivalence to separate decoded corpus',source_file=rel(path)))
            del f,txt,forms
    data=save_table(2,'tables/dataset_characterization.csv',pd.DataFrame(rows))
    save_table(2,'tables/dataset_class_distribution.csv',data[['dataset','representation','total_samples','benign_samples','malicious_samples','positive_prevalence','source_file']])
    character['representation']=character.representation.replace({'raw':'RAW','decoded':'CANONICALIZED'})
    save_table(2,'tables/dataset_textual_characteristics.csv',character,source=rel(ROOT/'results/tables/dataset_characterization.csv'))
    save_table(2,'tables/dataset_provenance.csv',manifest,source=rel(ROOT/'datasets/metadata/dataset_manifest.csv'))
    save_table(2,'derived/normalization_audit.parquet',pd.DataFrame(dups))
    save_table(2,'derived/canonicalization_effects.parquet',pd.DataFrame(effects))
    doc(2,['Distribuições de classes, tamanho e diversidade estão em `tables/dataset_characterization.csv`; diferenças lexicais são estratificadas por classe em `tables/dataset_textual_characteristics.csv`.',
        'RAW e CANONICALIZED são arquivos distintos, com tamanhos diferentes em parte das fontes. artificial é documentado, mas artificial_sqli é a variante da grade principal.'],
        'Arquivos originais processados um dataset por vez; sem treino. Caracterização lexical existente reutilizada com sua procedência. n_unique refere-se ao texto realmente carregado; prevalência é ataques/n. DOI, ano e método de geração permanecem ausentes quando não registrados.')

def phase5():
    d=valid();dups=read_parquet(directory(2)/'derived/normalization_audit.parquet')
    sizes=read_csv(directory(2)/'tables/dataset_characterization.csv').set_index(['dataset','representation']).total_samples
    save_table(3,'tables/duplicate_audit.csv',dups)
    overlap=read_csv(ROOT/'datasets/metadata/inter_dataset_overlaps.csv');overlap['representation']=overlap.representation.replace({'raw':'RAW','decoded':'CANONICALIZED'})
    save_table(3,'tables/cross_dataset_overlap.csv',overlap,source=rel(ROOT/'datasets/metadata/inter_dataset_overlaps.csv'))
    save_table(3,'tables/label_conflicts.csv',dups[dups.label_conflict_keys>0])
    before=[];checks=[]
    for r in d.to_dict('records'):
        counts=json.loads(r['split_counts']);dev=sum(x['n'] for s in ['train','validation'] for x in counts.get(s,[]))
        source_rep='CANONICALIZED' if 'CANONICALIZED' in r['representation'] else 'RAW'
        before_n=sum(sizes.loc[(s,source_rep)] for s in r['training_datasets'].split('+') if s) if r['experiment_type']!='baseline_id' else sizes.loc[(r['target_dataset'],source_rep)]
        before.append(dict(experiment_id=r['experiment_id'],target=r['target_dataset'],representation=r['representation'],train_n=r['train_n'],validation_n=r['validation_n'],preserved_target_n=r['test_n'],
            removed_same_family=sum(json.loads(r['same_family_removed']).values()),removed_target_overlap=sum(json.loads(r['target_overlap_removed']).values()),removed_label_conflicts=sum(json.loads(r['label_conflicts_removed']).values()),
            after_development=dev,before_development=before_n,total_removed_or_held_out=before_n-dev,limitation='ID difference includes held-out test; OOD difference is removed development samples; do not sum removal categories blindly'))
        target=r['target_dataset'];is_id=r['experiment_type']=='baseline_id'
        absent=target not in (r['actual_train_datasets']+'+'+r['validation_datasets']).split('+')
        checks.append(dict(experiment_id=r['experiment_id'],experiment_type=r['experiment_type'],target=target,
            outer_target_absent_from_development=absent if not is_id else None,
            evidence='saved split counts + static code inspection; not full row audit of every split',
            scaler_fit='training_only',feature_selection='predefined_no_fit',model_selection='fixed_hyperparameters',early_stopping='source_validation',
            threshold_selection='source_validation',oracle='target diagnostic only',calibration='no fitted calibrator',resampling='no full-run sampling'))
    save_table(3,'tables/before_after_audit.csv',pd.DataFrame(before))
    save_table(3,'tables/leakage_checks.csv',pd.DataFrame(checks))
    issue('PAIRWISE_FAMILY','MAJOR','Pairwise usa family_aware=False e contém site_cooking↔site_sqli. Separar pares relacionados das evidências de transferência entre fontes independentes.',rel(ROOT/'scripts/04_pairwise_cross_dataset/run_pairwise.py'))
    issue('AUDIT_SCOPE','LIMITATION','Isolamento completo verificado por metadados de todos os runs e código; somente splits selecionados são lidos por linha. Asserts históricos não substituem auditoria exaustiva dos hashes.',rel(ROOT/'src/data/splits.py'))
    issue('NEAR_DUPLICATES','LIMITATION','Deduplicação por chave canônica foi auditada; busca aproximada adicional de quase-duplicatas está desabilitada (near_dedup=false). Não alegar remoção de todas as variantes semanticamente similares.',rel(ROOT/'config/experiments.yaml'))
    doc(3,['Duplicatas e conflitos estão quantificados em `tables/duplicate_audit.csv` e `tables/label_conflicts.csv`; remoções por fold em `tables/before_after_audit.csv`.',
        'Pairwise permite pares da mesma família e precisa identificá-los. LODO e contribuição aplicam controle de família. Oracle usa o target somente como diagnóstico (`tables/leakage_checks.csv`).'],
        'Lowercase e whitespace auditados separadamente nesta análise; chave canônica combina URL decode recursivo, casefold e normalização whitespace. Overlaps inter-dataset reutilizados da auditoria salva. Alvo preservado; remoções de conflitos e overlap ocorrem no desenvolvimento. Validação reserva uma família inteira quando ambas as partições têm duas classes; fallback GroupShuffleSplit. Não houve busca source-aware de hiperparâmetros.', 'Partial')

def phase6():
    from src.features.lexical import extract,feature_set
    f=pd.DataFrame({'text':['a'],'url':['/a'],'body':['']});x=extract(f)
    fs=[]
    for name in x:
        group='sql' if name.startswith('sql_') else 'xss' if name.startswith('xss_') else 'characters' if name.startswith('char_') else 'structure_encoding_entropy'
        fs.append(dict(feature=name,group=group,position=len(fs)+1,source_file=rel(ROOT/'src/features/lexical.py')))
    save_table(4,'tables/engineered_features.csv',pd.DataFrame(fs))
    d=valid();rows=[]
    for (r,feat),g in d.groupby(['representation','feature_set']):
        dim=768 if r.startswith('CODEBERT') else 832 if r.startswith('EARLY') else feature_set(x,feat).shape[1]
        rows.append(dict(representation=r,feature_set=feat,dimensions=dim,n_runs=len(g),n_samples='fold-specific train_n/validation_n/test_n in master',missing_values='not logged; median imputer fit on training',experiment_ids=ids(g.experiment_id)))
    save_table(4,'tables/representations.csv',pd.DataFrame(rows))
    save_table(4,'tables/canonicalization_effects.csv',read_parquet(directory(2)/'derived/canonicalization_effects.parquet'))
    embeddings=[]
    for p in (ROOT/'datasets/processed/embeddings').glob('*/*.json'):
        m=read_json(p);embeddings.append({k:m.get(k) for k in ['dataset','representation','n','dimensions','truncated_n','truncated_fraction','elapsed_seconds','peak_vram_mib']}|{'encoder':json.dumps(m.get('model')),'source_file':rel(p)})
    save_table(4,'tables/embedding_metadata.csv',pd.DataFrame(embeddings))
    issue('CANONICALIZED_DEFINITION','MAJOR','CANONICALIZED é o nome editorial para decoded: arquivo pré-decodificado + unquote_plus até 10 passagens no loader. Casefold/whitespace pertencem à chave de deduplicação, não ao texto do encoder. Features lexicais usam lower; path_depth/enc_pct usam URL/body originais do arquivo.',rel(ROOT/'src/data/loader.py'))
    doc(4,['Dimensões e features reais constam em `tables/representations.csv` e `tables/engineered_features.csv`; truncamento CodeBERT em `tables/embedding_metadata.csv`.',
        'CANONICALIZED designa a representação decoded. Não significa que casefold e whitespace tenham sido aplicados ao texto do CodeBERT. Transformações isoladas do RAW estão em `tables/canonicalization_effects.csv`, com escopo explícito.'],
        'Dimensões calculadas pelo extrator existente em uma entrada sintética, sem fit. CodeBERT congelado: versão, max_length, pooling e truncamento lidos dos metadados do cache; dimensões densas não recebem interpretação semântica.')

def phase7():
    d=valid();cfg=yaml.safe_load(track(ROOT/'config/models.yaml').read_text())['models']
    save_table(5,'tables/models.csv',pd.DataFrame([dict(model=m,family={'logistic':'linear','catboost':'boosted_trees','mlp':'neural_mlp'}[m],implementation={'logistic':'sklearn.LogisticRegression','catboost':'CatBoostClassifier CPU','mlp':'sklearn.MLPClassifier partial_fit'}[m],source_file=rel(ROOT/'src/models/classical.py')) for m in ['logistic','catboost','mlp']]))
    save_table(5,'tables/model_hyperparameters.csv',pd.DataFrame([dict(model=m,parameter=k,value=json.dumps(v),source_file=rel(ROOT/'config/models.yaml'),historical_snapshot=False) for m,kv in cfg.items() for k,v in kv.items()]))
    save_table(5,'tables/model_run_counts.csv',summary(d,['model','representation','configuration_id'],metrics=[]))
    save_table(5,'tables/model_runtime.csv',summary(d,['experiment_type','model','representation'],['runtime','training_seconds','extraction_seconds','inference_seconds','selected_iterations']))
    save_table(5,'tables/selected_configs_by_target.csv',d[['experiment_id','target_dataset','model','configuration_id','selected_iterations','validation_datasets']].assign(selection='fixed configuration; source-validation early stopping only'))
    doc(5,['MLP compacto usa sklearn e CPU, com arquitetura e procedimento listados em `tables/models.csv` e `tables/model_hyperparameters.csv`.',
        'Não há evidência de busca de hiperparâmetros entre configurações; selected_iterations descreve early stopping (`tables/selected_configs_by_target.csv`).'],
        'Contagens de todos os runs utilizáveis; custo por modelo/protocolo. Transformação median imputer + StandardScaler ajustada exclusivamente no treino. CatBoost até 200 árvores, MLP até 40 épocas; configurações descritas a partir dos arquivos atuais e suas limitações históricas.')

def phase8():
    d=valid();idframe=d[d.experiment_type.eq('baseline_id')];pair=d[d.experiment_type.eq('pairwise')].copy()
    lodo=d[d.experiment_type.str.startswith('lodo_')].copy();main=lodo[lodo.experiment_type.eq('lodo_C_complete')]
    keys=['target_dataset','model','representation','feature_set']
    save_table(6,'ID/tables/id_results.csv',summary(idframe,keys),aggregation='mean/std(ddof=1)/median/min/max across seeds within target, model, representation')
    pair['source']=pair.training_datasets
    pair['related_source']=pair.source.isin(['site_cooking','site_sqli']) & pair.target_dataset.isin(['site_cooking','site_sqli'])
    pp=summary(pair,['source']+keys+['related_source'])
    save_table(6,'PAIRWISE/tables/pairwise_results.csv',pp)
    independent=pp[~pp.related_source].copy()
    for group,name in [('source','source_average'),('target_dataset','target_average')]:
        save_table(6,f'PAIRWISE/tables/{name}.csv',summary(independent,[group,'model','representation'],[m+'_mean' for m in METRICS]),aggregation='seeds first; unweighted mean over independent partner datasets')
    asym=[]
    for row in pp.to_dict('records'):
        matches=pp[(pp.source==row['target_dataset'])&(pp.target_dataset==row['source'])&(pp.model==row['model'])&(pp.representation==row['representation'])]
        if len(matches)==1 and row['source']<row['target_dataset']:
            b=matches.iloc[0];asym.append(dict(source=row['source'],target=row['target_dataset'],model=row['model'],representation=row['representation'],related_source=row['related_source'],
                forward_f1=row['f1_mean'],reverse_f1=b.f1_mean,asymmetry_f1=row['f1_mean']-b.f1_mean,experiment_ids=ids([row['experiment_ids'],b.experiment_ids])))
    save_table(6,'PAIRWISE/tables/transfer_asymmetry.csv',pd.DataFrame(asym))
    for metric in ['f1','mcc','pr_auc','recall','fpr','fnr']:
        mat=independent.groupby(['source','target_dataset'],as_index=False).agg(value=(metric+'_mean','mean'),experiment_ids=('experiment_ids',ids))
        mat['metric']=metric;mat['scope']='equal weight model/representation; seeds summarized first; related pairs excluded'
        save_table(6,f'PAIRWISE/tables/matrix_{metric}.csv',mat)
    by=summary(lodo,['experiment_type']+keys)
    save_table(6,'LODO/tables/lodo_by_target.csv',by)
    macro=summary(by,['experiment_type','model','representation'],[m+'_mean' for m in METRICS])
    save_table(6,'LODO/tables/lodo_macro_summary.csv',macro,aggregation='seeds first; unweighted targets; *_mean_min is worst target for higher-is-better metrics')
    matchkeys=keys+['seed']
    gaps=lodo.merge(idframe,on=matchkeys,suffixes=('_ood','_id'),validate='many_to_one')
    rows=[]
    for r in gaps.to_dict('records'):
        out={k:r[k] for k in matchkeys};out.update(experiment_type=r['experiment_type_ood'],experiment_id_ood=r['experiment_id_ood'],experiment_id_id=r['experiment_id_id'],
            id_test_n=r['test_n_id'],ood_test_n=r['test_n_ood'],limitation='ID held-out subset vs full OOD target; population not identical')
        for m in ['f1','mcc','pr_auc','recall','precision','roc_auc','balanced_accuracy']:
            out['gap_'+m]=r[m+'_id']-r[m+'_ood'];out['ood_'+m]=r[m+'_ood'];out['id_'+m]=r[m+'_id']
        out['ratio_f1']=r['f1_ood']/r['f1_id'] if r['f1_id'] else np.nan;rows.append(out)
    gg=save_table(6,'LODO/derived/gap_pairs.parquet',pd.DataFrame(rows))
    save_table(6,'LODO/tables/generalization_gap.csv',summary(gg,['experiment_type']+keys,['gap_'+m for m in ['f1','mcc','pr_auc','recall','precision','roc_auc','balanced_accuracy']]+['ood_f1','id_f1']))
    save_table(6,'LODO/tables/generalization_ratio.csv',summary(gg,['experiment_type']+keys,['ratio_f1']))
    scenario=[]
    for a,b in [('lodo_A_base','lodo_B_base_plus_cooking'),('lodo_B_base_plus_cooking','lodo_C_complete'),('lodo_A_base','lodo_C_complete')]:
        z=lodo[lodo.experiment_type==a].merge(lodo[lodo.experiment_type==b],on=matchkeys,suffixes=('_a','_b'),validate='one_to_one')
        for r in z.to_dict('records'):
            scenario.append({k:r[k] for k in matchkeys}|dict(scenario_a=a,scenario_b=b,requested_sources_a=r['training_datasets_a'],requested_sources_b=r['training_datasets_b'],effective_sources_a=r['effective_development_datasets_a'],effective_sources_b=r['effective_development_datasets_b'],delta_f1=r['f1_b']-r['f1_a'],experiment_id_a=r['experiment_id_a'],experiment_id_b=r['experiment_id_b']))
    ss=save_table(6,'LODO/derived/scenario_pairs.parquet',pd.DataFrame(scenario))
    save_table(6,'LODO/tables/scenario_common_targets.csv',summary(ss,['scenario_a','scenario_b']+keys,['delta_f1']))
    val=main[['experiment_id','target_dataset','model','representation','seed','validation_datasets','actual_train_datasets','configuration_id','selected_iterations','f1']].copy()
    val['internal_validation_score']=np.nan;val['selected_configuration']='fixed config, source-only early stopping';val['inner_fold_type']='one held-out family or group fallback; not inner CV grid'
    save_table(6,'SOURCE_AWARE_VALIDATION/tables/inner_fold_results.csv',val)
    save_table(6,'SOURCE_AWARE_VALIDATION/tables/selected_configurations.csv',val)
    save_table(6,'SOURCE_AWARE_VALIDATION/tables/validation_vs_ood.csv',val.assign(association_status='not estimable: internal score not saved'))
    # Embeddings use the decoded corpus only; compare them with the lexical decoded LODO.
    emb=d[d.experiment_type.eq('embedding_lodo')]
    save_table(6,'LODO/tables/embedding_and_fusion_results.csv',summary(emb,keys))
    comp=[]
    for _,a in emb.iterrows():
        b=main[(main.target_dataset==a.target_dataset)&(main.model==a.model)&(main.representation=='CANONICALIZED')&(main.seed==a.seed)]
        if len(b)==1:
            b=b.iloc[0];comp.append(dict(target_dataset=a.target_dataset,model=a.model,representation=a.representation,seed=a.seed,
                split_counts_equal=a.split_counts==b.split_counts,delta_f1=a.f1-b.f1,delta_pr_auc=a.pr_auc-b.pr_auc,
                experiment_id_dense=a.experiment_id,experiment_id_lexical=b.experiment_id))
    save_table(6,'LODO/derived/dense_vs_lexical.parquet',pd.DataFrame(comp))
    issue('VALIDATION_SCORE_MISSING','LIMITATION','Scores de validação e trajetória interna não foram preservados; não é possível correlacionar validação interna e OOD nem alegar nested source-aware tuning.',rel(ROOT/'src/evaluation/runner.py'))
    issue('ID_OOD_POPULATIONS','LIMITATION','ID avalia subconjunto interno após remoções; OOD avalia arquivo-alvo completo preservado. Gap descritivo inclui diferença de população avaliada.',rel(directory(6)/'LODO/tables/generalization_gap.csv'))
    doc(6,['Resultado principal: LODO C por target/modelo em `LODO/tables/lodo_by_target.csv`; ID separado em `ID/tables/id_results.csv`.',
        'Gap e razão de generalização estão em `LODO/tables/generalization_gap.csv` e `generalization_ratio.csv`. Targets ruins permanecem nas tabelas; médias macro não os substituem.',
        'Comparações A/B/C usam somente targets comuns (`LODO/tables/scenario_common_targets.csv`). Pares da mesma família são identificados e excluídos das médias de transferência independente.',
        'Embeddings e early fusion estão em `LODO/tables/embedding_and_fusion_results.csv`. Não existem scores internos suficientes para afirmar associação validação→OOD.'],
        'Principal metrics_source, threshold escolhido na validação de origem. PR-AUC=average_precision_score (não trapezoidal). Seeds resumidas dentro de cada condição. Gap=M_ID−M_OOD; razão F1_OOD/F1_ID, indefinida se denominador zero. Cenários não são combinados. SOURCE_AWARE_VALIDATION documenta somente os domínios e early stopping realmente existentes.','Partial')

def contribution_pairs(d):
    contrib=d[d.experiment_type.eq('contribution')];cfg=yaml.safe_load(track(ROOT/'config/experiments.yaml').read_text());pool=cfg['dataset_policy']['primary_datasets'];rows=[]
    for key,g in contrib.groupby(['target_dataset','model','representation','feature_set','seed']):
        target=key[0];fullset=set(pool)-{target};lookup={frozenset(r.training_datasets.split('+')):r for r in g.itertuples()}
        a=lookup.get(frozenset(fullset))
        if a is None:continue
        for source in sorted(fullset):
            b=lookup.get(frozenset(fullset-{source}))
            if b is None:continue
            r=dict(zip(['target_dataset','model','representation','feature_set','seed'],key))
            r.update(removed_source=source,experiment_id_full=a.experiment_id,experiment_id_removed=b.experiment_id,
                sources_full=a.training_datasets,sources_removed=b.training_datasets,effective_sources_full=a.effective_development_datasets,effective_sources_removed=b.effective_development_datasets,
                source_removed_was_effective=source in a.effective_development_datasets.split('+'),validation_changed=a.validation_datasets!=b.validation_datasets,
                validation_full=a.validation_datasets,validation_removed=b.validation_datasets,
                threshold_delta=a.threshold_source-b.threshold_source)
            for m in METRICS:
                r['full_'+m]=getattr(a,m);r['removed_'+m]=getattr(b,m);r['delta_'+m]=getattr(a,m)-getattr(b,m)
            r['benefit_fpr']=-r['delta_fpr'];r['benefit_fnr']=-r['delta_fnr'];rows.append(r)
    return pd.DataFrame(rows)

def phase9():
    d=valid();pairs=save_table(7,'derived/full_vs_removed.parquet',contribution_pairs(d))
    keys=['target_dataset','removed_source','model','representation','feature_set','source_removed_was_effective']
    metrics=['delta_'+m for m in METRICS]+['full_'+m for m in ['f1','mcc','pr_auc']]+['removed_'+m for m in ['f1','mcc','pr_auc']]+['threshold_delta','benefit_fpr','benefit_fnr']
    agg=save_table(7,'tables/source_contribution_full.csv',summary(pairs,keys,metrics))
    effective=agg[agg.source_removed_was_effective]
    for metric in ['f1','mcc']:
        s=summary(effective,['removed_source','target_dataset'],['delta_'+metric+'_mean'])
        save_table(7,f'tables/source_target_matrix_{metric}.csv',s,aggregation='seed means, then equal model/representation weights; family-filtered no-ops excluded')
    src=[]
    for (source,m,rep),g in effective.groupby(['removed_source','model','representation']):
        vals=g.delta_f1_mean;src.append(dict(source=source,model=m,representation=rep,mean_contribution=vals.mean(),median_contribution=vals.median(),
            n_targets=len(g),targets_helped=int((vals>CFG['neutral_tolerance']).sum()),targets_harmed=int((vals<-CFG['neutral_tolerance']).sum()),targets_neutral=int((vals.abs()<=CFG['neutral_tolerance']).sum()),experiment_ids=ids(g.experiment_ids)))
    save_table(7,'tables/source_summary.csv',pd.DataFrame(src))
    target=[]
    for key,g in effective.groupby(['target_dataset','model','representation']):
        best=g.loc[g.delta_f1_mean.idxmax()];worst=g.loc[g.delta_f1_mean.idxmin()]
        target.append(dict(zip(['target_dataset','model','representation'],key))|dict(most_useful_source=best.removed_source,best_delta_f1=best.delta_f1_mean,most_harmful_source=worst.removed_source,worst_delta_f1=worst.delta_f1_mean,experiment_ids=ids(g.experiment_ids)))
    save_table(7,'tables/target_summary.csv',pd.DataFrame(target))
    transfer=effective.rename(columns={'full_f1_mean':'metric_before','removed_f1_mean':'metric_after','delta_f1_mean':'delta'})
    save_table(7,'tables/negative_transfer.csv',transfer[transfer.delta < -CFG['neutral_tolerance']].sort_values('delta'))
    save_table(7,'tables/positive_transfer.csv',transfer[transfer.delta > CFG['neutral_tolerance']].sort_values('delta',ascending=False))
    save_table(7,'tables/neutral_transfer.csv',transfer[transfer.delta.abs()<=CFG['neutral_tolerance']])
    save_table(7,'tables/family_filtered_noops.csv',agg[~agg.source_removed_was_effective])
    # Descriptive source-count association: collapse seeds AND duplicate effective pools first.
    c=d[d.experiment_type.eq('contribution')]
    eff=summary(c,['target_dataset','model','representation','effective_development_datasets','n_effective_sources'],['f1','mcc'])
    save_table(7,'tables/per_effective_source_pool.csv',eff,aggregation='equal seeds; duplicate requested coalitions with identical effective pools included explicitly; deterministic duplicate results checked separately')
    issue('CONTRIBUTION_VALIDATION','LIMITATION','Remover uma fonte pode mudar a família de validação e early stopping. Efeitos medem mudança no procedimento completo, não efeito causal isolado de exemplos de treino.',rel(directory(7)/'derived/full_vs_removed.parquet'))
    issue('COALITION_NOOPS','MAJOR','Fonte da mesma família do target é removida antes do treino: distintas coalizões solicitadas podem ser idênticas na prática. n_effective_sources e effective_development_datasets devem orientar análise de diversidade.',rel(directory(7)/'tables/family_filtered_noops.csv'))
    doc(7,['A contribuição principal usa pool completo menos uma fonte com mesmo target/modelo/representação/seed (`tables/source_contribution_full.csv`).',
        'Os casos de negative transfer estão em `tables/negative_transfer.csv`; efeitos positivos e nulos também são preservados. Fontes removidas automaticamente pelo filtro de família ficam em `tables/family_filtered_noops.csv`.',
        'O arquivo legado dataset_shapley.csv não é utilizado como estimativa Shapley clássica.'],
        'C_i=M(full)−M(without_i); positivo indica contribuição para F1/MCC/AP/recall. Para FPR/FNR benefit=erro(without)−erro(full). Seeds pareadas primeiro; médias e desvios dentro da condição. Alteração de validação é registrada por par. Não interpretar o efeito como causalidade.', 'Complete')

def phase10():
    d=valid();cols=['experiment_id','experiment_type','target_dataset','training_datasets','model','representation','feature_set','seed','threshold_source','threshold_oracle','threshold_drift','oracle_gap','f1','f1_oracle','pr_auc','fpr','fnr','brier','ece_10']
    save_table(8,'tables/threshold_results.csv',d[cols])
    keys=['experiment_type','target_dataset','training_datasets','model','representation','feature_set']
    save_table(8,'tables/threshold_drift.csv',summary(d,keys,['threshold_drift','threshold_source','threshold_oracle']))
    save_table(8,'tables/oracle_gap.csv',summary(d,keys,['oracle_gap','f1','f1_oracle','pr_auc']))
    save_table(8,'tables/calibration_results.csv',summary(d,keys,['brier','ece_10','f1','fpr','fnr']))
    main=d[d.experiment_type.eq('lodo_C_complete')];chosen=[]
    for col in ['threshold_drift','oracle_gap']:
        for kind,index in [('largest',main[col].idxmax()),('lowest',main[col].idxmin()),('median',(main[col]-main[col].median()).abs().idxmin())]:
            r=main.loc[index];chosen.append(dict(experiment_id=r.experiment_id,selection_criterion=kind+'_'+col,value=r[col],target=r.target_dataset,model=r.model,representation=r.representation))
    save_table(8,'selected_runs/threshold_cases.csv',pd.DataFrame(chosen))
    comp=[]
    idf=d[d.experiment_type.eq('baseline_id')]
    for r in main.itertuples():
        b=idf[(idf.target_dataset==r.target_dataset)&(idf.model==r.model)&(idf.representation==r.representation)&(idf.seed==r.seed)]
        if len(b):
            b=b.iloc[0];comp.append(dict(target_dataset=r.target_dataset,model=r.model,representation=r.representation,seed=r.seed,delta_brier=r.brier-b.brier,delta_ece=r.ece_10-b.ece_10,ood_f1=r.f1,experiment_id_ood=r.experiment_id,experiment_id_id=b.experiment_id))
    cp=save_table(8,'derived/calibration_pairs.parquet',pd.DataFrame(comp))
    save_table(8,'tables/calibration_id_vs_ood.csv',summary(cp,['target_dataset','model','representation'],['delta_brier','delta_ece','ood_f1']))
    doc(8,['Threshold drift e oracle gap estão separados em `tables/threshold_drift.csv` e `tables/oracle_gap.csv`; oracle é diagnóstico pós-teste.',
        'Brier e ECE-10 já estavam nos arquivos de métricas e foram reutilizados (`tables/calibration_results.csv`). Não houve treinamento de calibrador.',
        'Scores são inspecionados somente nos casos selecionados (`selected_runs/threshold_cases.csv`). Scores de validação/source não foram salvos; comparação source vs target não é reconstruída.'],
        'Drift=abs(t_source−t_oracle); oracle gap=F1_oracle−F1_source. ECE usa 10 intervalos uniformes [0,1]; Brier=mean((p−y)^2). Probabilidades não são assumidas calibradas. Mudança ID/OOD inclui populações de teste diferentes. Associações usam seeds resumidas e targets como unidades.', 'Partial')

def rank_comparison(a,b,k):
    idx=a.index.intersection(b.index);a=a.loc[idx];b=b.loc[idx]
    if len(idx)<2:return (np.nan,np.nan,np.nan)
    ra=a.rank(ascending=False,method='average');rb=b.rank(ascending=False,method='average')
    rho=stats.spearmanr(ra,rb).statistic if ra.nunique()>1 and rb.nunique()>1 else np.nan
    tau=stats.kendalltau(ra,rb).statistic if ra.nunique()>1 and rb.nunique()>1 else np.nan
    # Deterministic ties: feature name as secondary key.
    aa=set(a.sort_index().sort_values(ascending=False,kind='stable').head(k).index);bb=set(b.sort_index().sort_values(ascending=False,kind='stable').head(k).index)
    return rho,tau,len(aa&bb)/len(aa|bb)

def phase11():
    d=valid();main=d[(d.experiment_type=='lodo_C_complete')&(d.model=='catboost')&(d.feature_set=='lex64')]
    pairs=read_parquet(directory(7)/'derived/full_vs_removed.parquet');pairs=pairs[pairs.model=='catboost']
    wanted=set(main.experiment_id)|set(pairs.experiment_id_full)|set(pairs.experiment_id_removed)
    lineage=read_parquet(GLOBAL/'SOURCE_LINEAGE.parquet').set_index('experiment_id');ranks={};rows=[]
    for eid in sorted(wanted):
        path=lineage.loc[eid,'feature_importance_file']
        if not path:continue
        f=read_csv(ROOT.parent/path);f['experiment_id']=eid;f['source_file']=path
        f['rank']=f.importance.rank(ascending=False,method='average');rows.append(f)
        ranks[eid]=f.set_index('feature').importance
    allf=pd.concat(rows,ignore_index=True)
    save_table(9,'derived/selected_feature_importances.parquet',allf)
    base=allf.merge(main[['experiment_id','target_dataset','representation','seed']],on='experiment_id')
    save_table(9,'tables/feature_rankings_by_target.csv',summary(base,['target_dataset','representation','feature'],['importance','rank']))
    stable=summary(base,['representation','feature'],['importance','rank'])
    freq=base.assign(in_top_k=base['rank']<=CFG['top_k']).groupby(['representation','feature']).in_top_k.mean()
    stable['top_k_frequency']=[freq.loc[(r.representation,r.feature)] for r in stable.itertuples()]
    save_table(9,'tables/stable_features.csv',stable.sort_values(['representation','top_k_frequency','importance_mean'],ascending=[True,False,False]))
    comparisons=[];effects=[]
    for r in pairs.itertuples():
        if r.experiment_id_full not in ranks or r.experiment_id_removed not in ranks:continue
        a=ranks[r.experiment_id_full];b=ranks[r.experiment_id_removed];rho,tau,jac=rank_comparison(a,b,CFG['top_k'])
        comparisons.append(dict(comparison='full_vs_removed',target_dataset=r.target_dataset,other_target=r.target_dataset,removed_source=r.removed_source,model='catboost',representation=r.representation,seed=r.seed,spearman=rho,kendall=tau,jaccard_topk=jac,instability=1-rho,delta_f1=r.delta_f1,delta_mcc=r.delta_mcc,source_removed_was_effective=r.source_removed_was_effective,experiment_id_a=r.experiment_id_full,experiment_id_b=r.experiment_id_removed))
        ra=a.rank(ascending=False,method='average');rb=b.rank(ascending=False,method='average')
        for feat in a.index.intersection(b.index):
            effects.append(dict(target_dataset=r.target_dataset,removed_source=r.removed_source,representation=r.representation,seed=r.seed,feature=feat,
                delta_importance=a[feat]-b[feat],delta_rank=ra[feat]-rb[feat],delta_f1=r.delta_f1,delta_mcc=r.delta_mcc,delta_recall=r.delta_recall,delta_fpr=r.delta_fpr,delta_threshold=r.threshold_delta,
                experiment_id_full=r.experiment_id_full,experiment_id_removed=r.experiment_id_removed))
    for (rep,seed),g in main.groupby(['representation','seed']):
        for a,b in itertools.combinations(list(g.itertuples()),2):
            if a.experiment_id not in ranks or b.experiment_id not in ranks:continue
            rho,tau,jac=rank_comparison(ranks[a.experiment_id],ranks[b.experiment_id],CFG['top_k'])
            comparisons.append(dict(comparison='target_vs_target',target_dataset=a.target_dataset,other_target=b.target_dataset,removed_source='',model='catboost',representation=rep,seed=seed,spearman=rho,kendall=tau,jaccard_topk=jac,instability=1-rho,delta_f1=np.nan,delta_mcc=np.nan,source_removed_was_effective=True,experiment_id_a=a.experiment_id,experiment_id_b=b.experiment_id))
    comp=save_table(9,'derived/rank_pairs.parquet',pd.DataFrame(comparisons))
    out=summary(comp,['comparison','target_dataset','other_target','removed_source','representation'],['spearman','kendall','jaccard_topk','instability','delta_f1'])
    save_table(9,'tables/feature_stability.csv',out);save_table(9,'tables/feature_rank_correlations.csv',out)
    save_table(9,'tables/jaccard_topk.csv',out)
    ef=save_table(9,'derived/source_removal_feature_pairs.parquet',pd.DataFrame(effects))
    save_table(9,'tables/source_removal_feature_effects.csv',summary(ef,['target_dataset','removed_source','representation','feature'],['delta_importance','delta_rank','delta_f1','delta_mcc','delta_recall','delta_fpr','delta_threshold']))
    ab=d[d.experiment_type.eq('ablation')]
    save_table(9,'tables/feature_ablation_by_target.csv',summary(ab,['target_dataset','model','representation','feature_set']))
    doc(9,['Rankings CatBoost e estabilidade estão em `tables/feature_rankings_by_target.csv`, `stable_features.csv` e `feature_stability.csv`.',
        'Alterações por remoção de fonte e sua coincidência com F1/MCC/recall/FPR estão em `tables/source_removal_feature_effects.csv`.',
        'Ablações existentes são incluídas em `tables/feature_ablation_by_target.csv`. Dimensões dos embeddings não foram interpretadas como features semânticas.'],
        'Somente importâncias CatBoost já existentes, lex64, LODO C e coalizões full/leave-one-source. Spearman/Kendall entre ranks médios, empates com average rank. Top-10 desempata por nome; Jaccard=interseção/união. Importância é model-specific e não causal; estável não implica invariância universal. RAW vs CANONICALIZED depende do pareamento auditado na fase RQ4.')

def split_fingerprint(path):
    """Multiset digest per split, independent of representation-specific sample IDs."""
    arrays=[]
    for chunk in pd.read_csv(track(path),usecols=['dataset','canonical_hash','y','split'],chunksize=50000):
        arrays.extend((chunk.dataset.astype(str)+'|'+chunk.canonical_hash+'|'+chunk.y.astype(str)+'|'+chunk.split).tolist())
    return digest('\n'.join(sorted(arrays)))

def phase12():
    d=valid();keys=['experiment_type','target_dataset','training_datasets','model','configuration_id','feature_set','seed','family_aware']
    p=d[d.representation=='RAW'].merge(d[d.representation=='CANONICALIZED'],on=keys,suffixes=('_raw','_can'),validate='one_to_one')
    lineage=read_parquet(GLOBAL/'SOURCE_LINEAGE.parquet').set_index('experiment_id');cache={};audit=[];paired=[]
    for r in p.to_dict('records'):
        a,b=r['experiment_id_raw'],r['experiment_id_can'];eq=r['split_counts_raw']==r['split_counts_can'];reason='different_split_counts'
        if eq:
            for eid in [a,b]:
                if eid not in cache:
                    path=lineage.loc[eid,'split_file'];cache[eid]=split_fingerprint(ROOT.parent/path) if path else None
            eq=cache[a] is not None and cache[a]==cache[b];reason='identical_canonical_multisets_per_split' if eq else 'different_split_membership'
        audit.append({k:r[k] for k in keys}|dict(experiment_id_raw=a,experiment_id_can=b,eligible=eq,pairing_reason=reason,test_n_raw=r['test_n_raw'],test_n_can=r['test_n_can']))
        if eq:
            o={k:r[k] for k in keys};o.update(experiment_id_raw=a,experiment_id_can=b,pairing_reason=reason)
            for m in METRICS+['threshold_source','threshold_drift']:
                o['raw_'+m]=r[m+'_raw'];o['can_'+m]=r[m+'_can'];o['delta_'+m]=r[m+'_can']-r[m+'_raw']
            paired.append(o)
    au=save_table(10,'RAW_VS_CANONICALIZED/tables/pairing_audit.csv',pd.DataFrame(audit))
    columns=keys+['experiment_id_raw','experiment_id_can','pairing_reason']+[prefix+m for m in METRICS+['threshold_source','threshold_drift'] for prefix in ['raw_','can_','delta_']]
    strict=save_table(10,'RAW_VS_CANONICALIZED/tables/paired_results.csv',pd.DataFrame(paired,columns=columns))
    if len(strict):
        by=summary(strict,['experiment_type','target_dataset','model','feature_set'],['delta_'+m for m in METRICS+['threshold_source','threshold_drift']])
        save_table(10,'RAW_VS_CANONICALIZED/tables/by_target.csv',by)
        save_table(10,'RAW_VS_CANONICALIZED/tables/by_model.csv',summary(by,['experiment_type','model','feature_set'],['delta_f1_mean','delta_mcc_mean','delta_pr_auc_mean']))
        wl=by[['experiment_type','target_dataset','model','feature_set','delta_f1_mean','experiment_ids']].copy();wl['outcome']=np.where(wl.delta_f1_mean>CFG['neutral_tolerance'],'improved',np.where(wl.delta_f1_mean<-CFG['neutral_tolerance'],'worsened','neutral'))
        save_table(10,'RAW_VS_CANONICALIZED/tables/win_tie_loss.csv',wl)
    else:
        for name in ['by_target','by_model','win_tie_loss']:save_table(10,f'RAW_VS_CANONICALIZED/tables/{name}.csv',pd.DataFrame(columns=['status','reason']).assign())
    sep=read_csv(ROOT/'results/runs/historical/index/dataset_separability.csv');sep['representation']=sep.representation.replace({'raw':'RAW','decoded':'CANONICALIZED'})
    sep['same_n_per_dataset']=False;sep['cross_dataset_dedup']=False;sep['class_balanced_per_dataset']=True;sep['status']='exploratory_only';sep['chance_macro_f1']=np.nan
    save_table(10,'DATASET_SEPARABILITY/tables/separability_all.csv',sep,source=rel(ROOT/'results/runs/historical/index/dataset_separability.csv'))
    for name in ['benign','malicious']:
        save_table(10,f'DATASET_SEPARABILITY/tables/separability_{name}.csv',pd.DataFrame([{'status':'not_executed','reason':'No saved class-specific model; new training forbidden.'}]),source=rel(ROOT/'scripts/12_dataset_separability/run_separability.py'))
    save_table(10,'DATASET_SEPARABILITY/tables/raw_vs_canonicalized.csv',sep,source=rel(ROOT/'results/runs/historical/index/dataset_separability.csv'))
    save_table(10,'RELATIONSHIPS/tables/separability_vs_generalization.csv',pd.DataFrame([{'status':'not_estimable','reason':'Only two global separability points, one seed; no target-wise separability and incomplete controls.'}]))
    issue('RAW_PAIRING','CRITICAL ISSUE','Não atribuir diferenças entre arquivos RAW/decoded à transformação isolada quando splits/populações diferem. Somente paired_results.csv satisfaz igualdade dos multiconjuntos canônicos por partição.',rel(directory(10)/'RAW_VS_CANONICALIZED/tables/pairing_audit.csv'))
    issue('SEPARABILITY_CONTROLS','MAJOR','Separabilidade existente usa min(2500,n_dataset_class), portanto n desigual entre datasets; não purga duplicatas entre splits nem entre fontes. Só há all-classes/seed42, não benign-only/malicious-only. Não é prova controlada de redução de separabilidade.',rel(ROOT/'scripts/12_dataset_separability/run_separability.py'))
    doc(10,['A elegibilidade pareada de cada comparação está em `RAW_VS_CANONICALIZED/tables/pairing_audit.csv`; apenas execuções elegíveis alimentam `paired_results.csv`.',
        'Separabilidade existente é exploratória: os tamanhos por origem não são iguais e duplicatas não foram controladas (`DATASET_SEPARABILITY/tables/separability_all.csv`). Os experimentos benign-only e malicious-only não existem.',
        'Sem observações de separabilidade por target, as relações separabilidade→generalização não são estimáveis (`RELATIONSHIPS/tables/separability_vs_generalization.csv`).'],
        'Parear protocolo/target/fontes/modelo/config/feature/seed/family policy. Exigir contagens iguais e multiconjuntos dataset+canonical_hash+label+split iguais. Delta=CANONICALIZED−RAW. O hash canônico permite alinhamento sem IDs dependentes de representação. Mesmo multiconjunto não prova equivalência individual de rótulos conflitantes; casos de erro serão pareados somente por chave única. Não realizar treino adicional para preencher condições ausentes.', 'Partial')

def holm(frame, family='family'):
    d=frame.copy();d['p_holm']=np.nan
    if not len(d):return d
    for _,g in d[d.p_value.notna()].groupby(family):
        order=g.sort_values('p_value');adjust=np.maximum.accumulate(np.minimum(1,order.p_value.to_numpy()*(len(order)-np.arange(len(order)))))
        d.loc[order.index,'p_holm']=adjust
    return d

_PERMUTATIONS={}
def exact_spearman(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float);ok=np.isfinite(x)&np.isfinite(y);x=x[ok];y=y[ok]
    if len(x)<3 or len(set(x))<2 or len(set(y))<2:return np.nan,np.nan
    a=stats.rankdata(x);b=stats.rankdata(y);a-=a.mean();b-=b.mean();den=np.linalg.norm(a)*np.linalg.norm(b)
    rho=float(np.dot(a,b)/den)
    if len(x)<=8:
        if len(x) not in _PERMUTATIONS:_PERMUTATIONS[len(x)]=np.asarray(list(itertools.permutations(range(len(x)))),dtype=np.int16)
        vals=(b[_PERMUTATIONS[len(x)]]@a)/den
        return rho,float(np.mean(np.abs(vals)>=abs(rho)-1e-12))
    return stats.spearmanr(x,y)

def phase13():
    main=valid();main=main[main.experiment_type.eq('lodo_C_complete')]
    target=summary(main,['target_dataset','model','representation'],METRICS+['threshold_drift','oracle_gap'])
    rng=np.random.default_rng(CFG['seed']);des=[];wil=[];fried=[];assoc=[]
    for (model,rep),g in target.groupby(['model','representation']):
        for metric in METRICS:
            v=g[metric+'_mean'].dropna().to_numpy();draw=rng.choice(v,(CFG['bootstrap_iterations'],len(v)),replace=True).mean(axis=1)
            des.append(dict(model=model,representation=rep,metric=metric,n_targets=len(v),mean=v.mean(),std=v.std(ddof=1),median=np.median(v),min=v.min(),max=v.max(),ci95_low=np.quantile(draw,.025),ci95_high=np.quantile(draw,.975),ci_scope='target bootstrap; convenience targets, exploratory',experiment_ids=ids(g.experiment_ids)))
    save_table(11,'statistics/descriptive_summary.csv',pd.DataFrame(des))
    def wtest(g,col,family,label):
        v=g[col].dropna();n=len(v)
        if n<5:stat,pval=np.nan,np.nan;status='insufficient_targets'
        elif np.allclose(v,0):stat,pval=0,1.;status='all_zero'
        else:stat,pval=stats.wilcoxon(v,alternative='two-sided',method='auto');status='exploratory'
        wil.append(dict(family=family,comparison=label,n_targets=n,statistic=stat,p_value=pval,mean_delta=v.mean(),median_delta=v.median(),status=status,experiment_ids=ids(g.experiment_ids)))
    pairs=read_csv(directory(10)/'RAW_VS_CANONICALIZED/tables/paired_results.csv')
    if len(pairs):
        ss=summary(pairs,['experiment_type','target_dataset','model','feature_set'],['delta_f1','delta_mcc','delta_pr_auc'])
        for key,g in ss.groupby(['experiment_type','model','feature_set']):
            for m in ['f1','mcc','pr_auc']:wtest(g,'delta_'+m+'_mean','canonicalization',str(key)+' '+m)
    else:issue('NO_PAIRED_CANON_TEST','LIMITATION','Nenhum par RAW/CANONICALIZED validado para inferência estatística.',rel(directory(10)/'RAW_VS_CANONICALIZED/tables/paired_results.csv'))
    cp=read_csv(directory(7)/'tables/source_contribution_full.csv');cp=cp[cp.source_removed_was_effective]
    for key,g in cp.groupby(['removed_source','model','representation']):
        for m in ['f1','mcc','pr_auc']:wtest(g,'delta_'+m+'_mean','source_removal_'+m,str(key)+' '+m)
    for rep,g in target.groupby('representation'):
        for metric in ['f1','mcc','pr_auc']:
            pivot=g.pivot(index='target_dataset',columns='model',values=metric+'_mean').dropna()
            if pivot.shape[1]>=3 and len(pivot)>=5:
                stat,pval=stats.friedmanchisquare(*(pivot[c] for c in pivot));fried.append(dict(family='models',representation=rep,metric=metric,n_targets=len(pivot),statistic=stat,p_value=pval,experiment_ids=ids(g.experiment_ids)))
    # Gate post-hoc by Holm-adjusted omnibus tests, not by unadjusted p-values.
    fadj=holm(pd.DataFrame(fried))
    for fr in fadj[fadj.p_holm<.05].itertuples():
        g=target[target.representation==fr.representation];pivot=g.pivot(index='target_dataset',columns='model',values=fr.metric+'_mean').dropna()
        for a,b in itertools.combinations(pivot.columns,2):
            tmp=pd.DataFrame({'difference':pivot[a]-pivot[b],'experiment_ids':[ids(g[g.target_dataset==t].experiment_ids) for t in pivot.index]})
            wtest(tmp,'difference','model_posthoc',f'{fr.representation}:{fr.metric}:{a}-{b}')
    save_table(11,'statistics/wilcoxon_results.csv',pd.DataFrame(wil))
    save_table(11,'statistics/friedman_results.csv',pd.DataFrame(fried))
    combined=pd.concat([pd.DataFrame(wil).assign(test='wilcoxon'),pd.DataFrame(fried).assign(test='friedman')],ignore_index=True)
    save_table(11,'statistics/holm_adjusted.csv',holm(combined))
    def association(frame,x,y,name,groupcols=['model','representation']):
        for key,g in frame.groupby(groupcols,dropna=False):
            z=g[[x,y]].dropna();n=len(z)
            if n>=5 and z[x].nunique()>1 and z[y].nunique()>1:rho,pval=exact_spearman(z[x],z[y]);status='exploratory_target_level'
            else:rho,pval=np.nan,np.nan;status='insufficient_or_constant'
            assoc.append(dict(relationship=name,group=str(key),n_targets=n,rho=rho,p_value=pval,p_method='exact two-sided permutation (n<=8)',family='cross_rq',status=status,experiment_ids=ids(g.experiment_ids)))
    gg=read_csv(directory(6)/'LODO/tables/generalization_gap.csv');gg=gg[gg.experiment_type.eq('lodo_C_complete')]
    join=target.merge(gg[['target_dataset','model','representation','gap_f1_mean']],on=['target_dataset','model','representation'],validate='one_to_one')
    association(join,'threshold_drift_mean','gap_f1_mean','threshold_drift_vs_generalization_gap')
    association(target,'oracle_gap_mean','f1_mean','oracle_gap_vs_ood_f1')
    association(target,'brier_mean','f1_mean','brier_vs_ood_f1')
    cpt=cp.groupby(['target_dataset','model','representation'],as_index=False).agg(mean_contribution=('delta_f1_mean','mean'),experiment_ids=('experiment_ids',ids))
    j=cpt.merge(target[['target_dataset','model','representation','f1_mean']],on=['target_dataset','model','representation'])
    association(j,'mean_contribution','f1_mean','source_contribution_vs_ood_f1')
    fp=read_parquet(directory(9)/'derived/rank_pairs.parquet');fp=fp[(fp.comparison=='full_vs_removed')&fp.source_removed_was_effective]
    fg=fp.groupby(['target_dataset','representation'],as_index=False).agg(instability=('instability','mean'),negative_transfer=('delta_f1',lambda v:float(np.maximum(-v,0).mean())),experiment_ids=('experiment_ids',ids))
    fg['model']='catboost';fj=fg.merge(target[['target_dataset','model','representation','f1_mean']],on=['target_dataset','model','representation'])
    association(fj,'instability','f1_mean','feature_instability_vs_ood_f1')
    association(fg,'instability','negative_transfer','feature_instability_vs_negative_transfer')
    fgap=fg.merge(gg[['target_dataset','model','representation','gap_f1_mean']],on=['target_dataset','model','representation'])
    association(fgap,'instability','gap_f1_mean','feature_instability_vs_generalization_gap')
    cal=read_csv(directory(8)/'tables/calibration_id_vs_ood.csv')
    association(cal,'delta_brier_mean','ood_f1_mean','calibration_degradation_vs_ood_f1')
    pools=read_csv(directory(7)/'tables/per_effective_source_pool.csv');nr=[]
    for key,g in pools.groupby(['target_dataset','model','representation']):
        rho=stats.spearmanr(g.n_effective_sources,g.f1_mean).statistic if g.n_effective_sources.nunique()>1 else np.nan
        nr.append(dict(zip(['target_dataset','model','representation'],key))|dict(rho=rho,n_effective_pools=len(g),experiment_ids=ids(g.experiment_ids)))
    save_table(11,'statistics/source_count_within_target.csv',pd.DataFrame(nr),aggregation='descriptive Spearman across effective pools within target; no pseudo-independent p-values across coalitions')
    save_table(11,'statistics/cross_rq_relationships.csv',holm(pd.DataFrame(assoc)))
    doc(11,['As unidades estatísticas são targets após resumo das seeds (`statistics/descriptive_summary.csv`). Intervalos bootstrap são exploratórios para este conjunto de fontes.',
        'Wilcoxon, Friedman e correção Holm estão em `statistics/wilcoxon_results.csv`, `friedman_results.csv` e `holm_adjusted.csv`.',
        'Associações previstas aparecem em `statistics/cross_rq_relationships.csv`; correlações entre número de fontes e F1 dentro de cada target são descritivas em `source_count_within_target.csv`.'],
        'Seeds não são unidades independentes. Wilcoxon bilateral sobre diferenças entre targets; mínimo cinco targets; Holm por família registrada. Friedman por representação/métrica para três modelos (aproximação qui-quadrado, n pequeno); post-hoc somente se omnibus p_Holm<.05. Spearman cross-RQ com permutação bilateral exata até oito targets, uma observação por target; sem inferência quando constante ou n<5. Não usar resultados estatísticos legados com pseudo-replicação. Brier combina calibração/discriminação e compartilha predições com F1; correlação não isola mecanismos.', 'Partial')
    issue('STATISTICAL_SCOPE','LIMITATION','Poucos targets e dependência por fontes de treino compartilhadas limitam inferência populacional. Ausência de significância não prova equivalência; múltiplas análises são exploratórias.',rel(directory(11)/'statistics/holm_adjusted.csv'))

def phase14():
    d=valid();line=read_parquet(GLOBAL/'SOURCE_LINEAGE.parquet');inv=read_parquet(GLOBAL/'file_inventory.parquet');meta=read_parquet(GLOBAL/'manifest_metadata.parquet')
    runtime=[]
    for key,g in d.groupby(['experiment_type','model','representation']):
        runtime.append(dict(zip(['experiment_type','model','representation'],key))|dict(n_runs=len(g),runtime_sum_seconds=g.runtime.sum(min_count=1),runtime_mean=g.runtime.mean(),runtime_median=g.runtime.median(),runtime_max=g.runtime.max(),training_seconds_sum=g.training_seconds.sum(min_count=1),extraction_seconds_sum=g.extraction_seconds.sum(min_count=1),experiment_ids=ids(g.experiment_id)))
    save_table(12,'tables/runtime_summary.csv',pd.DataFrame(runtime))
    storage=inv.groupby('category',as_index=False).agg(n_files=('path','size'),bytes=('bytes','sum'));storage['gib']=storage.bytes/2**30
    save_table(12,'tables/storage_summary.csv',storage,source=rel(GLOBAL/'file_inventory.parquet'))
    ac=d[['experiment_id','seed','target_dataset','training_datasets','representation','model','configuration_id']].merge(line,on='experiment_id').merge(meta.drop(columns=['row_id','experiment_ids','source_file']),on='experiment_id')
    for c in ['manifest_file','metric_file','prediction_file','score_file','threshold_file','feature_importance_file','checkpoint_file']:
        ac['has_'+c]=ac[c].notna()
    save_table(12,'tables/artifact_completeness.csv',ac)
    rng=np.random.default_rng(CFG['seed']);audits=[]
    paths=[directory(6)/'ID/tables/id_results.csv',directory(6)/'LODO/tables/lodo_by_target.csv',directory(8)/'tables/threshold_drift.csv']
    for path in paths:
        f=read_csv(path);col='threshold_drift_mean' if 'threshold_drift' in path.name else 'f1_mean'
        for index in rng.choice(len(f),min(5,len(f)),replace=False):
            row=f.iloc[index];eids=json.loads(row.experiment_ids);vals=[];files=[]
            for eid in eids:
                p=ROOT.parent/line.set_index('experiment_id').loc[eid,'metric_file'];original=read_json(p)
                val=original['thresholds']['threshold_drift'] if col.startswith('threshold') else original['metrics_source']['f1'];vals.append(val);files.append(rel(p))
            rec=float(np.mean(vals));audits.append(dict(reported_value=row[col],final_table=rel(path),final_row_id=row.row_id,column=col,experiment_ids=ids(eids),original_source_files=json.dumps(files),recalculated_value=rec,match=bool(np.isclose(row[col],rec,rtol=1e-12,atol=1e-12))))
    save_table(12,'tables/reproducibility_audit.csv',pd.DataFrame(audits))
    doc(12,['Custo reconstruído por soma dos tempos registrados em `tables/runtime_summary.csv`; não representa tempo de calendário, nem todos os custos de extração do encoder.',
        'Arquivos e espaço constam em `tables/storage_summary.csv`; completude de metadados em `tables/artifact_completeness.csv`.',
        'Valores de tabelas foram escolhidos com seed fixa e recalculados dos JSON originais (`tables/reproducibility_audit.csv`).'],
        'Somente stat dos artefatos grandes; checkpoints não são lidos. Runtime somado apenas para runs utilizáveis, falhas sem duração não imputadas. RSS é pico cumulativo do processo, não memória incremental por fold. Configuração atual tem hash, porém histórico imutável não existe. Auditoria numérica seleciona linhas de tabelas ID/LODO/threshold e reabre os JSON de métricas para média independente.', 'Partial')

def phase15():
    d=valid().set_index('experiment_id');line=read_parquet(GLOBAL/'SOURCE_LINEAGE.parquet').set_index('experiment_id')
    candidates=[];transitions=[]
    def choose(eid,reason):
        candidates.append(dict(experiment_id=eid,selection_criterion=reason,prediction_file=line.loc[eid,'prediction_file'],score_file=line.loc[eid,'score_file']))
    gap=read_parquet(directory(6)/'LODO/derived/gap_pairs.parquet');gap=gap[gap.experiment_type.eq('lodo_C_complete')]
    for reason,index in [('largest_generalization_gap',gap.gap_f1.idxmax()),('median_generalization_gap',(gap.gap_f1-gap.gap_f1.median()).abs().idxmin())]:
        r=gap.loc[index];choose(r.experiment_id_ood,reason);choose(r.experiment_id_id,reason+'_id_reference');transitions.append((r.experiment_id_id,r.experiment_id_ood,'ID_to_OOD'))
    cp=read_parquet(directory(7)/'derived/full_vs_removed.parquet');cp=cp[cp.source_removed_was_effective]
    for reason,index in [('largest_negative_transfer',cp.delta_f1.idxmin()),('largest_positive_transfer',cp.delta_f1.idxmax())]:
        r=cp.loc[index];choose(r.experiment_id_full,reason);choose(r.experiment_id_removed,reason+'_removal');transitions.append((r.experiment_id_full,r.experiment_id_removed,'full_to_removed'))
    th=read_csv(directory(8)/'selected_runs/threshold_cases.csv')
    for r in th.itertuples():choose(r.experiment_id,r.selection_criterion)
    paired=read_csv(directory(10)/'RAW_VS_CANONICALIZED/tables/paired_results.csv')
    if len(paired):
        for reason,index in [('largest_canonicalization_gain',paired.delta_f1.idxmax()),('largest_canonicalization_loss',paired.delta_f1.idxmin())]:
            r=paired.loc[index];choose(r.experiment_id_raw,reason+'_raw');choose(r.experiment_id_can,reason+'_can');transitions.append((r.experiment_id_raw,r.experiment_id_can,'RAW_to_CANONICALIZED'))
    selected=pd.DataFrame(candidates).drop_duplicates(['experiment_id','selection_criterion'])
    keep=list(dict.fromkeys(selected.experiment_id))[:CFG['score_case_limit']];selected=selected[selected.experiment_id.isin(keep)]
    save_table(0,'deep_analysis_candidates.csv',selected)
    predictions={};examples=[];hist=[];cal=[];cmchecks=[]
    for eid in keep:
        p=ROOT.parent/line.loc[eid,'prediction_file'];chunks=[]
        for chunk in pd.read_csv(track(p),usecols=['sample_id','true_label','predicted_label','score','decoded_input_hash'],chunksize=25000):
            if chunk.predicted_label.dtype==object:chunk['predicted_label']=chunk.predicted_label.astype(str).str.lower().map({'true':1,'false':0,'0':0,'1':1})
            chunk['predicted_label']=chunk.predicted_label.astype(int);chunks.append(chunk)
        f=pd.concat(chunks,ignore_index=True);f['sample_index']=np.arange(len(f));predictions[eid]=f
        row=d.loc[eid];fn=int(((f.true_label==1)&(f.predicted_label==0)).sum());fp=int(((f.true_label==0)&(f.predicted_label==1)).sum())
        cmchecks.append(dict(experiment_id=eid,fp_saved=row.fp,fp_recomputed=fp,fn_saved=row.fn,fn_recomputed=fn,match=bool(fp==row.fp and fn==row.fn),source_file=rel(p)))
        for label in [0,1]:
            z=f[f.true_label==label];counts,edges=np.histogram(z.score,bins=np.linspace(0,1,21))
            for a,b,n in zip(edges[:-1],edges[1:],counts):hist.append(dict(experiment_id=eid,target_dataset=row.target_dataset,model=row.model,representation=row.representation,label=label,bin_left=a,bin_right=b,n=int(n),fraction=n/len(z) if len(z) else np.nan,source_file=rel(p)))
        for a,b in zip(np.linspace(0,1,11)[:-1],np.linspace(0,1,11)[1:]):
            z=f[(f.score>=a)&((f.score<b) if b<1 else (f.score<=b))]
            if len(z):cal.append(dict(experiment_id=eid,bin_left=a,bin_right=b,n=len(z),mean_score=z.score.mean(),positive_fraction=z.true_label.mean(),source_file=rel(p)))
        for kind,mask in [('FP',(f.true_label==0)&(f.predicted_label==1)),('FN',(f.true_label==1)&(f.predicted_label==0))]:
            z=f[mask].copy();z['selection_hash']=z.sample_id.map(lambda x:digest(f'{CFG["seed"]}:{eid}:{kind}:{x}'))
            for x in z.sort_values('selection_hash').head(CFG['error_examples_per_kind']).to_dict('records'):
                examples.append(dict(experiment_id=eid,kind=kind,selection_criterion='smallest reproducible SHA256 within '+kind,prediction_file=rel(p),**x))
    transitionrows=[]
    for a,b,kind in transitions:
        if a not in predictions or b not in predictions:continue
        aa=predictions[a];bb=predictions[b];join='decoded_input_hash' if kind=='RAW_to_CANONICALIZED' else 'sample_id'
        aa=aa[~aa[join].duplicated(False)];bb=bb[~bb[join].duplicated(False)]
        paired=aa.merge(bb,on=join,suffixes=('_a','_b'),validate='one_to_one');paired=paired[paired.true_label_a==paired.true_label_b]
        ac=paired.predicted_label_a==paired.true_label_a;bc=paired.predicted_label_b==paired.true_label_b
        transitionrows.append(dict(experiment_id_a=a,experiment_id_b=b,transition=kind,n_matched=len(paired),a_correct_b_incorrect=int((ac&~bc).sum()),a_incorrect_b_correct=int((~ac&bc).sum()),matching_key=join,scope='unique-key common intersection only'))
        for label,mask in [('correct_to_incorrect',ac&~bc),('incorrect_to_correct',~ac&bc)]:
            z=paired[mask].copy();z['selection_hash']=z[join].map(lambda x:digest(f'{CFG["seed"]}:{a}:{b}:{x}'))
            for x in z.sort_values('selection_hash').head(CFG['error_examples_per_kind']).to_dict('records'):
                examples.append(dict(experiment_id=b,reference_experiment_id=a,kind=kind+'_'+label,selection_criterion='smallest reproducible SHA256 within transition',prediction_file=line.loc[b,'prediction_file'],sample_id=x.get('sample_id_b',x.get('sample_id')),sample_index=x['sample_index_b'],true_label=x['true_label_b'],predicted_label=x['predicted_label_b'],score=x['score_b']))
    ex=pd.DataFrame(examples)
    # Recover only selected payloads, one dataset at a time; no all-corpus resident frame.
    from src.data.loader import load_dataset
    payloads={}
    for (target,rep),g in d.loc[keep].groupby(['target_dataset','original_representation']):
        original='decoded' if rep in ['decoded','embedding','early_fusion'] else 'raw'
        relevant=ex[ex.experiment_id.isin(g.index)];wanted=set(relevant.sample_id)
        from src.data.loader import dataset_path
        track(dataset_path(target,original));f=load_dataset(target,original);f=f[f.sample_id.isin(wanted)]
        for row in f.itertuples():payloads[row.sample_id]=(row.row_number,row.text[:1500],len(row.text)>1500,rel(dataset_path(target,original)))
    ex['payload_row_number']=ex.sample_id.map(lambda x:payloads.get(x,(None,None,None,None))[0]);ex['payload_excerpt']=ex.sample_id.map(lambda x:payloads.get(x,(None,None,None,None))[1]);ex['payload_truncated']=ex.sample_id.map(lambda x:payloads.get(x,(None,None,None,None))[2]);ex['payload_file']=ex.sample_id.map(lambda x:payloads.get(x,(None,None,None,None))[3])
    save_table(0,'targeted_error_examples.csv',ex)
    save_table(0,'targeted_error_transitions.csv',pd.DataFrame(transitionrows))
    save_table(8,'derived/selected_score_distributions.csv',pd.DataFrame(hist))
    save_table(8,'derived/selected_reliability_bins.csv',pd.DataFrame(cal))
    save_table(12,'tables/selected_prediction_metric_audit.csv',pd.DataFrame(cmchecks))
    doc(13,['Methodology 4.13 is a disclosure statement and does not generate a corresponding Results section.'],
        'Nenhum resultado experimental é atribuído ao uso de IA. A assistência nesta análise não constitui evidência de desempenho.', 'Not applicable')

def figure(i,name,source,plotter,description):
    source=Path(source);d=read_csv(source);fig=plotter(d)
    for ext in ['png','pdf']:
        p=directory(i)/'figures'/f'{name}.{ext}';p.parent.mkdir(parents=True,exist_ok=True)
        fig.savefig(p,dpi=180,bbox_inches='tight')
        ARTIFACTS[:]=[a for a in ARTIFACTS if a['artifact_path']!=rel(p)]
        ARTIFACTS.append(dict(section=i,artifact_id=digest(rel(p))[:20],artifact_path=rel(p),methodology_section=f'4.{i}',tcc_section=SECTIONS[i][1],research_question=SECTIONS[i][2],analysis_description=description,
            master_table_filter='See source table row filters; no independent numeric computation',source_file_manifest=rel(directory(i)/'SOURCE_FILES.parquet'),source_columns=json.dumps(list(d.columns)),aggregation='plot source table without refitting',script=rel(SCRIPT),command=COMMAND,generated_at=GENERATED,experiment_id_manifest=rel(source),analytical_source=rel(source)))
    plt.close(fig)

def heat_plot(d,index,column,value,title,cmap='viridis',center=False):
    pivot=d.pivot(index=index,columns=column,values=value)
    fig,ax=plt.subplots(figsize=(max(6,len(pivot.columns)*1.05),max(4,len(pivot)*.65)))
    lim=max(abs(np.nanmin(pivot)),abs(np.nanmax(pivot))) if center else None
    im=ax.imshow(pivot.to_numpy(),aspect='auto',cmap=cmap,vmin=-lim if center else None,vmax=lim)
    ax.set_xticks(range(len(pivot.columns)),pivot.columns,rotation=45,ha='right');ax.set_yticks(range(len(pivot)),pivot.index)
    for a in range(len(pivot)):
        for b in range(len(pivot.columns)):
            v=pivot.iloc[a,b]
            if pd.notna(v):
                rgb=im.cmap(im.norm(v))[:3];light=.299*rgb[0]+.587*rgb[1]+.114*rgb[2]
                ax.text(b,a,f'{v:.2f}',ha='center',va='center',fontsize=8,color='black' if light>.58 else 'white')
    ax.set_title(title);fig.colorbar(im,ax=ax);return fig

def phase16():
    enrich_evidence()
    # Additional cross-RQ relationships with a single observation per target.
    d=valid();lodo=d[d.experiment_type.eq('lodo_C_complete')]
    p=read_csv(directory(6)/'PAIRWISE/tables/pairwise_results.csv');p=p[~p.related_source]
    targetpair=p.groupby(['target_dataset','model','representation'],as_index=False).agg(pairwise_f1=('f1_mean','mean'),experiment_ids=('experiment_ids',ids))
    lm=summary(lodo,['target_dataset','model','representation'],['f1'])
    relation=targetpair.merge(lm[['target_dataset','model','representation','f1_mean','experiment_ids']],on=['target_dataset','model','representation'],suffixes=('_pairwise','_lodo'))
    relation['experiment_ids']=[ids([a,b]) for a,b in zip(relation.experiment_ids_pairwise,relation.experiment_ids_lodo)]
    save_table(6,'LODO/tables/pairwise_vs_lodo.csv',relation)
    rho=[]
    for key,g in relation.groupby(['model','representation']):
        rr,pp=exact_spearman(g.pairwise_f1,g.f1_mean)
        rho.append(dict(model=key[0],representation=key[1],n_targets=len(g),rho=rr,p_value=pp,family='pairwise_vs_lodo',experiment_ids=ids(g.experiment_ids)))
    save_table(11,'statistics/pairwise_vs_lodo.csv',holm(pd.DataFrame(rho)))
    # Effective-pool duplicate check, prevents claiming all requested coalitions are independent.
    c=d[d.experiment_type.eq('contribution')]
    dup=[]
    for key,g in c.groupby(['target_dataset','model','representation','seed','effective_development_datasets']):
        if len(g)>1:dup.append(dict(zip(['target_dataset','model','representation','seed','effective_development_datasets'],key))|dict(n_requested_coalitions=len(g),f1_range=g.f1.max()-g.f1.min(),same_split_counts=g.split_counts.nunique()==1,experiment_ids=ids(g.experiment_id)))
    save_table(7,'tables/effective_pool_duplicates.csv',pd.DataFrame(dup))
    # Feature importance means are model-specific; retain source label in manuscript figures.
    for metric in ['f1','mcc','pr_auc']:
        figure(6,'pairwise_'+metric,directory(6)/f'PAIRWISE/tables/matrix_{metric}.csv',lambda f,m=metric:heat_plot(f,'source','target_dataset','value',f'Pairwise {m.upper()} — equal model/representation weights'),f'Pairwise {metric}; related-family pairs excluded; diagonal absent')
    for rep in ['RAW','CANONICALIZED']:
        src=read_csv(directory(6)/'LODO/tables/lodo_by_target.csv');src=src[(src.experiment_type=='lodo_C_complete')&(src.representation==rep)]
        path=f'LODO/tables/figure_lodo_{rep}.csv';save_table(6,path,src)
        figure(6,'lodo_'+rep,directory(6)/path,lambda f,r=rep:heat_plot(f,'target_dataset','model','f1_mean','LODO C F1 — '+r),'LODO C mean F1 over seeds, per target and model')
        gap=read_csv(directory(6)/'LODO/tables/generalization_gap.csv');gap=gap[(gap.experiment_type=='lodo_C_complete')&(gap.representation==rep)]
        path=f'LODO/tables/figure_gap_{rep}.csv';save_table(6,path,gap)
        figure(6,'gap_'+rep,directory(6)/path,lambda f,r=rep:heat_plot(f,'target_dataset','model','gap_f1_mean','ID minus OOD F1 — '+r,'coolwarm',True),'Generalization gap; ID and OOD populations differ')
    figure(7,'source_contribution',directory(7)/'tables/source_target_matrix_f1.csv',lambda f:heat_plot(f,'removed_source','target_dataset','delta_f1_mean_mean','Source contribution to F1 — equal model/representation weights','coolwarm',True),'Full minus removed, seeds first; no-op sources excluded')
    def lengths(f):
        z=f[f.representation=='RAW'];fig,ax=plt.subplots(figsize=(9,4))
        for label,g in z.groupby('class'):ax.plot(g.dataset,g.length_median,marker='o',label='attack' if label else 'benign')
        ax.set_yscale('log');ax.set_ylabel('Median input length (log)');ax.tick_params(axis='x',rotation=35);ax.legend();return fig
    figure(2,'length_by_class',directory(2)/'tables/dataset_textual_characteristics.csv',lengths,'Median RAW input length by dataset and class; not an empirical full distribution')
    def encodings(f):
        fig,axes=plt.subplots(1,2,figsize=(12,4),sharey=True)
        for ax,(rep,g) in zip(axes,f.groupby('representation')):
            for label,z in g.groupby('class'):ax.plot(z.dataset,z.encoding_rate,marker='o',label='attack' if label else 'benign')
            ax.set_title(rep);ax.tick_params(axis='x',rotation=60);ax.set_ylabel('Encoded-pattern presence in original columns');ax.legend()
        fig.tight_layout();return fig
    figure(2,'encoding_by_class',directory(2)/'tables/dataset_textual_characteristics.csv',encodings,'Presence of percent encodings in original URL/body columns, stratified by class')
    def overlap_plot(f):
        fig,axes=plt.subplots(1,2,figsize=(13,5))
        for ax,(rep,g) in zip(axes,f.groupby('representation')):
            names=sorted(set(g.a)|set(g.b));matrix=pd.DataFrame(np.nan,index=names,columns=names)
            for r in g.itertuples():matrix.loc[r.a,r.b]=r.exact_overlap;matrix.loc[r.b,r.a]=r.exact_overlap
            im=ax.imshow(np.log1p(matrix),cmap='magma');ax.set_xticks(range(len(names)),names,rotation=65,ha='right');ax.set_yticks(range(len(names)),names);ax.set_title(rep+' shared exact inputs (log1p)');fig.colorbar(im,ax=ax)
        fig.tight_layout();return fig
    figure(3,'cross_dataset_overlap',directory(3)/'tables/cross_dataset_overlap.csv',overlap_plot,'Exact normalized-input shared hash counts; separate raw and decoded source files; artificial variant shown but not a primary independent dataset')
    def scores(f):
        choices=f.experiment_id.drop_duplicates().head(4);fig,axes=plt.subplots(2,2,figsize=(11,7))
        for ax,eid in zip(axes.flat,choices):
            z=f[f.experiment_id==eid]
            for label,g in z.groupby('label'):ax.plot((g.bin_left+g.bin_right)/2,g.fraction,label='attack' if label else 'benign')
            ax.set_title(eid.replace('EXP_','')[:53],fontsize=8);ax.set_xlabel('Score');ax.set_ylabel('Class-conditional fraction');ax.legend()
        fig.tight_layout();return fig
    figure(8,'selected_score_distributions',directory(8)/'derived/selected_score_distributions.csv',scores,'First four prespecified selected runs; target class-conditional scores; selection-biased examples, not inference')
    def stable(f):
        fig,axes=plt.subplots(1,2,figsize=(12,5))
        for ax,(rep,g) in zip(axes,f.groupby('representation')):
            z=g.sort_values(['top_k_frequency','importance_mean'],ascending=False).head(10).iloc[::-1];ax.barh(z.feature,z.importance_mean);ax.set_title(rep);ax.set_xlabel('CatBoost mean importance')
        fig.tight_layout();return fig
    figure(9,'stable_features',directory(9)/'tables/stable_features.csv',stable,'Features ranked by top-10 frequency then mean CatBoost importance; no embedding dimensions')
    # Add numerical statements with row-level provenance rather than manually transcribed numbers.
    counts=read_csv(directory(1)/'tables/run_counts.csv').set_index('category')
    DOCS['1']['findings'].append(f"Foram contabilizados {int(counts.loc['total_encontrado','n'])} IDs, {int(counts.loc['total_utilizavel','n'])} runs utilizáveis e {int(counts.loc['contribution_utilizavel','n'])} de contribuição; {int(counts.loc['total_excluido','n'])} IDs excluídos com motivo. Fonte: `tables/run_counts.csv`, coluna n e chave category.")
    table=read_csv(directory(6)/'LODO/tables/lodo_by_target.csv');table=table[table.experiment_type.eq('lodo_C_complete')]
    gap=read_csv(directory(6)/'LODO/tables/generalization_gap.csv');gap=gap[gap.experiment_type.eq('lodo_C_complete')]
    for rep,g in table.groupby('representation'):
        worst=g.loc[g.f1_mean.idxmin()];best=g.loc[g.f1_mean.idxmax()];gr=gap[gap.representation==rep];gw=gr.loc[gr.gap_f1_mean.idxmax()]
        DOCS['6']['findings'].append(f"{rep}: menor F1 médio por condição = {worst.f1_mean:.6f} ({worst.target_dataset}/{worst.model}); maior = {best.f1_mean:.6f} ({best.target_dataset}/{best.model}). Fonte: `LODO/tables/lodo_by_target.csv`, row_id {worst.row_id} e {best.row_id}. Maior gap ID−OOD = {gw.gap_f1_mean:.6f} ({gw.target_dataset}/{gw.model}); `LODO/tables/generalization_gap.csv`, row_id {gw.row_id}.")
    macro=read_csv(directory(6)/'LODO/tables/lodo_macro_summary.csv');macro=macro[macro.experiment_type=='lodo_C_complete']
    for rep,g in macro.groupby('representation'):
        best=g.loc[g.f1_mean_mean.idxmax()]
        DOCS['6']['findings'].append(f"{rep}: {best.model} teve maior média não ponderada de F1 entre targets ({best.f1_mean_mean:.6f}); trata-se de ranking descritivo, não superioridade universal. `LODO/tables/lodo_macro_summary.csv`, row_id {best.row_id}.")
    neg=read_csv(directory(7)/'tables/negative_transfer.csv');pos=read_csv(directory(7)/'tables/positive_transfer.csv');neutral=read_csv(directory(7)/'tables/neutral_transfer.csv')
    if len(neg):
        n=neg.iloc[0];DOCS['7']['findings'].append(f"Há {len(neg)} condições com contribuição F1 negativa, {len(pos)} positiva e {len(neutral)} neutra após média das seeds (`tables/negative_transfer.csv`, `positive_transfer.csv`, `neutral_transfer.csv`; contagem de linhas). Portanto mais fontes não ajudaram sempre. Maior caso negativo: {n.removed_source}→{n.target_dataset}, {n.model}/{n.representation}: F1 full={n.metric_before:.6f}, sem fonte={n.metric_after:.6f}, contribuição={n.delta:.6f}; row_id {n.row_id} de `negative_transfer.csv`.")
    threshold=read_csv(directory(8)/'tables/threshold_results.csv');threshold=threshold[threshold.experiment_type=='lodo_C_complete'];t=threshold.loc[threshold.oracle_gap.idxmax()]
    DOCS['8']['findings'].append(f"Maior oracle gap LODO C = {t.oracle_gap:.6f}, em {t.target_dataset}/{t.model}/{t.representation}, seed {t.seed}. F1 com threshold de origem={t.f1:.6f}; F1 oracle diagnóstico={t.f1_oracle:.6f}; AP={t.pr_auc:.6f}. `tables/threshold_results.csv`, row_id {t.row_id}. Isso mostra margem diagnóstica de decisão para o ranking existente; não demonstra que retuning no target seria permitido.")
    stable=read_csv(directory(9)/'tables/stable_features.csv')
    for rep,g in stable.groupby('representation'):
        top=g.sort_values(['top_k_frequency','importance_mean'],ascending=False).iloc[0]
        DOCS['9']['findings'].append(f"{rep}: {top.feature} lidera por frequência Top-10 ({top.top_k_frequency:.6f}), importância média {top.importance_mean:.6f}; `tables/stable_features.csv`, row_id {top.row_id}. É estabilidade observada do ranking CatBoost, não invariância causal.")
    pairs=read_csv(directory(10)/'RAW_VS_CANONICALIZED/tables/paired_results.csv');audit=read_csv(directory(10)/'RAW_VS_CANONICALIZED/tables/pairing_audit.csv')
    DOCS['10']['findings'].append(f"Dos {len(audit)} candidatos pareados por configuração, {len(pairs)} satisfizeram igualdade de amostras por split. Protocolos elegíveis: {', '.join(sorted(pairs.experiment_type.unique()))}; targets: {', '.join(sorted(pairs.target_dataset.unique()))}. Fonte: `RAW_VS_CANONICALIZED/tables/pairing_audit.csv` e `paired_results.csv`. Não há estimativa pareada LODO do efeito isolado da canonicalização.")
    adjusted=read_csv(directory(11)/'statistics/holm_adjusted.csv');ok=adjusted.p_holm.notna();sig=adjusted[ok & (adjusted.p_holm<.05)]
    DOCS['11']['findings'].append(f"Entre {int(ok.sum())} testes com p ajustado disponível, {len(sig)} têm p_Holm<0.05, nas famílias pré-especificadas no arquivo. `statistics/holm_adjusted.csv`, filtro p_holm.notna(); isso não converte ausência de detecção nos demais testes em prova de equivalência.")
    repaudit=read_csv(directory(12)/'tables/reproducibility_audit.csv')
    DOCS['12']['findings'].append(f"Foram reconstruídos {len(repaudit)} valores finais diretamente dos JSON originais; {int(repaudit.match.sum())} conferiram à tolerância 1e-12. Fonte: `tables/reproducibility_audit.csv`, coluna match.")
    numerical_interpretations()
    write_documents()

def enrich_evidence():
    """Integrity and summaries supporting final claims, without rereading bulk artifacts."""
    d=valid();rows=[]
    for r in d.itertuples():
        tp,tn,fp,fn=r.tp,r.tn,r.fp,r.fn
        denominator=2*tp+fp+fn
        f1=2*tp/denominator if denominator else 0.
        recall=tp/(tp+fn) if tp+fn else np.nan;fpr=fp/(tn+fp) if tn+fp else np.nan
        rows.append(dict(experiment_id=r.experiment_id,confusion_n=tp+tn+fp+fn,saved_n=r.test_n,
            f1_saved=r.f1,f1_from_confusion=f1,recall_from_confusion=recall,fpr_from_confusion=fpr,
            nonnegative_counts=min(tp,tn,fp,fn)>=0,match=bool(np.isclose(r.f1,f1,equal_nan=True) and np.isclose(r.recall,recall,equal_nan=True) and np.isclose(r.fpr,fpr,equal_nan=True) and tp+tn+fp+fn==r.test_n)))
    save_table(1,'tables/metric_consistency.csv',pd.DataFrame(rows))
    req=[]
    for m in METRICS:
        s=pd.to_numeric(d[m],errors='coerce');req.append(dict(metric=m,n_null=int(s.isna().sum()),n_inf=int(np.isinf(s).sum()),min=s.min(),max=s.max(),experiment_ids=ids(d.experiment_id)))
    save_table(1,'tables/metric_missingness.csv',pd.DataFrame(req))
    inv=read_parquet(GLOBAL/'file_inventory.parquet')
    save_table(1,'tables/empty_files.csv',inv[inv['empty']],source=rel(GLOBAL/'file_inventory.parquet'))
    counts=read_csv(directory(2)/'tables/dataset_characterization.csv')
    cls=read_csv(directory(2)/'tables/dataset_textual_characteristics.csv')
    # Exact quantiles from saved distributions, never synthesize individual inputs.
    save_table(2,'tables/selected_class_controlled_lexical_differences.csv',cls[['dataset','representation','class','n','length_median','length_p10','length_p90','entropy_mean','encoding_rate','sql_select_presence','sql_union_presence','inline_comment_rate','non_ascii_rate','experiment_ids','source_file']])
    cp=read_csv(directory(7)/'tables/source_summary.csv')
    save_table(7,'tables/source_overall_summary.csv',summary(cp,['source','representation'],['mean_contribution','median_contribution','targets_helped','targets_harmed']),aggregation='first seeds within condition, then equal targets in each model, then equal model weighting; not independence of all coalitions')
    ranks=read_parquet(directory(9)/'derived/rank_pairs.parquet');rankseed=summary(ranks,['comparison','target_dataset','other_target','removed_source','representation'],['spearman','kendall','jaccard_topk','instability'])
    save_table(9,'tables/stability_overview.csv',summary(rankseed,['comparison','representation'],['spearman_mean','kendall_mean','jaccard_topk_mean']),aggregation='seeds within target-pair/source-removal condition first; descriptive average over these conditions')
    ab=d[d.experiment_type.eq('ablation')];base=ab[ab.feature_set=='lex64'];abl=[]
    for r in ab[ab.feature_set!='lex64'].itertuples():
        g=base[(base.target_dataset==r.target_dataset)&(base.model==r.model)&(base.representation==r.representation)&(base.seed==r.seed)]
        if len(g)==1:
            b=g.iloc[0];abl.append(dict(target_dataset=r.target_dataset,model=r.model,representation=r.representation,feature_set=r.feature_set,seed=r.seed,delta_f1=r.f1-b.f1,delta_mcc=r.mcc-b.mcc,experiment_id_ablation=r.experiment_id,experiment_id_lex64=b.experiment_id))
    aa=save_table(9,'derived/ablation_pairs.parquet',pd.DataFrame(abl))
    save_table(9,'tables/ablation_effects_by_target.csv',summary(aa,['target_dataset','model','representation','feature_set'],['delta_f1','delta_mcc']))
    missing=read_csv(directory(10)/'RAW_VS_CANONICALIZED/tables/pairing_audit.csv')
    needed=missing[missing.experiment_type.eq('lodo_C_complete')&(missing.model=='catboost')]
    save_table(9,'tables/raw_vs_canonicalized_stability_eligibility.csv',needed.assign(status='not estimated where population/split differs'))
    dense=read_parquet(directory(6)/'LODO/derived/dense_vs_lexical.parquet')
    save_table(6,'LODO/tables/dense_vs_lexical_by_target.csv',summary(dense,['target_dataset','model','representation','split_counts_equal'],['delta_f1','delta_pr_auc']))
    selected=read_csv(GLOBAL/'deep_analysis_candidates.csv');lineage=read_parquet(GLOBAL/'SOURCE_LINEAGE.parquet').set_index('experiment_id');splitchecks=[]
    for eid in selected.experiment_id.unique():
        sp=lineage.loc[eid,'split_file'];sets=collections.defaultdict(set);ns=collections.Counter()
        for chunk in pd.read_csv(track(ROOT.parent/sp),usecols=['canonical_hash','split','dataset'],chunksize=25000):
            for label,g in chunk.groupby('split'):sets[label].update(g.canonical_hash);ns[label]+=len(g)
        tv=len(sets['train']&sets['validation']);tt=len(sets['train']&sets['test']);vt=len(sets['validation']&sets['test'])
        splitchecks.append(dict(experiment_id=eid,n_train=ns['train'],n_validation=ns['validation'],n_test=ns['test'],train_validation_overlap=tv,train_test_overlap=tt,validation_test_overlap=vt,match=tv==tt==vt==0,source_file=sp))
    save_table(3,'tables/selected_split_hash_audit.csv',pd.DataFrame(splitchecks),aggregation='exact set intersections of canonical hashes; targeted selection, not exhaustive all-run row audit')

def numerical_interpretations():
    dat=read_csv(directory(2)/'tables/dataset_characterization.csv');prim=dat[dat.primary]
    DOCS['2']['findings'].append(f"As {len(prim)} versões das fontes primárias têm prevalência positiva {prim.positive_prevalence.min():.6f} a {prim.positive_prevalence.max():.6f} (`tables/dataset_characterization.csv`, filtro primary=True). Isso controla a prevalência global entre arquivos, mas não torna os conteúdos equivalentes nem garante balanço após remoções no desenvolvimento.")
    dup=read_csv(directory(3)/'tables/label_conflicts.csv')
    for r in dup[(dup.normalization=='canonical_key')].itertuples():
        DOCS['3']['findings'].append(f"{r.dataset}/{r.representation} tem {r.label_conflict_keys} chaves canônicas com rótulos conflitantes (`tables/label_conflicts.csv`, row_id {r.row_id}). O teste preserva essas entradas; esse ruído limita o desempenho interpretável.")
    sep=read_csv(directory(10)/'DATASET_SEPARABILITY/tables/separability_all.csv')
    for r in sep.itertuples():DOCS['10']['findings'].append(f"Separabilidade exploratória {r.representation}: Macro-F1={r.macro_f1:.6f}, n={r.n}, seed={r.seed}; `DATASET_SEPARABILITY/tables/separability_all.csv`, row_id {r.row_id}. Sem controles suficientes, isso não prova redução controlada de separabilidade.")
    stability=read_csv(directory(9)/'tables/stability_overview.csv')
    for r in stability.itertuples():DOCS['9']['findings'].append(f"{r.comparison}/{r.representation}: média descritiva de Spearman={r.spearman_mean_mean:.6f}, Jaccard Top-10={r.jaccard_topk_mean_mean:.6f}; `tables/stability_overview.csv`, row_id {r.row_id}. A média de condições não é tratada como n de targets independentes.")
    sr=read_csv(directory(7)/'tables/source_overall_summary.csv')
    for rep,g in sr.groupby('representation'):
        best=g.loc[g.mean_contribution_mean.idxmax()];worst=g.loc[g.mean_contribution_mean.idxmin()]
        DOCS['7']['findings'].append(f"{rep}: maior contribuição média descritiva entre modelos/targets é {best.source} ({best.mean_contribution_mean:.6f}); menor é {worst.source} ({worst.mean_contribution_mean:.6f}). `tables/source_overall_summary.csv`, row_id {best.row_id} e {worst.row_id}. Os contadores targets_helped/harmed em `source_summary.csv` mostram exceções; média positiva não implica ajuda consistente.")
    relation=read_csv(directory(11)/'statistics/pairwise_vs_lodo.csv')
    sig=relation.p_holm.lt(.05).sum()
    DOCS['6']['findings'].append(f"A associação pairwise médio→LODO não foi detectada após Holm em {len(relation)-sig} de {len(relation)} estratos modelo/representação; ver M04.11/statistics/pairwise_vs_lodo.csv, filtro p_holm≥0.05. Isso não prova ausência de associação; há poucos targets.")
    tests=read_csv(directory(11)/'statistics/holm_adjusted.csv');fr=tests[tests.test=='friedman']
    DOCS['11']['findings'].append(f"Nenhum ranking de modelos é confirmado pelos testes Friedman corrigidos quando p_Holm≥0.05; {int(fr.p_holm.ge(.05).sum())} de {len(fr)} omnibus nessa situação (`statistics/holm_adjusted.csv`, filtro test=friedman). Post-hoc só seria realizado após omnibus ajustado significativo.")
    relationships=read_csv(directory(11)/'statistics/cross_rq_relationships.csv')
    for name,g in relationships.groupby('relationship'):
        hits=g[g.p_holm<.05]
        DOCS['11']['findings'].append(f"Relação {name}: {len(hits)} de {len(g)} estratos com p_Holm<0.05; tabela `statistics/cross_rq_relationships.csv`, filtro relationship={name}. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.")
    selected=relationships[relationships.relationship.str.startswith('feature_instability')]
    if not selected.p_holm.lt(.05).any():DOCS['9']['findings'].append('Não foi detectada associação ajustada entre instabilidade e OOD F1, gap ou negative transfer nos estratos avaliados. Fonte: M04.11/statistics/cross_rq_relationships.csv, filtro relationship.startswith(feature_instability); p_Holm≥0.05. Não significa que as relações sejam inexistentes.')
    ab=read_csv(directory(9)/'tables/ablation_effects_by_target.csv')
    for rep,g in ab.groupby('representation'):
        worst=g.loc[g.delta_f1_mean.idxmin()];best=g.loc[g.delta_f1_mean.idxmax()]
        DOCS['9']['findings'].append(f"Ablações {rep}: maior melhora observada vs lex64 = {best.delta_f1_mean:.6f} ({best.target_dataset}/{best.model}/{best.feature_set}); maior queda = {worst.delta_f1_mean:.6f} ({worst.target_dataset}/{worst.model}/{worst.feature_set}). `tables/ablation_effects_by_target.csv`, row_id {best.row_id} e {worst.row_id}. São extremos descritivos pós-teste, não seleção de features validada para deployment.")

def section_sources(i):
    arts=[a for a in ARTIFACTS if a['section']==i];used=set();aux=set()
    for a in arts:
        path=ROOT.parent/a['artifact_path']
        if path.suffix not in ['.csv','.parquet']:continue
        table=pd.read_parquet(path) if path.suffix=='.parquet' else pd.read_csv(path)
        if 'experiment_ids' in table:
            for s in table.experiment_ids.dropna():used.update(json.loads(s))
        if 'source_file' in table:aux.update(table.source_file.dropna().astype(str))
    if i in [1,12]:used.update(master().experiment_id)
    line=read_parquet(GLOBAL/'SOURCE_LINEAGE.parquet');selected=line[line.experiment_id.isin(used)].copy()
    selected=selected.rename(columns={'metric_file':'source_metric_file','prediction_file':'source_prediction_file','score_file':'source_score_file','threshold_file':'source_threshold_file','feature_importance_file':'source_feature_file','manifest_file':'source_manifest'})
    folder=GLOBAL if i==0 else directory(i);folder.mkdir(parents=True,exist_ok=True);selected.to_parquet(folder/'SOURCE_FILES.parquet',index=False)
    pd.DataFrame({'source_file':sorted(aux)}).to_csv(folder/'AUXILIARY_SOURCES.csv',index=False)
    pd.DataFrame(arts).to_csv(folder/'TRACEABILITY.csv',index=False)
    return arts,selected,aux

def trace_text(i,arts,sources,aux):
    folder=GLOBAL if i==0 else directory(i)
    inputs=set()
    for c in sources.columns:
        if c!='experiment_id':inputs.update(sources[c].dropna().astype(str))
    inputs.update(aux)
    read_paths={x['path'] for x in READS.values()}
    actual=len(inputs&read_paths)
    return f"""## Data Sources and Traceability

Original source-file mapping: `{rel(folder/'SOURCE_FILES.parquet')}`. This mapping contains {len(sources)} experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `{rel(folder/'AUXILIARY_SOURCES.csv')}`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{{raw,decoded}}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: {actual}. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `{rel(GLOBAL/'master_results.parquet')}`. Lineage: `{rel(GLOBAL/'SOURCE_LINEAGE.parquet')}`. Registry: `{rel(GLOBAL/'run_registry.parquet')}`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `{rel(SCRIPT)}`. Configuration: `{rel(SCRIPT.parent/'config.json')}`.

Command (from project root):
```bash
{COMMAND}
```

Derived files, tables and figures: `{rel(folder/'TRACEABILITY.csv')}` lists all {len(arts)} registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
"""

def metric_provenance(arts):
    lines=['## Metric Provenance','','| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |','|---|---|---|---|---|---|']
    for a in arts:
        if not a['artifact_path'].endswith(('.csv','.parquet')):continue
        desc=a['analysis_description'].replace('|','/')
        lines.append(f"| {desc} | `{a['artifact_path']}` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | {a['aggregation']} | `{rel(SCRIPT)}` |")
    return '\n'.join(lines)+'\n'

def write_documents():
    for i in range(1,14):
        folder=directory(i);folder.mkdir(parents=True,exist_ok=True)
        data=DOCS.get(str(i),{'findings':['No result available.'],'method':'Not applicable.','status':'Partial'})
        if i==13:
            text='# Use of Generative Artificial Intelligence\n\nMethodology 4.13 is a disclosure statement and does not generate a corresponding Results section.\n\n## Data Sources and Traceability\n\nNo experimental input files, experiment IDs, metrics, seed aggregations, derived formulas, tables or figures. Script: `'+rel(SCRIPT)+'`. Command: `'+COMMAND+'`. Only this disclosure README is generated.\n'
            (folder/'README.md').write_text(text);continue
        arts,sources,aux=section_sources(i);trace=trace_text(i,arts,sources,aux);prov=metric_provenance(arts)
        tables=[a['artifact_path'] for a in arts if a['artifact_path'].endswith('.csv') and '/tables/' in a['artifact_path']]
        figures=[a['artifact_path'] for a in arts if a['artifact_path'].endswith('.pdf')]
        readme=f"# {SECTIONS[i][3]}\n\nMethodology section: 4.{i}\n\nTCC Results section: {SECTIONS[i][1]}\n\nResearch Question: {SECTIONS[i][2]}\n\nPurpose: {SECTIONS[i][3]}\n\nAnalysis coverage: {data['status']} (detalhes de escopo em RESULTS e analysis_scope_notes).\n\nMain generated artifacts:\n\n"+'\n'.join(f'- `{v}`' for v in (tables[:5]+figures[:2]))+'\n\n'+trace
        (folder/'README.md').write_text(readme)
        method=f"# Analysis Method — 4.{i} / {SECTIONS[i][1]}\n\n{data['method']}\n\nO que/por quê: {SECTIONS[i][3]}, para {SECTIONS[i][2]}. Foram usados os arquivos e IDs mapeados em SOURCE_FILES.parquet; pilotos/falhas/não aplicáveis em M04.01/tables/excluded_runs.csv. Não se imputam métricas ausentes. Os dados não foram usados para escolher novamente modelos ou thresholds. Artefatos por linha permitem recuperar os filtros exatos e seeds.\n\n"+prov+'\n'+trace
        (folder/'ANALYSIS_METHOD.md').write_text(method)
        result=f"# Results — {SECTIONS[i][1]} / {SECTIONS[i][2]}\n\n"+'\n\n'.join(data['findings'])
        result+='\n\n## Interpretation and scope\n\n'+data['method']+'\n\nAs observações se limitam às fontes avaliadas. Não demonstram causalidade nem transferência universal. Casos selecionados apoiam interpretação e não estimam prevalência de erros. Detalhes de escopo e cobertura estão em `_global/analysis_scope_notes.md`.\n'
        if i==11:
            result+='\n## Negative and Null Findings\n\nOs testes com p_Holm≥0.05 estão preservados em `statistics/holm_adjusted.csv`; devem ser descritos como ausência de diferença detectável, nunca equivalência. Pares insuficientes/constantes constam de `wilcoxon_results.csv` e `cross_rq_relationships.csv`. Ausência de pareamento LODO impede estimar seu efeito isolado de canonicalização. Separabilidade controlada por classe não foi executada; isso é falta de evidência, não efeito nulo. Negative transfer observado está em M04.07/tables/negative_transfer.csv.\n'
        else:result+='\n## Positive, Negative and Null Results\n\nTodas as condições das tabelas são preservadas, incluindo baixo desempenho e efeitos negativos/zero. Não significância e indisponibilidade são distintas; resultados inexistentes estão marcados, não substituídos por zeros. Consulte as tabelas completas e a síntese estatística antes de afirmar superioridade.\n'
        result+='\n'+prov+'\n'+trace
        (folder/'RESULTS.md').write_text(result)

def global_trace():
    return f"""## Data Sources and Traceability

Original inputs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`, `artigo/docs/experiment_registry/experiments.csv`, original dataset metadata/configuration, and selected predictions/features/splits only. Full paths and IDs: `_global/SOURCE_LINEAGE.parquet` and `_global/SOURCE_FILES.parquet`. Actual unique files read and byte counts: `_global/FILES_READ.parquet`, `_global/file_read_summary.csv`. No checkpoint content read.

Master table: `_global/master_results.parquet`; registry: `_global/run_registry.parquet`. Columns, exact row filters, groupings, artifacts/tables/figures and formulas are documented per section in TRACEABILITY.csv, ANALYSIS_METHOD.md and Metric Provenance. Seeds are averaged within condition; targets are the statistical units. Each reported value is linked to a table row_id with experiment_ids. Missing conditions are not imputed. Complete generated artifact catalog: `_global/ARTIFACT_CATALOG.csv`.

Script: `{rel(SCRIPT)}`. Config: `{rel(SCRIPT.parent/'config.json')}`. Command: `{COMMAND}`. Derived outputs are all within `artigo/analise_resultados_tcc/`. Follow each section's SOURCE_FILES.parquet for original metrics, predictions, scores, thresholds, features and manifests. Use trace_value.py for a specific cell.
"""

def phase17():
    lines=['# Analysis Index','']
    for i in range(1,14):
        data=DOCS[str(i)];lines += [f'## Methodology 4.{i} -> Results {SECTIONS[i][1] or "NO EXPERIMENTAL RESULTS"}','',f'Folder: `{SECTIONS[i][0]}`','',f'Status: {data["status"]}','']
        if i!=13:
            arts=[a for a in ARTIFACTS if a['section']==i]
            lines+=['Main tables:','']+[f'- `{a["artifact_path"]}`' for a in arts if '/tables/' in a['artifact_path']][:6]
            lines+=['','Main figures:','']+[f'- `{a["artifact_path"]}`' for a in arts if a['artifact_path'].endswith('.pdf')]
            lines+=['',f'Method: `{SECTIONS[i][0]}/ANALYSIS_METHOD.md`','',f'Results: `{SECTIONS[i][0]}/RESULTS.md`','']
        lines+=['---','']
    lines +=[global_trace()];(GLOBAL/'ANALYSIS_INDEX.md').write_text('\n'.join(lines))
    counts=read_csv(directory(1)/'tables/run_counts.csv')
    text='# Experiment Inventory\n\n'+counts[['category','n']].to_string(index=False)+'\n\nSource: M04.01/tables/run_counts.csv; counts are registry/status reconciled, not number of files indiscriminately. Registry duplicate IDs: `_global/duplicate_registry_ids.csv`. Missing planned combinations: M04.01/tables/missing_runs.csv. Exclusion reasons: M04.01/tables/excluded_runs.csv.\n\n'+global_trace()
    (GLOBAL/'experiment_inventory.md').write_text(text)
    issues='# Unresolved Issues\n\nThese flags restrict scientific interpretation; no original results were edited.\n\n'+'\n\n'.join(f"### {r['code']} — {r['severity']}\n\n{r['message']}\n\nEvidence: `{r['evidence']}`" for r in ISSUES)+'\n\n'+global_trace()
    (GLOBAL/'analysis_scope_notes.md').write_text(issues)

def phase18():
    sections=[('5.1 Experimental Coverage and Integrity',[1,3]),('5.2 Dataset, Representation, and Model Characterization',[2,4,5]),
        ('5.3 Cross-Dataset Generalization — RQ1',[6]),('5.4 Source-Dataset Contribution — RQ2',[7]),('5.5 Decision Behavior — RQ3',[8]),
        ('5.6 Feature Stability — RQ3',[9]),('5.7 Canonicalization and Dataset Separability — RQ4',[10]),('5.8 Statistical Synthesis',[11]),('5.9 Reproducibility',[12])]
    lines=['# Chapter 5 — Results and Analysis','',
        'Este guia apresenta achados rastreáveis. “Complete” significa análise possível concluída; “Partial” sinaliza limitações de evidência que impedem parte das perguntas. Não preencher essas lacunas com resultados inventados.','']
    for title,indices in sections:
        lines +=['## '+title,'','Main findings:','']
        for i in indices:
            lines +=[f'Fonte analítica: `{SECTIONS[i][0]}/RESULTS.md`.','']
            for finding in DOCS[str(i)]['findings']:lines +=[finding.replace('`tables/',f'`{SECTIONS[i][0]}/tables/').replace('`LODO/',f'`{SECTIONS[i][0]}/LODO/').replace('`statistics/',f'`{SECTIONS[i][0]}/statistics/'),'']
        arts=[a for a in ARTIFACTS if a['section'] in indices]
        lines+=['Tables to include:','']+[f'- `{a["artifact_path"]}`' for a in arts if '/tables/' in a['artifact_path']][:5]
        lines+=['','Figures to include:','']+[f'- `{a["artifact_path"]}`' for a in arts if a['artifact_path'].endswith('.pdf')][:4]
        lines+=['','Source analysis folders:','']+[f'- `{SECTIONS[i][0]}`' for i in indices]
        lines+=['','Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.','',
            'Important limitations:','']+[DOCS[str(i)]['method'] for i in indices]
        if 6 in indices:lines+=['','Direct RQ answer: há transferência com magnitude heterogênea e perdas frente ao ID; os piores targets/condições e ranking descritivo estão nas tabelas citadas. Relação pairwise→LODO em LODO/tables/pairwise_vs_lodo.csv e M04.11/statistics/pairwise_vs_lodo.csv. Não alegar generalização universal.']
        if 7 in indices:lines+=['','Direct RQ answer: mais fontes nem sempre ajudam; negative transfer é observado nas condições citadas. O sinal depende do target/modelo e mudanças na validação; não é causalidade isolada de uma fonte.']
        if 8 in indices:lines+=['','Direct RQ answer: oracle gap positivo quantifica margem de decisão, mas não prova que toda queda OOD decorra do threshold. Não escolher t_oracle para deployment ou avaliação principal.']
        if 9 in indices:lines+=['','Direct RQ answer: estabilidade é propriedade observada dos rankings CatBoost; features associadas a uma origem são possíveis dependências do dataset. Não chamar features de invariantes causais.']
        if 10 in indices:lines+=['','Direct RQ answer: efeito isolado de canonicalização em OOD não identificável no protocolo salvo. Separabilidade disponível é exploratória e não sustenta a hipótese controlada RAW vs CANONICALIZED. Não generalizar os pares ID/ECML para LODO.']
        lines+=['','Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.','',
            'Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.','', '---','']
    lines +=[global_trace()];(OUT/'FINAL_TCC_RESULTS_GUIDE.md').write_text('\n'.join(lines))

def phase19():
    section_sources(0)
    catalog=pd.DataFrame(ARTIFACTS).drop_duplicates('artifact_path',keep='last');catalog.to_csv(GLOBAL/'ARTIFACT_CATALOG.csv',index=False)
    # Record auxiliary code/config hashes without modifying originals.
    hashes=[]
    for path in [SCRIPT,SCRIPT.parent/'config.json',*ROOT.glob('config/*.yaml'),*ROOT.glob('src/**/*.py')]:
        hashes.append(dict(path=rel(path),sha256=hashlib.sha256(track(path).read_bytes()).hexdigest()))
    pd.DataFrame(hashes).to_csv(GLOBAL/'analysis_code_hashes.csv',index=False)
    reads=pd.DataFrame(READS.values());reads.to_parquet(GLOBAL/'FILES_READ.parquet',index=False)
    reads['extension']=reads.path.map(lambda x:Path(x).suffix)
    reads.groupby('extension',as_index=False).agg(n_files=('path','size'),bytes=('bytes','sum')).to_csv(GLOBAL/'file_read_summary.csv',index=False)
    errors=[];allids=set(read_parquet(GLOBAL/'run_registry.parquet').experiment_id);tables=0;rows=0
    for a in ARTIFACTS:
        path=ROOT.parent/a['artifact_path']
        if not path.exists():errors.append('Missing artifact '+str(path));continue
        if path.suffix not in ['.csv','.parquet']:continue
        f=pd.read_parquet(path) if path.suffix=='.parquet' else pd.read_csv(path);tables+=1;rows+=len(f)
        if not {'row_id','experiment_ids','source_file'}<=set(f):errors.append('Missing row provenance '+str(path));continue
        if f.row_id.duplicated().any():errors.append('Duplicate row_id '+str(path))
        for s in f.experiment_ids.dropna().unique():
            try:unknown=set(json.loads(s))-allids
            except Exception:errors.append('Invalid experiment_ids '+str(path));continue
            if unknown:errors.append('Unknown experiments '+str(sorted(unknown)))
    for path in OUT.rglob('*.md'):
        content=path.read_text()
        if '## Data Sources and Traceability' not in content:errors.append('Missing traceability section '+str(path))
        if path.name in ['ANALYSIS_METHOD.md','RESULTS.md'] and '## Metric Provenance' not in content:errors.append('Missing metric provenance '+str(path))
    rep=read_csv(directory(12)/'tables/reproducibility_audit.csv');pred=read_csv(directory(12)/'tables/selected_prediction_metric_audit.csv')
    if not rep.match.all():errors.append('Numerical reconstruction mismatch')
    if not pred.match.all():errors.append('Prediction/metrics mismatch')
    consistency=read_csv(directory(1)/'tables/metric_consistency.csv')
    if not consistency.match.all() or not consistency.nonnegative_counts.all():errors.append('All-run confusion metrics inconsistency')
    splitchecks=read_csv(directory(3)/'tables/selected_split_hash_audit.csv')
    if not splitchecks.match.all():errors.append('Selected split leakage detected')
    if any(p.endswith('.joblib') for p in READS):errors.append('Checkpoint opened')
    missing=read_csv(directory(1)/'tables/missing_runs.csv')
    if len(missing):errors.append('Expected runs missing')
    d=master()
    if (d.usable & d.experiment_type.eq('contribution')).sum()!=13170:errors.append('Contribution count differs from expected 13170')
    result={'status':'PASS' if not errors else 'FAIL','scientific_scope':'Complete analysis of available evidence; partial answers where paired or controlled evidence absent',
        'checked_tables':tables,'checked_table_rows':rows,'numeric_reconstruction_checks':len(rep),'prediction_checks':len(pred),'n_unique_files_read':len(READS),
        'checkpoints_opened':0,'new_trainings':0,'errors':errors,'generated_at':GENERATED,
        'analysis_elapsed_seconds':time.perf_counter()-ANALYSIS_STARTED,'analysis_peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'analysis_software_versions':{m:importlib.metadata.version(m) for m in ['pandas','pyarrow','numpy','scipy','matplotlib','PyYAML']}}
    (GLOBAL/'ANALYSIS_SUMMARY.json').write_text(json.dumps(result,indent=2))
    report='# Analysis Summary\n\nMachine-readable summary: `ANALYSIS_SUMMARY.json`.\n\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n\n'
    report+='Covered: coverage, exclusions, row-level lineage, target-level seed aggregation, separate ID/pairwise/LODO, source-removal paired targets, oracle diagnostic labels, no semantic embedding ranks, negative/null preservation, numeric reconstruction.\n\nScope note: full per-row checks over external datasets and historical environment snapshots are outside this package. See analysis_scope_notes.md.\n\n'+global_trace()
    (GLOBAL/'ANALYSIS_SUMMARY.md').write_text(report)
    if errors:raise RuntimeError('Final audit failed: '+repr(errors[:10]))

PHASES={0:phase0,1:phase1,2:phase2,3:phase3,4:phase4,5:phase5,6:phase6,7:phase7,8:phase8,9:phase9,10:phase10,11:phase11,12:phase12,13:phase13,14:phase14,15:phase15,16:phase16,17:phase17,18:phase18,19:phase19}

def checkpoint(phase):
    (GLOBAL/'analysis_state.json').write_text(json.dumps({'last_completed_phase':phase,'issues':ISSUES,'artifacts':ARTIFACTS,'docs':DOCS,'reads':READS},ensure_ascii=False,indent=2))

def main():
    global CFG,ISSUES,ARTIFACTS,DOCS,READS
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=SCRIPT.parent/'config.json');p.add_argument('--from-phase',type=int,default=0);p.add_argument('--to-phase',type=int,default=19)
    a=p.parse_args();CFG=json.loads(a.config.read_text());GLOBAL.mkdir(parents=True,exist_ok=True)
    if a.from_phase and (GLOBAL/'analysis_state.json').exists():
        st=json.loads((GLOBAL/'analysis_state.json').read_text());ISSUES=st['issues'];ARTIFACTS=st['artifacts'];DOCS=st['docs'];READS=st['reads']
    for phase in range(a.from_phase,a.to_phase+1):
        if phase not in PHASES:raise RuntimeError(f'Phase {phase} not implemented')
        print(f'PHASE {phase} START {datetime.now().isoformat()}',flush=True)
        PHASES[phase]();checkpoint(phase)
        print(f'PHASE {phase} COMPLETE',flush=True)

if __name__=='__main__':main()
