import pandas as pd
import numpy as np

# Assembled LM table
tab = pd.read_parquet("data/processed/nyc_h3_cells.parquet")
ev = tab["flood_risk"]
print("evidence score: mean=%.3f median=%.3f" % (ev.mean(), ev.median()))

# OOF predictions
oof = pd.read_csv("models/nyc_smoke/spatial_cv_oof_predictions.csv")
oof = oof.merge(tab[["h3_index", "flood_risk", "flood_class"]], on="h3_index", how="left")
print("oof proba: mean=%.3f median=%.3f" % (oof["y_proba"].mean(), oof["y_proba"].median()))

# Full-fit score (75 mm/h scenario)
pfi = pd.read_parquet("outputs/pfi_h_scenarios.parquet")
pfi75 = pfi[pfi["scenario"] == "ida_like"]
full = pfi75[["h3_index", "PFI_h", "flood_probability"]].drop_duplicates("h3_index")
print("full-fit PFI_h: mean=%.3f median=%.3f" % (full["PFI_h"].mean(), full["PFI_h"].median()))
print("full-fit flood_probability: mean=%.3f median=%.3f" % (
    full["flood_probability"].mean(), full["flood_probability"].median()))

# Pearson r between OOF proba and full-fit
m = oof.merge(full, on="h3_index", how="inner")
r_pfi = np.corrcoef(m["y_proba"], m["PFI_h"])[0, 1]
r_prob = np.corrcoef(m["y_proba"], m["flood_probability"])[0, 1]
print("n merged=%d  Pearson(oof, PFI_h)=%.3f  Pearson(oof, flood_probability)=%.3f" % (
    len(m), r_pfi, r_prob))

# scenario invariance check
print("scenarios:", sorted(pfi["scenario"].unique()))
g = pfi.groupby("scenario")["PFI_h"].mean()
print("PFI_h mean by scenario:\n", g)
print("within-cell range across scenarios (max-min):", 
      pfi.groupby("h3_index")["PFI_h"].agg(lambda s: s.max() - s.min()).max())
