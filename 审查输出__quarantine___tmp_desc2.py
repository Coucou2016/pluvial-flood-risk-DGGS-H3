import pandas as pd
import numpy as np

tab = pd.read_parquet("data/processed/nyc_h3_cells.parquet")
ev = tab["flood_risk"]
print("evidence: mean=%.4f median=%.4f  n>=0.8=%d" % (ev.mean(), ev.median(), (ev >= 0.8).sum()))

oof = pd.read_csv("models/nyc_smoke/spatial_cv_oof_predictions.csv")
pfi = pd.read_parquet("outputs/pfi_h_scenarios.parquet")
pfi = pfi[pfi["scenario"] == "ida_like"][["h3_index", "PFI_h"]]

m = tab[["h3_index", "flood_risk"]].merge(oof[["h3_index", "y_proba"]], on="h3_index").merge(pfi, on="h3_index")
print("n=%d" % len(m))
print("r(obs, oof) = %.3f" % np.corrcoef(m["flood_risk"], m["y_proba"])[0, 1])
print("r(obs, pfi) = %.3f" % np.corrcoef(m["flood_risk"], m["PFI_h"])[0, 1])
print("r(oof, pfi) = %.3f" % np.corrcoef(m["y_proba"], m["PFI_h"])[0, 1])

# expanded HWM
exp = pd.read_parquet("data/processed/nyc_h3_cells_expanded.parquet")
print("expanded ida_hwm_count sum=%d, n cells with hwm=%d" % (
    exp["ida_hwm_count"].sum(), (exp["ida_hwm_count"] > 0).sum()))

# random split accuracies
import json
for p in ["models/nyc_smoke/run_metadata.json", "models/nyc_expanded/run_metadata.json"]:
    d = json.load(open(p))
    print(p, "random_split_val_accuracy=%.4f" % d["metrics"]["random_split_val_accuracy"])
