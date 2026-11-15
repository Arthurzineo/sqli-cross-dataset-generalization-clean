"""Shared deterministic cohorts, cache provenance and source-only splitting."""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='2'
import json
import hashlib
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data.loader import load_dataset, dataset_path, decode_until_stable, canonical
from src.data.splits import make_split, _remove_label_conflicts
from src.features.lexical import extract
from src.utils.config import datasets_config
from src.utils.provenance import atomic_json, sha256, stable_hash

class NotApplicable(ValueError):pass

def dump_table(path, frame):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    frame.to_parquet(temp,index=False);temp.replace(path)

def source_identity(config):
    return {d:{'path':str(dataset_path(d,'raw')),'sha256':sha256(dataset_path(d,'raw'))} for d in config['datasets']}

def code_identity():
    paths=[*Path(__file__).parent.glob('*.py'),ROOT/'src/data/loader.py',ROOT/'src/data/splits.py',ROOT/'src/features/lexical.py',ROOT/'src/models/classical.py',ROOT/'src/evaluation/metrics.py',ROOT/'src/utils/config.py',ROOT/'src/utils/provenance.py',ROOT/'config/datasets.yaml']
    return {str(p):sha256(p) for p in sorted(paths)}

def paired_views(raw, source_hash):
    """Same rows/labels/order; CANONICALIZED is derived from the RAW input."""
    a=raw.copy().reset_index(drop=True)
    a['sample_id']=[hashlib.sha256(f'{d}:{source_hash}:{r}'.encode()).hexdigest() for d,r in zip(a.dataset,a.row_number)]
    a['canonical_hash']=a.text.map(lambda x:hashlib.sha256(canonical(x).encode()).hexdigest())
    b=a.copy()
    for column in ['text','url','body']:b[column]=a[column].map(decode_until_stable)
    return a,b

def prepare(config,out):
    sources=source_identity(config);identity={'protocol':config['protocol'],'sources':sources,'code':code_identity(),'pilot_cap':config.get('pilot_cap',0)}
    key=stable_hash(identity);cache=out/'cache'/key;marker=cache/'READY.json'
    if marker.exists():
        saved=json.loads(marker.read_text())
        for file,expected in saved['cache_sha256'].items():
            if not Path(file).exists() or sha256(Path(file))!=expected:raise RuntimeError('Corrupt paired cache: '+file)
        return cache
    cache.mkdir(parents=True,exist_ok=True);frames=[];offset=0;metadata=[];feature_names=None;arrays={'RAW':[],'CANONICALIZED':[]}
    for dataset in config['datasets']:
        raw=load_dataset(dataset,'raw');a,b=paired_views(raw,sources[dataset]['sha256'])
        cap=config.get('pilot_cap',0)
        if cap:
            chosen=a.groupby('y',group_keys=False).sample(n=min(cap,int(a.y.value_counts().min())),random_state=42).index.sort_values()
            a=a.loc[chosen].reset_index(drop=True);b=b.loc[chosen].reset_index(drop=True)
        for rep,f in [('RAW',a),('CANONICALIZED',b)]:
            x=extract(f);feature_names=list(x.columns);arrays[rep].append(x.to_numpy(dtype='float32'))
        meta=a[['sample_id','dataset','family','row_number','y','canonical_hash']].copy()
        meta['feature_row']=np.arange(len(a))+offset;meta['raw_source_file']=sources[dataset]['path'];meta['raw_source_sha256']=sources[dataset]['sha256'];frames.append(meta);offset+=len(a)
        metadata.append({'dataset':dataset,'n':len(a),'n_changed':int(a.text.ne(b.text).sum()),'changed_fraction':float(a.text.ne(b.text).mean()),'source_file':sources[dataset]['path'],'source_sha256':sources[dataset]['sha256'],'pilot_cap_per_class':cap})
    meta=pd.concat(frames,ignore_index=True);dump_table(cache/'cohort.parquet',meta)
    for rep,blocks in arrays.items():
        path=cache/(rep+'.npy');temp=cache/(rep+'.tmp.npy');np.save(temp,np.concatenate(blocks));temp.replace(path)
    atomic_json(cache/'feature_names.json',feature_names);dump_table(cache/'input_audit.parquet',pd.DataFrame(metadata))
    cache_files=[cache/'cohort.parquet',cache/'RAW.npy',cache/'CANONICALIZED.npy',cache/'feature_names.json',cache/'input_audit.parquet']
    atomic_json(marker,{'cache_id':key,'identity':identity,'n':len(meta),'dimensions':len(feature_names),'cache_sha256':{str(p):sha256(p) for p in cache_files}})
    return cache

def group_holdout(frame, seed, fraction):
    if frame.canonical_hash.nunique()<2:raise NotApplicable('Fewer than two canonical groups')
    train,test=next(GroupShuffleSplit(n_splits=1,test_size=fraction,random_state=seed).split(frame,groups=frame.canonical_hash))
    return frame.iloc[train].copy(),frame.iloc[test].copy()

def isolate(parts):
    hashes={k:set(v.canonical_hash) for k,v in parts.items()}
    for a,b in [('train','validation'),('train','test'),('validation','test')]:
        if hashes[a]&hashes[b]:raise AssertionError(f'Canonical leakage: {a}/{b}')
    if not len(parts['train']) or parts['train'].y.nunique()<2:raise NotApplicable('Training set does not contain both attack classes')
    if not len(parts['validation']) or parts['validation'].y.nunique()<2:raise NotApplicable('Validation does not contain both attack classes')
    if not len(parts['test']):raise NotApplicable('Empty test')

