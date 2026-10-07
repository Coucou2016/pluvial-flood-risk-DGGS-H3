import numpy as np, pandas as pd

for name, path in [("LM", "models/nyc_smoke/spatial_cv_folds.csv"),
                   ("Exp", "models/nyc_expanded/spatial_cv_folds.csv")]:
    df = pd.read_csv(path)
    acc = df["accuracy"].to_numpy(float); f1 = df["f1"].to_numpy(float)
    r2 = df["r2"].to_numpy(float); mae = df["mae"].to_numpy(float)
    prev = (df["n_positive_test"] / df["n_test"]).to_numpy(float)
    print(f"== {name} (n_folds={len(df)}) ==")
    print(f"accuracy mean={acc.mean():.3f} std(pop)={acc.std(ddof=0):.3f}")
    print(f"f1       mean={f1.mean():.3f} std(pop)={f1.std(ddof=0):.3f}")
    print(f"r2       mean={r2.mean():.3f} std(pop)={r2.std(ddof=0):.3f}")
    print(f"mae      mean={mae.mean():.3f} std(pop)={mae.std(ddof=0):.3f}")
    ap_acc = prev.mean(); ap_f1 = (2 * prev / (1 + prev)).mean()
    an_acc = (1 - prev).mean()
    print(f"pooled_prevalence={df.n_positive_test.sum() / df.n_test.sum():.4f}")
    print(f"always_pos_acc(foldmean)={ap_acc:.3f}  always_pos_f1(foldmean)={ap_f1:.3f}  always_neg_acc(foldmean)={an_acc:.3f}")
    print("per-fold acc/f1:", ["%.3f/%.3f" % (a, b) for a, b in zip(acc, f1)])
    print("per-fold n_pos:", df.n_positive_test.tolist(), "n_test:", df.n_test.tolist())
    print()
