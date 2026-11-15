#!/usr/bin/env python3
"""Exploratory global stable Top-10 ablation; reuse controlled LODO splits."""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'supplemental'))
from common import atomic_json, code_identity, np, pd, sha256, stable_hash
from run import completed


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--feature-group', choices=['stable', 'sqli', 'lexical'], default='stable')
    args = parser.parse_args()
    analysis = ROOT / 'analise_resultados_tcc'
    ranking_path = analysis / 'ADDITIONAL_MANUSCRIPT_ANALYSES/tables/top10_cross_dataset_stable_features.csv'
    if args.feature_group != 'stable':
        ranking_path = analysis / 'ADDITIONAL_MANUSCRIPT_ANALYSES/derived/historical_stable_features_snapshot.parquet'
    ranking = pd.read_parquet(ranking_path) if ranking_path.suffix == '.parquet' else pd.read_csv(ranking_path)
    ranking = ranking.loc[ranking.representation == 'CANONICALIZED'].copy()
    selection_rule = 'Existing global Top-10 list, unchanged.'
    if args.feature_group != 'stable':
        # Two disjoint groups: SQL tokens/comments versus generic text/URL shape.
        if args.feature_group == 'sqli':
            ranking = ranking.loc[ranking.feature.str.startswith('sql_')]
        else:
            ranking = ranking.loc[~ranking.feature.str.startswith(('sql_', 'xss_')) & ranking.feature.ne('path_traversal')]
        ranking = ranking.sort_values(['top_k_frequency', 'rank_mean', 'feature'], ascending=[False, True, True]).head(10)
        selection_rule = ('Within group: descending historical Top-10 frequency, then ascending mean rank, '
                          'then feature name. SQL group includes only sql_*; lexical group excludes sql_*, '
                          'xss_* and path_traversal. Both groups are lexical counts, not semantic SQL parsing.')
    selected = ranking.feature.tolist()
    assert len(selected) == len(set(selected)) == 10
    runs = pd.read_csv(analysis / 'SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/lodo_per_run.csv')
    runs = runs.loc[(runs.model == 'catboost') & (runs.representation == 'CANONICALIZED') & (runs.seed == args.seed)].sort_values('target')
    assert len(runs) == runs.target.nunique() == 7
    baselines = [json.loads(Path(p).read_text()) for p in runs.original_metric_file]
    for baseline in baselines:
        assert baseline['status'] == 'COMPLETED' and baseline['kind'] == 'lodo'
        assert sha256(Path(baseline['split_file'])) == baseline['split_sha256']
        for file, digest in baseline['code_sha256'].items():
            assert sha256(Path(file)) == digest, f'Baseline code changed: {file}'
    caches = {b['cache'] for b in baselines}
    assert len(caches) == 1
    source_cache = Path(next(iter(caches)))
    marker = json.loads((source_cache / 'READY.json').read_text())
    for file, digest in marker['cache_sha256'].items():
        assert sha256(Path(file)) == digest, f'Cache changed: {file}'
    names = json.loads((source_cache / 'feature_names.json').read_text())
    # Preserve the original column order, changing only the selected subset.
    indices = [i for i, name in enumerate(names) if name in selected]
    feature_names = [names[i] for i in indices]
    assert len(indices) == 10
    prefix = 'top10_can_catboost_seed' if args.feature_group == 'stable' else 'top10_' + args.feature_group + '_can_catboost_seed'
    out = ROOT / 'experimentos_exploratorios' / (prefix + str(args.seed) + '_' + datetime.now().strftime('%Y%m%dT%H%M%S%f'))
    cache = out / 'cache'
    cache.mkdir(parents=True, exist_ok=False)
    matrix = np.load(source_cache / 'CANONICALIZED.npy', mmap_mode='r')
    np.save(cache / 'CANONICALIZED.npy', np.asarray(matrix[:, indices], dtype='float32'))
    atomic_json(cache / 'feature_names.json', feature_names)
    atomic_json(cache / 'READY.json', {'dimensions': 10, 'source_cache': str(source_cache),
        'cache_sha256': {str(p): sha256(p) for p in [cache / 'CANONICALIZED.npy', cache / 'feature_names.json']}})
    ranking[[c for c in ['feature', 'top_k_frequency', 'rank_mean'] if c in ranking]].to_csv(out / 'selected_features.csv', index=False)
    note = ('Exploratory retrospective ablation: fixed Top-10 from historical global LODO rankings. '
            'Feature selection is not nested per held-out target; other historical folds include that target as a source. '
            'One seed only. Baseline64 reuses saved controlled results for the same seed and exact splits. '
            'Thresholds are reselected independently on source validation after each fit.')
    atomic_json(out / 'manifest.json', {'seed': args.seed, 'features': feature_names,
        'feature_group': args.feature_group, 'selection_rule': selection_rule,
        'ranking_file': str(ranking_path), 'ranking_sha256': sha256(ranking_path),
        'baseline_metric_files': runs.original_metric_file.tolist(), 'note': note,
        'runner_sha256': sha256(Path(__file__)), 'source_code_sha256': code_identity()})
    print('OUTPUT', out, flush=True)
    print('FEATURES', args.feature_group, ', '.join(selected), flush=True)
    rows = []
    for baseline, original_file in zip(baselines, runs.original_metric_file):
        original_job = json.loads(Path(original_file).with_name('job.json').read_text())
        config = dict(original_job['config'])
        config.update(output=str(out.relative_to(ROOT)), save_checkpoints=True)
        spec = dict(original_job)
        spec.update(cache=str(cache), config=config, config_hash=stable_hash(config),
                    code_sha256=code_identity(), selected_features=feature_names,
                    baseline_metrics_file=original_file, exploratory_note=note)
        eid = 'TOP10_' + stable_hash({'baseline': original_job['experiment_id'], 'features': feature_names})[:24]
        spec.update(experiment_id=eid, run_dir=str(out / 'runs' / eid))
        job_path = Path(spec['run_dir']) / 'job.json'
        atomic_json(job_path, spec)
        print('RUN', baseline['target'], flush=True)
        with (job_path.parent / 'run.log').open('w') as log:
            subprocess.run([sys.executable, str(ROOT / 'scripts/supplemental/run.py'), '--worker', str(job_path)], stdout=log, stderr=subprocess.STDOUT, check=True)
        assert completed(spec)
        result = json.loads(job_path.with_name('metrics.json').read_text())
        assert result['split_sha256'] == baseline['split_sha256']
        assert result['software'] == baseline['software'], 'Environment differs from baseline'
        assert result['config']['model_config'] == baseline['config']['model_config']
        for part in ['train_n', 'validation_n', 'test_n']:
            assert result[part] == baseline[part]
        row = {'target': baseline['target'], 'seed': args.seed, 'baseline_file': original_file,
               'top10_file': str(job_path.with_name('metrics.json'))}
        for metric in ['f1', 'mcc', 'pr_auc', 'precision', 'recall', 'fpr', 'brier', 'ece_10']:
            row[metric + '_64'] = baseline['metrics_test'][metric]
            row[metric + '_10'] = result['metrics_test'][metric]
            row['delta_' + metric] = row[metric + '_10'] - row[metric + '_64']
        for key in ['threshold_source', 'selected_iterations', 'training_seconds']:
            row[key + '_64'] = baseline[key]
            row[key + '_10'] = result[key]
        rows.append(row)
        pd.DataFrame(rows).to_csv(out / 'comparison.csv', index=False)
        print('DONE', row['target'], 'F1_64', round(row['f1_64'], 6), 'F1_10', round(row['f1_10'], 6), 'delta', round(row['delta_f1'], 6), flush=True)
    frame = pd.DataFrame(rows)
    means = frame.select_dtypes(include='number').drop(columns='seed').mean().to_dict()
    atomic_json(out / 'summary.json', {'note': note, 'targets': len(frame), 'means': means,
        'f1_wins': int((frame.delta_f1 > 1e-12).sum()), 'f1_losses': int((frame.delta_f1 < -1e-12).sum())})
    print(frame[['target', 'f1_64', 'f1_10', 'delta_f1']].to_string(index=False), flush=True)
    print('MEANS', json.dumps(means), flush=True)


if __name__ == '__main__':
    main()
