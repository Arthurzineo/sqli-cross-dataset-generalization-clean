#!/usr/bin/env python3
"""Plan by default. Each real training is an isolated, sequential subprocess."""
from common import *
import argparse
import fcntl
import platform
import resource
import subprocess
import time
import traceback
import importlib.metadata
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score,accuracy_score,confusion_matrix
from threadpoolctl import threadpool_limits
from src.models.classical import fit
from src.evaluation.metrics import calculate
from src.utils.provenance import now,git_commit

def metrics(y,score,threshold):
    m=calculate(y,score,threshold)
    if not np.any(np.asarray(y)==1):
        for k in ['precision','recall','f1','fnr']:m[k]=None
    return m

def resources():
    available=None
    if Path('/proc/meminfo').exists():
        for ln in Path('/proc/meminfo').read_text().splitlines():
            if ln.startswith('MemAvailable:'):available=int(ln.split()[1])*1024
    return {'available_ram_bytes':available,'cpu_count':os.cpu_count(),'platform':platform.platform(),'python':platform.python_version()}

def guard(config):
    available=resources()['available_ram_bytes']
    if available is not None and available<config['min_available_ram_gib']*2**30:
        raise RuntimeError('Insufficient available RAM; stopped before fit. Resume later; no silent sampling.')

def worker(job_path):
    job=json.loads(Path(job_path).read_text());config=job['config'];run=Path(job['run_dir']);start=time.perf_counter()
    run.mkdir(parents=True,exist_ok=True);atomic_json(run/'status.json',{'status':'RUNNING','experiment_id':job['experiment_id'],'started_at':now()})
    try:
        guard(config)
        limit=int(config['max_address_space_gib']*2**30);resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
        split_path=Path(job['split_file'])
        if sha256(split_path)!=job['split_sha256']:raise RuntimeError('Split mutated after job creation')
        cache=Path(job['cache']);matrix_path=cache/(job['representation']+'.npy')
        marker=json.loads((cache/'READY.json').read_text())
        if sha256(matrix_path)!=marker['cache_sha256'][str(matrix_path)]:raise RuntimeError('Feature cache checksum mismatch')
        f=pd.read_parquet(split_path);x=np.load(matrix_path,mmap_mode='r')
        train=f[f.split=='train'];val=f[f.split=='validation'];test=f[f.split=='test'];saved=[]
        X=np.asarray(x[train.feature_row],dtype='float32');T=np.asarray(x[test.feature_row],dtype='float32')
        training_start=time.perf_counter()
        with threadpool_limits(limits=config['threads']):
            if job['kind']=='separability':
                origins=config['datasets'];lookup={v:i for i,v in enumerate(origins)}
                transform=make_pipeline(SimpleImputer(strategy='median'),StandardScaler())
                tx=transform.fit_transform(X);model=LogisticRegression(C=1.0,max_iter=500,random_state=job['seed'])
                model.fit(tx,train.dataset.map(lookup));training_seconds=time.perf_counter()-training_start
                infer_start=time.perf_counter();score=model.predict_proba(transform.transform(T));inference_seconds=time.perf_counter()-infer_start
                prediction=np.asarray(model.classes_)[score.argmax(axis=1)];y=test.dataset.map(lookup).to_numpy()
                result={'metrics_origin':{'macro_f1':float(f1_score(y,prediction,labels=list(lookup.values()),average='macro',zero_division=0)),
                    'accuracy':float(accuracy_score(y,prediction)),'chance_accuracy_uniform':1/len(origins),'chance_macro_f1_balanced_asymptotic':1/len(origins),
                    'confusion_matrix':confusion_matrix(y,prediction,labels=list(lookup.values())).tolist(),'origin_order':origins}}
                saved.append(test[['sample_id','dataset','y']].assign(role='test',true_origin=y,predicted_origin=prediction,**{f'score_origin_{i}':score[:,j] for j,i in enumerate(model.classes_)}))
                iterations=int(model.n_iter_[0]);source_threshold=None
            else:
                isolate({'train':train,'validation':val,'test':test})
                V=np.asarray(x[val.feature_row],dtype='float32')
                model,transform,iterations=fit(job['model'],X,train.y.to_numpy(),V,val.y.to_numpy(),config['model_config'],job['seed'],config['threads'])
                training_seconds=time.perf_counter()-training_start
                infer_start=time.perf_counter();vs=model.predict_proba(transform.transform(V))[:,1];ts=model.predict_proba(transform.transform(T))[:,1];inference_seconds=time.perf_counter()-infer_start
                source_threshold,_=fast_threshold(val.y,vs)
                common_mask=test.is_common_test.to_numpy(dtype=bool)
                result={'threshold_source':source_threshold,'metrics_validation':metrics(val.y,vs,source_threshold),
                    'metrics_common':metrics(test.y.to_numpy()[common_mask],ts[common_mask],source_threshold),
                    'metrics_test':metrics(test.y,ts,source_threshold)}
                # Oracle is computed only after fit/source threshold is frozen, and is diagnostic.
                oracle,_=fast_threshold(test.y,ts)
                result['oracle_diagnostic']={'threshold':oracle,'metrics':metrics(test.y,ts,oracle)}
                for part,values,role in [(val,vs,'validation'),(test,ts,'test')]:
                    saved.append(part[['sample_id','dataset','y','is_common_test']].assign(role=role,score=values,predicted_label=(values>=source_threshold).astype(int),threshold=source_threshold))
                if job['model']=='catboost':
                    names=json.loads((cache/'feature_names.json').read_text())
                    dump_table(run/'feature_importance.parquet',pd.DataFrame({'feature':names,'importance':model.get_feature_importance(),'experiment_id':job['experiment_id']}))
        preds=pd.concat(saved,ignore_index=True);preds['experiment_id']=job['experiment_id'];dump_table(run/'predictions.parquet',preds)
        if config['save_checkpoints']:
            import joblib
            joblib.dump({'model':model,'transform':transform},run/'checkpoint.joblib')
        result.update(job|{'status':'COMPLETED','finished_at':now(),'runtime_seconds':time.perf_counter()-start,'training_seconds':training_seconds,
            'inference_seconds':inference_seconds,'inference_scope':'test' if job['kind']=='separability' else 'validation+test',
            'selected_iterations':iterations,'rss_peak_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'hardware':resources(),
            'software':{name:importlib.metadata.version(name) for name in ['numpy','pandas','pyarrow','scikit-learn','catboost']},'git_commit':git_commit(ROOT),
            'prediction_file':str(run/'predictions.parquet'),'train_n':len(train),'validation_n':len(val),'test_n':len(test),
            'feature_importance_file':str(run/'feature_importance.parquet') if (run/'feature_importance.parquet').exists() else None})
        atomic_json(run/'metrics.json',result)
        outputs={str(p):sha256(p) for p in run.iterdir() if p.name in ['predictions.parquet','metrics.json','feature_importance.parquet','checkpoint.joblib']}
        atomic_json(run/'status.json',{'status':'COMPLETED','experiment_id':job['experiment_id'],'outputs_sha256':outputs,'finished_at':now()})
    except Exception as e:
        atomic_json(run/'status.json',{'status':'FAILED','experiment_id':job['experiment_id'],'error':repr(e),'finished_at':now()})
        traceback.print_exc();raise

