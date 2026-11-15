"""Synthetic correctness tests; never read or train on research datasets."""
import unittest
import tempfile
import subprocess
from common import *
from run import jobs_for,completed
from existing_analysis import exact_shapley

def fixture():
    rows=[]
    for source in ['a','b','c','d']:
        for y in [0,1]:
            for i in range(40):
                url=f'/{source}/item/{i}?id={i}';body=f'value={i}' if not y else f'value={i}%27%20OR%201=1--'
                rows.append(dict(dataset=source,family=source,row_number=1+len(rows),y=y,url=url,body=body,text=url+' '+body))
    raw=pd.DataFrame(rows);a,b=paired_views(raw,'synthetic_source');a['feature_row']=np.arange(len(a));b['feature_row']=np.arange(len(b))
    return a,b

class Tests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads(Path(__file__).with_name('config.json').read_text());self.config['datasets']=['a','b','c','d'];self.config['seeds']=[42]
        self.config['pilot_cap']=0

    def test_paired_ids_and_lexical_encoding(self):
        a,b=fixture();self.assertTrue(a.sample_id.equals(b.sample_id));self.assertTrue(a.y.equals(b.y));self.assertTrue(a.canonical_hash.equals(b.canonical_hash))
        self.assertGreater(extract(a).enc_pct.sum(),0);self.assertEqual(extract(b).enc_pct.sum(),0)

    def test_common_test_and_target_exclusion(self):
        a,_=fixture();idp,ood,common,_=target_splits(a,'a',42,self.config)
        self.assertEqual(set(idp['test'].sample_id),set(common.sample_id));self.assertLessEqual(set(common.sample_id),set(ood['test'].sample_id))
        self.assertNotIn('a',set(ood['train'].dataset)|set(ood['validation'].dataset));isolate(idp);isolate(ood)
        frozen=set(ood['validation'].sample_id)
        for s in ood['train'].dataset.unique():
            parts=ood|{'train':ood['train'][ood['train'].dataset!=s]};isolate(parts);self.assertEqual(frozen,set(parts['validation'].sample_id))

    def test_separability_balance_and_shared_hashes(self):
        a,_=fixture();a.loc[a.index[-1],'canonical_hash']=a.canonical_hash.iloc[0]
        for condition in ['all','benign','malicious']:
            train,test,audit=origin_split(a,condition,42,self.config)
            for f in [train,test]:self.assertEqual(f.groupby(['dataset','y']).size().nunique(),1)
            self.assertFalse(set(train.canonical_hash)&set(test.canonical_hash));self.assertEqual(audit['removed_cross_origin_rows'],2)

    def test_single_class_target_does_not_discard_lodo(self):
        a,_=fixture();a=a[~((a.dataset=='a')&(a.y==1))]
        idp,ood,common,audit=target_splits(a,'a',42,self.config)
        self.assertIsNone(idp);self.assertIsNotNone(audit['id_not_applicable'])
        self.assertEqual(ood['test'].y.nunique(),1);isolate(ood)

    def test_threshold_matches_bruteforce_including_ties(self):
        from sklearn.metrics import f1_score
        rng=np.random.default_rng(3)
        for _ in range(12):
            y=rng.integers(0,2,40);s=np.round(rng.random(40),1);candidate=np.unique(np.r_[0,s,1])
            vals=[f1_score(y,s>=t,zero_division=0) for t in candidate];t,v=fast_threshold(y,s)
            self.assertEqual(t,candidate[np.argmax(vals)]);self.assertAlmostEqual(v,max(vals))

    def test_exact_shapley_efficiency_and_missing_coalition(self):
        values={frozenset():.2,frozenset(['a']):.4,frozenset(['b']):.3,frozenset(['a','b']):.8}
        result=exact_shapley(['a','b'],values);self.assertAlmostEqual(result['a'],.35);self.assertAlmostEqual(result['b'],.25)
        with self.assertRaises(ValueError):exact_shapley(['a','b'],{k:v for k,v in values.items() if k})

    def test_end_to_end_synthetic_workers_and_consolidation(self):
        a,b=fixture();config=self.config;config['min_available_ram_gib']=.1
        with tempfile.TemporaryDirectory(prefix='sqli_supplemental_test_') as tmp:
            out=Path(tmp);cache=out/'cache'/'fixture';cache.mkdir(parents=True)
            cols=['sample_id','dataset','family','row_number','y','canonical_hash','feature_row'];dump_table(cache/'cohort.parquet',a[cols])
            for rep,f in [('RAW',a),('CANONICALIZED',b)]:np.save(cache/(rep+'.npy'),extract(f).to_numpy(dtype='float32'))
            atomic_json(cache/'feature_names.json',list(extract(a).columns))
            atomic_json(cache/'READY.json',{'cache_sha256':{str(cache/(r+'.npy')):sha256(cache/(r+'.npy')) for r in ['RAW','CANONICALIZED']}})
            # 4 paired binary fits, 6 controlled-origin fits, and one fit per other model.
            jobs=list(jobs_for('paired',config,out,cache,['a'],[42],['logistic']))+list(jobs_for('separability',config,out,cache,['a'],[42],['logistic']))
            for model in ['catboost','mlp']:jobs.append(next(jobs_for('paired',config,out,cache,['a'],[42],[model])))
            contribution=list(jobs_for('contribution',config,out,cache,['a'],[42],['logistic']))
            # Full source model is reusable across stages; add one removal pair to test frozen validation.
            self.assertIn(contribution[0]['experiment_id'],{j['experiment_id'] for j in jobs})
            jobs.extend([j for j in contribution if j['kind']=='contribution_fixed_validation'][:2])
            for job in jobs:
                path=Path(job['run_dir'])/'job.json';atomic_json(path,job)
                proc=subprocess.run([sys.executable,str(Path(__file__).with_name('run.py')),'--worker',str(path)],capture_output=True,text=True)
                self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr);self.assertTrue(completed(job))
            proc=subprocess.run([sys.executable,str(Path(__file__).with_name('consolidate.py')),'--root',str(out)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            report=json.loads((out/'analysis/AUDIT.json').read_text());self.assertEqual(report['common_test_pairs'],2);self.assertEqual(report['frozen_validation_pairs'],2)
            job=jobs[0];status=Path(job['run_dir'])/'metrics.json';status.write_text(status.read_text()+' ')
            self.assertFalse(completed(job),'Resume must reject mutated artifacts')

if __name__=='__main__':
    import argparse
    from src.utils.provenance import now
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path);args=parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if args.report:atomic_json(args.report,{'generated_at':now(),'tests_run':result.testsRun,'successful':result.wasSuccessful(),
        'failures':[(str(test),trace) for test,trace in result.failures+result.errors],
        'synthetic_worker_fits':14,'research_dataset_trainings':0,'code_sha256':code_identity(),'command':sys.argv,
        'scope':'synthetic isolated workers; pairing, target isolation, single-class behavior, balanced origin splits, exact threshold, Shapley, consolidation, resume checksum'})
    sys.exit(0 if result.wasSuccessful() else 1)
