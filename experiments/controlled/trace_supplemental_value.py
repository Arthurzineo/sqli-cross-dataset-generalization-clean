#!/usr/bin/env python3
"""Read-only resolution of a supplemental scientific table cell to its sources."""
import argparse
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]/'analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS'


def trace(table_path,row_id,column):
    path=Path(table_path)
    if not path.is_absolute():path=path if path.exists() else ROOT/path
    path=path.resolve()
    if not path.is_relative_to(ROOT.resolve()):raise ValueError('Select a supplemental analysis table, not a historical table')
    frame=pd.read_parquet(path) if path.suffix=='.parquet' else pd.read_csv(path)
    row=frame.loc[frame.row_id.eq(row_id)]
    if len(row)!=1:raise ValueError('row_id must identify exactly one row')
    if column not in row:raise ValueError('Unknown column: '+column)
    values=json.loads(row.to_json(orient='records',double_precision=15))[0]
    eids=json.loads(values['experiment_ids'])
    lineage=pd.read_parquet(ROOT/'SOURCE_FILES.parquet')
    sources=lineage[lineage.experiment_id.isin(eids)]
    if set(sources.experiment_id)!=set(eids):raise ValueError('Incomplete source mapping')
    traceability=pd.read_csv(ROOT/'TRACEABILITY.csv')
    recipe=traceability[traceability.artifact_path.map(lambda p:Path(p).with_suffix(''))==path.with_suffix('')]
    if len(recipe)!=1:raise ValueError('Missing or ambiguous analytical recipe')
    return dict(table=str(path),row_id=row_id,column=column,reported_value=values[column],row_dimensions=values,
                experiment_ids=eids,original_sources=json.loads(sources.to_json(orient='records')),
                recipe=json.loads(recipe.to_json(orient='records'))[0])


def main():
    p=argparse.ArgumentParser();p.add_argument('--table',required=True);p.add_argument('--row-id',required=True);p.add_argument('--column',required=True)
    args=p.parse_args();print(json.dumps(trace(args.table,args.row_id,args.column),ensure_ascii=False,indent=2,allow_nan=False))


if __name__=='__main__':main()
