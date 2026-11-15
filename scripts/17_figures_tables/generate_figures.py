#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.utils.config import ROOT


master_path=ROOT/"results/runs/historical/index/all_experiments.csv"
if not master_path.exists(): raise SystemExit("Execute consolidate_results.py primeiro.")
frame=pd.read_csv(master_path);frame=frame[frame.pilot.fillna(0).astype(int)==0];plt.style.use("seaborn-v0_8-whitegrid")
if not frame.empty and "metrics_source_f1" in frame:
    for chapter,name in (("pairwise","pairwise_f1"),("lodo_","lodo_f1"),("ablation","ablation_f1")):
        data=frame[frame.chapter.astype(str).str.startswith(chapter)]
        if data.empty: continue
        table=data.pivot_table(index="target",columns="model",values="metrics_source_f1",aggfunc="mean")
        fig,ax=plt.subplots(figsize=(max(6,len(table.columns)*1.2),max(4,len(table)*.55)))
        image=ax.imshow(table.to_numpy(),vmin=0,vmax=1,cmap="viridis",aspect="auto")
        ax.set_xticks(range(len(table.columns)),table.columns,rotation=30,ha="right");ax.set_yticks(range(len(table.index)),table.index)
        for row in range(len(table.index)):
            for column in range(len(table.columns)):
                value=table.iloc[row,column]
                if pd.notna(value): ax.text(column,row,f"{value:.2f}",ha="center",va="center",color="white" if value<.55 else "black")
        fig.colorbar(image,ax=ax);ax.set_title(f"F1 ({chapter})")
        fig.tight_layout();fig.savefig(ROOT/f"figures/final/{name}.png",dpi=220);plt.close(fig)
pred_files=[]
for path in (ROOT/"runs/predictions").glob("*.csv"):
    status=ROOT/"runs/status"/f"{path.stem}.json"
    if status.exists():
        import json
        result=ROOT/"results/raw"/f"{path.stem}.json"
        if (json.loads(status.read_text()).get("status")=="COMPLETED" and result.exists()
                and int(json.loads(result.read_text()).get("pilot",0) or 0)==0): pred_files.append(path)
if pred_files:
    # Amostra antes de concatenar: limite explícito evita carregar dezenas de milhões de predictions.
    pieces=[]; cap_per_file_class=50
    for file_number,path in enumerate(sorted(pred_files)):
        part=pd.read_csv(path,usecols=["dataset","true_label","score"])
        pieces.extend(group.sample(min(cap_per_file_class,len(group)),random_state=42+file_number)
                      for _,group in part.groupby("true_label"))
    sample=pd.concat(pieces,ignore_index=True);datasets=sorted(sample.dataset.unique())
    columns=3;rows=int(np.ceil(len(datasets)/columns));fig,axes=plt.subplots(rows,columns,figsize=(12,3.2*rows),squeeze=False)
    for ax,dataset in zip(axes.flat,datasets):
        subset=sample[sample.dataset==dataset]
        for label,color in ((0,"tab:blue"),(1,"tab:red")):
            ax.hist(subset.loc[subset.true_label==label,"score"],bins=25,density=True,alpha=.5,label=str(label),color=color)
        ax.set_title(dataset);ax.set_xlim(0,1);ax.legend(title="classe")
    for ax in axes.flat[len(datasets):]: ax.set_visible(False)
    fig.suptitle("Distribuição dos scores por dataset e classe");fig.tight_layout()
    fig.savefig(ROOT/"figures/final/score_distributions.png",dpi=180);plt.close(fig)
print("Figuras disponíveis regeneradas em figures/final")
