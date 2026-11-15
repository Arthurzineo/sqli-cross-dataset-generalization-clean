#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score,normalized_mutual_info_score,silhouette_score
from sklearn.preprocessing import StandardScaler

from src.features.embeddings import load_cached
from src.utils.config import ROOT, experiment_config


p = argparse.ArgumentParser(); p.add_argument("--datasets", default=""); p.add_argument("--representation", default="decoded")
p.add_argument("--model", default="codebert"); p.add_argument("--cap", type=int, default=1500); p.add_argument("--seed", type=int, default=42)
args = p.parse_args(); datasets = args.datasets.split(",") if args.datasets else experiment_config()["dataset_policy"]["primary_datasets"]
X, index = load_cached(datasets, args.representation, args.model)
rng = np.random.default_rng(args.seed); selected=[]
for _, group in index.groupby(["dataset", "y"], sort=True):
    selected.extend(rng.choice(group.index, min(args.cap, len(group)), replace=False))
selected=np.asarray(sorted(selected)); X=np.asarray(X[selected]); index=index.iloc[selected].reset_index(drop=True)
scaled=StandardScaler().fit_transform(X); coordinates=PCA(n_components=2, random_state=args.seed).fit_transform(scaled)
sample=min(10000,len(index)); subset=rng.choice(len(index),sample,replace=False)
dataset_codes=pd.Categorical(index.dataset).codes; class_codes=index.y.to_numpy()
rows=[{"representation":args.representation,"model":args.model,"n":len(index),
       "silhouette_dataset":silhouette_score(scaled[subset],dataset_codes[subset]) if len(set(dataset_codes))>1 else np.nan,
       "silhouette_class":silhouette_score(scaled[subset],class_codes[subset]) if len(set(class_codes))>1 else np.nan}]
clusters=KMeans(n_clusters=len(np.unique(dataset_codes)),random_state=args.seed,n_init=10).fit_predict(scaled)
rows[0].update({"kmeans_ari_dataset":adjusted_rand_score(dataset_codes,clusters),
                "kmeans_nmi_dataset":normalized_mutual_info_score(dataset_codes,clusters),
                "kmeans_ari_class":adjusted_rand_score(class_codes,clusters),
                "kmeans_nmi_class":normalized_mutual_info_score(class_codes,clusters)})
centroids=pd.DataFrame(scaled).assign(dataset=index.dataset.values,y=index.y.values).groupby(["dataset","y"]).mean()
dist=[]
for i,left in enumerate(centroids.index):
    for right in list(centroids.index)[i+1:]:
        dist.append({"left_dataset":left[0],"left_class":left[1],"right_dataset":right[0],"right_class":right[1],
                     "euclidean":float(np.linalg.norm(centroids.loc[left]-centroids.loc[right]))})
pd.DataFrame(rows).to_csv(ROOT/"results/runs/historical/index/embedding_silhouette.csv",index=False)
pd.DataFrame(dist).to_csv(ROOT/"results/runs/historical/index/embedding_centroid_distances.csv",index=False)
pd.DataFrame({"pc1":coordinates[:,0],"pc2":coordinates[:,1],"dataset":index.dataset,"y":index.y}).to_csv(
    ROOT/"results/runs/historical/index/embedding_pca_coordinates.csv",index=False)
for color,name in ((index.dataset,"dataset"),(index.y.map({0:"benign",1:"attack"}),"class")):
    fig,ax=plt.subplots(figsize=(8,6))
    for value in pd.unique(color):
        mask=np.asarray(color==value); ax.scatter(coordinates[mask,0],coordinates[mask,1],s=5,alpha=.35,label=str(value))
    ax.set(xlabel="PC1",ylabel="PC2",title=f"{args.model}: PCA por {name}"); ax.legend(markerscale=2,fontsize=7)
    fig.tight_layout(); fig.savefig(ROOT/f"figures/exploratory/embedding_pca_by_{name}.png",dpi=180); plt.close(fig)
try:
    import umap
    umap_coordinates=umap.UMAP(n_components=2,n_neighbors=15,min_dist=.1,random_state=args.seed,n_jobs=1).fit_transform(scaled)
    pd.DataFrame({"u1":umap_coordinates[:,0],"u2":umap_coordinates[:,1],"dataset":index.dataset,"y":index.y}).to_csv(
        ROOT/"results/runs/historical/index/embedding_umap_coordinates.csv",index=False)
except ImportError:
    print("UMAP indisponível; PCA e clustering foram concluídos.")
print(pd.DataFrame(rows).to_string(index=False))
