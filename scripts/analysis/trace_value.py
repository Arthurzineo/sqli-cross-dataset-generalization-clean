#!/usr/bin/env python3
"""Resolve a final table cell to exact experiment IDs and original source paths."""
import argparse
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--table',required=True,type=Path)
p.add_argument('--row-id',required=True)
p.add_argument('--column',required=True)
a=p.parse_args()
table=pd.read_parquet(a.table) if a.table.suffix=='.parquet' else pd.read_csv(a.table)
row=table.loc[table.row_id==a.row_id]
if len(row)!=1:raise SystemExit('row_id must identify exactly one row')
r=row.iloc[0]
lineage=pd.read_parquet(ROOT/'analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet')
experiment_ids=json.loads(r.experiment_ids)
print(json.dumps({'table':str(a.table.resolve()),'row_id':a.row_id,'column':a.column,
    'reported_value':r[a.column],'source_file':r.source_file,'row_dimensions':json.loads(row.to_json(orient='records'))[0],
    'experiment_ids':experiment_ids,'original_sources':json.loads(lineage[lineage.experiment_id.isin(experiment_ids)].to_json(orient='records'))},ensure_ascii=False,indent=2,default=str))
