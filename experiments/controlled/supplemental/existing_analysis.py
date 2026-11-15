#!/usr/bin/env python3
"""No-training supplements: exact declared-game Shapley and streaming split audit."""
from common import *
import argparse
import math
import itertools
import collections

def exact_shapley(players,values):
    players=tuple(sorted(players));n=len(players);required={frozenset(c) for k in range(n+1) for c in itertools.combinations(players,k)}
    missing=required-set(values)
    if missing:raise ValueError(f'Missing {len(missing)} coalitions; do not impute them')
    result={}
    for player in players:
        total=0.
        for coalition in required:
            if player in coalition:continue
            k=len(coalition);weight=math.factorial(k)*math.factorial(n-k-1)/math.factorial(n)
            total+=weight*(values[coalition|{player}]-values[coalition])
        result[player]=total
    return result

def empty_value(metric,prevalence):
    # Explicit analytic, source-free p=0.5, t=0.5 => all-positive reference.
    return {'f1':2*prevalence/(1+prevalence),'mcc':0.,'pr_auc':prevalence,'recall':1.,'fpr':1.,'fnr':0.}[metric]

def shapley(master_path,out):
    df=pd.read_parquet(master_path);df=df[df.usable & df.experiment_type.eq('contribution')]
    master_hash=sha256(master_path)
    specs=datasets_config();rows=[];games=[];skips=[]
    for key,g in df.groupby(['target_dataset','model','representation','feature_set','seed']):
        target=key[0];players=sorted({p for s in g.effective_development_datasets for p in s.split('+') if p})
        expected={p for s in g.training_datasets for p in s.split('+') if p and specs[p]['family']!=specs[target]['family']}
        if set(players)!=expected:raise ValueError('Effective player set differs from source-family policy')
        groups={frozenset(k.split('+')):gg for k,gg in g.groupby('effective_development_datasets')}
        counts=g[['n_attack','test_n']].drop_duplicates()
        if len(counts)!=1:raise ValueError('Target populations differ inside coalition game')
        npos,ntotal=counts.iloc[0];pi=float(npos/ntotal)
        for metric in ['f1','mcc','pr_auc','recall','fpr','fnr']:
            if metric in ['mcc','pr_auc'] and pi in [0,1]:
                skips.append(dict(target=target,model=key[1],representation=key[2],seed=key[4],metric=metric,reason='single-class target'));continue
            values={frozenset():empty_value(metric,pi)};lineage=[]
            for coalition,gg in groups.items():
                vals=gg[metric].to_numpy(dtype=float)
                if not np.isfinite(vals).all() or not np.allclose(vals,vals[0],atol=1e-10,rtol=0):raise ValueError('Inconsistent repeated effective coalition; inspect before averaging')
                values[coalition]=float(vals[0]);lineage.extend(gg.experiment_id)
            # No averaging over missing coalitions and no use of mislabeled legacy Shapley.
            phis=exact_shapley(players,values)
            residual=sum(phis.values())-(values[frozenset(players)]-values[frozenset()])
            if abs(residual)>1e-9:raise AssertionError('Shapley efficiency identity failed')
            game_id=stable_hash({'group':key,'metric':metric,'reference':'all_positive_p05_t05','master_sha256':master_hash})[:24]
            games.append(dict(game_id=game_id,target=target,model=key[1],representation=key[2],feature_set=key[3],seed=key[4],metric=metric,
                n_players=len(players),n_coalitions=len(values),empty_value=values[frozenset()],full_value=values[frozenset(players)],
                efficiency_residual=residual,empty_reference='analytic p=0.5,t=0.5 (all positive), evaluated on saved target labels; not a trained run',
                experiment_ids=json.dumps(sorted(set(lineage))),source_file=str(master_path)))
            for p,value in phis.items():rows.append(dict(game_id=game_id,target=target,model=key[1],representation=key[2],feature_set=key[3],seed=key[4],source=p,metric=metric,shapley=value,benefit_shapley=-value if metric in ['fpr','fnr'] else value,experiment_ids=json.dumps(sorted(set(lineage)))))
    dump_table(out/'exact_shapley.parquet',pd.DataFrame(rows));dump_table(out/'shapley_games.parquet',pd.DataFrame(games));dump_table(out/'shapley_nonapplicable.parquet',pd.DataFrame(skips,columns=['target','model','representation','seed','metric','reason']))
    atomic_json(out/'SHAPLEY_AUDIT.json',{'reference':'all-positive, source-free analytic baseline','source_file':str(master_path),'source_sha256':sha256(master_path),'n_games':len(games),'n_shapley_values':len(rows),'new_trainings':0,'max_efficiency_residual':max(abs(r['efficiency_residual']) for r in games) if games else None})