def target_splits(meta,target,seed,config):
    target_rows=meta[meta.dataset==target].copy()
    development,common_test=group_holdout(target_rows,seed,config['test_fraction'])
    development,conflicts=_remove_label_conflicts(development)
    development=development.sort_values(['dataset','row_number']).drop_duplicates('canonical_hash')
    id_issue=None
    try:
        idtrain,idval=group_holdout(development,seed+1,config['validation_fraction']/(1-config['test_fraction']))
        idparts={'train':idtrain,'validation':idval,'test':common_test};isolate(idparts)
    except ValueError as e:
        idparts=None;id_issue=str(e)
    sources=sorted(set(meta.dataset)-{target})
    train,val,test,audit=make_split(meta.sort_values(['dataset','row_number']), 'lodo',target,seed,sources,True)
    if target in set(train.dataset)|set(val.dataset):raise AssertionError('Target in OOD development')
    # Purging is against the ENTIRE target, not just the common holdout.
    oodparts={'train':train,'validation':val,'test':test};isolate(oodparts)
    if set(common_test.sample_id)-set(test.sample_id):raise AssertionError('Common target holdout absent from OOD test')
    return idparts,oodparts,common_test,{'id_label_conflicts_removed':conflicts,'id_not_applicable':id_issue,'ood_audit':audit}

def save_split(out,parts,common_test,audit,cache_id):
    pieces=[]
    for split,frame in parts.items():pieces.append(frame.assign(split=split,is_common_test=frame.sample_id.isin(common_test.sample_id)))
    manifest=pd.concat(pieces,ignore_index=True)
    key=stable_hash({'cache_id':cache_id,'rows':manifest[['sample_id','split','is_common_test']].to_dict('records')})
    path=out/'splits'/(key+'.parquet')
    if not path.exists():dump_table(path,manifest)
    elif not pd.read_parquet(path)[['sample_id','split','is_common_test']].equals(manifest[['sample_id','split','is_common_test']]):raise RuntimeError('Split identity collision')
    atomic_json(out/'splits'/(key+'.json'),{'split_id':key,'cache_id':cache_id,'split_file':str(path),'sha256':sha256(path),'audit':audit,'counts':manifest.groupby(['split','dataset','y']).size().rename('n').reset_index().to_dict('records')})
    return key,path

def origin_split(meta,condition,seed,config):
    """Discard every shared-origin hash, balance every origin/class, paired views."""
    original=len(meta);origins=list(config['datasets']);shared=meta.groupby('canonical_hash').dataset.nunique();shared=set(shared[shared>1].index)
    f=meta[~meta.canonical_hash.isin(shared)].copy();removed_shared=original-len(f)
    conflicts=f.groupby('canonical_hash').y.nunique();bad=set(conflicts[conflicts>1].index)
    f=f[~f.canonical_hash.isin(bad)].sort_values(['dataset','row_number']).drop_duplicates('canonical_hash')
    labels=[0,1] if condition=='all' else [0] if condition=='benign' else [1]
    f=f[f.y.isin(labels)];counts=f.groupby(['dataset','y']).size()
    if any((d,y) not in counts for d in origins for y in labels):raise NotApplicable('One requested dataset/class absent after purge')
    n=min(config['separability_cap_per_dataset_class'],int(counts.min()))
    if n<4:raise NotApplicable('Insufficient samples per origin/class')
    selected=pd.concat([f[(f.dataset==d)&(f.y==y)].sample(n,random_state=seed) for d in origins for y in labels],ignore_index=True)
    # Identical integer counts in EACH origin/class, including held-out test.
    ntest=max(1,int(np.floor(n*config['test_fraction'])));train_indices=[];test_indices=[]
    for _,g in selected.groupby(['dataset','y'],sort=True):
        chosen=g.sample(ntest,random_state=seed+1).index
        test_indices.extend(chosen);train_indices.extend(g.index.difference(chosen))
    a,b=selected.loc[train_indices].copy(),selected.loc[test_indices].copy()
    if set(a.canonical_hash)&set(b.canonical_hash):raise AssertionError('Origin-classifier leakage')
    return a,b,{'condition':condition,'n_per_dataset_class':n,'removed_cross_origin_rows':removed_shared,'removed_conflicting_hashes':len(bad),'n_before':original,'n_after':len(selected),'classes':labels,'origins':origins,'cap_explicit':config['separability_cap_per_dataset_class']}

def fast_threshold(y,scores):
    """Exact F1 optimum over observed scores + 0/1; ties choose smallest threshold."""
    y=np.asarray(y,dtype=int);scores=np.asarray(scores,dtype=float)
    if len(y)==0 or not np.isfinite(scores).all():raise ValueError('Invalid threshold input')
    order=np.argsort(scores,kind='stable');s=scores[order];yy=y[order];c=np.unique(np.r_[0.,s,1.])
    starts=np.searchsorted(s,c,side='left');before=np.r_[0,np.cumsum(yy)];tp=before[-1]-before[starts];pred=len(s)-starts
    denom=pred+before[-1];f1=np.divide(2*tp,denom,out=np.zeros_like(tp,dtype=float),where=denom>0)
    idx=int(np.argmax(f1));return float(c[idx]),float(f1[idx])
