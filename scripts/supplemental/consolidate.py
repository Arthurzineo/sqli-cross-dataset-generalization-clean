#!/usr/bin/env python3
"""Consolidate new protocols separately; fail on broken pairing or provenance."""
from common import *
import argparse

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT/'complementos_generalizacao_v1/full');a=p.parse_args();rows=[];line=[]
    for path in sorted((a.root/'runs').glob('SUPP_*/metrics.json')):
        result=json.loads(path.read_text());status=json.loads((path.parent/'status.json').read_text())
        if status['status']!='COMPLETED':continue
        if not all(Path(f).exists() and sha256(Path(f))==value for f,value in status['outputs_sha256'].items()):raise RuntimeError('Result checksum mismatch: '+str(path))
        r={k:result.get(k) for k in ['experiment_id','kind','target','model','representation','seed','condition','removed_source','split_id','config_hash','runtime_seconds','train_n','validation_n','test_n','threshold_source']}
        r['training_sources']=json.dumps(result.get('training_sources'));r['validation_sources']=json.dumps(result.get('validation_sources'));r['pilot_cap']=result['config'].get('pilot_cap',0)
        r['execution_context']=stable_hash({'config':result['config_hash'],'cache':result['cache'],'code':result['code_sha256']})
        for col in ['training_seconds','inference_seconds','rss_peak_mib']:r[col]=result.get(col)
        oracle=result.get('oracle_diagnostic',{})
        r['threshold_oracle_diagnostic']=oracle.get('threshold')
        r['oracle_f1_diagnostic']=oracle.get('metrics',{}).get('f1')
        r['threshold_drift']=abs(r['threshold_source']-r['threshold_oracle_diagnostic']) if r['threshold_source'] is not None and r['threshold_oracle_diagnostic'] is not None else None
        source_f1=result.get('metrics_test',{}).get('f1')
        r['oracle_gap_f1']=r['oracle_f1_diagnostic']-source_f1 if r['oracle_f1_diagnostic'] is not None and source_f1 is not None else None
        for part in ['test','common','validation','origin']:
            for metric,value in result.get('metrics_'+part,{}).items():
                if isinstance(value,(int,float)) or value is None:r[part+'_'+metric]=value
        r['experiment_ids']=json.dumps([result['experiment_id']]);r['original_metric_file']=str(path);rows.append(r)
        line.append({'experiment_id':result['experiment_id'],'metric_file':str(path),'prediction_file':result['prediction_file'],'split_file':result['split_file'],'job_file':str(path.parent/'job.json'),'feature_file':result.get('feature_importance_file'),'status_file':str(path.parent/'status.json')})
    if not rows:raise SystemExit('No completed supplemental runs; no results invented')
    d=pd.DataFrame(rows);out=a.root/'analysis';out.mkdir(parents=True,exist_ok=True)
    def table(name,f):
        f=f.copy();f['row_id']=[stable_hash([name,j])[:20] for j in range(len(f))];dump_table(out/name,f)
    table('master_results.parquet',d);table('SOURCE_LINEAGE.parquet',pd.DataFrame(line))
    keys=['kind','target','model','seed','condition','removed_source','config_hash','execution_context']
    for c in keys:
        if c not in d:d[c]=None
    raw=d[d.representation=='RAW'];can=d[d.representation=='CANONICALIZED'];joined=raw.merge(can,on=keys,suffixes=('_raw','_can'),validate='one_to_one');pairs=[]
    for r in joined.to_dict('records'):
        if r['split_id_raw']!=r['split_id_can']:raise AssertionError('RAW/CANONICALIZED split mismatch')
        row={k:r[k] for k in keys};row['experiment_ids']=json.dumps([r['experiment_id_raw'],r['experiment_id_can']]);row['split_id']=r['split_id_raw']
        for metric in ['test_f1','test_mcc','test_pr_auc','common_f1','validation_f1','test_fpr','test_fnr','test_brier','test_ece_10','threshold_source','threshold_drift','oracle_gap_f1','origin_macro_f1','origin_accuracy']:
            if metric+'_raw' in r:
                v,w=r[metric+'_raw'],r[metric+'_can'];row['delta_'+metric]=w-v if v is not None and w is not None else None
        pairs.append(row)
    table('raw_vs_canonicalized_pairs.parquet',pd.DataFrame(pairs))
    idruns=d[d.kind=='id'];lodo=d[d.kind=='lodo'];idpairs=[]
    j=idruns.merge(lodo,on=['target','model','representation','seed','config_hash','execution_context'],suffixes=('_id','_ood'),validate='one_to_one')
    for r in j.to_dict('records'):
        ids=[r['experiment_id_id'],r['experiment_id_ood']]
        # Validate actual evaluated sample IDs, not just sample counts.
        sets=[]
        for eid in ids:
            pred=pd.read_parquet(a.root/'runs'/eid/'predictions.parquet',columns=['sample_id','role','is_common_test'])
            sets.append(set(pred.loc[(pred.role=='test')&pred.is_common_test,'sample_id']))
        if sets[0]!=sets[1]:raise AssertionError('ID/OOD common test mismatch')
        idpairs.append({k:r[k] for k in ['target','model','representation','seed','config_hash','execution_context']}|{'experiment_ids':json.dumps(ids),'n_common':len(sets[0]),'f1_id':r['common_f1_id'],'f1_ood':r['common_f1_ood'],'gap_f1':r['common_f1_id']-r['common_f1_ood'] if r['common_f1_id'] is not None and r['common_f1_ood'] is not None else None})
    table('id_vs_ood_same_test.parquet',pd.DataFrame(idpairs))
    removed=d[d.kind=='contribution_fixed_validation'];contribution=[]
    for r in removed.to_dict('records'):
        full=lodo[(lodo.target==r['target'])&(lodo.model==r['model'])&(lodo.representation==r['representation'])&(lodo.seed==r['seed'])&(lodo.execution_context==r['execution_context'])]
        if len(full)!=1:continue
        f=full.iloc[0]
        def ids_for(eid,role):
            path=a.root/'runs'/eid/'predictions.parquet';x=pd.read_parquet(path,columns=['sample_id','role']);return set(x.loc[x.role==role,'sample_id'])
        if ids_for(f.experiment_id,'validation')!=ids_for(r['experiment_id'],'validation') or ids_for(f.experiment_id,'test')!=ids_for(r['experiment_id'],'test'):raise AssertionError('Frozen validation/test changed')
        contribution.append({k:r[k] for k in ['target','model','representation','seed','removed_source','execution_context']}|{'experiment_ids':json.dumps([f.experiment_id,r['experiment_id']]),**{'delta_'+metric:f['test_'+metric]-r['test_'+metric] if f['test_'+metric] is not None and r['test_'+metric] is not None else None for metric in ['f1','mcc']},'delta_threshold':f.threshold_source-r['threshold_source']})
    table('fixed_validation_contribution.parquet',pd.DataFrame(contribution))
    for name,frame,groupcols in [('raw_vs_canonicalized',pd.DataFrame(pairs),['kind','target','model','condition','removed_source']),('matched_id_ood',pd.DataFrame(idpairs),['target','model','representation']),('fixed_contribution',pd.DataFrame(contribution),['target','model','representation','removed_source'])]:
        summary=[]
        groupcols=groupcols+['execution_context']
        if len(frame):
            for key,g in frame.groupby(groupcols,dropna=False):
                row=dict(zip(groupcols,key));row['experiment_ids']=json.dumps(sorted({eid for text in g.experiment_ids for eid in json.loads(text)}));row['n_seeds']=g.seed.nunique()
                for col in g:
                    if col.startswith(('delta_','gap_')):row[col+'_mean']=g[col].mean();row[col+'_std']=g[col].std()
                summary.append(row)
        table(name+'_seed_summary.parquet',pd.DataFrame(summary))
    atomic_json(out/'AUDIT.json',{'completed_runs':len(d),'raw_canonicalized_pairs':len(pairs),'common_test_pairs':len(idpairs),'frozen_validation_pairs':len(contribution),'checks':'hashes, identical splits, common evaluated IDs, frozen validation/test IDs','legacy_results_modified':False})

if __name__=='__main__':main()
