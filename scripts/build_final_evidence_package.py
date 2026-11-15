#!/usr/bin/env python3
"""Editorial evidence package: copy existing results, join small summaries; no fit/reanalysis."""
import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import json
import shutil
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.utils.provenance import sha256,atomic_json,now,stable_hash
AN=ROOT/'analise_resultados_tcc'
OUT=AN/'FINAL_EVIDENCE_PACKAGE'
SUP=AN/'SUPPLEMENTAL_CONTROLLED_ANALYSIS'
BASE=ROOT/'complementos_generalizacao_v1'
M={i:next(AN.glob(f'M04_{i:02d}_*')) for i in range(1,14)}
CMD=f'{sys.executable} {Path(__file__).resolve()}'
MET=['precision','recall','f1','pr_auc','mcc','fpr','fnr','roc_auc','balanced_accuracy','brier','ece_10']


def union_ids(g):
    return json.dumps(sorted({eid for txt in g.experiment_ids for eid in json.loads(txt)}))


def summary(frame,keys,metrics):
    rows=[]
    for key,g in frame.groupby(keys,dropna=False):
        if not isinstance(key,tuple):key=(key,)
        r=dict(zip(keys,key));r['experiment_ids']=union_ids(g);r['n_rows']=len(g)
        if 'seed' in g:r['n_seeds']=g.seed.nunique();r['seeds']=json.dumps(sorted(map(int,g.seed.unique())))
        for col in metrics:
            v=pd.to_numeric(g[col],errors='coerce').dropna()
            for suffix,value in [('mean',v.mean()),('std',v.std(ddof=1)),('median',v.median()),('min',v.min()),('max',v.max())]:r[col+'_'+suffix]=value
        rows.append(r)
    return pd.DataFrame(rows)


def fmt(v):
    if v is None or (isinstance(v,float) and np.isnan(v)):return 'N/A'
    if isinstance(v,(float,np.floating)):return f'{v:.6f}'
    return str(v).replace('|','\\|').replace('\n',' ')


def markdown(frame,cols,limit=None):
    if limit is not None:frame=frame.head(limit)
    if not len(frame):return 'Nenhuma linha disponível; não imputar resultados.'
    cols=[c for c in cols if c in frame]
    return '\n'.join(['| '+' | '.join(cols)+' |','|'+'|'.join(['---']*len(cols))+'|']+
        ['| '+' | '.join(fmt(row[c]) for c in cols)+' |' for _,row in frame.iterrows()])


