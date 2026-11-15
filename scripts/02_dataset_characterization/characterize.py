#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np, pandas as pd
from src.data.loader import load_dataset
from src.features.lexical import extract
from src.utils.config import ROOT, datasets_config


def main():
    rows, distributions = [], []
    for representation in ["raw", "decoded"]:
        for dataset in datasets_config():
            frame = load_dataset(dataset, representation); features = extract(frame)
            original=(frame.url.astype(str)+" "+frame.body.astype(str))
            for label in [0, 1]:
                mask = frame.y.to_numpy() == label; subset = features.loc[mask]
                length = subset.len_total
                row = {"representation": representation, "dataset": dataset, "class": label, "n": int(mask.sum()),
                    "length_mean": length.mean(), "length_median": length.median(), "length_std": length.std(),
                    "length_p10": length.quantile(.1), "length_p90": length.quantile(.9), "length_p99": length.quantile(.99),
                    "encoding_rate": float((subset.enc_pct > 0).mean()), "entropy_mean": subset.entropy.mean()}
                texts=frame.loc[mask,"text"].astype(str); originals=original.loc[mask]
                row.update({"double_encoding_rate":float(originals.str.contains(r"%25[0-9a-fA-F]{2}",regex=True).mean()),
                    "non_ascii_rate":float(texts.map(lambda x:any(ord(c)>127 for c in x)).mean()),
                    "tab_newline_rate":float(texts.str.contains(r"[\t\r\n]",regex=True).mean()),
                    "inline_comment_rate":float(texts.str.contains(r"(--|/\*)",regex=True).mean())})
                for name in ["char_sq","char_dq","char_pct","char_equals","char_semicolon","sql_select","sql_union",
                             "sql_insert","sql_update","sql_delete","sql_drop","sql_or","sql_and","sql_comment_dash","sql_comment_block"]:
                    row[name + "_presence"] = float((subset[name] > 0).mean())
                rows.append(row)
                described = subset.describe(percentiles=[.1,.5,.9,.99]).T.reset_index().rename(columns={"index":"feature"})
                described.insert(0, "class", label); described.insert(0, "dataset", dataset); described.insert(0, "representation", representation)
                distributions.append(described)
    table=pd.DataFrame(rows);table.to_csv(ROOT / "results/tables/dataset_characterization.csv", index=False)
    table.to_csv(ROOT / "results/tables/table_A_dataset_characterization.csv", index=False)
    pd.concat(distributions).to_csv(ROOT / "results/raw/lexical_distributions.csv", index=False)
    print("Caracterização concluída")


if __name__ == "__main__": main()