def audit_splits(master_path,lineage_path,out,limit=None):
    m=pd.read_parquet(master_path);m=m[m.usable];line=pd.read_parquet(lineage_path).set_index('experiment_id');out.mkdir(parents=True,exist_ok=True)
    count=0
    for r in m.itertuples():
        path=ROOT.parent/line.loc[r.experiment_id,'split_file'];stat=path.stat();destination=out/(r.experiment_id+'.json')
        identity={'file':str(path),'size':stat.st_size,'mtime_ns':stat.st_mtime_ns}
        if destination.exists() and json.loads(destination.read_text()).get('input_identity')==identity:continue
        if limit is not None and count>=limit:break
        sets=collections.defaultdict(set);ns=collections.Counter();origins=collections.defaultdict(set)
        for f in pd.read_csv(path,usecols=['canonical_hash','split','dataset'],chunksize=25000):
            for part,g in f.groupby('split'):sets[part].update(g.canonical_hash);ns[part]+=len(g);origins[part].update(g.dataset)
        intersections={a+'_'+b:len(sets[a]&sets[b]) for a,b in [('train','validation'),('train','test'),('validation','test')]}
        target_leak=r.experiment_type!='baseline_id' and r.target_dataset in origins['train']|origins['validation']
        size_match=ns['train']==r.train_n and ns['validation']==r.validation_n and ns['test']==r.test_n
        atomic_json(destination,{'experiment_id':r.experiment_id,'input_identity':identity,'split_sha256':sha256(path),
            'counts':dict(ns),'intersections':intersections,'outer_target_in_development':target_leak,'counts_match_saved_metrics':bool(size_match),
            'status':'PASS' if not any(intersections.values()) and not target_leak and size_match else 'CRITICAL_ISSUE'})
        count+=1
    done=[json.loads(p.read_text()) for p in out.glob('EXP_*.json')]
    atomic_json(out/'SUMMARY.json',{'planned_valid_runs':len(m),'audited_runs':len(done),'full_audit_complete':len(done)==len(m),'critical_issues':sum(x['status']!='PASS' for x in done),'new_trainings':0,'limit_per_invocation':limit})

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['shapley','audit-splits'],required=True);p.add_argument('--limit',type=int)
    p.add_argument('--master',type=Path,default=ROOT/'analise_resultados_tcc/_global/master_results.parquet')
    p.add_argument('--lineage',type=Path,default=ROOT/'analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet')
    p.add_argument('--output',type=Path,default=ROOT/'complementos_generalizacao_v1/existing_analysis');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    if a.stage=='shapley':
        shapley(a.master,a.output)
        games=pd.read_parquet(a.output/'shapley_games.parquet')
        ids={eid for value in games.experiment_ids for eid in json.loads(value)}
        line=pd.read_parquet(a.lineage);line=line[line.experiment_id.isin(ids)]
        if len(line)!=len(ids) or line.experiment_id.duplicated().any():raise ValueError('Incomplete/duplicated original source mapping')
        dump_table(a.output/'SOURCE_FILES.parquet',line)
        atomic_json(a.output/'EXECUTION.json',{'command':sys.argv,'script_sha256':sha256(Path(__file__)),
            'master_file':str(a.master.resolve()),'master_sha256':sha256(a.master),
            'lineage_file':str(a.lineage.resolve()),'lineage_sha256':sha256(a.lineage),
            'experiment_count':len(ids),'original_metrics_opened':0,'analytical_input_files_read':2,
            'aggregation':'exact factorial-weighted source marginals separately per target/model/representation/feature_set/seed/metric; no seed pooling',
            'source_mapping':'SOURCE_FILES.parquet','source_path_base':str(ROOT.parent),
            'new_trainings':0})
    else:audit_splits(a.master,a.lineage,a.output/'split_audit',a.limit)

if __name__=='__main__':main()
