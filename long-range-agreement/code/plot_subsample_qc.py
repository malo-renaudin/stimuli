#!/usr/bin/env python3

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from wordfreq import zipf_frequency


def parse_args():
    parser = argparse.ArgumentParser(description="Generate QC plots for v2_subsampled_runs.csv")
    parser.add_argument("--input", type=Path, default=Path("run_lists/v2_subsampled_runs.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("run_lists"))
    parser.add_argument("--single-run-id", type=int, default=None, help="Run ID for single-run hierarchy tree.")
    return parser.parse_args()


def letters(text):
    return sum(1 for ch in str(text) if ch.isalpha())


def with_slot_metrics(df):
    out = df.copy()
    out["Verb_Frequency"] = out["Verb_Lemma"].astype(str).str.lower().map(lambda w: zipf_frequency(w, "fr"))
    out["Subject_Frequency"] = out["Subject_Lemma"].astype(str).str.lower().map(lambda w: zipf_frequency(w, "fr"))
    out["PP1_Frequency"] = out["PP1_Lemma"].astype(str).str.lower().map(lambda w: zipf_frequency(w, "fr"))
    out["PP2_Frequency"] = out["PP2_Lemma"].astype(str).str.lower().map(lambda w: zipf_frequency(w, "fr"))

    out["Verb_Length"] = out["Verb_Lemma"].map(letters)
    out["Subject_Length"] = out["Subject_Lemma"].map(letters)
    out["PP1_Length"] = out["PP1_Lemma"].map(letters)
    out["PP2_Length"] = out["PP2_Lemma"].map(letters)
    return out


def norm_gender(series):
    mapping = {"m": "Masculine", "f": "Feminine", "masculine": "Masculine", "feminine": "Feminine"}
    return series.astype(str).str.lower().map(mapping).fillna(series.astype(str))


def save_distance_plots(df, out_dir):
    distance_order = ["short", "medium", "long"]
    gram_order = ["grammatical", "violation"]

    by_distance = df.groupby("Structure", as_index=False).agg(
        Verb_Frequency_Median=("Verb_Frequency", "median"),
        Subject_Frequency_Median=("Subject_Frequency", "median"),
        PP1_Frequency_Median=("PP1_Frequency", "median"),
        PP2_Frequency_Median=("PP2_Frequency", "median"),
        Verb_Length_Median=("Verb_Length", "median"),
        Subject_Length_Median=("Subject_Length", "median"),
        PP1_Length_Median=("PP1_Length", "median"),
        PP2_Length_Median=("PP2_Length", "median"),
    ).sort_values("Structure")

    by_distance.to_csv(out_dir / "v2_subsampled_medians_by_distance.csv", index=False)

    x = np.arange(len(by_distance))
    width = 0.2
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

    axes[0].bar(x - 1.5 * width, by_distance["Verb_Frequency_Median"], width, label="Verb")
    axes[0].bar(x - 0.5 * width, by_distance["Subject_Frequency_Median"], width, label="Subject")
    axes[0].bar(x + 0.5 * width, by_distance["PP1_Frequency_Median"], width, label="PP1")
    axes[0].bar(x + 1.5 * width, by_distance["PP2_Frequency_Median"], width, label="PP2")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(by_distance["Structure"])
    axes[0].set_title("Median Frequency by Distance")
    axes[0].set_xlabel("Distance")
    axes[0].set_ylabel("Median Zipf")
    axes[0].legend(fontsize=8)

    axes[1].bar(x - 1.5 * width, by_distance["Verb_Length_Median"], width, label="Verb")
    axes[1].bar(x - 0.5 * width, by_distance["Subject_Length_Median"], width, label="Subject")
    axes[1].bar(x + 0.5 * width, by_distance["PP1_Length_Median"], width, label="PP1")
    axes[1].bar(x + 1.5 * width, by_distance["PP2_Length_Median"], width, label="PP2")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(by_distance["Structure"])
    axes[1].set_title("Median Length by Distance")
    axes[1].set_xlabel("Distance")
    axes[1].set_ylabel("Median Letters")
    axes[1].legend(fontsize=8)

    fig.savefig(out_dir / "v2_subsampled_bars_by_distance.png", dpi=220)
    plt.close(fig)

    by_dist_gram = df.groupby(["Structure", "VP_Grammaticality"], as_index=False).agg(
        Verb_Frequency_Median=("Verb_Frequency", "median"),
        Subject_Frequency_Median=("Subject_Frequency", "median"),
        PP1_Frequency_Median=("PP1_Frequency", "median"),
        PP2_Frequency_Median=("PP2_Frequency", "median"),
        Verb_Length_Median=("Verb_Length", "median"),
        Subject_Length_Median=("Subject_Length", "median"),
        PP1_Length_Median=("PP1_Length", "median"),
        PP2_Length_Median=("PP2_Length", "median"),
    ).sort_values(["Structure", "VP_Grammaticality"])

    by_dist_gram.to_csv(out_dir / "v2_subsampled_medians_by_distance_grammaticality.csv", index=False)

    slots = [
        ("Verb", "Verb_Frequency_Median", "Verb_Length_Median"),
        ("Subject", "Subject_Frequency_Median", "Subject_Length_Median"),
        ("PP1", "PP1_Frequency_Median", "PP1_Length_Median"),
        ("PP2", "PP2_Frequency_Median", "PP2_Length_Median"),
    ]

    fig2, axes2 = plt.subplots(4, 2, figsize=(16, 14), constrained_layout=True)
    for i, (slot, freq_col, len_col) in enumerate(slots):
        pivot_f = by_dist_gram.pivot(index="Structure", columns="VP_Grammaticality", values=freq_col).reindex(distance_order)
        pivot_l = by_dist_gram.pivot(index="Structure", columns="VP_Grammaticality", values=len_col).reindex(distance_order)

        idx = np.arange(len(distance_order))
        w = 0.35

        axf = axes2[i, 0]
        axf.bar(idx - w / 2, pivot_f[gram_order[0]].values, w, label=gram_order[0])
        axf.bar(idx + w / 2, pivot_f[gram_order[1]].values, w, label=gram_order[1])
        axf.set_xticks(idx)
        axf.set_xticklabels(distance_order)
        axf.set_title(f"{slot} Frequency by Distance x Grammaticality")
        axf.set_ylabel("Median Zipf")
        if i == 0:
            axf.legend(fontsize=8)

        axl = axes2[i, 1]
        axl.bar(idx - w / 2, pivot_l[gram_order[0]].values, w, label=gram_order[0])
        axl.bar(idx + w / 2, pivot_l[gram_order[1]].values, w, label=gram_order[1])
        axl.set_xticks(idx)
        axl.set_xticklabels(distance_order)
        axl.set_title(f"{slot} Length by Distance x Grammaticality")
        axl.set_ylabel("Median Letters")
        if i == 0:
            axl.legend(fontsize=8)

    fig2.savefig(out_dir / "v2_subsampled_bars_by_distance_grammaticality.png", dpi=220)
    plt.close(fig2)


def save_hierarchy_all_runs(df, out_dir):
    structure_order = ["short", "medium", "long"]
    gram_order = ["grammatical", "violation"]

    rows = []
    rows.append({"Level": "dataset", "Path": "all", "Count": len(df)})
    rows.append({"Level": "run_total", "Path": "all/runs", "Count": df["Run"].nunique()})
    for run in sorted(df["Run"].unique()):
        run_df = df[df["Run"] == run]
        rows.append({"Level": "run", "Path": f"all/run_{run}", "Count": len(run_df)})
        for structure in structure_order:
            rs = run_df[run_df["Structure"] == structure]
            rows.append({"Level": "structure_in_run", "Path": f"all/run_{run}/{structure}", "Count": len(rs)})
            for gram in gram_order:
                rsg = rs[rs["VP_Grammaticality"] == gram]
                rows.append({"Level": "gram_in_run_structure", "Path": f"all/run_{run}/{structure}/{gram}", "Count": len(rsg)})

    counts_df = pd.DataFrame(rows)
    counts_df.to_csv(out_dir / "v2_subsampled_hierarchy_counts.csv", index=False)

    out_tree = out_dir / "v2_subsampled_hierarchy_tree.png"
    fig, ax = plt.subplots(figsize=(18, 9), constrained_layout=True)
    ax.set_title("Hierarchical Trial Counts (Subsampled V2)")
    ax.axis("off")

    x_level = {0: 0.05, 1: 0.28, 2: 0.56, 3: 0.85}
    runs = sorted(df["Run"].unique())
    run_y = np.linspace(0.1, 0.9, len(runs))
    run_y_map = {run: y for run, y in zip(runs, run_y)}

    root_xy = (x_level[0], 0.5)
    ax.text(root_xy[0], root_xy[1], f"All trials\nN={len(df)}", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#e8f1ff", edgecolor="#3567a8"))

    for run in runs:
        y_run = run_y_map[run]
        run_df = df[df["Run"] == run]
        run_xy = (x_level[1], y_run)
        ax.plot([root_xy[0] + 0.05, run_xy[0] - 0.05], [root_xy[1], run_xy[1]], color="#8aa1c1", lw=1.5)
        ax.text(run_xy[0], run_xy[1], f"Run {run}\nN={len(run_df)}", ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#eef6ea", edgecolor="#4f7f3a"))

        y_offsets = [-0.08, 0.0, 0.08]
        for structure, dy in zip(structure_order, y_offsets):
            y_s = y_run + dy
            rs = run_df[run_df["Structure"] == structure]
            s_xy = (x_level[2], y_s)
            ax.plot([run_xy[0] + 0.05, s_xy[0] - 0.05], [run_xy[1], s_xy[1]], color="#8aa1c1", lw=1.0)
            ax.text(s_xy[0], s_xy[1], f"{structure}\nN={len(rs)}", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="#fff6e8", edgecolor="#b07a2f"))

            leaf_offsets = [-0.022, 0.022]
            for gram, ddy in zip(gram_order, leaf_offsets):
                y_g = y_s + ddy
                rsg = rs[rs["VP_Grammaticality"] == gram]
                g_xy = (x_level[3], y_g)
                ax.plot([s_xy[0] + 0.05, g_xy[0] - 0.05], [s_xy[1], g_xy[1]], color="#c8a675", lw=0.9)
                label = "gram" if gram == "grammatical" else "viol"
                ax.text(g_xy[0], y_g, f"{label}: {len(rsg)}", ha="center", va="center", fontsize=8,
                        bbox=dict(boxstyle="round,pad=0.18", facecolor="#fff", edgecolor="#999"))

    fig.savefig(out_tree, dpi=220)
    plt.close(fig)

    out_bars = out_dir / "v2_subsampled_hierarchy_bars.png"
    fig2, axes = plt.subplots(1, 3, figsize=(16, 4.8), constrained_layout=True)

    run_counts = df.groupby("Run").size().reindex(runs)
    axes[0].bar([str(r) for r in runs], run_counts.values)
    axes[0].set_title("Trials per Run")
    axes[0].set_xlabel("Run")
    axes[0].set_ylabel("Count")

    structure_counts = df.groupby("Structure").size().reindex(structure_order)
    axes[1].bar(structure_order, structure_counts.values)
    axes[1].set_title("Trials by Structure")
    axes[1].set_xlabel("Structure")
    axes[1].set_ylabel("Count")

    sg = df.groupby(["Structure", "VP_Grammaticality"]).size().unstack(fill_value=0).reindex(structure_order)
    base = np.zeros(len(structure_order), dtype=float)
    for gram in gram_order:
        vals = sg[gram].values
        axes[2].bar(structure_order, vals, bottom=base, label=gram)
        base += vals
    axes[2].set_title("Structure x Grammaticality")
    axes[2].set_xlabel("Structure")
    axes[2].set_ylabel("Count")
    axes[2].legend(fontsize=8)

    fig2.savefig(out_bars, dpi=220)
    plt.close(fig2)


def save_single_run_hierarchy(df, out_dir, single_run_id):
    structure_order = ["short", "medium", "long"]
    gram_order = ["grammatical", "violation"]
    num_order = ["singular", "plural"]

    if single_run_id is None:
        run_id = sorted(df["Run"].unique().tolist())[0]
    else:
        run_id = single_run_id

    run_df = df[df["Run"] == run_id].copy()
    if run_df.empty:
        raise RuntimeError(f"Requested run id {run_id} is not present in input data.")

    rows = []
    rows.append({"level": "run", "path": f"run_{run_id}", "count": len(run_df)})
    for s in structure_order:
        d1 = run_df[run_df["Structure"] == s]
        rows.append({"level": "structure", "path": f"run_{run_id}/{s}", "count": len(d1)})
        for g in gram_order:
            d2 = d1[d1["VP_Grammaticality"] == g]
            rows.append({"level": "grammaticality", "path": f"run_{run_id}/{s}/{g}", "count": len(d2)})
            for subj in num_order:
                d3 = d2[d2["Subject_Number"] == subj]
                rows.append({"level": "subject_number", "path": f"run_{run_id}/{s}/{g}/subj_{subj}", "count": len(d3)})
                for pp1 in num_order:
                    d4 = d3[d3["PP1_Number"] == pp1]
                    rows.append({"level": "pp1_number", "path": f"run_{run_id}/{s}/{g}/subj_{subj}/pp1_{pp1}", "count": len(d4)})
                    for pp2 in num_order:
                        d5 = d4[d4["PP2_Number"] == pp2]
                        rows.append({
                            "level": "pp2_number",
                            "path": f"run_{run_id}/{s}/{g}/subj_{subj}/pp1_{pp1}/pp2_{pp2}",
                            "count": len(d5),
                        })

    pd.DataFrame(rows).to_csv(out_dir / "v2_subsampled_single_run_hierarchy_counts.csv", index=False)

    fig, ax = plt.subplots(figsize=(19, 10), constrained_layout=True)
    ax.axis("off")
    ax.set_title(f"Hierarchical Trial Counts for Run {run_id}")

    x = {"run": 0.04, "structure": 0.18, "gram": 0.34, "subj": 0.52, "pp1": 0.70, "pp2": 0.88}
    root_xy = (x["run"], 0.5)
    ax.text(*root_xy, f"Run {run_id}\nN={len(run_df)}", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#e8f1ff", edgecolor="#3c6ea5"))

    leaf_ys = np.linspace(0.03, 0.97, 48)
    leaf_idx = 0
    coord_pp2 = {}
    coord_pp1 = {}
    coord_subj = {}
    coord_gram = {}
    coord_struct = {}

    for s in structure_order:
        struct_leaf_ys = []
        for g in gram_order:
            gram_leaf_ys = []
            for subj in num_order:
                subj_leaf_ys = []
                for pp1 in num_order:
                    pp1_leaf_ys = []
                    for pp2 in num_order:
                        y = leaf_ys[leaf_idx]
                        leaf_idx += 1
                        coord_pp2[(s, g, subj, pp1, pp2)] = y
                        pp1_leaf_ys.append(y)
                        subj_leaf_ys.append(y)
                        gram_leaf_ys.append(y)
                        struct_leaf_ys.append(y)
                    coord_pp1[(s, g, subj, pp1)] = float(np.mean(pp1_leaf_ys))
                coord_subj[(s, g, subj)] = float(np.mean(subj_leaf_ys))
            coord_gram[(s, g)] = float(np.mean(gram_leaf_ys))
        coord_struct[s] = float(np.mean(struct_leaf_ys))

    structure_counts = run_df.groupby("Structure").size().to_dict()
    sg_counts = run_df.groupby(["Structure", "VP_Grammaticality"]).size().to_dict()
    subj_counts = run_df.groupby(["Structure", "VP_Grammaticality", "Subject_Number"]).size().to_dict()
    pp1_counts = run_df.groupby(["Structure", "VP_Grammaticality", "Subject_Number", "PP1_Number"]).size().to_dict()
    pp2_counts = run_df.groupby(["Structure", "VP_Grammaticality", "Subject_Number", "PP1_Number", "PP2_Number"]).size().to_dict()

    for s in structure_order:
        y_s = coord_struct[s]
        ax.plot([root_xy[0] + 0.03, x["structure"] - 0.03], [root_xy[1], y_s], color="#7a98b8", lw=1.2)
        ax.text(x["structure"], y_s, f"{s}\nN={structure_counts.get(s, 0)}", ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#eef7ea", edgecolor="#4d7f3c"))

        for g in gram_order:
            y_g = coord_gram[(s, g)]
            c_g = sg_counts.get((s, g), 0)
            ax.plot([x["structure"] + 0.03, x["gram"] - 0.03], [y_s, y_g], color="#89a3be", lw=1.0)
            ax.text(x["gram"], y_g, f"{g}\nN={c_g}", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.27", facecolor="#fff7ea", edgecolor="#b07a2f"))

            for subj in num_order:
                y_subj = coord_subj[(s, g, subj)]
                c_subj = subj_counts.get((s, g, subj), 0)
                ax.plot([x["gram"] + 0.03, x["subj"] - 0.03], [y_g, y_subj], color="#b6a17a", lw=0.95)
                ax.text(x["subj"], y_subj, f"subj {subj}\nN={c_subj}", ha="center", va="center", fontsize=8.5,
                        bbox=dict(boxstyle="round,pad=0.22", facecolor="#ffffff", edgecolor="#999999"))

                for pp1 in num_order:
                    y_pp1 = coord_pp1[(s, g, subj, pp1)]
                    c_pp1 = pp1_counts.get((s, g, subj, pp1), 0)
                    ax.plot([x["subj"] + 0.03, x["pp1"] - 0.03], [y_subj, y_pp1], color="#c0b090", lw=0.9)
                    ax.text(x["pp1"], y_pp1, f"pp1 {pp1}\nN={c_pp1}", ha="center", va="center", fontsize=8,
                            bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", edgecolor="#aaaaaa"))

                    for pp2 in num_order:
                        y_pp2 = coord_pp2[(s, g, subj, pp1, pp2)]
                        c_pp2 = pp2_counts.get((s, g, subj, pp1, pp2), 0)
                        ax.plot([x["pp1"] + 0.03, x["pp2"] - 0.03], [y_pp1, y_pp2], color="#d0c5b0", lw=0.8)
                        ax.text(x["pp2"], y_pp2, f"pp2 {pp2}: {c_pp2}", ha="center", va="center", fontsize=7.5,
                                bbox=dict(boxstyle="round,pad=0.16", facecolor="#ffffff", edgecolor="#bbbbbb"))

    fig.savefig(out_dir / "v2_subsampled_single_run_tree.png", dpi=220)
    plt.close(fig)


def save_gender_plots(df, out_dir):
    run_order = sorted(df["Run"].unique().tolist())
    plot_order = ["Masculine", "Feminine"]
    df2 = df.copy()
    df2["Subject_Gender_Label"] = norm_gender(df2["Subject_Gender"])

    counts = df2.groupby(["Run", "Subject_Gender_Label"]).size().reset_index(name="Count")
    full_index = pd.MultiIndex.from_product([run_order, plot_order], names=["Run", "Subject_Gender_Label"])
    counts = counts.set_index(["Run", "Subject_Gender_Label"]).reindex(full_index, fill_value=0).reset_index()
    counts.to_csv(out_dir / "v2_subsampled_subject_gender_by_run.csv", index=False)

    pivot = counts.pivot(index="Run", columns="Subject_Gender_Label", values="Count").reindex(run_order)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)

    x = np.arange(len(run_order))
    w = 0.36
    axes[0].bar(x - w / 2, pivot["Masculine"].values, w, label="Masculine")
    axes[0].bar(x + w / 2, pivot["Feminine"].values, w, label="Feminine")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([str(r) for r in run_order])
    axes[0].set_xlabel("Run")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Subject Gender Counts per Run")
    axes[0].legend(fontsize=8)

    totals = pivot.sum(axis=1).values
    masc_prop = (pivot["Masculine"].values / totals) * 100
    fem_prop = (pivot["Feminine"].values / totals) * 100
    axes[1].bar([str(r) for r in run_order], masc_prop, label="Masculine")
    axes[1].bar([str(r) for r in run_order], fem_prop, bottom=masc_prop, label="Feminine")
    axes[1].set_xlabel("Run")
    axes[1].set_ylabel("Percent")
    axes[1].set_title("Subject Gender Proportions per Run")
    axes[1].set_ylim(0, 100)
    axes[1].legend(fontsize=8)

    fig.savefig(out_dir / "v2_subsampled_subject_gender_by_run.png", dpi=220)
    plt.close(fig)

    cond_order = sorted(df2["Noun_Congruency"].astype(str).unique().tolist())
    gram_order = ["grammatical", "violation"]

    counts2 = (
        df2.groupby(["VP_Grammaticality", "Noun_Congruency", "Subject_Gender_Label"])
        .size()
        .reset_index(name="Count")
    )
    full_idx2 = pd.MultiIndex.from_product(
        [gram_order, cond_order, plot_order],
        names=["VP_Grammaticality", "Noun_Congruency", "Subject_Gender_Label"],
    )
    counts2 = (
        counts2.set_index(["VP_Grammaticality", "Noun_Congruency", "Subject_Gender_Label"])
        .reindex(full_idx2, fill_value=0)
        .reset_index()
    )
    counts2.to_csv(out_dir / "v2_subsampled_subject_gender_by_condition_grammaticality.csv", index=False)

    fig2, axes2 = plt.subplots(2, 2, figsize=(16, 8), constrained_layout=True)
    for i, gram in enumerate(gram_order):
        sub = counts2[counts2["VP_Grammaticality"] == gram]
        pivot = sub.pivot(index="Noun_Congruency", columns="Subject_Gender_Label", values="Count").reindex(cond_order)

        x = np.arange(len(cond_order))
        w = 0.4
        ax = axes2[i, 0]
        ax.bar(x - w / 2, pivot["Masculine"].values, w, label="Masculine")
        ax.bar(x + w / 2, pivot["Feminine"].values, w, label="Feminine")
        ax.set_xticks(x)
        ax.set_xticklabels(cond_order)
        ax.set_xlabel("Condition (Noun_Congruency)")
        ax.set_ylabel("Count")
        ax.set_title(f"Subject Gender Counts | {gram}")
        ax.legend(fontsize=8)

        totals = pivot.sum(axis=1).values
        masc_prop = np.divide(pivot["Masculine"].values, totals, out=np.zeros_like(totals, dtype=float), where=totals != 0) * 100
        fem_prop = np.divide(pivot["Feminine"].values, totals, out=np.zeros_like(totals, dtype=float), where=totals != 0) * 100
        ax2 = axes2[i, 1]
        ax2.bar(cond_order, masc_prop, label="Masculine")
        ax2.bar(cond_order, fem_prop, bottom=masc_prop, label="Feminine")
        ax2.set_xlabel("Condition (Noun_Congruency)")
        ax2.set_ylabel("Percent")
        ax2.set_title(f"Subject Gender Proportions | {gram}")
        ax2.set_ylim(0, 100)
        ax2.legend(fontsize=8)

    fig2.savefig(out_dir / "v2_subsampled_subject_gender_by_condition_grammaticality.png", dpi=220)
    plt.close(fig2)


def main():
    args = parse_args()
    df = pd.read_csv(args.input)

    required = [
        "Run",
        "Structure",
        "VP_Grammaticality",
        "Noun_Congruency",
        "Subject_Lemma",
        "Subject_Gender",
        "Subject_Number",
        "PP1_Lemma",
        "PP1_Number",
        "PP2_Lemma",
        "PP2_Number",
        "Verb_Lemma",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required columns: {', '.join(missing)}")

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    df = with_slot_metrics(df)

    save_distance_plots(df, out_dir)
    save_hierarchy_all_runs(df, out_dir)
    save_single_run_hierarchy(df, out_dir, args.single_run_id)
    save_gender_plots(df, out_dir)

    print(f"QC plots and tables written to {out_dir}")


if __name__ == "__main__":
    main()