def jobs_for(stage,config,out,cache,targets,seeds,models):
    meta=pd.read_parquet(cache/'cohort.parquet');config_hash=stable_hash(config);codes=code_identity()
    def job(kind,target,seed,model,rep,split_id,path,**extra):
        spec={'kind':kind,'target':target,'seed':seed,'model':model,'representation':rep,'split_id':split_id,'split_file':str(path),'split_sha256':sha256(path),
            'cache':str(cache),'config':config,'config_hash':config_hash,'code_sha256':codes,**extra}
        eid='SUPP_'+stable_hash(spec)[:28];spec.update(experiment_id=eid,run_dir=str(out/'runs'/eid));return spec
    if stage=='separability':
        for seed in seeds:
            for condition in config['separability_conditions']:
                try:
                    train,test,audit=origin_split(meta,condition,seed,config)
                    sid,path=save_split(out,{'train':train,'test':test},test,audit,cache.name)
                except NotApplicable as e:
                    atomic_json(out/'not_applicable'/f'origin_{condition}_{seed}.json',{'status':'NOT_APPLICABLE','reason':str(e),'seed':seed,'condition':condition});continue
                for rep in config['representations']:yield job('separability',None,seed,'origin_logistic',rep,sid,path,condition=condition)
    else:
        for target in targets:
            for seed in seeds:
                try:idparts,oodparts,common,audit=target_splits(meta,target,seed,config)
                except (NotApplicable,ValueError) as e:
                    atomic_json(out/'not_applicable'/f'{stage}_{target}_{seed}.json',{'status':'NOT_APPLICABLE','reason':str(e),'target':target,'seed':seed});continue
                # Full LODO is exactly the same job across stages: resume reuses it.
                cases=[('lodo',None,oodparts)]
                if stage=='paired':
                    if idparts is not None:cases.insert(0,('id',None,idparts))
                    else:atomic_json(out/'not_applicable'/f'id_{target}_{seed}.json',{'status':'NOT_APPLICABLE','reason':audit['id_not_applicable'],'target':target,'seed':seed,'lodo_still_eligible':True})
                if stage=='contribution':
                    for source in sorted(oodparts['train'].dataset.unique()):
                        parts=oodparts|{'train':oodparts['train'][oodparts['train'].dataset!=source].copy()}
                        try:isolate(parts)
                        except NotApplicable as e:
                            atomic_json(out/'not_applicable'/f'remove_{target}_{seed}_{source}.json',{'status':'NOT_APPLICABLE','reason':str(e)});continue
                        cases.append(('contribution_fixed_validation',source,parts))
                for kind,removed,parts in cases:
                    sid,path=save_split(out,parts,common,audit|{'removed_source':removed,'validation_frozen':True,'dedup_ownership':'sorted dataset,row_number before any removal'},cache.name)
                    for model in models:
                        for rep in config['representations']:yield job(kind,target,seed,model,rep,sid,path,removed_source=removed,
                            training_sources=sorted(parts['train'].dataset.unique()),validation_sources=sorted(parts.get('validation',meta.iloc[:0]).dataset.unique()))

