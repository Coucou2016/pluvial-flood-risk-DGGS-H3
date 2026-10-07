from pluvial_flood_risk.pipeline import smoke_test


def test_smoke_test_runs():
    result = smoke_test()
    assert result["n_cells_trained"] > 50
    assert result["n_cells_predicted"] > 50
    assert result["train_metrics"]["val_accuracy"] > 0.5
    assert "spatial_cv_accuracy_mean" in result["train_metrics"]
    assert result["data_provenance"] == "synthetic"
