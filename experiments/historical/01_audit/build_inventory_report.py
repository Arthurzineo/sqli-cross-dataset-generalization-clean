#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import pandas as pd
from src.utils.config import ROOT,datasets_config


manifest=pd.read_csv(ROOT/"datasets/metadata/dataset_manifest.csv")
audit=pd.read_csv(ROOT/"datasets/metadata/audit_summary.csv")
overlap=pd.read_csv(ROOT/"datasets/metadata/inter_dataset_overlaps.csv")
decoded=audit[audit.representation=="decoded"]
def markdown(frame):
    values=frame.fillna("").astype(str)
    return "\n".join(["| "+" | ".join(values.columns)+" |","|"+"---|"*len(values.columns)]+[
        "| "+" | ".join(row)+" |" for row in values.to_numpy().tolist()])
lines=["# Inventário auditado dos datasets","",markdown(decoded),"","## Origens declaradas",""]
for dataset,spec in datasets_config().items():
    lines.append(f"- **{dataset}** — família `{spec['family']}`, tipo `{spec['source_type']}`; {spec.get('notes','')}")
related=overlap[(overlap.canonical_overlap>0)|(overlap.decoded_hash_overlap>0)]
lines += ["","## Sobreposições não nulas","",markdown(related) if len(related) else "Nenhuma.","",
          "Os rótulos acima foram lidos das colunas declaradas; não foram inferidos dos nomes dos arquivos."]
(ROOT/"reports/intermediate/DATASET_INVENTORY.md").write_text("\n".join(lines),encoding="utf-8")
print("Inventário gerado")