def completed(job):
    path=Path(job['run_dir'])/'status.json'
    if not path.exists():return False
    status=json.loads(path.read_text())
    return status.get('status')=='COMPLETED' and all(Path(p).exists() and sha256(p)==expected for p,expected in status.get('outputs_sha256',{}).items()) and bool(status.get('outputs_sha256'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=Path(__file__).with_name('config.json'))
    p.add_argument('--stage',choices=['plan','prepare','paired','separability','contribution','all'],default='plan')
    p.add_argument('--targets');p.add_argument('--models');p.add_argument('--seeds');p.add_argument('--pilot-cap',type=int,default=0);p.add_argument('--max-runs',type=int);p.add_argument('--worker',type=Path)
    a=p.parse_args()
    if a.worker:worker(a.worker);return
    config=json.loads(a.config.read_text());config['pilot_cap']=a.pilot_cap
    if config['threads']>2:raise ValueError('This conservative pipeline allows at most two threads')
    targets=a.targets.split(',') if a.targets else config['datasets'];models=a.models.split(',') if a.models else config['models'];seeds=list(map(int,a.seeds.split(','))) if a.seeds else config['seeds']
    if not set(targets)<=set(config['datasets']) or not set(models)<=set(config['models']):raise ValueError('Unknown targets/models')
    base=(ROOT/config['output']).resolve()
    if not base.is_relative_to(ROOT) or base==ROOT:raise ValueError('Output must be a dedicated directory within artigo')
    out=base/('pilot_cap_'+str(a.pilot_cap) if a.pilot_cap else 'full');out.mkdir(parents=True,exist_ok=True)
    with (out/'execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.stage=='plan':
            n=len(targets)*len(seeds)*len(models)*len(config['representations'])
            plan={'paired_id_plus_lodo_fits':2*n,'separability_fits':len(config['separability_conditions'])*len(seeds)*len(config['representations']),
                'fixed_validation_contribution_upper_bound':n*len(config['datasets']),'contribution_note':'exact count depends on effective training sources, excluding frozen validation sources',
                'targets':targets,'seeds':seeds,'models':models,'pilot_cap':a.pilot_cap,'resources':resources(),'new_training_started':False,'config':config}
            atomic_json(out/'PLAN.json',plan);print(json.dumps(plan,indent=2));return
        cache=prepare(config,out)
        if a.stage=='prepare':print(cache);return
        stages=['paired','separability','contribution'] if a.stage=='all' else [a.stage];count=0
        for stage in stages:
            for job in jobs_for(stage,config,out,cache,targets,seeds,models):
                if completed(job):print('RESUME_SKIP',job['experiment_id'],flush=True);continue
                if a.max_runs is not None and count>=a.max_runs:return
                guard(config);path=Path(job['run_dir'])/'job.json';atomic_json(path,job)
                print('RUN',job['experiment_id'],stage,job['target'],job['model'],job['representation'],flush=True)
                with (Path(job['run_dir'])/'run.log').open('a') as log:
                    subprocess.run([sys.executable,__file__,'--worker',str(path)],stdout=log,stderr=subprocess.STDOUT,check=True)
                count+=1
                print('COMPLETE',count,job['experiment_id'],flush=True)

if __name__=='__main__':main()