class Package:
    def __init__(self):
        OUT.mkdir(parents=True,exist_ok=True);self.copies={};self.recipes=[];self.claims=[];self.frames={};self.start=time.perf_counter()
        self.h=pd.read_parquet(AN/'_global/master_results.parquet');self.valid_h=self.h[self.h.usable].copy()
        self.s=pd.read_parquet(BASE/'full/analysis/master_results.parquet');self.si=self.s.set_index('experiment_id')
        self.hl=pd.read_parquet(AN/'_global/SOURCE_LINEAGE.parquet');self.sl=pd.read_parquet(BASE/'full/analysis/SOURCE_LINEAGE.parquet')
        self.all_ids=set(self.h.experiment_id)|set(self.s.experiment_id)

    def copy(self,path,category='analytical'):
        path=Path(path).resolve()
        if str(path) in self.copies:return self.copies[str(path)]['copy_path']
        if not path.is_file():return None
        if path.is_relative_to(AN) and not path.is_relative_to(OUT):rel=Path('evidence/analysis')/path.relative_to(AN)
        else:rel=Path('evidence/project')/path.relative_to(ROOT)
        dest=OUT/rel;dest.parent.mkdir(parents=True,exist_ok=True);original_hash=sha256(path)
        if not dest.exists() or sha256(dest)!=original_hash:shutil.copy2(path,dest)
        assert sha256(dest)==original_hash
        self.copies[str(path)]={'original_path':str(path),'copy_path':str(rel),'bytes':path.stat().st_size,'sha256':original_hash,'category':category}
        return str(rel)

    def load(self,path):
        self.copy(path);return pd.read_parquet(path) if Path(path).suffix=='.parquet' else pd.read_csv(path)

    def ref(self,path):
        return '`'+str(self.copy(path) or path)+'`'

    def sup(self,name):return self.load(SUP/(name+'.csv'))
    def old(self,section,name):return self.load(M[section]/(name+'.csv'))

    def save(self,name,frame,sources,formula):
        frame=frame.copy().reset_index(drop=True)
        if 'experiment_ids' not in frame:frame['experiment_ids']='[]'
        assert all(set(json.loads(v))<=self.all_ids for v in frame.experiment_ids)
        frame['row_id']=[stable_hash([name,i,r])[:24] for i,r in enumerate(frame.astype(str).to_dict('records'))]
        path=OUT/'writing_tables'/(name+'.csv');path.parent.mkdir(exist_ok=True)
        frame.to_csv(path,index=False);frame.to_parquet(path.with_suffix('.parquet'),index=False)
        self.frames[name]=frame
        self.recipes.append(dict(artifact_id=name,artifact_path=str(path.relative_to(OUT)),analytical_sources=json.dumps([self.copy(s) for s in sources]),
            aggregation=formula,source_columns=json.dumps(list(frame.columns)),script=str(Path(__file__).resolve()),command=CMD,generated_at=now(),
            source_file_manifest='ORIGINAL_SOURCE_MAPPING.parquet'))
        return frame

    def provenance(self):
        return f'''\n## Data Sources and Traceability

Este documento usa somente evidências já existentes e extrações editoriais de tabelas pequenas. Não houve treinamento, recalculo de scores, nova busca de modelos ou novos testes de hipóteses. Histórico e complemento controlado permanecem separados.

Cópias verificadas byte a byte: `COPY_MANIFEST.csv` (caminho original, cópia local, tamanho, SHA-256). Originais por experiment_id: `ORIGINAL_SOURCE_MAPPING.parquet`; as métricas pequenas e importâncias foram copiadas, mas datasets brutos, checkpoints, embeddings, predições e grandes manifests de splits NÃO são duplicados. Seus caminhos originais permanecem no mapping. Copiamos os relatórios da auditoria, não reexecutamos a auditoria. Para caracterização sem experiment_id, a coluna source_file e os AUXILIARY_SOURCES.csv dos capítulos identificam as fontes de dados.

Entradas principais: `evidence/analysis/_global/master_results.parquet` e `evidence/project/complementos_generalizacao_v1/full/analysis/master_results.parquet`; registros e source lineages respectivos nas mesmas árvores. Tabelas/figuras históricas e complementares estão em `evidence/analysis/`, com seus TRACEABILITY.csv e métodos originais. Número de arquivos copiados e tabelas editoriais: `PACKAGE_AUDIT.json`. Colunas/filtros/agrupamentos/fórmulas das extrações novas: `WRITING_TABLE_TRACEABILITY.csv`; agregações de seeds: dentro do alvo/modelo/vista/composição, antes de médias macro entre alvos. Todas as tabelas editoriais contêm row_id e experiment_ids quando aplicáveis. Fonte primária de cada achado: mapping + IDs da linha indicada, não um resultado sem procedência.

Verificação adicional dos extremos de transferência: `NUMERICAL_RECONSTRUCTION_AUDIT.csv` reconstrói F1/MCC/AP full, removed e delta diretamente das cópias dos metrics.json, nas mesmas seeds elegíveis, e compara aos valores não arredondados da tabela editorial. `CLAIM_VERIFICATION.csv` verifica a existência da cadeia de arquivos e IDs dos achados; não confundir essa verificação estrutural com uma reexecução de toda a análise.

Script de empacotamento: `{Path(__file__).resolve()}`. Comando: `{CMD}`. Scripts que geraram as análises: cópias de `artigo/scripts/analysis/final_analysis.py` e `artigo/scripts/analyze_supplemental_results.py`, além de seus configs e scripts experimentais. Scripts não foram reexecutados para criar este pacote. Top15: `CLAIM_LEDGER.csv` e `FINAL_TRACEABILITY.md`; números curtos: `FINAL_NUMBERS_FOR_PAPER.md`. Resultados não existentes ou sem cadeia suficiente são marcados SEM RESULTADO CONSOLIDADO NESTE PACOTE e não entram nesse arquivo curto.
'''

    def doc(self,name,text):
        lines=[]
        for line in (text+self.provenance()).splitlines():
            if lines and lines[-1].strip() and (lines[-1].startswith('#') or
                    (line.startswith('- ') and not lines[-1].startswith('- '))):
                lines.append('')
            lines.append(line)
        (OUT/name).write_text('\n'.join(lines)+'\n')

    def copy_evidence(self):
        folders=[AN/'_global',SUP,*M.values()]
        for folder in folders:
            for path in folder.rglob('*'):
                if path.is_file() and path.suffix in ['.csv','.parquet','.md','.png','.pdf','.json']:self.copy(path)
        self.copy(AN/'FINAL_TCC_RESULTS_GUIDE.md')
        for path in (BASE/'full/analysis').glob('*'):
            if path.is_file():self.copy(path)
        for path in [BASE/'full/PLAN.json',BASE/'sequence/STATE.json',BASE/'existing_analysis/split_audit/SUMMARY.json',BASE/'VALIDATION.json']:
            self.copy(path)
        for path in (BASE/'existing_analysis').glob('*'):
            if path.is_file():self.copy(path)
        # Known paths from existing lineage, never recursive traversal of 280 GB.
        old=self.hl.copy();old['protocol']='historical'
        new=self.sl.rename(columns={'feature_file':'feature_importance_file'}).copy();new['protocol']='controlled_supplement'
        mapping=pd.concat([old,new],ignore_index=True).drop(columns=['row_id'],errors='ignore')
        for col in ['metric_file','manifest_file','threshold_file','feature_importance_file','status_file','job_file']:
            if col not in mapping:continue
            copied=[]
            for value in mapping[col]:
                if not isinstance(value,str) or not value:copied.append(None);continue
                path=Path(value);path=path if path.is_absolute() else ROOT.parent/path
                # Feature CSV and small JSON only. Never read/copy large split manifests here.
                if path.suffix not in ['.json','.parquet','.csv'] or '_split' in path.name:copied.append(None);continue
                copied.append(self.copy(path,'primary_small_artifact'))
            mapping['copy_'+col]=copied
        mapping.to_parquet(OUT/'ORIGINAL_SOURCE_MAPPING.parquet',index=False);self.mapping=mapping
        # Static scripts/configs and the already-saved full hash-audit records are modest evidence, not new analysis.
        for root in [ROOT/'src',ROOT/'config',ROOT/'scripts/analysis',ROOT/'scripts/supplemental',BASE/'sequence/source_snapshots']:
            for path in root.rglob('*'):
                if path.is_file() and path.suffix in ['.py','.json','.yaml','.yml']:self.copy(path,'code_config')
        for path in (BASE/'existing_analysis/split_audit').glob('EXP_*.json'):self.copy(path,'saved_audit_record')
        for path in (ROOT/'datasets/metadata').glob('*'):
            if path.is_file() and path.suffix in ['.csv','.json','.parquet']:self.copy(path,'dataset_metadata')
        for path in [ROOT/'docs/experiment_registry/experiments.csv',ROOT/'results/tables/dataset_characterization.csv',
                     ROOT/'scripts/analyze_supplemental_results.py',ROOT/'scripts/trace_supplemental_value.py',Path(__file__).resolve()]:self.copy(path)

    def editorial_tables(self):
        s=self.s;mcols=['test_'+c for c in MET]
        self.id= self.save('id_controlled',summary(s[s.kind=='id'],['target','model','representation'],mcols),[BASE/'full/analysis/master_results.parquet'],
            'Descriptive seed means/std/median/min/max of existing ID metrics; no new fit/statistical test')
        self.lodo=self.sup('tables/lodo_by_target')
        self.macro=self.save('lodo_macro_complete',summary(self.lodo,['model','representation'],['test_'+c+'_mean' for c in MET]),[SUP/'tables/lodo_by_target.csv'],
            'Equal target weights after existing seed means; *_std is target dispersion, not seed uncertainty')
        macro_deltas=[]
        for model,g in self.macro.groupby('model'):
            views=g.set_index('representation');row=dict(model=model,experiment_ids=union_ids(g))
            for metric in ['f1','mcc','pr_auc']:
                column='test_'+metric+'_mean_mean'
                row[metric+'_raw']=views.loc['RAW',column]
                row[metric+'_canonicalized']=views.loc['CANONICALIZED',column]
                row['delta_'+metric]=row[metric+'_canonicalized']-row[metric+'_raw']
            macro_deltas.append(row)
        self.macro_deltas=self.save('lodo_macro_canonicalization_deltas',pd.DataFrame(macro_deltas),[OUT/'writing_tables/lodo_macro_complete.csv'],
            'CAN minus RAW macro means on identical seven targets, seed means first; descriptive arithmetic, no new statistical test')
        pair=self.load(BASE/'full/analysis/id_vs_ood_same_test.parquet');rows=[]
        for r in pair.itertuples():
            eid_id,eid_ood=json.loads(r.experiment_ids);a=self.si.loc[eid_id];b=self.si.loc[eid_ood]
            out=dict(target=r.target,model=r.model,representation=r.representation,seed=r.seed,experiment_ids=r.experiment_ids)
            for met in ['f1','mcc','pr_auc','brier','ece_10']:
                out[met+'_id']=a['common_'+met];out[met+'_ood']=b['common_'+met];out[met+'_gap']=a['common_'+met]-b['common_'+met]
            rows.append(out)
        self.gaps=self.save('same_test_gaps',summary(pd.DataFrame(rows),['target','model','representation'],[c for c in rows[0] if c.endswith(('_id','_ood','_gap'))]),
            [BASE/'full/analysis/master_results.parquet',BASE/'full/analysis/id_vs_ood_same_test.parquet'],'Same evaluated IDs from existing matched pairs; mean/std over seedwise ID-OOD (Brier degradation is negative gap)')
        cp=self.sup('derived/source_contribution_per_seed')
        self.contribution=self.save('contribution_full_removed',summary(cp,['target','removed_source','model','representation'],
            [c for c in cp if c.startswith(('full_','removed_','delta_','benefit_')) and c not in ['removed_source']]),[SUP/'derived/source_contribution_per_seed.csv'],
            'Full and removed means on the SAME eligible seeds; delta=full-removed; positive FPR/FNR delta is worse, unlike F1')
        rows=[]
        for key,g in self.contribution.groupby(['model','representation']):
            d=g.delta_f1_mean
            rows.append(dict(zip(['model','representation'],key))|dict(n_conditions=len(g),removal_improved=int((d< -1e-9).sum()),removal_worsened=int((d>1e-9).sum()),
                removal_tied=int((abs(d)<=1e-9).sum()),proportion_improved=float((d< -1e-9).mean()),proportion_worsened=float((d>1e-9).mean()),proportion_tied=float((abs(d)<=1e-9).mean()),experiment_ids=union_ids(g)))
        self.removal_signs=self.save('removal_outcomes',pd.DataFrame(rows),[OUT/'writing_tables/contribution_full_removed.csv'],'Unit=target/source/model/view condition after seed means; tolerance1e-9 numerical tie, NOT equivalence margin')
        sr=[]
        for key,g in self.contribution.groupby(['removed_source','model','representation']):
            d=g.delta_f1_mean
            sr.append(dict(zip(['removed_source','model','representation'],key))|dict(n_targets=len(g),mean_delta_f1=d.mean(),median_delta_f1=d.median(),std_delta_f1=d.std(),
                mean_delta_mcc=g.delta_mcc_mean.mean(),helped=int((d>1e-9).sum()),harmed=int((d< -1e-9).sum()),neutral=int((abs(d)<=1e-9).sum()),experiment_ids=union_ids(g)))
        self.source=self.save('source_rankings',pd.DataFrame(sr),[OUT/'writing_tables/contribution_full_removed.csv'],'Equal eligible target weights; source consistency operationalized as across-target SD and sign counts')
        binary=s[s.kind!='separability'];tc=['threshold_source','threshold_oracle_diagnostic','threshold_drift','test_f1','oracle_f1_diagnostic','oracle_gap_f1','test_pr_auc','test_roc_auc','test_brier','test_ece_10']
        self.thresholds=self.save('thresholds_all_conditions',summary(binary,['kind','target','model','representation','removed_source','training_sources','validation_sources'],tc),
            [BASE/'full/analysis/master_results.parquet'],'Aggregate only identical source composition/condition; source/oracle thresholds per seed retained in copied master')
        self.threshold_model=self.save('thresholds_lodo_macro',summary(self.sup('tables/decision_by_target'),['model','representation'],['threshold_drift_mean','oracle_gap_f1_mean']),
            [SUP/'tables/decision_by_target.csv'],'Mean/median/min/max across target-level seed means, not pooled source-removal counts')
        pairs=self.load(BASE/'full/analysis/raw_vs_canonicalized_pairs.parquet');rows=[]
        for r in pairs.itertuples():
            raw,can=json.loads(r.experiment_ids);a=self.si.loc[raw];b=self.si.loc[can]
            out=dict(kind=r.kind,target=r.target,model=r.model,seed=r.seed,removed_source=r.removed_source,condition=r.condition,
                training_sources=a.training_sources,validation_sources=a.validation_sources,split_id=r.split_id,experiment_ids=r.experiment_ids)
            for met in ['test_'+c for c in MET]+['threshold_drift','oracle_gap_f1','threshold_source','origin_macro_f1','origin_accuracy']:
                out[met+'_raw']=a[met];out[met+'_canonicalized']=b[met];out['delta_'+met]=b[met]-a[met]
            rows.append(out)
        self.canon=self.save('paired_raw_canonicalized_all',pd.DataFrame(rows),[BASE/'full/analysis/raw_vs_canonicalized_pairs.parquet',BASE/'full/analysis/master_results.parquet'],
            'Exact existing paired IDs/split; CAN-RAW; no pooling across ID,LODO,source-removal,origin classifier')
        self.featuretop=self.sup('tables/stable_features')
        self.featuretop=self.featuretop.sort_values(['representation','importance_pct_mean_mean'],ascending=[True,False])
        self.featuretop['global_rank_by_importance']=self.featuretop.groupby('representation').cumcount()+1
        self.save('feature_top10',self.featuretop.groupby('representation',group_keys=False).head(10),[SUP/'tables/stable_features.csv'],'Top10 by existing target-balanced mean importance; average within-run rank is rank_mean_mean; not feature-selection validation')
        # Pairwise rankings retain family-related flag; also expose strict non-related comparison.
        pw=self.old(6,'PAIRWISE/tables/pairwise_results');asym=self.old(6,'PAIRWISE/tables/transfer_asymmetry');rows=[]
        for key,g in pw.groupby(['model','representation']):
            for scope,pool in [('all_pairs',g),('unrelated_only',g[~g.related_source])]:
                for label,r in [('best',pool.loc[pool.f1_mean.idxmax()]),('worst',pool.loc[pool.f1_mean.idxmin()])]:
                    rows.append(dict(model=key[0],representation=key[1],scope=scope,extreme=label,source=r.source,target=r.target_dataset,f1=r.f1_mean,mcc=r.mcc_mean,pr_auc=r.pr_auc_mean,related_source=r.related_source,experiment_ids=r.experiment_ids))
        self.pw_extremes=self.save('pairwise_extremes',pd.DataFrame(rows),[M[6]/'PAIRWISE/tables/pairwise_results.csv'],'Extrema of existing seed means; all pairs and unrelated-only scopes separate')
        self.pw_asym=self.save('pairwise_largest_asymmetry',asym.assign(abs_asymmetry=abs(asym.asymmetry_f1)).sort_values('abs_asymmetry',ascending=False).groupby(['model','representation'],sort=False).head(1),
            [M[6]/'PAIRWISE/tables/transfer_asymmetry.csv'],'Maximum absolute forward-reverse F1 difference per model/view; preserves original experiment IDs')
        self.pw_sources=self.old(6,'PAIRWISE/tables/source_average');self.pw_targets=self.old(6,'PAIRWISE/tables/target_average')
        # Tables of existing origin confusion metrics: only these 30 small JSONs are read, never score arrays.
        confusion=[]
        for r in s[s.kind=='separability'].itertuples():
            d=json.loads(Path(r.original_metric_file).read_text())['metrics_origin'];cm=np.asarray(d['confusion_matrix'])
            for i,origin in enumerate(d['origin_order']):
                for j,pred in enumerate(d['origin_order']):
                    confusion.append(dict(condition=r.condition,representation=r.representation,seed=r.seed,true_origin=origin,predicted_origin=pred,n=int(cm[i,j]),
                        row_fraction=float(cm[i,j]/cm[i].sum()),experiment_ids=json.dumps([r.experiment_id])))
        self.origin_confusion=self.save('origin_confusions',summary(pd.DataFrame(confusion),['condition','representation','true_origin','predicted_origin'],['n','row_fraction']),
            [BASE/'full/analysis/master_results.parquet'],'Extract existing saved confusion matrices from 30 small metric JSONs; seed means of counts/fractions; no classifier execution')

    def card(self,title,values,table,filter_text,ids_json='[]',model='conforme filtro',target='conforme filtro',representation='conforme filtro',seeds='conforme n_seeds/seeds da tabela',
             aggregation='conforme tabela e WRITING_TABLE_TRACEABILITY.csv',source='ORIGINAL_SOURCE_MAPPING.parquet',figure=None,observation='',composition='conforme training_sources/validation_sources nos metrics.json ou master',script='artigo/scripts/analyze_supplemental_results.py',claim=None):
        if Path(table).is_absolute():table=self.copy(table)
        row=dict(finding_id=claim or stable_hash([title,table,filter_text])[:16],statement=title,values=values,table=table,filter=filter_text,
            experiment_ids=ids_json,targets=target,models=model,representation=representation,seeds=seeds,aggregation=aggregation,
            source_composition=composition,original_mapping=source,script=script,command=CMD,figure=figure or 'N/A',observation=observation)
        self.claims.append(row)
        return f'''### {title}

**Resultado:** {title}
**Valor:** {values}
**Target(s):** {target}
**Modelo(s):** {model}
**Representação:** {representation}
**Source composition:** {composition}
**Seeds:** {seeds}
**Agregação:** {aggregation}
**Fonte primária:** `{source}` (colunas originais e cópias; filtrar pelos experiment_ids)
**Tabela consolidada:** `{table}`; filtro/linha: {filter_text}
**Figura:** `{figure or 'N/A — nenhuma figura específica existente'}`
**Script:** `{script}`; comando de compilação editorial: `{CMD}`
**Experiment IDs:** `CLAIM_LEDGER.csv`, finding_id={row['finding_id']}; relação completa na linha/tabela e `ORIGINAL_SOURCE_MAPPING.parquet`.
**Observação:** {observation or 'Resultado descritivo das condições observadas; não extrapolar para outras populações.'}

'''

    def evidence_block(self,title,frame,path,cols,positive,negative,exceptions,safe,unsafe,figure=None,limit=None):
        path=self.copy(path) if Path(path).is_absolute() and not Path(path).is_relative_to(OUT) else str(Path(path).relative_to(OUT)) if Path(path).is_absolute() else str(path)
        return f'''## {title}

{markdown(frame,cols,limit)}

**Tabela principal / valores completos:** `{path}`. Todas as linhas e colunas adicionais estão na cópia, sem seleção de melhor seed.
**Figura principal:** `{figure or 'N/A — não há figura específica já produzida'}`.
**Positivo:** {positive}
**Negativo/nulo:** {negative}
**Exceções:** {exceptions}
**Conclusão segura:** {safe}
**Não concluir:** {unsafe}
**Conferência:** filtro pelas dimensões mostradas e row_id da tabela; experiment_ids → ORIGINAL_SOURCE_MAPPING.parquet → cópia da métrica original. Colunas numéricas são as métricas/unidades nomeadas no cabeçalho; std é entre seeds quando n_seeds é informado, ou entre alvos nas tabelas macro. Fontes/transformações em WRITING_TABLE_TRACEABILITY.csv e TRACEABILITY.csv copiados dos capítulos.

'''

    def executive_and_methods(self):
        counts=self.old(1,'tables/run_counts');coverage=self.old(1,'tables/run_coverage_by_type')
        v=self.valid_h;seeds=sorted(map(int,v.seed.unique()));targets=sorted(v.target_dataset.unique())
        space=pd.DataFrame([dict(protocol='historical',dimension=c,n=v[c].nunique(),values=json.dumps(sorted(v[c].dropna().astype(str).unique())),experiment_ids=json.dumps(v.experiment_id.tolist()))
            for c in ['target_dataset','model','representation','seed','training_datasets','experiment_type']])
        space=self.save('experimental_space',space,[AN/'_global/master_results.parquet'],'Distinct values of usable historical registry; training_datasets is requested composition, not always effective train pool')
        issues=self.load(AN/'_global/metric_integrity_issues.csv');problem_ids=set(issues.experiment_id)
        consistent=self.old(1,'tables/metric_consistency');missing=self.old(1,'tables/missing_runs')
        artifact=self.old(12,'tables/artifact_completeness');ar=[]
        for col in artifact:
            if col.startswith('has_'):ar.append(dict(artifact=col,present=int(artifact[col].sum()),missing=int((~artifact[col]).sum()),experiment_ids=union_ids(artifact)))
        art=self.save('artifact_availability',pd.DataFrame(ar),[M[12]/'tables/artifact_completeness.csv'],'Saved completeness audit counts; feature importance absent for non-applicable models is not a failed training')
        text=['# Respostas completas à solicitação final de escrita','','## 0–2. Escopo, uso e rastreabilidade','',
            'Este é um dossiê de consulta, não o texto do artigo. HISTÓRICO e COMPLEMENTO CONTROLADO são protocolos distintos. Métricas principais de transformação/ID–OOD/contribuição usam o complemento pareado; pairwise, embeddings, ablações e caracterização histórica mantêm seus rótulos e limitações. Não houve novos treinamentos, novas correlações/testes ou recálculo de scores. Tabelas editoriais são filtros, joins e agregações das métricas analíticas existentes.',
            'Arquivos obrigatórios estão na raiz; evidências são cópias reais sob evidence/, não links simbólicos. COPY_MANIFEST.csv permite conferir integridade. Onde não há evidência, aparece SEM RESULTADO CONSOLIDADO NESTE PACOTE. Dados originais grandes permanecem externos, com caminho completo; métricas pequenas, configs e rankings estão copiados.', '',
            '## 3. Resumo executivo', '',markdown(counts,['category','n']),
            f'Histórico: {len(v)} execuções utilizáveis; complemento: {len(self.s)}; total científico em protocolos separados: {len(v)+len(self.s)}. Os 13.170 são somente contribution histórico, não todo o projeto. Os cinco IDs além da grade histórica prevista são três falhas e dois pilotos concluídos. Os 60 SKIPPED estruturais da grade são excluídos, não resultados zero. Fontes: '+self.ref(M[1]/'tables/run_counts.csv')+' e '+self.ref(M[1]/'tables/run_coverage_by_type.csv')+'.',
            'Complemento: 420 ID/LODO + 30 origem + 984 remoções = 1.434 concluídos, sem falhas registradas na execução. Piloto real adicional de quatro fits é separado e excluído do corpus científico. O plano prévio de contribuição era um teto, não contagem exata de fits elegíveis; não chamar a diferença para esse teto de runs faltantes. O full LODO é reutilizado nas remoções. Fontes: '+self.ref(BASE/'full/analysis/AUDIT.json')+', '+self.ref(BASE/'full/PLAN.json')+', '+self.ref(BASE/'sequence/STATE.json')+'.',
            '**Escopo do inventário:** artigo/runs e respectivos registros, não todos os projetos exploratórios anteriores do computador.', '',
            '### 3.2 Espaço experimental', '',markdown(space,['protocol','dimension','n','values']),
            'Datasets caracterizados: oito nomes (inclui artificial). Targets reportáveis: sete; artificial_sqli é a variante usada na grade. artificial e artificial_sqli não são fontes independentes. Origem relacionada: site_cooking/site_sqli compartilham site_lab. Há três modelos detectores; origin_logistic é um classificador auxiliar de origem, não um quarto detector. Representação textual RAW/CANONICALIZED é distinta da família de features lex64/CodeBERT/fusão.',
            'Composições solicitadas não equivalem a composições efetivas: consultar effective_development_datasets no histórico e training_sources/validation_sources no complemento. Listagem completa por run nas duas masters; por condição em writing_tables/thresholds_all_conditions.csv.', '',
            '### 3.3 Arquivos principais','',
            'Registry: '+self.ref(AN/'_global/run_registry.parquet')+'. Master histórica: '+self.ref(AN/'_global/master_results.parquet')+'. Master complementar: '+self.ref(BASE/'full/analysis/master_results.parquet')+'.',
            'Lineages: `ORIGINAL_SOURCE_MAPPING.parquet` reúne as duas; coverage: '+self.ref(AN/'_global/run_coverage.csv')+'. Relatórios: '+self.ref(AN/'FINAL_TCC_RESULTS_GUIDE.md')+' e '+self.ref(SUP/'RESULTS.md')+'. Tabelas/figuras/estatística: evidence/analysis/M04_*/ e evidence/analysis/SUPPLEMENTAL_CONTROLLED_ANALYSIS/{tables,figures,statistics}/; extratos editoriais em writing_tables/.', '',
            '### 3.4 Integridade e problemas','',
            f'Runs históricos esperados faltantes: {len(missing)} na grade auditada. Flags históricas de integridade: {len(issues)} registros em {len(problem_ids)} IDs; {len(problem_ids & set(v.experiment_id))} desses IDs são utilizáveis. Os registros são invalid_metric_file/invalid_manifest por caminhos ausentes em runs excluídos; NÃO são prova de 124 métricas numéricas NaN/Inf. Fonte: '+self.ref(AN/'_global/metric_integrity_issues.csv')+'.',
            f'Concordância de métricas versus confusão salva: {int(consistent["match"].sum())}/{len(consistent)} linhas na auditoria histórica. Missingness por métrica (inclui não aplicáveis): '+self.ref(M[1]/'tables/metric_missingness.csv')+'. Não substituir ausências por zero.',
            markdown(art,['artifact','present','missing']),
            'Ausência de commit e snapshots históricos limita reconstrução exata dos hiperparâmetros históricos; o complemento tem config/hash/snapshot. Ausência de importância em regressão/MLP não implica artefato obrigatório faltante. Seeds/composições elegíveis das remoções podem variar; não inventar combinações para completar grade. Evidência dos controles novos: '+self.ref(SUP/'FINAL_TRACEABILITY_AUDIT.json')+'.', '',
            '## 4. Dataset characterization (Metodologia 4.2)','']
        ds=self.old(2,'tables/dataset_characterization');dt=self.old(2,'tables/dataset_textual_characteristics');can=self.old(4,'tables/canonicalization_effects')
        text += [self.evidence_block('4.1 Valores por dataset e vista',ds,M[2]/'tables/dataset_characterization.csv',
            ['dataset','representation','total_samples','benign_samples','malicious_samples','positive_prevalence','unique_samples','unique_canonical_samples','primary'],
            'Prevalência global controlada nas cópias balanceadas.','Balanceamento não elimina diferenças lexicais/coleta.','Oito nomes caracterizados, sete targets; artificial é auxiliar.',
            'Comparar comprimento/encoding estratificados por classe.','RAW e arquivo decoded histórico como se fossem as mesmas linhas.',self.copy(M[2]/'figures/length_by_class.pdf'))]
        text += ['### 4.2 Comprimento, codificação e léxico por classe','',markdown(dt,['dataset','representation','class','n','length_mean','length_median','length_std','length_p10','length_p90','length_p99','encoding_rate','double_encoding_rate','non_ascii_rate','inline_comment_rate']),
            'Tabela completa inclui presença de select/union/insert/update/delete/drop/or/and, comentários -- e /* */, caracteres especiais e entropia: '+self.ref(M[2]/'tables/dataset_textual_characteristics.csv')+'. Rates são frações de entradas, não percentuais nem contagens de tokens. class=0 benigno; class=1 ataque. Non-ASCII não é uma medida completa de toda normalização Unicode. Uma frequência agregada de “qualquer keyword SQL” não foi salva; NÃO somar presenças sobrepostas. Mediana/desvio global não devem ser reconstruídos como média das estatísticas de classe.', '',
            '### 4.3 Contrastes e seleção para o texto','']
        primary=ds[ds.primary & ds.representation.eq('RAW')]
        for label,idx in [('Maior dataset primário RAW',primary.total_samples.idxmax()),('Menor dataset primário RAW',primary.total_samples.idxmin())]:
            r=primary.loc[idx];text.append(f'{label}: {r.dataset}, n={r.total_samples}; fonte dataset_characterization.csv, row_id={r.row_id}.')
        raw=dt[dt.representation.eq('RAW') & dt.dataset.isin(primary.dataset)]
        for col,label in [('length_mean','Maior comprimento médio de uma classe'),('encoding_rate','Maior encoding rate de uma classe'),('double_encoding_rate','Maior double-encoding rate'),('non_ascii_rate','Maior non-ASCII rate')]:
            r=raw.loc[raw[col].idxmax()];text.append(f'{label}: {r.dataset}, class={r["class"]}, {col}={r[col]:.6f}; dataset_textual_characteristics.csv, row_id={r.row_id}.')
        text += ['Não há um ranking validado de “dataset lexicalmente mais distinto” em uma única métrica. Distinções benignas e maliciosas devem ser discutidas pelas distribuições de cada classe; consultar selected_class_controlled_lexical_differences.csv.','Para o texto: número de targets, prevalência global, maior e menor n e um contraste de encoding; os demais percentis/rates por classe ficam na tabela/suplemento. Fontes acima, sem inventar medidas ausentes.','',
            '## 5. Audit, duplicates and leakage (Metodologia 4.3)','']
        dup=self.old(3,'tables/duplicate_audit');over=self.old(3,'tables/cross_dataset_overlap');labels=self.old(3,'tables/label_conflicts')
        text += [markdown(dup[dup.normalization.isin(['exact','canonical'])],['dataset','representation','normalization','n','unique','duplicate_excess','duplicate_rows_all','label_conflict_keys']),
            'Intra-dataset: duplicate_excess=n−unique (linhas excedentes); duplicate_rows_all conta todas as ocorrências das chaves repetidas. Não confundir as duas medidas. Tabela com lowercase e whitespace separadamente: '+self.ref(M[3]/'tables/duplicate_audit.csv')+'.',
            'Inter-dataset: tabela completa por par RAW/CANONICALIZED: '+self.ref(M[3]/'tables/cross_dataset_overlap.csv')+'. Somar overlaps de pares produz INCIDÊNCIAS POR PAR, não número global de payloads distintos compartilhados. O total global de chaves compartilhadas distintas não foi consolidado: SEM RESULTADO CONSOLIDADO NESTE PACOTE; não inventar por soma.',
            markdown(over.sort_values('canonical_overlap',ascending=False).head(10),['representation','a','b','exact_overlap','canonical_overlap','decoded_hash_overlap']),
            'Conflitos de rótulos: '+self.ref(M[3]/'tables/label_conflicts.csv')+'. Duplicatas criadas apenas ao decodificar as MESMAS linhas RAW: '+self.ref(M[4]/'tables/canonicalization_effects.csv')+'. Esse escopo não é o mesmo que comparar dois arquivos de tamanhos distintos.', '',
            '### 5.2 Antes/depois','',
            'O antes/depois correto da preparação depende do fold. Não existe um único n removido por dataset válido para todos os alvos. A tabela '+self.ref(M[3]/'tables/before_after_audit.csv')+' fornece before_development, after_development, removed_target_overlap, removed_label_conflicts, removed_same_family e preserved_target_n por run. No ID, diferença inclui teste retido; não chamar toda a diferença de remoção. Percentual por fold, quando necessário: 100×(before_development−after_development)/before_development, respeitando essa limitação. Um total global de exemplos eliminados sem dupla contagem entre folds: SEM RESULTADO CONSOLIDADO NESTE PACOTE.',
            'No complemento, as linhas RAW/CAN pareadas são mantidas na coorte; remoções ocorrem nas partições de desenvolvimento. Caracterização do cache: '+self.ref(SUP/'tables/paired_dataset_characterization.csv')+'. Origem balanceada tem seleção intencional separada, não “limpeza” do detector.', '',
            '### 5.3 Leakage — resposta explícita','',
            '**Leakage detected: NO, nas verificações efetivamente executadas.** A auditoria dos 16.650 manifests históricos terminou sem critical issues. Evidência: '+self.ref(BASE/'existing_analysis/split_audit/SUMMARY.json')+' e registros por ID copiados em evidence/project/complementos_generalizacao_v1/existing_analysis/split_audit/.',
            'Training OOD: alvo ausente e hashes entre partições disjuntos nos manifests. Scaler/imputer: fit somente no treino segundo código. Feature selection: grupos predefinidos, sem seletor ajustado no target. Hyperparameter/model selection: parâmetros fixos; early stopping em validação fonte. Threshold: validação fonte. Calibration: não há calibrador ajustado, apenas diagnósticos Brier/ECE. Resampling: não há subamostragem silenciosa nos fits completos; balanceamento do classificador de origem é declarado. Oracle usa rótulos do teste somente depois, como diagnóstico. Fonte por run: '+self.ref(M[3]/'tables/leakage_checks.csv')+' e scripts copiados.',
            '**Limite:** auditoria de manifests + inspeção de código não é prova independente de todos os arrays internos de cada processo histórico. Ausência universal de leakage/near-duplicates semânticas: SEM RESULTADO CONSOLIDADO NESTE PACOTE. Fatos para o artigo: cobertura auditada, zero flags nos controles executados, isolamento fonte/alvo, política de conflitos e limite de escopo.','',
            '## 6. Input and feature representations (Metodologia 4.4)','']
        reps=self.old(4,'tables/representations');embed=self.old(4,'tables/embedding_metadata')
        text += [markdown(reps,['representation','feature_set','dimensions','n_runs']),
            'RAW: loader remove sufixo HTTP/1.x, extrai path/query/fragment de URL e concatena body; portanto não é byte-a-byte do CSV. Histórico CANONICALIZED: arquivo decoded separado + unquote_plus recursivo até dez passagens. Novo complemento: mesmas linhas RAW e decodificação recursiva em text, URL e body. Casefold/whitespace formam a chave canônica de isolamento; não se deve afirmar que todo texto do encoder recebeu essas operações. Features lexicais aplicam lower e enc_pct/path_depth consultam URL/body. Fonte real: scripts copiados src/data/loader.py, src/features/lexical.py e scripts/supplemental/common.py.',
            markdown(can,['dataset','n','changed_n','changed_fraction','length_before','length_after','encoding_before','encoding_after','duplicates_created']),
            'Os números acima são o efeito de decodificar as MESMAS linhas RAW, não redução entre arquivos históricos. Mudança de tokens específica por padrão não foi consolidada: SEM RESULTADO CONSOLIDADO NESTE PACOTE. Grupos interpretáveis: 22 contagens de caracteres, 19 palavras SQL + dois comentários, 14 padrões XSS, sete medidas gerais/estruturais (comprimento, profundidade, proporções, encoding, traversal, entropia). Nem todo campo chamado “lexical” é semântico de SQL. Lista exata: '+self.ref(M[4]/'tables/engineered_features.csv')+'.',
            'CodeBERT congelado: microsoft/codebert-base, revisão 3b0952feddeffad0063f274080e3c23d75e7eb39, max_length=256, pooling CLS, batch=8; 768 dimensões. Fusão lexical+embedding=832. Aplicados no corpus decoded histórico, não no novo pareamento. Dimensões densas não recebem interpretação semântica de feature stability.',
            markdown(embed,['dataset','n','dimensions','truncated_n','truncated_fraction','elapsed_seconds','peak_vram_mib']),
            'Fonte de truncamento/config por cache: '+self.ref(M[4]/'tables/embedding_metadata.csv')+'. O grupo sql21 existe como opção de código, mas não aparece como condição reportável separada nesta grade; não inventar execução.','',
            '## 7. Models and training (Metodologia 4.5)','']
        hp=self.old(5,'tables/model_hyperparameters');runs=self.old(5,'tables/model_run_counts');runtime=self.old(5,'tables/model_runtime')
        text += [markdown(hp,['model','parameter','value','historical_snapshot']),
            'Logística (linear), CatBoost CPU (árvores boosted), MLP tabular sklearn (64,32). Hiperparâmetros da tabela refletem config/código histórico, sem snapshot imutável para todos os fits antigos; no complemento estão preservados nos metrics.json e source_snapshots. Early stopping não é busca de hiperparâmetros. Não houve nested source-aware tuning; selected_iterations é iteração escolhida pela validação fonte.',
            'Treino: imputer mediana e StandardScaler ajustados no treino. Parâmetros sklearn não explicitados no config seguem defaults da versão instalada; versão histórica ausente em parte dos registros não deve ser inventada. Config completa nova está copiada por run.',
            'Modelos principais: os três, por cobrirem famílias distintas e a mesma grade lexical pareada. CodeBERT/fusão são representações secundárias do histórico; origin_logistic é diagnóstico de dataset, não competidor SQLi. Não escolher os modelos principais só por vencerem F1.',
            'Contagens/seeds por modelo/representação: '+self.ref(M[5]/'tables/model_run_counts.csv')+'. Runtime histórico: '+self.ref(M[5]/'tables/model_runtime.csv')+'. Runtime novo: '+self.ref(SUP/'tables/runtime_summary.csv')+'. Seeds previstas: '+str(seeds)+'. Não há lacunas da grade histórica além das exclusões estruturais/falhas já reconciliadas. Falhas por modelo: coverage_by_model.csv; não atribuir as falhas de pilotos a uma condição utilizável concluída.',
            markdown(runs,['model','representation','n_runs','n_seeds']),
            'Runtime histórico por protocolo/modelo/representação, em segundos (médias por execução; não duração cronológica da campanha):',
            markdown(runtime,['experiment_type','model','representation','n_runs','runtime_mean','training_seconds_mean','inference_seconds_mean']),
            'No complemento, cada detector concluiu 140 fits ID/LODO + 328 remoções; o auxiliar de origem concluiu 30. Evidência: '+self.ref(SUP/'tables/coverage.csv')+'. Execução sequencial CPU, até duas threads, sem fine-tuning novo.','']
        self.response='\n'.join(text)

    def rq1(self):
        text=['## 8. RQ1 — cross-dataset generalization','',
            '### 8.1 ID','',
            'Tabela completa mean/std/median/min/max para cada dataset×modelo×vista: `writing_tables/id_controlled.csv`. Valores novos com 5 seeds; o ID histórico separado está em '+self.ref(M[6]/'ID/tables/id_results.csv')+'. Não somar os dois protocolos.',
            markdown(self.id,['target','model','representation','n_seeds','test_precision_mean','test_recall_mean','test_f1_mean','test_f1_std','test_pr_auc_mean','test_mcc_mean','test_fpr_mean','test_fnr_mean']),
            'ROC-AUC e balanced accuracy mean/std estão nas colunas adicionais da mesma tabela. Ranking ID por alvo/vista e métrica, sem escolher seed:','']
        winners=[]
        for key,g in self.id.groupby(['target','representation']):
            for metric in ['test_f1_mean','test_mcc_mean']:
                best=g.loc[g[metric].idxmax()];winners.append(dict(target=key[0],representation=key[1],metric=metric,model=best.model,value=best[metric],experiment_ids=union_ids(g)))
        w=self.save('id_winners',pd.DataFrame(winners),[OUT/'writing_tables/id_controlled.csv'],'Highest condition seed mean; other models preserved in ID table; ties must be inspected in source precision')
        text += [markdown(w,['target','representation','metric','model','value']),
            'Mais fácil/difícil ID depende do modelo/vista:','']
        for key,g in self.id.groupby(['model','representation']):
            hi=g.loc[g.test_f1_mean.idxmax()];lo=g.loc[g.test_f1_mean.idxmin()]
            text.append(f'{key}: maior {hi.target} F1={hi.test_f1_mean:.6f}; menor {lo.target} F1={lo.test_f1_mean:.6f}. writing_tables/id_controlled.csv, filtros acima.')
        text += ['Significância de RAW vs CAN especificamente no ID novo: NÃO há teste de hipóteses executado para esse contraste; SEM RESULTADO CONSOLIDADO NESTE PACOTE para alegação de significância. Diferenças descritivas por seed estão em writing_tables/paired_raw_canonicalized_all.csv (kind=id). Não importar o p de LODO para ID.', '',
            '### 8.2 Pairwise — histórico, separado do complemento','',markdown(self.pw_extremes,['model','representation','scope','extreme','source','target','f1','mcc','pr_auc','related_source']),
            '**Tabela principal:** writing_tables/pairwise_extremes.csv; dados integrais: '+self.ref(M[6]/'PAIRWISE/tables/pairwise_results.csv')+'.',
            'Maiores assimetrias por modelo/vista:',markdown(self.pw_asym,['source','target','model','representation','forward_f1','reverse_f1','asymmetry_f1','related_source']),
            'Matrizes existentes F1/MCC/AP/Recall/FPR/FNR: evidence/analysis/'+str(M[6].name)+'/PAIRWISE/tables/matrix_{f1,mcc,pr_auc,recall,fpr,fnr}.csv. Todas as direções e assimetrias permanecem nos arquivos, não só extremos.', '',
            'Fontes e alvos médios, histórico pairwise (inclui pares relacionados conforme protocolo):','']
        rankings=[]
        for scope,frame,entity in [('source',self.pw_sources,'source'),('target',self.pw_targets,'target_dataset')]:
            for key,g in frame.groupby(['model','representation']):
                for rank,index in [('best',g.f1_mean_mean.idxmax()),('worst',g.f1_mean_mean.idxmin())]:
                    r=g.loc[index];rankings.append(dict(scope=scope,model=key[0],representation=key[1],rank=rank,dataset=r[entity],f1=r.f1_mean_mean,experiment_ids=r.experiment_ids))
        rr=self.save('pairwise_source_target_extremes',pd.DataFrame(rankings),[M[6]/'PAIRWISE/tables/source_average.csv',M[6]/'PAIRWISE/tables/target_average.csv'],'Extrema of existing unweighted averages over peers; includes related-source pairs from historical protocol')
        text += [markdown(rr,['scope','model','representation','rank','dataset','f1']),
            'Positivo: existem transferências altas entre fontes distintas. Negativo: grandes assimetrias e direções fracas. Exceção: site_cooking↔site_sqli é relacionado e não prova transferência entre fontes independentes. Não comparar macro pairwise ao LODO como efeito isolado de quantidade de dados; treinamentos e validações são diferentes.', '',
            '### 8.3 LODO — resultado controlado principal', '',
            markdown(self.lodo,['target','model','representation','n_seeds','test_f1_mean','test_f1_std','test_mcc_mean','test_pr_auc_mean','test_recall_mean','test_precision_mean','test_fpr_mean','test_fnr_mean']),
            'Tabela principal: '+self.ref(SUP/'tables/lodo_by_target.csv')+'. Todos os std estão nas colunas de cada métrica. Todos os runs, sem escolher melhor seed: '+self.ref(SUP/'tables/lodo_per_run.csv')+'.',
            'Gap F1/MCC/AP no MESMO teste: `writing_tables/same_test_gaps.csv`, colunas {f1,mcc,pr_auc}_{id,ood,gap}_{mean,std,...}. No LODO principal a métrica usa arquivo-alvo completo; o gap usa o holdout comum. Não subtrair F1_ID do F1 completo do alvo.',
            markdown(self.gaps,['target','model','representation','n_seeds','f1_id_mean','f1_ood_mean','f1_gap_mean','mcc_gap_mean','pr_auc_gap_mean']),
            'Macro de desempenho OOD (mesmo conjunto de sete alvos):',markdown(self.macro,['model','representation','test_f1_mean_mean','test_f1_mean_median','test_f1_mean_std','test_f1_mean_min','test_mcc_mean_mean','test_pr_auc_mean_mean','test_recall_mean_mean','test_fpr_mean_mean']),
            '**Macro gap:** '+self.ref(SUP/'tables/generalization_gap_macro.csv')+'. Fonte dos valores acima: writing_tables/lodo_macro_complete.csv; média igual por alvo após seeds. Dispersão macro é entre alvos, não IC nem dispersão das seeds.', '',
            '### 8.4 Resposta numérica da RQ1','']
        for rep,g in self.macro.groupby('representation'):
            g=g.sort_values('test_f1_mean_mean',ascending=False)
            text.append(rep+': ordenação descritiva '+', '.join(f'{r.model} F1={r.test_f1_mean_mean:.6f}' for r in g.itertuples())+'. Não prova todas as diferenças entre modelos: ver post-hoc copiado.')
        for key,g in self.lodo.groupby(['model','representation']):
            hi=g.loc[g.test_f1_mean.idxmax()];lo=g.loc[g.test_f1_mean.idxmin()]
            text.append(f'{key}: melhor target={hi.target}, F1={hi.test_f1_mean:.6f}; pior={lo.target}, F1={lo.test_f1_mean:.6f}. Fonte lodo_by_target.csv, filtros target/model/representation.')
        lo=self.gaps.loc[self.gaps.f1_gap_mean.idxmin()];hi=self.gaps.loc[self.gaps.f1_gap_mean.idxmax()]
        text += [f'Menor gap F1={lo.f1_gap_mean:.6f} ({lo.target}/{lo.model}/{lo.representation}); maior={hi.f1_gap_mean:.6f} ({hi.target}/{hi.model}/{hi.representation}). Fonte writing_tables/same_test_gaps.csv.',
            '**Resposta:** os detectores transferem desempenho, mas com heterogeneidade por alvo e modelo e perda versus ID no mesmo teste. RAW/CAN controlados mudam essa transferência. Melhor macro não esconde o pior alvo. Boa generalização é evidenciada pelas condições OOD altas; má generalização pelos gaps e mínimos acima. Não há prova universal ou causal. Tabelas de embedding/fusão históricas estão copiadas, mas não devem receber conclusões do novo pareamento lexical.',
            '**Figuras principais:** evidence/analysis/SUPPLEMENTAL_CONTROLLED_ANALYSIS/figures/lodo_by_target.pdf e id_ood_common_test_gap.pdf. Pairwise: figuras já existentes no capítulo histórico RQ1. **Negativo/nulo:** diferenças de modelos nem todas passam o post-hoc e gap agregado não passa Holm na família examinada; ver estatística.','']
        self.response+='\n'+'\n'.join(text)

    def rq2_decision(self):
        c=self.contribution;negative=c.sort_values('delta_f1_mean').head(10);positive=c.sort_values('delta_f1_mean',ascending=False).head(10)
        self.save('top10_negative_transfer',negative,[OUT/'writing_tables/contribution_full_removed.csv'],'Lowest seed-mean full-minus-removed F1; all eligible seeds, not best seed')
        self.save('top10_positive_transfer',positive,[OUT/'writing_tables/contribution_full_removed.csv'],'Largest seed-mean full-minus-removed F1')
        text=['## 9. RQ2 — contribuição das fontes','',
            'Todos os valores full/removed/delta por target×source×modelo×vista estão em `writing_tables/contribution_full_removed.csv`: F1, MCC, AP, Recall, FPR, FNR e demais métricas, com mean/std/mediana/min/max e n_seeds. Full e removed são resumidos SOMENTE nas mesmas seeds elegíveis daquela remoção. Não usar o full de cinco seeds contra removed de três.',
            '### 9.1 Por fonte','',markdown(self.source,['removed_source','model','representation','n_targets','mean_delta_f1','median_delta_f1','mean_delta_mcc','helped','harmed','neutral','std_delta_f1']),
            'Tabela: writing_tables/source_rankings.csv. Útil/menos útil: maior/menor mean_delta_f1 dentro de modelo/vista; prejudicial frequente: maior harmed; consistência: menor std_delta_f1 (não garante benefício); dependência do alvo: maior std_delta_f1. Não produzir ranking universal misturando modelos.','']
        for key,g in self.source.groupby(['model','representation']):
            useful=g.loc[g.mean_delta_f1.idxmax()];bad=g.loc[g.mean_delta_f1.idxmin()];harm=g.loc[g.harmed.idxmax()];stable=g.loc[g.std_delta_f1.idxmin()];variable=g.loc[g.std_delta_f1.idxmax()]
            text.append(f'{key}: mais útil {useful.removed_source} ({useful.mean_delta_f1:+.6f}); menos útil {bad.removed_source} ({bad.mean_delta_f1:+.6f}); maior harmed {harm.removed_source} ({harm.harmed}/{harm.n_targets}); menor SD {stable.removed_source} ({stable.std_delta_f1:.6f}); maior SD {variable.removed_source} ({variable.std_delta_f1:.6f}). Empates visíveis na tabela; não afirmar desempate estatístico.')
        cols=['target','removed_source','model','representation','n_seeds','full_f1_mean','removed_f1_mean','delta_f1_mean','full_mcc_mean','removed_mcc_mean','delta_mcc_mean']
        text+=['','### 9.2 Dez maiores casos negativos',markdown(negative,cols),'','### 9.3 Dez maiores casos positivos',markdown(positive,cols),
            'Fontes: writing_tables/top10_negative_transfer.csv e top10_positive_transfer.csv; arquivos completos mantêm AP/Recall/FPR/FNR.', '',
            '### 9.4 Resposta quantitativa',markdown(self.removal_signs,['model','representation','n_conditions','removal_improved','removal_worsened','removal_tied','proportion_improved','proportion_worsened','proportion_tied']),
            'Unidade: condição alvo/fonte/modelo/vista após média das seeds; não são alvos independentes. tolerance=1e-9 é empate numérico, não equivalência prática. Tabela writing_tables/removal_outcomes.csv.',
            '**Conclusão:** adicionar fontes não melhora consistentemente toda condição. Positivos e negativos coexistem com validação/teste fixos. **Negativo/nulo:** testes globais por fonte não passaram Holm; efeitos locais não autorizam declarar uma fonte universalmente nociva. **Exceção:** fonte reservada à validação não é removível. **Limite:** tamanho do treino muda; não isola efeito de diversidade mantendo N constante. Figura: evidence/analysis/SUPPLEMENTAL_CONTROLLED_ANALYSIS/figures/source_contribution.pdf.', '',
            '## 10. RQ3 — decision behavior','',
            '### 10.1 Thresholds por condição e composição','',
            'Tabela completa: writing_tables/thresholds_all_conditions.csv; original por seed: evidence/project/complementos_generalizacao_v1/full/analysis/master_results.parquet. Inclui target/model/view/composição de treino e validação, t_source/t_oracle, drift, F1 source/oracle e oracle gap, mean/std/median/min/max. Se a composição de validação muda entre seeds, ela é uma condição distinta nessa tabela. Resumo LODO por target: '+self.ref(SUP/'tables/decision_by_target.csv')+'. Macro entre alvos:',
            markdown(self.threshold_model,['model','representation','threshold_drift_mean_mean','threshold_drift_mean_median','threshold_drift_mean_min','threshold_drift_mean_max','oracle_gap_f1_mean_mean','oracle_gap_f1_mean_median','oracle_gap_f1_mean_min','oracle_gap_f1_mean_max']),
            '### 10.2 Dez maiores falhas — condições resumidas, não melhor seed','']
        dec=self.sup('tables/decision_by_target');self.decision=dec
        for met in ['threshold_drift_mean','oracle_gap_f1_mean']:
            top=dec.sort_values(met,ascending=False).head(10);self.save('top10_'+met,top,[SUP/'tables/decision_by_target.csv'],'Sort LODO target/model/view seed means; original score paths via IDs in mapping')
            text+=[markdown(top,['target','model','representation','n_seeds','test_f1_mean','oracle_f1_diagnostic_mean','oracle_gap_f1_mean','threshold_drift_mean','test_pr_auc_mean','test_roc_auc_mean']),
                'Score files: coluna prediction_file em ORIGINAL_SOURCE_MAPPING.parquet, filtrando experiment_ids das linhas acima. São scores source-validation e target; não foram copiados os arquivos grandes nem abertos indiscriminadamente neste empacotamento.']
        high=dec[(dec.test_pr_auc_mean>=.85)&(dec.oracle_gap_f1_mean>=.10)].sort_values('oracle_gap_f1_mean',ascending=False)
        low=dec[(dec.test_pr_auc_mean<.8)&(dec.test_f1_mean<.75)&(dec.oracle_f1_diagnostic_mean<.8)]
        self.save('diagnostic_high_ranking_threshold_failure',high,[SUP/'tables/decision_by_target.csv'],'Editorial descriptive filter AP>=.85 and oracle F1 recovery>=.10; not preregistered test')
        self.save('diagnostic_low_discrimination',low,[SUP/'tables/decision_by_target.csv'],'Editorial descriptive filter AP<.8, F1source<.75, F1oracle<.8; no new metric')
        text+=['### 10.3 Discriminação versus decisão','Filtro editorial explícito: AP≥0,85 e oracle gap≥0,10 (não teste estatístico):',
            markdown(high,['target','model','representation','test_pr_auc_mean','test_roc_auc_mean','test_f1_mean','oracle_f1_diagnostic_mean','oracle_gap_f1_mean']),
            'Baixa discriminação: AP<0,8, F1 source<0,75 e F1 oracle<0,8; não rebatizar casos fora desses limites:',
            markdown(low,['target','model','representation','test_pr_auc_mean','test_f1_mean','oracle_f1_diagnostic_mean']),
            '**Seguro:** parte da perda pode ocorrer na transferência da decisão; oracle mostra potencial diagnóstico, não desempenho operacional atingível sem labels do target.', '',
            '### 10.4 Scores e casos dirigidos','']
        cases=self.sup('selected_runs/cases');scores=self.sup('tables/selected_score_distributions')
        text += [markdown(cases,['criterion','target','model','representation','seed','selection_value','selection_unit']),
            'Todos os mean/median benign/malicious por validação fonte e teste alvo estão em '+self.ref(SUP/'tables/selected_score_distributions.csv')+' (role, label, experiment_ids). Histograma por bin: '+self.ref(SUP/'derived/selected_score_histograms.csv')+'. Medida numérica única de overlap de distribuições: SEM RESULTADO CONSOLIDADO NESTE PACOTE, não foi calculada. Exemplo de figura: figures/selected_score_shift.pdf no complemento.',
            '### 10.5 Calibração','',
            'Métricas: Brier score e ECE de dez bins. Não foi ajustado um calibrador. ID/OOD no mesmo teste: writing_tables/same_test_gaps.csv, brier_{id,ood,gap}_mean e ece_10_{id,ood,gap}_mean. Degradação OOD−ID é o negativo do gap dessa tabela.',
            markdown(self.gaps,['target','model','representation','brier_id_mean','brier_ood_mean','brier_gap_mean','ece_10_id_mean','ece_10_ood_mean','ece_10_gap_mean']),
            'RAW/CAN por run: writing_tables/paired_raw_canonicalized_all.csv, delta_test_brier/delta_test_ece_10. Full/removed: writing_tables/contribution_full_removed.csv, full/removed/delta_brier e ece_10. Comparações históricas estão separadas em M04_08/tables/calibration_id_vs_ood.csv; não usá-las como teste idêntico.', '',
            '### 10.6 Resposta científica','A composição das fontes altera threshold, métricas de erro e, nos casos selecionados, distribuições dos scores; o detector não perde apenas ranking. Os dez casos de maior oracle gap acima são os exemplos numéricos principais. Importâncias e scores são diagnósticos: não provar mecanismo causal. Os maiores gaps não devem orientar tuning sobre o próprio teste. Associação oracle gap/F1 tem acoplamento matemático por construção.','']
        for label,metric,direction in [('menor Brier ID','brier_id_mean','min'),('maior degradação Brier OOD','brier_gap_mean','min')]:
            r=self.gaps.loc[self.gaps[metric].idxmin()];text.append(f'{label}: {r.target}/{r.model}/{r.representation}, Brier ID={r.brier_id_mean:.6f}, OOD={r.brier_ood_mean:.6f}, OOD−ID={-r.brier_gap_mean:+.6f}. writing_tables/same_test_gaps.csv, row_id={r.row_id}. É extremo entre condições, não modelo globalmente mais calibrado.')
        self.response+='\n'+'\n'.join(text)

    def features_rq4_statistics(self):
        top=self.frames['feature_top10'];st=self.sup('tables/feature_stability');fe=self.sup('tables/source_removal_feature_effects')
        self.stability=st;self.feature_effects=fe
        unstable=self.featuretop.sort_values('rank_mean_std',ascending=False).head(15)
        effects=fe.assign(abs_importance_drift=abs(fe.delta_importance_pct_mean)).sort_values('abs_importance_drift',ascending=False).head(10)
        self.save('feature_instability_examples',effects,[SUP/'tables/source_removal_feature_effects.csv'],'Largest absolute mean native-importance percentage-point changes; preserve paired performance/rank/threshold deltas')
        stat=self.sup('statistics/tests_holm');self.stat=stat
        oldrel=self.old(11,'statistics/cross_rq_relationships');self.oldrel=oldrel
        text=['## 11. RQ3 — feature stability','',
            'Modelo aplicável: CatBoost com 64 features lexicais interpretáveis. Nenhuma dimensão de embedding é interpretada como característica semântica. Importância nativa normalizada não é SHAP, ganho causal ou percentual de F1.',
            '### 11.1 Top10 e estabilidade de presença',markdown(top,['representation','feature','global_rank_by_importance','importance_pct_mean_mean','rank_mean_mean','top10_mean_mean','rank_mean_std']),
            'Tabela writing_tables/feature_top10.csv; top10_mean_mean é frequência média de presença no top10 (0–1), seeds dentro do alvo e peso igual entre alvos. Rankings completos por target em '+self.ref(SUP/'tables/features_by_target.csv')+'; cada run em '+self.ref(SUP/'derived/feature_importance_per_run.csv')+'.',
            '### 11.2 Correlações de ranks e Top-K',markdown(st,['comparison','representation','n_observations','n_seeds','spearman_mean','spearman_std','kendall_mean','jaccard_top10_mean']),
            'Pares completos target/target e full/removed e RAW/CAN: '+self.ref(SUP/'derived/feature_rank_pairs.csv')+'. Esses pares são dependentes; sua média não cria unidades independentes para um teste. Comparações cross_target incluem pares relacionados site_lab. K=10; empates de rank por média e top10 por nome lexicográfico.',
            '### 11.3–11.4 Mais estáveis/instáveis',
            'Estáveis pela frequência Top10 e rank: ordenar stable_features.csv por top10_mean_mean e rank_mean_mean. Mais variáveis entre alvos pelo SD do rank médio:',
            markdown(unstable,['representation','feature','rank_mean_mean','rank_mean_std','importance_pct_mean_mean','top10_mean_mean']),
            'Os datasets em que aparecem estão em features_by_target.csv. Não dizer que variação de importância, por si só, torna uma feature nociva.',
            '### 11.5 Remoção de fonte e drift: exemplos concretos',markdown(effects,['target','removed_source','representation','feature','n_seeds','delta_importance_pct_mean','delta_rank_mean','delta_f1_mean','delta_mcc_mean','delta_threshold_mean','delta_recall_mean','delta_fpr_mean']),
            'Convenção: todas essas diferenças são FULL−REMOVED. Portanto o efeito de remover é o negativo de cada delta exibido. Ex.: delta_rank negativo significa rank numérico menor (mais importante) no full. Tabela writing_tables/feature_instability_examples.csv.',
            '### 11.6 Relações efetivamente calculadas',markdown(stat[stat.comparison.str.contains('feature instability')],['comparison','n_units','statistic','p_value','p_holm','reason']),
            'Histórico (protocolo antigo; separado):',markdown(oldrel[oldrel.relationship.str.contains('feature_instability')],['relationship','group','n_targets','rho','p_value','p_holm','p_method']),
            'Feature instability vs gap e vs negative transfer estão no histórico; no complemento foi analisada associação com OOD F1 e magnitude absoluta da mudança ao remover. Não renomear magnitude absoluta como transferência negativa com sinal. Nenhum novo p-value foi calculado neste dossiê.',
            '**Resposta:** a composição altera a estrutura de importâncias/ranks; não há suporte estatístico robusto corrigido para afirmar que menor estabilidade necessariamente implica pior OOD. Positivo: estabilidade descritiva maior após canonicalização. Nulo: associações ajustadas não detectáveis. Exceção: top features e efeitos variam por representação/target. Não inferir mecanismo causal.', '',
            '## 12. RQ4 — RAW vs CANONICALIZED','',
            'Pares novos validados: 717 = 105 ID + 105 LODO + 492 remoções + 15 origem. Esses tipos não podem ser misturados numa única taxa de melhoria. Fonte '+self.ref(BASE/'full/analysis/AUDIT.json')+' e writing_tables/paired_raw_canonicalized_all.csv. RAW e CAN têm mesmo split_id e IDs de amostras. Os pares históricos elegíveis são separados na pasta M04_10; não ampliar indevidamente sua cobertura.',
            '### 12.1 Por target/model/composição/seed','Todos os valores RAW/CAN/delta (F1/MCC/AP/Recall/FPR/FNR/Brier/ECE/thresholds) estão em `writing_tables/paired_raw_canonicalized_all.csv`. Colunas training_sources e validation_sources explicitam composição; removed_source e kind diferenciam protocolos. Métricas de origem são N/A para detectores e vice-versa.',
            '### 12.2 Win/tie/loss',markdown(self.sup('tables/canonicalization_win_tie_loss'),['model','improved','neutral','worsened','n_targets']),
            'Unidade alvo/modelo após média pareada das seeds; empate |delta|≤1e-9 é tolerância numérica, não equivalência prática. Vinte ganhos não são vinte fontes independentes.',
            '### 12.3 Macro de F1/MCC/AP',markdown(self.macro,['model','representation','test_f1_mean_mean','test_mcc_mean_mean','test_pr_auc_mean_mean']),
            'Delta macro por modelo = diferença das linhas CAN−RAW, sobre os mesmos sete targets. Tabela writing_tables/lodo_macro_complete.csv; fontes por alvo mantidas. Não usar macro de conjuntos de teste diferentes para afirmar ganho direto.',
            markdown(self.macro_deltas,['model','f1_raw','f1_canonicalized','delta_f1','mcc_raw','mcc_canonicalized','delta_mcc','pr_auc_raw','pr_auc_canonicalized','delta_pr_auc']),
            'Fonte explícita dos deltas: writing_tables/lodo_macro_canonicalization_deltas.csv, com os experiment_ids de ambas as vistas.',
            '### 12.4 Threshold e calibração',markdown(self.threshold_model,['model','representation','threshold_drift_mean_mean','oracle_gap_f1_mean_mean']),
            'Detalhes pareados por seed e target em paired_raw_canonicalized_all.csv e decision_by_target.csv. Brier/ECE full versus source-removed também estão na tabela da RQ2; positivos desses deltas são piores para erro/calibração.',
            '### 12.5 Estabilidade',markdown(st[st.comparison.isin(['cross_target','source_removal'])],['comparison','representation','spearman_mean','kendall_mean','jaccard_top10_mean']),
            'A diferença CAN−RAW dessas médias é descritiva; não há um teste que torne os pares de ranks independentes.', '',
            '## 13. Dataset separability','']
        sep=self.sup('tables/separability');delta=self.sup('tables/separability_paired_deltas');origin=self.sup('tables/separability_by_origin');controls=self.sup('tables/separability_controls')
        self.sep=sep;self.sepd=delta
        text += ['Config real: classificação multiclasse de origem com regressão logística; purge de todas as chaves canônicas compartilhadas entre origens, conflitos e deduplicação; amostragem igual por dataset/classe; mesmos exemplos RAW/CAN. Todas as classes balanceadas, benign-only e malicious-only. Seeds e tamanhos por partição:',
            markdown(controls[['condition','n_per_dataset_class','removed_cross_origin_rows','train_per_origin_class','test_per_origin_class']].drop_duplicates(),['condition','n_per_dataset_class','removed_cross_origin_rows','train_per_origin_class','test_per_origin_class']),
            'Amostragem balanceada é requisito desse diagnóstico, não subamostragem escondida dos detectores. Origem é label apenas aqui, não feature do detector.',
            '### 13.1–13.3 Todas as classes / benignos / maliciosos',markdown(sep,['condition','representation','n_seeds','origin_macro_f1_mean','origin_macro_f1_std','origin_accuracy_mean','origin_chance_accuracy_uniform_mean']),
            'Fonte '+self.ref(SUP/'tables/separability.csv')+'. Chance de accuracy uniforme é 1/7; para macro-F1, é referência assintótica balanceada, não valor exato garantido de uma amostra aleatória finita.',
            '### 13.4 Por origem','']
        for key,g in origin.groupby(['condition','representation']):
            hi=g.loc[g.origin_f1_mean.idxmax()];lo=g.loc[g.origin_f1_mean.idxmin()]
            text.append(f'{key}: mais fácil={hi.target}, F1 origem={hi.origin_f1_mean:.6f}; mais difícil={lo.target}, F1 origem={lo.origin_f1_mean:.6f}. Fontes em separability_by_origin.csv.')
        off=self.origin_confusion[self.origin_confusion.true_origin!=self.origin_confusion.predicted_origin].sort_values('row_fraction_mean',ascending=False).head(12)
        text += [markdown(off,['condition','representation','true_origin','predicted_origin','n_mean','row_fraction_mean']),
            'Matrizes completas: writing_tables/origin_confusions.csv. n_mean é média de contagens entre seeds, pode ser fracionário; row_fraction é fração de exemplos daquela origem prevista como a outra.',
            '### 13.5 Efeito de canonicalização',markdown(delta,['condition','delta_origin_macro_f1_mean','delta_origin_macro_f1_std','delta_origin_accuracy_mean']),
            '### 13.6 Relações com OOD',markdown(stat[stat.comparison.str.contains('origin F1 vs OOD F1')],['comparison','n_units','statistic','p_value','p_holm']),
            'Correlacionou-se F1 por origem no classificador auxiliar com F1 OOD do detector, unidade target. Associações com MCC e gap no novo protocolo e delta separability vs delta OOD: não foram executadas; SEM RESULTADO CONSOLIDADO NESTE PACOTE. Não atribuir p-values de F1 a MCC/gap.',
            '### 13.7 Resposta integrada RQ4','Performance: predominância de ganhos pareados, com exceção MLP/proprio. Separability: diminui, mas continua alta e distante da referência uniforme. Features: maior estabilidade descritiva; thresholds/calibração: efeitos heterogêneos por alvo. Não demonstrado: menor separabilidade causar maior F1. Figura principal: controlled_separability.pdf; performance em canonicalization_effect.pdf. Limitação: fontes de laboratório relacionadas e poucos targets.', '',
            '## 14. Estatística realmente executada','',
            '**Seeds were not treated as independent targets: YES.** Cinco seeds no ID/LODO/origem; remoções elegíveis podem ter menos, exibidas em n_seeds. Resumos têm mean/std/median. Origem usa variação de seed descritiva, não cinco novos domínios.',
            '### 14.2–14.4 Wilcoxon / Friedman / Holm','Tabelas completas de testes novos: '+self.ref(SUP/'statistics/tests_holm.csv')+'; post-hoc: '+self.ref(SUP/'statistics/model_posthoc.csv')+'; sensibilidade de fontes relacionadas: '+self.ref(SUP/'statistics/canonicalization_family_sensitivity.csv')+'. Histórico: '+self.ref(M[11]/'statistics/holm_adjusted.csv')+' e cross_rq_relationships.csv (permutação exata para pequenas amostras). Não somar p-values nem tratar as duas análises como réplicas independentes.',
            markdown(stat[stat.family.isin(['canonicalization','id_ood_gap','model_comparison'])],['family','comparison','test','unit','n_units','statistic','p_value','p_holm','effect_mean']),
            'Todas as famílias e comparações (inclusive as não significativas) estão em FINAL_STATISTICAL_RESULTS.md e writing_tables/statistics_master.csv. Reject = p ajustado <0,05; não aplicável se p ausente. Métrica dos Wilcoxon/Friedman principais novos: F1; Spearman informa o par de métricas no comparison. Não assumir F1 para os testes históricos que especificam MCC/AP.',
            '### 14.5 ICs','Histórico LODO C: intervalos de 95% por bootstrap de médias de targets, primeiro seeds agregadas; percentis 2,5 e 97,5. Fonte '+self.ref(M[11]/'statistics/descriptive_summary.csv')+'; iterações e seed em evidence/project/scripts/analysis/config.json. Não são ICs populacionais confirmatórios de fontes aleatórias. Complemento: nenhum IC foi calculado; std não é IC.',
            '### 14.6 Tamanho de efeito','Deltas brutos de F1/MCC/AP e coeficientes rho foram reportados. Cohen d/rank-biserial/Cliff delta não foram calculados: SEM RESULTADO CONSOLIDADO NESTE PACOTE. Não chamar statistic do Wilcoxon de tamanho de efeito.',
            '### 14.7 Tabela mestre','writing_tables/statistics_master.csv identifica protocolo, família e teste e conserva p/ajuste originais; as cópias de origem continuam sendo a fonte primária dos p-values.', '',
            '## 15. Cross-RQ relationships','']
        crossnew=stat[stat.family=='cross_rq_associations'];count=self.old(11,'statistics/source_count_within_target');self.count=count
        text += [markdown(crossnew,['comparison','n_units','statistic','p_value','p_holm','reason']),
            'Histórico completo: '+self.ref(M[11]/'statistics/cross_rq_relationships.csv')+'. Fonte count vs OOD é apenas rho descritivo, sem p-value por coalizões dependentes:',
            markdown(count,['target_dataset','model','representation','rho','n_effective_pools']),
            'Cobertura das relações solicitadas: source count vs OOD = histórico descritivo; source contribution vs OOD = histórico; feature instability vs OOD = histórico e novo, com agregações distintas; ThresholdDrift vs gap = ambos (teste comum somente no novo); OracleGap vs OOD = ambos; origem/separability vs OOD F1 = novo; Delta separability vs Delta OOD = não executado; canonicalization effect vs threshold drift = diferenças descritivas disponíveis, correlação dedicada não executada. As duas últimas associações inferenciais são SEM RESULTADO CONSOLIDADO NESTE PACOTE.',
            'Direção/magnitude são o sinal/valor de rho nas tabelas; p-values e n ficam na mesma linha. Não transformar ausência de detecção em ausência de relação, nem correlação em causalidade. OracleGap contém −F1_source; registrar acoplamento matemático.', '',
            '## 16. Negative and null findings','Consultar FINAL_NEGATIVE_FINDINGS.md: efeitos contrários, inconsistentes, perdas ao adicionar fonte, casos fracos OOD, sensibilidade a origem relacionada e todas as famílias sem rejeição.', '',
            '## 17–19. Achados, Abstract e Discussion','Top15 e seus números: FINAL_SCIENTIFIC_FINDINGS.md. Sugestões de até cinco resultados quantitativos para Abstract e agrupamento para Discussion estão no mesmo documento. Não é um Abstract pronto.', '',
            '## 20–21. Tabelas e figuras recomendadas','FINAL_TABLES_FOR_PAPER.md e FINAL_FIGURES_FOR_PAPER.md informam finalidade, colunas, linhas, cópia e uso no texto/suplemento.', '',
            '## 22–24. Números e rastreabilidade','FINAL_NUMBERS_FOR_PAPER.md é a seleção curta. FINAL_TRACEABILITY.md e CLAIM_LEDGER.csv ligam achados→valores→tabelas→IDs→originais. COPY_MANIFEST.csv prova integridade das cópias. METRIC_PROVENANCE usa os manifests de cada capítulo, preservados.', '',
            '## 25–27. Limites, decisões humanas e aprovação para escrita','Não houve fit nem rerun das análises. Decidir: margem de equivalência prática (1e-9 é só empate numérico); quais figuras entram no texto; prioridade do protocolo novo versus retrospectivo; se a sensibilidade por família deve ser a inferência principal; como delimitar a contribuição sobre embeddings antigos. Nenhum resultado é garantido universalmente. Itens SEM RESULTADO CONSOLIDADO NESTE PACOTE não entram em FINAL_NUMBERS_FOR_PAPER.md.']
        self.response+='\n'+'\n'.join(text)
        # Stack existing tests without rerunning any tests or changing their correction families.
        pieces=[]
        for protocol,path in [('controlled',SUP/'statistics/tests_holm.csv'),('controlled_posthoc',SUP/'statistics/model_posthoc.csv'),('controlled_family_sensitivity',SUP/'statistics/canonicalization_family_sensitivity.csv'),
                              ('historical',M[11]/'statistics/holm_adjusted.csv'),('historical_relationships',M[11]/'statistics/cross_rq_relationships.csv')]:
            f=self.load(path);f['protocol']=protocol;f['source_table']=self.copy(path);f['source_row_id']=f.get('row_id')
            f['rejected_at_0_05']=f.p_holm.map(lambda x:'NOT_APPLICABLE' if pd.isna(x) else 'YES' if x<.05 else 'NO');pieces.append(f)
        self.statmaster=self.save('statistics_master',pd.concat(pieces,ignore_index=True),[SUP/'statistics/tests_holm.csv',SUP/'statistics/model_posthoc.csv',SUP/'statistics/canonicalization_family_sensitivity.csv',M[11]/'statistics/holm_adjusted.csv',M[11]/'statistics/cross_rq_relationships.csv'],
            'Append with protocol labels; no tests rerun; p-values and original Holm families unchanged; rejection flag p_holm<.05')

    def findings(self):
        self.finding_records=[]
        def add(number,title,values,table,subset,filter_text,model,target,rep,safe,notclaim,support='Descritivo; não causal',figure=None,seeds='5 por condição salvo n_seeds explícito',aggregation='Média das seeds dentro do alvo; depois peso igual por alvo quando macro',script='artigo/scripts/analyze_supplemental_results.py'):
            fid=f'F{number:02d}';path=self.copy(table) if not str(table).startswith('writing_tables/') else str(table)
            result=self.card(title,values,path,filter_text,union_ids(subset) if len(subset) else '[]',model,target,rep,seeds,aggregation,figure=figure,
                observation=safe+' NÃO afirmar: '+notclaim,script=script,claim=fid)
            self.finding_records.append(dict(id=fid,title=title,values=values,table=path,filter=filter_text,models=model,targets=target,representation=rep,
                support=support,figure=figure or 'N/A',safe=safe,notclaim=notclaim,card=result))
        gap=self.sup('tables/generalization_gap_macro');g=gap[gap.model=='catboost'].set_index('representation')
        add(1,'Canonicalização reduz o gap ID–OOD observado no CatBoost',f'RAW gap F1={g.loc["RAW","gap_f1_mean_mean"]:.6f}; CAN={g.loc["CANONICALIZED","gap_f1_mean_mean"]:.6f}',
            SUP/'tables/generalization_gap_macro.csv',g.reset_index(),'model=catboost; representation RAW/CAN','catboost','sete targets','RAW vs CANONICALIZED',
            'Comparação em mesmo holdout por ID/LODO; macro igual por alvo.','Redução do gap prova generalização universal; o gap sozinho também depende de ID.',figure=self.copy(SUP/'figures/id_ood_common_test_gap.pdf'))
        l=self.lodo[self.lodo.representation=='CANONICALIZED'];worst=l.loc[l.test_f1_mean.idxmin()];best=l.loc[l.test_f1_mean.idxmax()]
        add(2,'Desempenho OOD permanece heterogêneo entre alvos/modelos',f'CAN: mínimo F1={worst.test_f1_mean:.6f} ({worst.target}/{worst.model}); máximo={best.test_f1_mean:.6f} ({best.target}/{best.model})',
            SUP/'tables/lodo_by_target.csv',l,'representation=CANONICALIZED; extrema over target/model seed means','logistic,catboost,mlp','sete targets','CANONICALIZED',
            'Os extremos preservam dificuldades locais.','Máximo é desempenho esperado em novo domínio arbitrário.',figure=self.copy(SUP/'figures/lodo_by_target.pdf'))
        wins=self.sup('tables/canonicalization_win_tie_loss');can=self.sup('tables/canonicalization_by_target');bad=can.loc[can.delta_test_f1_mean.idxmin()]
        add(3,'Ganhos de canonicalização são predominantes, não universais',f'{int(wins.improved.sum())}/{int(wins.n_targets.sum())} target/model cells improved; piora {bad.target}/{bad.model} ΔF1={bad.delta_test_f1_mean:+.6f}',
            SUP/'tables/canonicalization_by_target.csv',can,'sign of delta_test_f1_mean; tie tolerance1e-9','logistic,catboost,mlp','sete targets','paired RAW/CAN',
            'Vinte condições positivas e uma negativa, após seed means.','Vinte fontes independentes ou efeito garantido em todos os modelos.',support='Wilcoxon/Holm e sensibilidade em F13',figure=self.copy(SUP/'figures/canonicalization_effect.pdf'))
        neg=self.contribution[self.contribution.delta_f1_mean< -1e-9];pos=self.contribution[self.contribution.delta_f1_mean>1e-9];neutral=self.contribution[abs(self.contribution.delta_f1_mean)<=1e-9]
        add(4,'Adicionar fontes não ajuda toda condição',f'Remoção melhora {len(neg)}/{len(self.contribution)} ({len(neg)/len(self.contribution):.6f}); piora {len(pos)}/{len(self.contribution)}; empate {len(neutral)}',
            'writing_tables/contribution_full_removed.csv',self.contribution,'delta_f1_mean full-minus-removed; ±1e-9','logistic,catboost,mlp','targets/sources elegíveis','RAW/CAN',
            'Contagens de condições após seeds, com validação/teste fixos.','Essas proporções são probabilidades populacionais de uma fonte ajudar.',figure=self.copy(SUP/'figures/source_contribution.pdf'),seeds='2–5 conforme tabela; não completar ausentes')
        for number,subset,title in [(5,neg.sort_values('delta_f1_mean').head(1),'Maior caso de transferência negativa'),(6,pos.sort_values('delta_f1_mean',ascending=False).head(1),'Maior caso de contribuição positiva')]:
            r=subset.iloc[0]
            add(number,title,f'F1 full={r.full_f1_mean:.6f}; removed={r.removed_f1_mean:.6f}; full−removed={r.delta_f1_mean:+.6f}; source={r.removed_source}',
                'writing_tables/contribution_full_removed.csv',subset,f'row_id={r.row_id}',r.model,r.target,r.representation,
                'Mesmo target/validação/teste e mesmas seeds elegíveis.','Essa fonte é universalmente benéfica/nociva; tamanho de treino não foi igualado.',seeds=str(int(r.n_seeds)))
        d=self.decision;r=d.loc[d.oracle_gap_f1_mean.idxmax()]
        add(7,'Falha de threshold pode coexistir com boa discriminação',f'AP={r.test_pr_auc_mean:.6f}; F1 source={r.test_f1_mean:.6f}; oracle={r.oracle_f1_diagnostic_mean:.6f}; gap={r.oracle_gap_f1_mean:.6f}',
            SUP/'tables/decision_by_target.csv',d.loc[[r.name]],f'row_id={r.row_id}',r.model,r.target,r.representation,
            'Oracle mede margem diagnóstica usando rótulos do teste.','F1 oracle é performance operacional obtida sem conhecer o alvo.',figure=self.copy(SUP/'figures/selected_score_shift.pdf'))
        r=d.loc[d.test_pr_auc_mean.idxmin()]
        add(8,'Nem toda perda é resolvida pelo threshold',f'AP={r.test_pr_auc_mean:.6f}; F1 source={r.test_f1_mean:.6f}; F1 oracle={r.oracle_f1_diagnostic_mean:.6f}',
            SUP/'tables/decision_by_target.csv',d.loc[[r.name]],f'row_id={r.row_id}',r.model,r.target,r.representation,
            'Caso de menor AP médio; recuperação oracle ainda deixa desempenho limitado.','O problema é exclusivamente o threshold.')
        st=self.stability[self.stability.comparison=='cross_target'].set_index('representation')
        add(9,'Ranks lexicais apresentam maior estabilidade descritiva após canonicalização',f'Spearman cross-target RAW={st.loc["RAW","spearman_mean"]:.6f}, CAN={st.loc["CANONICALIZED","spearman_mean"]:.6f}; Jaccard10 RAW={st.loc["RAW","jaccard_top10_mean"]:.6f}, CAN={st.loc["CANONICALIZED","jaccard_top10_mean"]:.6f}',
            SUP/'tables/feature_stability.csv',st.reset_index(),'comparison=cross_target','catboost','pares dos sete targets','RAW/CAN',
            'Médias de pares dependentes de rankings; diferença descritiva.','Features invariantes ou mecanismo causal de generalização.',aggregation='Média dos pares de ranks registrados, dependentes; não teste de alvos independentes')
        fe=self.feature_effects;r=fe.loc[abs(fe.delta_importance_pct_mean).idxmax()]
        add(10,'Composição altera fortemente a importância de features específicas',f'{r.feature}: full−removed importance={r.delta_importance_pct_mean:+.6f} pontos percentuais; rank={r.delta_rank_mean:+.6f}; ΔF1={r.delta_f1_mean:+.6f}; source={r.removed_source}',
            SUP/'tables/source_removal_feature_effects.csv',fe.loc[[r.name]],f'row_id={r.row_id}','catboost',r.target,r.representation,
            'Drift de importância coincide com mudança de performance nesse par.','Mudança da feature causou o delta F1.',seeds=str(int(r.n_seeds)))
        ss=self.sep[self.sep.condition=='all'].set_index('representation')
        add(11,'Canonicalização reduz separabilidade, mas origem continua previsível',f'Macro-F1 origem RAW={ss.loc["RAW","origin_macro_f1_mean"]:.6f}; CAN={ss.loc["CANONICALIZED","origin_macro_f1_mean"]:.6f}; accuracy chance={ss.loc["RAW","origin_chance_accuracy_uniform_mean"]:.6f}',
            SUP/'tables/separability.csv',ss.reset_index(),'condition=all','origin_logistic','sete labels de origem','RAW/CAN',
            'Amostras/classes balanceadas e purge compartilhado; chance macro-F1 apenas assintótica.','Origem previsível prova que o detector SQLi usa origem ou explica causalmente OOD.',figure=self.copy(SUP/'figures/controlled_separability.pdf'))
        ft=self.featuretop;raw=ft[ft.representation=='RAW'].iloc[0];ca=ft[ft.representation=='CANONICALIZED'].iloc[0]
        add(12,'Características dominantes dependem da representação',f'RAW top={raw.feature}, importance={raw.importance_pct_mean_mean:.6f}%; CAN top={ca.feature}, importance={ca.importance_pct_mean_mean:.6f}%',
            SUP/'tables/stable_features.csv',ft,'largest importance_pct_mean_mean per representation','catboost','sete targets','RAW/CAN',
            'Importância nativa normalizada, primeiro seeds e depois alvos.','Percentual é ganho de F1 ou melhor feature causal/universal.')
        fam=self.sup('statistics/canonicalization_family_sensitivity');s=self.stat[self.stat.family=='canonicalization']
        add(13,'Inferência depende de reconhecer fontes relacionadas',f'p Holm por arquivos={s.p_holm.min():.6f}–{s.p_holm.max():.6f}; por família={fam.p_holm.min():.6f}–{fam.p_holm.max():.6f}',
            SUP/'statistics/canonicalization_family_sensitivity.csv',fam,'all models; compare tests_holm family=canonicalization','logistic,catboost,mlp','sete arquivos / seis famílias','CAN−RAW',
            'Ganhos observados persistem, mas evidência ajustada fica abaixo do critério de rejeição quando se agrupam origens relacionadas.','Falha em rejeitar prova equivalência, ou p<.05 nos arquivos é confirmação universal.',support='Wilcoxon bilateral, Holm nas três comparações; p>0.05 na sensibilidade')
        c=self.count
        add(14,'Quantidade de fontes tem associação favorável, com exceções',f'Rho positivo em {int((c.rho>0).sum())}/{len(c)} condições; negativo em {int((c.rho<0).sum())}',
            M[11]/'statistics/source_count_within_target.csv',c,'rho across effective pools within target/model/view','logistic,catboost,mlp','sete targets','RAW/CAN histórico',
            'Associação descritiva no protocolo histórico de coalizões efetivas.','Mais fontes causam ganho; validação/tamanho/composição também mudam.',support='Sem p-value: pools de fontes não são observações independentes',script='artigo/scripts/analysis/final_analysis.py')
        cross=self.stat[self.stat.family=='cross_rq_associations'];source=self.stat[self.stat.family=='source_contribution']
        add(15,'Associações entre RQs e utilidade global de fontes não são robustamente detectadas',f'Cross-RQ: {int((cross.p_holm>=.05).sum())}/{len(cross)} sem rejeição após Holm; contribuição por fonte: {int((source.p_holm>=.05).sum())}/{len(source)}',
            SUP/'statistics/tests_holm.csv',pd.concat([cross,source]),'families cross_rq_associations, source_contribution','conforme comparação','alvos disponíveis','RAW/CAN',
            'Preservar nulos e limites de poder/independência.','Ausência de efeito ou relação; casos locais não demonstram ranking universal.',support='P-values ajustados e n por linha; nenhuma relação causal')
        blocks=['# Top 15 Scientific Findings','','Ordem por relevância científica, não somente F1. São sínteses das tabelas existentes; graus de evidência e protocolos explicitados.']
        trace=['# Final Traceability','','Cada Fxx corresponde a uma linha de CLAIM_LEDGER.csv. A coluna experiment_ids pode ser longa; não é omitida do arquivo.']
        for f in self.finding_records:
            blocks += [f'\n## Finding {f["id"]}\n',f'**Statement:** {f["title"]}',f'**Numbers:** {f["values"]}',f'**Targets:** {f["targets"]}',f'**Models:** {f["models"]}',
                f'**Representation:** {f["representation"]}',f'**Statistical support:** {f["support"]}',f'**Main table:** `{f["table"]}`; {f["filter"]}',f'**Main figure:** `{f["figure"]}`',
                f'**Source analytical file:** tabela acima; cadeia de origem em WRITING_TABLE_TRACEABILITY.csv/COPY_MANIFEST.csv',
                '**Original source mapping:** `ORIGINAL_SOURCE_MAPPING.parquet`; IDs em CLAIM_LEDGER.csv',f'**Safe interpretation:** {f["safe"]}',f'**Do NOT claim:** {f["notclaim"]}',
                '\n'+f['card']]
            trace += [f'\n## {f["id"]} — {f["title"]}\n',f'Final values: {f["values"]}',f'Final table / filter: `{f["table"]}`; {f["filter"]}',
                'Analytical source: COPY_MANIFEST.csv original_path/copy_path e WRITING_TABLE_TRACEABILITY.csv (se tabela editorial).',
                f'Experiment IDs: CLAIM_LEDGER.csv, finding_id={f["id"]}; tabela citada também preserva IDs.',
                'Original file mapping: ORIGINAL_SOURCE_MAPPING.parquet; copy_metric_file e copy_feature_importance_file apontam às cópias.',
                'Script/command: na linha correspondente de CLAIM_LEDGER.csv; receita original nos TRACEABILITY.csv copiados. Valores só são permitidos no arquivo curto se a auditoria do pacote aprovar a cadeia.']
        blocks += ['\n## Top Results for Abstract (até cinco; não é um Abstract pronto)\n',
            '1. F01: gap ID/OOD em mesmo teste — usar o modelo/vista explicitamente, sem fingir média de todos os modelos.',
            '2. F03: ganho de canonicalização em condições alvo/modelo, com perda preservada e ressalva de famílias relacionadas.',
            '3. F04: transferência negativa com validação/teste fixos — proporção de condições, não de fontes independentes.',
            '4. F07: um exemplo representativo de discriminação versus threshold; oracle é diagnóstico.',
            '5. F11: origem continua discriminável após canonicalização em protocolo balanceado.',
            '\n## Top Results for Discussion\n',
            'Generalization: F01/F02; desempenho no mesmo domínio não é prova de transferência universal.',
            'Negative transfer: F04/F05/F06/F14; composição importa, quantidade não é garantia.',
            'Threshold/calibration: F07/F08; separar ranking, probabilidades e regra operacional. Calibração quantitativa completa em writing_tables/same_test_gaps.csv.',
            'Feature stability: F09/F10/F12; importância é dependência do modelo, não causalidade.',
            'Canonicalization: F03/F13; ganhos frequentes, exceção real e inferência sensível à independência.',
            'Dataset bias/separability: F11/F15; origem reconhecível não prova mecanismo do detector; correlações inconclusivas não são ausência de relação.']
        self.doc('FINAL_SCIENTIFIC_FINDINGS.md','\n'.join(blocks));self.doc('FINAL_TRACEABILITY.md','\n'.join(trace))

    def other_docs(self):
        stattext=['# Final Statistical Results','','Tabela mestre do pacote: `writing_tables/statistics_master.csv`. Os arquivos originais corrigidos foram copiados e continuam separados por protocolo. Nenhuma hipótese foi testada novamente. Seeds foram resumidas dentro do alvo; não tratadas como targets independentes.',
            '## Complemento: todos os testes, incluindo não significativos',markdown(self.stat,['family','comparison','test','n_units','statistic','p_value','p_holm','effect_mean','reason']),
            '## Post-hoc após omnibus',markdown(self.sup('statistics/model_posthoc'),['representation','model_a','model_b','n_targets','delta_f1_mean','p_value','p_holm','omnibus_p_holm']),
            '## Sensibilidade por família de origem',markdown(self.sup('statistics/canonicalization_family_sensitivity'),['model','n_families','effect_mean','p_value','p_holm']),
            '## Histórico','Todos os Wilcoxon/Friedman/Holm estão em '+self.ref(M[11]/'statistics/holm_adjusted.csv')+'. Todas as correlações exatas/permutacionais: '+self.ref(M[11]/'statistics/cross_rq_relationships.csv')+'. Não substituir o método de p-value histórico pelo aproximado do complemento.',
            '## Confidence intervals','IC95 histórico de LODO C: bootstrap de médias de targets, com seeds já agregadas; limites em descriptive_summary.csv, método/seed/iterações no script/config copiados. Não há novo IC no complemento. A incerteza entre seeds e entre targets são diferentes.',
            markdown(self.old(11,'statistics/descriptive_summary').query('metric == "f1"'),['model','representation','metric','n_targets','mean','std','ci95_low','ci95_high','ci_scope']),
            '## Effect size','Deltas brutos e correlações são efeitos reportados; tamanhos padronizados/rank-biserial não calculados. SEM RESULTADO CONSOLIDADO NESTE PACOTE para qualquer valor desses métodos. Não inferir equivalência de p>0,05.',
            '## Critério e limitações','Reject quando p_holm<0,05 na família original. Origem: seeds apenas descritivas. Poucos alvos relacionados e pools compartilhados limitam inferência. Sem ocultar zeros, sinais contrários, não significativos ou não aplicáveis.']
        self.doc('FINAL_STATISTICAL_RESULTS.md','\n'.join(stattext))
        negative=['# Negative and Null Findings','','## Canonicalização piorou em uma condição LODO',
            markdown(self.sup('tables/canonicalization_by_target').query('delta_test_f1_mean < 0'),['target','model','n_seeds','delta_test_f1_mean','delta_test_mcc_mean','delta_test_pr_auc_mean']),
            'Fonte: evidence/analysis/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/canonicalization_by_target.csv; não esconder perda MLP/proprio.',
            '## Fontes adicionais prejudiciais','Top10 completo em writing_tables/top10_negative_transfer.csv:',markdown(self.frames['top10_negative_transfer'],['target','removed_source','model','representation','full_f1_mean','removed_f1_mean','delta_f1_mean','n_seeds']),
            '## Testes sem rejeição após correção',markdown(self.stat.groupby('family',group_keys=False).apply(lambda g:pd.Series({'n':len(g),'not_rejected':int((g.p_holm>=.05).sum()),'not_applicable':int(g.p_holm.isna().sum())}),include_groups=False).reset_index(),['family','n','not_rejected','not_applicable']),
            'Fonte: statistics/tests_holm.csv do complemento; significância de canonicalização muda sob sensibilidade por família (ver F13). Não chamar esses nulos de prova de ausência de efeito.',
            '## Desempenho OOD limitado e decisão insuficiente',markdown(self.decision.sort_values('test_f1_mean').head(5),['target','model','representation','test_f1_mean','test_pr_auc_mean','oracle_f1_diagnostic_mean']),
            'Fonte: tables/decision_by_target.csv. Nem todo baixo F1 é recuperável por threshold. As falhas ID→OOD podem ser conferidas no teste comum em writing_tables/same_test_gaps.csv.',
            '## Feature stability e separability','Todas as correlações novas desses grupos permanecem em statistics/tests_holm.csv, inclusive as não significativas. Maior estabilidade média e menor separabilidade não demonstram causalidade sobre F1.',
            '## Ausências não são resultados nulos','Sem score-overlap scalar, sem testes dedicados de ID RAW/CAN novo, sem correlação dedicada delta separability vs delta OOD, sem MCC/gap versus separability no complemento. SEM RESULTADO CONSOLIDADO NESTE PACOTE; não relatar como efeito zero.']
        self.doc('FINAL_NEGATIVE_FINDINGS.md','\n'.join(negative))
        ds=self.old(2,'tables/dataset_characterization');num=['# Numbers for Paper','','Somente números com tabelas/linhas e mapping conferíveis; não usar achados SEM RESULTADO CONSOLIDADO NESTE PACOTE. Fxx resolve todos os detalhes em CLAIM_LEDGER.csv. São protocolos distintos, não réplicas independentes.',
            '## Dataset characterization','Targets primários: 7; datasets caracterizados: 8 incluindo artificial auxiliar. Fonte evidence/analysis/'+M[2].name+'/tables/dataset_characterization.csv, distinct dataset e filtro primary=True. Prevalência: 0,5 em cada cópia balanceada; coluna positive_prevalence. Seeds/modelo: não aplicáveis à contagem do dataset.',
            markdown(ds[ds.primary & ds.representation.eq('RAW')],['dataset','total_samples','benign_samples','malicious_samples','unique_samples']),
            '## Experimental coverage','Histórico: 16.710 previstos; 16.715 IDs encontrados; 16.652 COMPLETED; 16.650 utilizáveis; 65 excluídos; 3 FAILED; 0 incompletos. Fonte evidence/analysis/'+M[1].name+'/tables/run_counts.csv, category correspondente. Contribuição histórica: 13.170 utilizáveis.',
            'Complemento: 1.434 runs (210 ID, 210 LODO, 984 remoções, 30 origem). Fonte evidence/analysis/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/coverage.csv, somar n_observations por kind. Total científico em protocolos separados: 18.084; não inclui pilotos. Três detectores, cinco seeds previstas; origem é tarefa auxiliar.',
            '## RQ1']
        for ids_,heading in [(['F01','F02'],None),(['F04','F05','F06','F14'],'RQ2'),(['F07','F08','F09','F10','F12'],'RQ3'),(['F03','F11'],'RQ4'),(['F13','F15'],'Statistics')]:
            if heading:num+=['','## '+heading]
            for f in self.finding_records:
                if f['id'] in ids_:num.append(f'- **{f["id"]}:** {f["values"]}. Contexto: targets={f["targets"]}; models={f["models"]}; representation={f["representation"]}. Tabela `{f["table"]}`; filtro `{f["filter"]}`. Detalhes/seeds/agregação e originais: CLAIM_LEDGER.csv.')
        self.doc('FINAL_NUMBERS_FOR_PAPER.md','\n'.join(num))
        recommendations=[
            ('1','Datasets e classes',M[2]/'tables/dataset_characterization.csv',['dataset','representation','total_samples','benign_samples','malicious_samples','positive_prevalence','unique_samples'],'main; primary=True no texto, artificial no suplemento'),
            ('2','Cobertura e exclusões',M[1]/'tables/run_counts.csv',['category','n'],'main junto de cobertura complementar separada'),
            ('3','F1/MCC/AP LODO por target',SUP/'tables/lodo_by_target.csv',['target','model','representation','n_seeds','test_f1_mean','test_f1_std','test_mcc_mean','test_pr_auc_mean'],'main; outras métricas supplementary'),
            ('4','ID/OOD no mesmo teste',OUT/'writing_tables/same_test_gaps.csv',['target','model','representation','f1_id_mean','f1_ood_mean','f1_gap_mean','mcc_gap_mean','pr_auc_gap_mean'],'main'),
            ('5','Full versus fonte removida',OUT/'writing_tables/contribution_full_removed.csv',['target','removed_source','model','representation','n_seeds','full_f1_mean','removed_f1_mean','delta_f1_mean'],'main top casos; tabela completa supplementary'),
            ('6','Threshold e oracle diagnóstico',SUP/'tables/decision_by_target.csv',['target','model','representation','test_f1_mean','test_pr_auc_mean','oracle_f1_diagnostic_mean','oracle_gap_f1_mean','threshold_drift_mean'],'main casos; completo supplementary'),
            ('7','Features consistentes',OUT/'writing_tables/feature_top10.csv',['representation','feature','importance_pct_mean_mean','rank_mean_mean','top10_mean_mean'],'main; ranks por target supplementary'),
            ('8','Separabilidade balanceada',SUP/'tables/separability.csv',['condition','representation','origin_macro_f1_mean','origin_macro_f1_std','origin_accuracy_mean'],'main'),
            ('9','Testes e sensibilidade',OUT/'writing_tables/statistics_master.csv',['protocol','family','comparison','n_units','p_value','p_holm','rejected_at_0_05'],'main seleção justificada; TODOS no supplementary'),
            ('S1','Pairwise completo',M[6]/'PAIRWISE/tables/pairwise_results.csv',['source','target_dataset','model','representation','f1_mean','mcc_mean','pr_auc_mean','related_source'],'supplementary'),
            ('S2','CodeBERT/fusão histórica',M[6]/'LODO/tables/embedding_and_fusion_results.csv',['target_dataset','model','representation','f1_mean','mcc_mean','pr_auc_mean'],'supplementary; não misturar pareamento novo'),
            ('S3','Ablações históricas',M[9]/'tables/ablation_effects_by_target.csv',['target_dataset','model','representation','feature_set','delta_f1_mean','delta_mcc_mean'],'supplementary'),
            ('S4','Reconstrução numérica',SUP/'tables/reproducibility_audit.csv',['final_table','reported_value','recalculated_value','match'],'supplementary')]
        text=['# Final Tables for Paper',''];self.table_recommendations=[]
        for number,purpose,path,cols,placement in recommendations:
            d=pd.read_csv(path);local=str(path.relative_to(OUT)) if path.is_relative_to(OUT) else self.copy(path)
            present=[c for c in cols if c in d];self.table_recommendations.append(dict(table=number,purpose=purpose,path=local,n_rows=len(d),columns=json.dumps(present),placement=placement))
            text += [f'## Table {number} — {purpose}','',f'Purpose: {purpose}',f'Source CSV: `{local}`; Parquet correspondente quando disponível.',
                     f'Columns: {", ".join(present)}',f'Number of rows in full source: {len(d)}',f'Placement: {placement}',
                     'Cada linha conserva IDs ou source_file; usar legenda com protocolo, média/std das seeds e significado de delta. Não copiar milhares de IDs para o texto.','']
        self.doc('FINAL_TABLES_FOR_PAPER.md','\n'.join(text))
        figs=[('lodo_by_target','Quais alvos são difíceis OOD?','tables/lodo_by_target.csv','Heterogeneidade por alvo/modelo/vista','main'),
            ('id_ood_common_test_gap','Quanto se perde no mesmo teste ao sair do ID?','tables/id_ood_same_test.csv','Gap em populações realmente iguais','main'),
            ('source_contribution','Quais fontes ajudam ou prejudicam cada alvo?','tables/source_contribution_by_target.csv','Sinais não uniformes; cinza significa condição inelegível','main'),
            ('canonicalization_effect','A transformação melhora todos os alvos?','tables/canonicalization_by_target.csv','Ganhos e exceção, pareamento estrito','main'),
            ('controlled_separability','Origem continua distinguível?','tables/separability.csv','Origem previsível apesar de queda; controles de classe/tamanho','main'),
            ('selected_score_shift','Ranking e threshold falham da mesma maneira?','derived/selected_score_histograms.csv','Caso automático representativo; não distribuição de todos os runs','supplementary')]
        text=['# Final Figures for Paper',''];self.figure_recommendations=[]
        for name,question,table,message,placement in figs:
            path=self.copy(SUP/'figures'/(name+'.pdf'));data=self.copy(SUP/table)
            self.figure_recommendations.append(dict(title=name,question=question,path=path,source_data=data,message=message,placement=placement))
            text += [f'## Figure — {name}','',f'Scientific question: {question}',f'Source data: `{data}`',f'Existing file copy: `{path}` (PNG correspondente também copiado)',
                f'Main message: {message}',f'Placement: {placement}','IDs e fonte original: TRACEABILITY.csv do complemento, manifesto da tabela e ORIGINAL_SOURCE_MAPPING.parquet.','']
        text += ['## Figuras históricas adicionais','Heatmaps pairwise e caracterização de comprimentos estão copiados sob evidence/analysis/M04_06.../PAIRWISE/figures e M04_02.../figures. Usar em suplemento identificando protocolo histórico; não trocar legenda para o novo pareamento.']
        self.doc('FINAL_FIGURES_FOR_PAPER.md','\n'.join(text))
        self.doc('FULL_REQUEST_RESPONSE.md',self.response)

    def finish(self):
        pd.DataFrame(self.claims).to_csv(OUT/'CLAIM_LEDGER.csv',index=False)
        pd.DataFrame(self.recipes).to_csv(OUT/'WRITING_TABLE_TRACEABILITY.csv',index=False)
        pd.DataFrame(self.table_recommendations).to_csv(OUT/'RECOMMENDED_TABLES.csv',index=False)
        pd.DataFrame(self.figure_recommendations).to_csv(OUT/'RECOMMENDED_FIGURES.csv',index=False)
        self.doc('README.md','''# Final Evidence Package

Começar por FULL_REQUEST_RESPONSE.md: respostas numeradas à solicitação, com valores e tabelas completas. FINAL_NUMBERS_FOR_PAPER.md é a consulta curta; FINAL_SCIENTIFIC_FINDINGS.md contém Top15, candidatos ao Abstract e agrupamento para Discussion. FINAL_STATISTICAL_RESULTS.md e FINAL_NEGATIVE_FINDINGS.md preservam os limites e os nulos. FINAL_TABLES_FOR_PAPER.md / FINAL_FIGURES_FOR_PAPER.md organizam o material editorial. FINAL_TRACEABILITY.md e CLAIM_LEDGER.csv resolvem cada achado aos originais.

As evidências são cópias reais sob evidence/, com SHA-256 em COPY_MANIFEST.csv. ORIGINAL_SOURCE_MAPPING.parquet inclui os caminhos originais e copy_* para métricas pequenas, manifestações JSON, status e importâncias. NÃO foram copiados checkpoints, datasets brutos, embeddings, grandes splits ou predições. Isso mantém o pacote pequeno sem reabrir o corpus inteiro. Os caminhos externos desses artefatos continuam disponíveis; tabelas de erros/scores dirigidos já calculadas foram copiadas.

Contagens do histórico e complemento não devem ser misturadas sem identificação. O pacote faz filtros/joins/summaries editoriais das tabelas analíticas, não novos fits, testes de hipóteses, bootstrap ou análise dos scores. Itens explicitamente SEM RESULTADO CONSOLIDADO NESTE PACOTE não são resultados nulos.

Regerar o pacote: usar o comando em Data Sources and Traceability. Ele copia e verifica apenas os caminhos analíticos e artefatos pequenos enumerados pelas lineages; não percorre checkpoints/predictions/splits grandes.
''')
        # Verify the chain for every Top15 finding against copied metric artifacts.
        byid=self.mapping.set_index('experiment_id');checks=[]
        for claim in self.claims:
            eids=json.loads(claim['experiment_ids']);unknown=set(eids)-set(byid.index)
            missing=[]
            for eid in eids:
                value=byid.loc[eid].get('copy_metric_file')
                if not isinstance(value,str) or not (OUT/value).is_file():missing.append(eid)
            table=OUT/claim['table'];ok=not unknown and not missing and table.exists() and len(eids)>0
            checks.append(dict(finding_id=claim['finding_id'],verified_for_paper=ok,n_experiment_ids=len(eids),unknown_ids=json.dumps(sorted(unknown)),missing_copied_metrics=json.dumps(missing),table_exists=table.exists()))
        check=pd.DataFrame(checks);check.to_csv(OUT/'CLAIM_VERIFICATION.csv',index=False)
        assert check.verified_for_paper.all(), 'Some claims lack copied original metrics; exclude from short numbers'
        # Independently reconstruct the positive/negative transfer extremes from
        # their copied primary metrics, not from rounded values in the report.
        numerical=[]
        for claim in self.claims:
            if claim['finding_id'] not in ['F05','F06']:continue
            ids=json.loads(claim['experiment_ids'])
            paths=[byid.loc[eid,'copy_metric_file'] for eid in ids]
            runs=[json.loads((OUT/path).read_text()) for path in paths]
            removed=next(r['removed_source'] for r in runs if r['removed_source'])
            frame=self.contribution
            row=frame[(frame.target==runs[0]['target']) & (frame.model==runs[0]['model']) &
                      (frame.representation==runs[0]['representation']) & (frame.removed_source==removed)].iloc[0]
            for metric in ['f1','mcc','pr_auc']:
                full=np.mean([r['metrics_test'][metric] for r in runs if not r['removed_source']])
                rem=np.mean([r['metrics_test'][metric] for r in runs if r['removed_source']])
                for label,value in [('full',full),('removed',rem),('delta',full-rem)]:
                    column=label+'_'+metric+'_mean';reported=float(row[column])
                    match=bool(np.isclose(value,reported,rtol=0,atol=1e-12))
                    numerical.append(dict(finding_id=claim['finding_id'],column=column,reported_value=reported,
                        recalculated_value=value,match=match,row_id=row.row_id,
                        final_table='writing_tables/contribution_full_removed.csv',
                        experiment_ids=json.dumps(ids),copied_primary_metrics=json.dumps(paths)))
        numeric_check=pd.DataFrame(numerical)
        numeric_check.to_csv(OUT/'NUMERICAL_RECONSTRUCTION_AUDIT.csv',index=False)
        assert numeric_check.match.all()
        for name,frame in self.frames.items():
            assert frame.row_id.is_unique
            pd.testing.assert_frame_equal(pd.read_parquet(OUT/'writing_tables'/(name+'.parquet')),frame,check_dtype=False)
        for path in OUT.glob('*.md'):assert '## Data Sources and Traceability' in path.read_text()
        pd.DataFrame(self.copies.values()).to_csv(OUT/'COPY_MANIFEST.csv',index=False)
        audit={'generated_at':now(),'script':str(Path(__file__).resolve()),'script_sha256':sha256(Path(__file__).resolve()),'command':CMD,
            'historical_usable_runs':len(self.valid_h),'supplemental_usable_runs':len(self.s),'total_usable_distinct_protocol_runs':len(self.valid_h)+len(self.s),
            'primary_targets':self.valid_h.target_dataset.nunique(),'detector_models':sorted(self.valid_h.model.unique()),
            'copied_files':len(self.copies),'copied_bytes':sum(r['bytes'] for r in self.copies.values()),'writing_tables':len(self.frames),
            'top_findings_verified':int(check.verified_for_paper.sum()),'new_training_runs':0,'new_hypothesis_tests':0,'large_artifacts_read_or_copied':False,
            'primary_metric_values_reconstructed':len(numeric_check),'primary_metric_values_match':bool(numeric_check.match.all()),
            'all_copy_hashes_match':True,'runtime_seconds':time.perf_counter()-self.start,
            'editorial_operations':'copy/hash verification, filter, sort, join and seed/target summaries from existing analytical tables; extract 30 saved origin confusion JSON matrices',
            'external_large_artifacts':'Original predictions, embeddings, checkpoints, datasets and split CSVs remain outside; paths in mapping',
            'scope':'Copied analytical evidence; not universal causal/generalization claims; NOT VERIFIED flags in response remain excluded from short numbers'}
        atomic_json(OUT/'PACKAGE_AUDIT.json',audit);print(json.dumps(audit,indent=2))


def main():
    package=Package()
    for step in ['copy_evidence','editorial_tables','executive_and_methods','rq1','rq2_decision','features_rq4_statistics','findings','other_docs','finish']:
        print(now(),step,flush=True);getattr(package,step)()


if __name__=='__main__':main()
