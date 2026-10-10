"""Audit the supplied 2015 files and independently reproduce the essay's models.

Usage: python scripts/reproduce.py --data-dir data/raw --output results/verified
No microdata are written to the output folder. Reported inference is historical,
model-based output and does not account for the complex survey design.
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import importlib.metadata
import numpy as np
import pandas as pd
import pyreadr
import rdata
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def coefficient_table(model):
    return pd.DataFrame({"term": model.params.index,
                         "coefficient": model.params.to_numpy(),
                         "standard_error": model.bse.to_numpy(),
                         "z_value": model.tvalues.to_numpy(),
                         "p_value": model.pvalues.to_numpy()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("results/verified"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = sorted(args.data_dir.glob("lfs-71M0001XCB-E-2015-*_F1.RData"))
    if len(files) != 12:
        raise ValueError(f"Expected the 12 supplied monthly files; found {len(files)}")
    inventory, september, january = [], None, None
    for path in files:
        objects = pyreadr.read_r(str(path))
        if list(objects) != ["table"]:
            raise ValueError(f"Unexpected objects in {path.name}: {list(objects)}")
        frame = objects["table"]
        assert frame.SURVYEAR.nunique() == 1 and frame.SURVYEAR.iloc[0] == 2015
        assert frame.SURVMNTH.nunique() == 1
        month = int(frame.SURVMNTH.iloc[0])
        inventory.append({"file": path.name, "object": "table", "year": 2015,
                          "month": month, "rows": len(frame), "columns": len(frame.columns),
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        if month == 9:
            september, september_path = frame, path
        if month == 1:
            january = frame
    assert {x["month"] for x in inventory} == set(range(1, 13))
    pd.DataFrame(inventory).sort_values("month").to_csv(args.output / "monthly_inventory.csv", index=False)
    assert september is not None and january is not None
    raw = september
    # Match R's source expression. Verify that missing NAICS is never paired with LFSSTAT==1.
    assert not ((raw.LFSSTAT == 1) & raw.NAICS_18.isna()).any()
    assert raw.LFSSTAT.notna().all()
    y = ((raw.LFSSTAT == 1) & (raw.NAICS_18 == 11)).astype(int)
    assert set(raw.SEX.unique()) == {1, 2}
    assert set(raw.MARSTAT.unique()) <= set(range(1, 7))
    d = pd.DataFrame({"SEX": raw.SEX,
                      "child05_original": raw.AGYOWNKN.isin([1, 2]).astype(int),
                      "partnered": raw.MARSTAT.isin([1, 2]).astype(int),
                      "child617_original": raw.AGYOWNKN.isin([3, 5]).astype(int)})
    X1 = sm.add_constant(d[["SEX"]])
    X2 = sm.add_constant(d)
    for variable in ["child05_original", "partnered", "child617_original"]:
        X2[f"SEX:{variable}"] = d.SEX * d[variable]
    class_weights = np.where(y == 1, 1, y.sum() / (len(y) - y.sum()))
    m1 = sm.GLM(y, X1, family=sm.families.Binomial()).fit()
    m2 = sm.GLM(y, X2, family=sm.families.Binomial(), freq_weights=class_weights).fit()
    assert m1.converged and m2.converged
    coefficient_table(m1).to_csv(args.output / "stage1_historical.csv", index=False)
    coefficient_table(m2).to_csv(args.output / "stage2_historical_class_weighted.csv", index=False)
    paper1 = [-2.83191, -0.38667]
    paper2 = [0.06875, -0.2645, 0.90721, 0.43491, 0.6965, -0.3462, -0.0919, -0.0713]
    se1 = [0.05406, 0.03583]
    se2 = [0.13507, 0.08551, 0.25212, 0.1745, 0.25192, 0.16205, 0.11053, 0.15833]
    comparisons = []
    for stage, model, coefficients, errors in [(1, m1, paper1, se1), (2, m2, paper2, se2)]:
        for i, term in enumerate(model.params.index):
            comparisons.append({"stage": stage, "term": term,
                                "paper_coefficient": coefficients[i], "reproduced_coefficient": model.params.iloc[i],
                                "paper_standard_error": errors[i], "reproduced_standard_error": model.bse.iloc[i],
                                "coefficient_within_rounding": bool(abs(model.params.iloc[i] - coefficients[i]) < 0.00005),
                                "se_within_rounding": bool(abs(model.bse.iloc[i] - errors[i]) < 0.000005)})
    assert all(x["coefficient_within_rounding"] and x["se_within_rounding"] for x in comparisons)
    pd.DataFrame(comparisons).to_csv(args.output / "paper_comparison.csv", index=False)
    desc = pd.DataFrame({"outcome_proxy": y, "female": raw.SEX - 1,
                         "child05_original": d.child05_original, "partnered": d.partnered,
                         "child617_original": d.child617_original,
                         "child1824_original": np.where(raw.AGYOWNKN.isna(), np.nan, (raw.AGYOWNKN == 6).astype(int))})
    pd.DataFrame({"variable": desc.columns, "observed": desc.count().values,
                  "missing": desc.isna().sum().values, "mean": desc.mean().values}).to_csv(
        args.output / "descriptive.csv", index=False)
    # Read the exact uploaded file's embedded labels, not a later revised data release.
    parsed = rdata.parser.parse_file(september_path)
    table = parsed.object.value[0]
    convert = lambda obj: rdata.conversion.convert(rdata.parser.RData(parsed.versions, parsed.extra, obj))
    names = convert(table.attributes)["names"]
    metadata = []
    for variable in ["SEX", "LFSSTAT", "MARSTAT", "NAICS_18", "AGYOWNKN", "FWEIGHT"]:
        attr = convert(table.value[list(names).index(variable)].attributes)
        metadata.extend([f"## {variable}", str(attr.get("label", ""))])
        labels = attr.get("labels")
        if labels is not None:
            metadata.extend(f"{code:g}: {label}" for code, label in zip(labels.values, labels.coords[labels.dims[0]].values))
        else:
            metadata.append("No value labels")
        metadata.append("")
    (args.output / "embedded_labels.txt").write_text("\n".join(metadata))
    subset_path = args.data_dir / "lfs-71M0001XCB-E-2015-January_F1-subset.tab"
    subset_match = None
    if subset_path.exists():
        subset = pd.read_csv(subset_path, sep="\t")
        subset_match = subset.shape[0] == len(january) and np.array_equal(
            subset.to_numpy(dtype=float), january[subset.columns].to_numpy(dtype=float), equal_nan=True)
        assert subset_match
    groups = pd.DataFrame({"sex": raw.SEX.map({1: "Male", 2: "Female"}), "outcome": y}).groupby("sex").outcome.agg(["sum", "count", "mean"]).loc[["Male", "Female"]]
    groups.to_csv(args.output / "observed_outcome_by_sex.csv")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    bars = ax.barh(groups.index[::-1], groups["mean"].iloc[::-1] * 100, color=["#E07A5F", "#234E70"], height=.48)
    ax.bar_label(bars, fmt="%.2f%%", padding=6)
    ax.set(xlim=(0, 5), xlabel="Share of respondents (%)", title="At work in professional, scientific and technical services\nSeptember 2015 · unweighted sample")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=.15)
    ax.set_axisbelow(True)
    fig.text(.02, -.055, "Historical outcome: LFSSTAT = 1 and NAICS_18 = 11. This is an industry measure, not all STEM occupations.\nSource: supplied LFS September 2015 file; n = 102,095. Descriptive association only.", fontsize=9)
    fig.savefig(args.output / "observed_outcome_by_sex.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    summary = {"verified_month": "2015-09", "rows": len(raw), "outcome_count": int(y.sum()),
               "outcome_mean": float(y.mean()), "all_10_coefficients_and_standard_errors_match_rounding": True,
               "january_tab_matches_rdata_subset": subset_match,
               "child_age_code4_count": int((raw.AGYOWNKN == 4).sum()),
               "child_age_unrecorded_count": int(raw.AGYOWNKN.isna().sum()),
               "python": platform.python_version(),
               "packages": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "pyreadr", "rdata", "statsmodels", "matplotlib"]}}
    (args.output / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
