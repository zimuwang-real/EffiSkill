from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..paths import outputs_root, results_root
from ..scoring import TOPK_VALUES, score_run


TOOL_NAME = "EffiSkill"
MODEL_ORDER = ["GPT-5-mini", "Qwen3-Coder-30B"]
LANGUAGE_ORDER = ["Python", "C++"]
METHOD_ORDER = ["Instruction", "RAG", "CoT", "SBLLM", "FasterPy", "EffiCoder", TOOL_NAME]
TABLE_METHOD_ORDER = ["Instruction", "RAG", "CoT", "SBLLM", "FasterPy", "EffiCoder", TOOL_NAME]
FIGURE_FILENAMES = {
    "topk": "figure4_topk_growth.pdf",
    "bucket": "figure5_speedup_bins.pdf",
    "win_loss": "supplementary_task_level_comparison.pdf",
}


@dataclass(frozen=True)
class RunSpec:
    model: str
    method: str
    language: str
    path: str
    lang_key: str


RUN_SPECS = [
    RunSpec("GPT-5-mini", "Instruction", "Python", "python/gpt-5-mini/instruction", "python3"),
    RunSpec("GPT-5-mini", "RAG", "Python", "python/gpt-5-mini/rag", "python3"),
    RunSpec("GPT-5-mini", "CoT", "Python", "python/gpt-5-mini/cot", "python3"),
    RunSpec("GPT-5-mini", "SBLLM", "Python", "python/gpt-5-mini/sbllm", "python3"),
    RunSpec("GPT-5-mini", "FasterPy", "Python", "python/gpt-5-mini/fasterpy", "python3"),
    RunSpec("GPT-5-mini", TOOL_NAME, "Python", "python/gpt-5-mini/effiskill", "python3"),
    RunSpec("GPT-5-mini", "Instruction", "C++", "cpp/gpt-5-mini/instruction", "cpp"),
    RunSpec("GPT-5-mini", "RAG", "C++", "cpp/gpt-5-mini/rag", "cpp"),
    RunSpec("GPT-5-mini", "CoT", "C++", "cpp/gpt-5-mini/cot", "cpp"),
    RunSpec("GPT-5-mini", "SBLLM", "C++", "cpp/gpt-5-mini/sbllm", "cpp"),
    RunSpec("GPT-5-mini", "FasterPy", "C++", "cpp/gpt-5-mini/fasterpy", "cpp"),
    RunSpec("GPT-5-mini", TOOL_NAME, "C++", "cpp/gpt-5-mini/effiskill", "cpp"),
    RunSpec("Qwen3-Coder-30B", "Instruction", "Python", "python/qwen3-coder-30b/instruction", "python3"),
    RunSpec("Qwen3-Coder-30B", "RAG", "Python", "python/qwen3-coder-30b/rag", "python3"),
    RunSpec("Qwen3-Coder-30B", "CoT", "Python", "python/qwen3-coder-30b/cot", "python3"),
    RunSpec("Qwen3-Coder-30B", "SBLLM", "Python", "python/qwen3-coder-30b/sbllm", "python3"),
    RunSpec("Qwen3-Coder-30B", "FasterPy", "Python", "python/qwen3-coder-30b/fasterpy", "python3"),
    RunSpec("Qwen3-Coder-30B", "EffiCoder", "Python", "python/qwen3-coder-30b/efficoder", "python3"),
    RunSpec("Qwen3-Coder-30B", TOOL_NAME, "Python", "python/qwen3-coder-30b/effiskill", "python3"),
    RunSpec("Qwen3-Coder-30B", "Instruction", "C++", "cpp/qwen3-coder-30b/instruction", "cpp"),
    RunSpec("Qwen3-Coder-30B", "RAG", "C++", "cpp/qwen3-coder-30b/rag", "cpp"),
    RunSpec("Qwen3-Coder-30B", "CoT", "C++", "cpp/qwen3-coder-30b/cot", "cpp"),
    RunSpec("Qwen3-Coder-30B", "SBLLM", "C++", "cpp/qwen3-coder-30b/sbllm", "cpp"),
    RunSpec("Qwen3-Coder-30B", "FasterPy", "C++", "cpp/qwen3-coder-30b/fasterpy", "cpp"),
    RunSpec("Qwen3-Coder-30B", "EffiCoder", "C++", "cpp/qwen3-coder-30b/efficoder", "cpp"),
    RunSpec("Qwen3-Coder-30B", TOOL_NAME, "C++", "cpp/qwen3-coder-30b/effiskill", "cpp"),
]


def rq1_eval_dir() -> Path:
    return results_root() / "effibench-x"


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "axes.titlesize": 18.0,
            "axes.labelsize": 17.0,
            "xtick.labelsize": 17.0,
            "ytick.labelsize": 17.0,
            "legend.fontsize": 17.0,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def load_method_task_frame(base_dir: Path, spec: RunSpec) -> pd.DataFrame:
    frame = score_run(base_dir / spec.path, spec.lang_key)
    frame.insert(2, "Model", spec.model)
    frame.insert(3, "Language", spec.language)
    frame.insert(4, "Method", spec.method)
    return frame


def build_master_task_frame(base_dir: Path) -> pd.DataFrame:
    frames = [load_method_task_frame(base_dir, spec) for spec in RUN_SPECS]
    master = pd.concat(frames, ignore_index=True)
    master["Model"] = pd.Categorical(master["Model"], MODEL_ORDER, ordered=True)
    master["Language"] = pd.Categorical(master["Language"], LANGUAGE_ORDER, ordered=True)
    master["Method"] = pd.Categorical(master["Method"], METHOD_ORDER, ordered=True)
    return master.sort_values(["Language", "Model", "Method", "problem_id"]).reset_index(drop=True)


def summarize_topk(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (language, model, method), group in master.groupby(["Language", "Model", "Method"], observed=True):
        for k in TOPK_VALUES:
            rows.append(
                {
                    "Language": language,
                    "Model": model,
                    "Method": method,
                    "k": k,
                    "OPT (%)": group[f"top{k}_opt"].mean() * 100.0,
                }
            )
    return pd.DataFrame(rows)


def summarize_buckets(master: pd.DataFrame, ratio_col: str = "top8_ratio") -> pd.DataFrame:
    bins = [0.999999, 1.000001, 1.10, 1.25, 1.50, np.inf]
    labels = ["No improvement", "Mild (1.00-1.10)", "Moderate (1.10-1.25)", "Strong (1.25-1.50)", "Very strong (>1.50)"]
    rows = []
    for (language, model, method), group in master.groupby(["Language", "Model", "Method"], observed=True):
        bucketed = pd.cut(group[ratio_col], bins=bins, labels=labels, right=False, include_lowest=True)
        counts = bucketed.value_counts(normalize=True).reindex(labels, fill_value=0.0)
        for label in labels:
            rows.append(
                {
                    "Language": language,
                    "Model": model,
                    "Method": method,
                    "Bucket": label,
                    "Tasks (%)": counts[label] * 100.0,
                }
            )
    return pd.DataFrame(rows)


def summarize_terminal_outcomes(master: pd.DataFrame) -> pd.DataFrame:
    """Appendix D.4 / Table 7: partition of all tasks by terminal outcome."""
    rows = []
    for (language, model, method), group in master.groupby(["Language", "Model", "Method"], observed=True):
        ranks = sorted({int(c.split("_")[1]) for c in group.columns if c.startswith("rank_") and c.endswith("_public_pass")})
        public = pd.DataFrame({r: group[f"rank_{r}_public_pass"].astype("boolean").fillna(False) for r in ranks})
        private = pd.DataFrame({r: group[f"rank_{r}_private_pass"].astype("boolean").fillna(False) for r in ranks})
        has_public = public.any(axis=1)
        private_correct = (public & private).any(axis=1)
        success = group["top8_opt"].astype(bool)
        rows.append({
            "Language": language, "Model": model, "Method": method,
            "Success": int(success.sum()),
            "No public survivor": int((~has_public).sum()),
            "Public, no private-correct": int((has_public & ~private_correct & ~success).sum()),
            "Private-correct < 1.10x": int((private_correct & ~success).sum()),
            "Total": int(len(group)),
        })
    return pd.DataFrame(rows)


def summarize_speedup_geomean(master: pd.DataFrame, ratio_col: str = "top8_ratio") -> pd.DataFrame:
    """Section 5.4: clipped all-task geometric mean of the best private speedup (missing/failing = 1.0)."""
    rows = []
    for (language, model, method), group in master.groupby(["Language", "Model", "Method"], observed=True):
        ratios = np.clip(group[ratio_col].astype(float).fillna(1.0).to_numpy(), 1.0, None)
        rows.append({"Language": language, "Model": model, "Method": method,
                     "Geometric mean speedup": float(np.exp(np.log(ratios).mean()))})
    return pd.DataFrame(rows)


def summarize_mean_speedup(master: pd.DataFrame, strong_threshold: float = 1.50) -> pd.DataFrame:
    rows = []
    for (language, model, method), group in master.groupby(["Language", "Model", "Method"], observed=True):
        record = {
            "Language": language,
            "Model": model,
            "Method": method,
            "task_count": int(len(group)),
            "very_strong_rate": float((group["top8_ratio"] >= strong_threshold).mean()),
            "very_strong_rate_pct": float((group["top8_ratio"] >= strong_threshold).mean() * 100.0),
            "OPT@1 (%)": float(group["top1_opt"].mean() * 100.0),
            "OPT@8 (%)": float(group["top8_opt"].mean() * 100.0),
        }
        for k in TOPK_VALUES:
            mean_ratio = float(group[f"top{k}_ratio"].mean())
            record[f"mean_top{k}_ratio"] = mean_ratio
            record[f"mean_top{k}_improvement_pct"] = (mean_ratio - 1.0) * 100.0
        rows.append(record)
    out = pd.DataFrame(rows)
    out["Language"] = pd.Categorical(out["Language"], LANGUAGE_ORDER, ordered=True)
    out["Model"] = pd.Categorical(out["Model"], MODEL_ORDER, ordered=True)
    out["Method"] = pd.Categorical(out["Method"], METHOD_ORDER, ordered=True)
    return out.sort_values(["Language", "Model", "Method"]).reset_index(drop=True)


def summarize_best_baseline_gaps(mean_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for language in LANGUAGE_ORDER:
        for model in MODEL_ORDER:
            subset = mean_summary[(mean_summary["Language"] == language) & (mean_summary["Model"] == model)]
            if subset.empty:
                continue
            tool = subset[subset["Method"] == TOOL_NAME]
            baselines = subset[subset["Method"] != TOOL_NAME].copy()
            if tool.empty or baselines.empty:
                continue
            baselines = baselines.sort_values(["mean_top8_ratio", "Method"], ascending=[False, True])
            best = baselines.iloc[0]
            tool_row = tool.iloc[0]
            best_mean = float(best["mean_top8_ratio"])
            tool_mean = float(tool_row["mean_top8_ratio"])
            rows.append(
                {
                    "Language": language,
                    "Model": model,
                    "Best baseline": best["Method"],
                    "EffiSkill mean_top8_ratio": tool_mean,
                    "Best baseline mean_top8_ratio": best_mean,
                    "mean_top8_gap": tool_mean - best_mean,
                    "mean_top8_relative_gap_pct": ((tool_mean / best_mean) - 1.0) * 100.0 if best_mean else np.nan,
                    "EffiSkill OPT@8 (%)": float(tool_row["OPT@8 (%)"]),
                    "Best baseline OPT@8 (%)": float(best["OPT@8 (%)"]),
                    "OPT@8 gap (pp)": float(tool_row["OPT@8 (%)"] - best["OPT@8 (%)"]),
                }
            )
    return pd.DataFrame(rows)


def summarize_family_level_deltas(master: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        master.groupby(["Language", "Model", "family", "Method"], observed=True)
        .agg(task_count=("problem_id", "nunique"), mean_top8_ratio=("top8_ratio", "mean"), opt8_rate=("top8_opt", "mean"))
        .reset_index()
    )
    rows = []
    for (language, model, family), subset in grouped.groupby(["Language", "Model", "family"], observed=True):
        tool = subset[subset["Method"] == TOOL_NAME]
        baselines = subset[subset["Method"] != TOOL_NAME].copy()
        if tool.empty or baselines.empty:
            continue
        baselines = baselines.sort_values(["mean_top8_ratio", "Method"], ascending=[False, True])
        best = baselines.iloc[0]
        tool_row = tool.iloc[0]
        best_mean = float(best["mean_top8_ratio"])
        tool_mean = float(tool_row["mean_top8_ratio"])
        rows.append(
            {
                "Language": language,
                "Model": model,
                "family": family,
                "task_count": int(tool_row["task_count"]),
                "Best baseline": best["Method"],
                "EffiSkill mean_top8_ratio": tool_mean,
                "Best baseline mean_top8_ratio": best_mean,
                "mean_top8_delta": tool_mean - best_mean,
                "mean_top8_relative_delta_pct": ((tool_mean / best_mean) - 1.0) * 100.0 if best_mean else np.nan,
                "EffiSkill OPT@8 (%)": float(tool_row["opt8_rate"] * 100.0),
                "Best baseline OPT@8 (%)": float(best["opt8_rate"] * 100.0),
                "OPT@8 delta (pp)": float((tool_row["opt8_rate"] - best["opt8_rate"]) * 100.0),
            }
        )
    return pd.DataFrame(rows).sort_values(["Language", "Model", "mean_top8_delta", "family"]).reset_index(drop=True)


def strongest_baseline_lookup(summary: pd.DataFrame, metric_col: str, language: str, model: str) -> str:
    subset = summary[
        (summary["Language"] == language)
        & (summary["Model"] == model)
        & (summary["Method"] != TOOL_NAME)
    ].copy()
    subset = subset.sort_values([metric_col, "Method"], ascending=[False, True])
    return str(subset.iloc[0]["Method"])


def pairwise_task_compare(master: pd.DataFrame, metric_col: str = "top8_ratio") -> pd.DataFrame:
    summary = (
        master.groupby(["Language", "Model", "Method"], observed=True)[metric_col]
        .mean()
        .reset_index()
        .rename(columns={metric_col: "mean_metric"})
    )
    rows = []
    for language in LANGUAGE_ORDER:
        for model in MODEL_ORDER:
            baseline = strongest_baseline_lookup(summary, "mean_metric", language, model)
            tool = master[
                (master["Language"] == language) & (master["Model"] == model) & (master["Method"] == TOOL_NAME)
            ][["problem_id", metric_col]]
            base = master[
                (master["Language"] == language) & (master["Model"] == model) & (master["Method"] == baseline)
            ][["problem_id", metric_col]]
            merged = tool.merge(base, on="problem_id", suffixes=("_tool", "_base"))
            rows.append(
                {
                    "Language": language,
                    "Model": model,
                    "Baseline": baseline,
                    "EffiSkill Wins": int((merged[f"{metric_col}_tool"] > merged[f"{metric_col}_base"]).sum()),
                    "Ties": int(np.isclose(merged[f"{metric_col}_tool"], merged[f"{metric_col}_base"]).sum()),
                    "Losses": int((merged[f"{metric_col}_tool"] < merged[f"{metric_col}_base"]).sum()),
                }
            )
    return pd.DataFrame(rows)


# Explicit per-endpoint bootstrap seeds (Appendix D.2, Table 5).
BOOTSTRAP_SEEDS = {
    ("GPT-5-mini", "Python", "OPT@1 (%)"): 3442445853,
    ("GPT-5-mini", "Python", "OPT@8 (%)"): 1694924378,
    ("GPT-5-mini", "C++", "OPT@1 (%)"): 3503316074,
    ("GPT-5-mini", "C++", "OPT@8 (%)"): 2198235361,
    ("Qwen3-Coder-30B", "Python", "OPT@1 (%)"): 1800306935,
    ("Qwen3-Coder-30B", "Python", "OPT@8 (%)"): 495226222,
    ("Qwen3-Coder-30B", "C++", "OPT@1 (%)"): 1186028528,
    ("Qwen3-Coder-30B", "C++", "OPT@8 (%)"): 2590448128,
}
BOOTSTRAP_REPS = 10000


def bootstrap_paired(delta: np.ndarray, reps: int = BOOTSTRAP_REPS, seed: int = 0, chunk_size: int = 2000) -> dict[str, float]:
    """One-sided paired task bootstrap: margin, percentile 95% CI (percentage points) and raw p."""
    delta = np.asarray(delta, dtype=float)
    if len(delta) == 0:
        return {"margin": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "p_raw": float("nan")}
    rng = np.random.default_rng(seed)
    means = []
    remaining = reps
    while remaining > 0:
        batch = min(chunk_size, remaining)
        sample_index = rng.integers(0, len(delta), size=(batch, len(delta)))
        means.append(delta[sample_index].mean(axis=1))
        remaining -= batch
    sample_means = np.concatenate(means)
    return {
        "margin": float(delta.mean() * 100.0),
        "ci_low": float(np.percentile(sample_means, 2.5) * 100.0),
        "ci_high": float(np.percentile(sample_means, 97.5) * 100.0),
        "p_raw": float((np.count_nonzero(sample_means <= 0) + 1) / (reps + 1)),
    }


def holm_adjust(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    m = len(p_values)
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p_values[idx]))
        adjusted[idx] = running
    return adjusted


def compute_opt_summary(master: pd.DataFrame) -> tuple[pd.DataFrame, dict[tuple[str, str, str, str], str], pd.DataFrame]:
    rows = []
    frames: dict[tuple[str, str, str], pd.DataFrame] = {}
    for spec in RUN_SPECS:
        frame = master[
            (master["Model"] == spec.model)
            & (master["Method"] == spec.method)
            & (master["Language"] == spec.language)
        ].copy()
        frames[(spec.model, spec.method, spec.language)] = frame
        rows.append(
            {
                "Model": spec.model,
                "Method": spec.method,
                "Language": spec.language,
                "OPT@1 (%)": frame["top1_opt"].mean() * 100.0,
                "OPT@8 (%)": frame["top8_opt"].mean() * 100.0,
            }
        )

    summary = pd.DataFrame(rows)
    summary["Model"] = pd.Categorical(summary["Model"], MODEL_ORDER, ordered=True)
    summary["Language"] = pd.Categorical(summary["Language"], LANGUAGE_ORDER, ordered=True)
    summary["Method"] = pd.Categorical(summary["Method"], METHOD_ORDER, ordered=True)
    summary = summary.sort_values(["Model", "Language", "Method"]).reset_index(drop=True)

    tests = []
    metrics = [("OPT@1 (%)", "top1_opt"), ("OPT@8 (%)", "top8_opt")]
    for model in MODEL_ORDER:
        for language in LANGUAGE_ORDER:
            group = summary[(summary["Model"] == model) & (summary["Language"] == language)]
            if group.empty:
                continue
            non_tool = group[group["Method"] != TOOL_NAME].copy()
            for metric_label, frame_metric in metrics:
                best_non_tool_value = float(non_tool[metric_label].max())
                tied = non_tool[non_tool[metric_label] == best_non_tool_value].sort_values("Method")
                best_non_tool_method = str(tied.iloc[0]["Method"])
                tool_frame = frames[(model, TOOL_NAME, language)].set_index("problem_id")
                baseline_frame = frames[(model, best_non_tool_method, language)].set_index("problem_id")
                aligned = tool_frame.join(baseline_frame, lsuffix="_tool", rsuffix="_base", how="inner")
                delta = aligned[f"{frame_metric}_tool"].to_numpy(dtype=float) - aligned[f"{frame_metric}_base"].to_numpy(dtype=float)
                seed = BOOTSTRAP_SEEDS[(model, language, metric_label)]
                tests.append({
                    "Backbone": model, "Language": language, "Endpoint": metric_label.replace(" (%)", ""),
                    "Baseline": best_non_tool_method, "Seed": seed, "_metric": metric_label,
                    **bootstrap_paired(delta, seed=seed),
                })

    holm = holm_adjust([t["p_raw"] for t in tests])
    marker_lookup: dict[tuple[str, str, str, str], str] = {}
    for test, p_holm in zip(tests, holm):
        test["p_holm"] = p_holm
        test["significant"] = bool(p_holm < 0.05)
        if test["significant"]:
            marker_lookup[(test["Backbone"], test["Language"], TOOL_NAME, test.pop("_metric"))] = "*"
        else:
            test.pop("_metric")
    return summary, marker_lookup, pd.DataFrame(tests)


def format_display_value(value: float, marker: str, tex: bool = False) -> str:
    rounded = f"{value:.2f}"
    if marker == "*":
        return rounded + ("$^{*}$" if tex else "*")
    return rounded


def method_palette() -> dict[str, str]:
    return {
        "Instruction": "#7F8C8D",
        "RAG": "#D35400",
        "CoT": "#148F77",
        "SBLLM": "#8E44AD",
        "FasterPy": "#CA6F1E",
        "EffiCoder": "#5D6D7E",
        TOOL_NAME: "#C0392B",
    }


def iter_method_order(methods: list[str]) -> list[str]:
    method_set = {str(method) for method in methods}
    return [method for method in METHOD_ORDER if method in method_set]


def save_pdf(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="pdf", bbox_inches="tight")
    plt.close(fig)


def plot_topk_growth_pdf(topk_summary: pd.DataFrame, out_dir: Path) -> Path:
    palette = method_palette()
    fig, axes = plt.subplots(2, 2, figsize=(7.9, 6.35), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.11, right=0.995, top=0.945, bottom=0.26, wspace=0.30, hspace=0.48)
    settings = [(language, model) for language in LANGUAGE_ORDER for model in MODEL_ORDER]
    panel_labels = ["(a)", "(b)", "(c)", "(d)"]

    for ax, (language, model), panel_label in zip(axes.ravel(), settings, panel_labels):
        subset = topk_summary[(topk_summary["Language"] == language) & (topk_summary["Model"] == model)]
        for method in iter_method_order(subset["Method"].tolist()):
            method_frame = subset[subset["Method"] == method].sort_values("k")
            color = palette[method]
            line_width = 2.8 if method == TOOL_NAME else 2.1
            marker_size = 5.8 if method == TOOL_NAME else 4.4
            alpha = 1.0 if method == TOOL_NAME else 0.78
            zorder = 4 if method == TOOL_NAME else 2
            ax.plot(
                method_frame["k"],
                method_frame["OPT (%)"],
                marker="o",
                markersize=marker_size,
                linewidth=line_width,
                color=color,
                alpha=alpha,
                zorder=zorder,
                label=method,
            )
        model_short = model.replace("Qwen3-Coder-30B-A3B-Instruct", "Qwen-30B")
        ax.set_title(f"{panel_label} {language} / {model_short}", loc="left", weight="bold", pad=4)
        ax.set_xlim(1, 8)
        ax.set_xticks(range(1, 9))
        ax.set_ylim(0, 75)
        ax.grid(axis="y", linestyle=":", linewidth=0.8, alpha=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    for ax in axes[:, 0]:
        ax.set_ylabel("OPT@k (%)")
    fig.supxlabel("Candidate Budget $k$", y=0.115, fontsize=14.5)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.005), columnspacing=1.6, handlelength=2.5)
    path = out_dir / FIGURE_FILENAMES["topk"]
    save_pdf(fig, path)
    return path


def plot_win_loss_pdf(win_loss: pd.DataFrame, out_dir: Path) -> Path:
    colors = {"EffiSkill Wins": "#C0392B", "Ties": "#B2BABB", "Losses": "#2471A3"}
    fig, axes = plt.subplots(2, 2, figsize=(7.7, 5.8))
    fig.subplots_adjust(left=0.08, right=0.995, top=0.935, bottom=0.24, wspace=0.30, hspace=0.62)
    panel_labels = ["(a)", "(b)", "(c)", "(d)"]

    for ax, (_, row), panel_label in zip(axes.ravel(), win_loss.iterrows(), panel_labels):
        labels = ["EffiSkill Wins", "Ties", "Losses"]
        counts = np.array([row[label] for label in labels], dtype=float)
        total = counts.sum()
        widths = counts / total * 100.0
        left = 0.0
        for label, width, count in zip(labels, widths, counts):
            ax.barh([0], [width], left=left, color=colors[label], height=0.55)
            if width >= 9:
                ax.text(left + width / 2, 0, f"{int(count)}", ha="center", va="center", color="white", fontsize=12.2, weight="bold")
            else:
                ax.text(left + width + 1.2, 0, f"{int(count)}", ha="left", va="center", color=colors[label], fontsize=11.2, weight="bold")
            left += width
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_yticks([])
        ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.35)
        model_short = row["Model"].replace("Qwen3-Coder-30B-A3B-Instruct", "Qwen-30B")
        baseline_short = str(row["Baseline"]).replace("Qwen3-Coder-30B-A3B-Instruct", "Qwen-30B")
        ax.set_title(f"{panel_label} {row['Language']} / {model_short}\nvs {baseline_short}", loc="left", weight="bold", pad=4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.supxlabel("Tasks (%)", y=0.12, fontsize=14.5)
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=colors[label]) for label in colors]
    fig.legend(legend_handles, list(colors), loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.005))
    path = out_dir / FIGURE_FILENAMES["win_loss"]
    save_pdf(fig, path)
    return path


def plot_bucket_pdf(bucket_summary: pd.DataFrame, out_dir: Path) -> Path:
    bucket_order = [
        "No improvement",
        "Mild (1.00-1.10)",
        "Moderate (1.10-1.25)",
        "Strong (1.25-1.50)",
        "Very strong (>1.50)",
    ]
    bucket_colors = {
        "No improvement": "#D5D8DC",
        "Mild (1.00-1.10)": "#F7C86B",
        "Moderate (1.10-1.25)": "#76C893",
        "Strong (1.25-1.50)": "#4EA8DE",
        "Very strong (>1.50)": "#9D4EDD",
    }
    fig, axes = plt.subplots(2, 2, figsize=(8.5, 7.05), sharex=True)
    fig.subplots_adjust(left=0.16, right=0.995, top=0.945, bottom=0.26, wspace=0.50, hspace=0.50)
    settings = [(language, model) for language in LANGUAGE_ORDER for model in MODEL_ORDER]
    panel_labels = ["(a)", "(b)", "(c)", "(d)"]

    for ax, (language, model), panel_label in zip(axes.ravel(), settings, panel_labels):
        subset = bucket_summary[(bucket_summary["Language"] == language) & (bucket_summary["Model"] == model)]
        methods = iter_method_order(subset["Method"].tolist())
        y_positions = np.arange(len(methods))
        left = np.zeros(len(methods))
        for bucket in bucket_order:
            values = []
            for method in methods:
                row = subset[(subset["Method"] == method) & (subset["Bucket"] == bucket)]
                values.append(float(row["Tasks (%)"].iloc[0]) if not row.empty else 0.0)
            values = np.array(values)
            ax.barh(y_positions, values, left=left, color=bucket_colors[bucket], edgecolor="white", linewidth=0.7, label=bucket)
            left += values

        ax.set_yticks(y_positions)
        ax.set_yticklabels(methods)
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.35)
        model_short = model.replace("Qwen3-Coder-30B-A3B-Instruct", "Qwen-30B")
        ax.set_title(f"{panel_label} {language} / {model_short}", loc="left", weight="bold", pad=4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="y", labelsize=11.8, pad=1)
        for label in ax.get_yticklabels():
            if label.get_text() == TOOL_NAME:
                label.set_fontweight("bold")
                label.set_color("#C0392B")

    fig.supxlabel("Tasks (%)", y=0.12, fontsize=14.5)
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=bucket_colors[bucket]) for bucket in bucket_order]
    fig.legend(legend_handles, bucket_order, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.005))
    path = out_dir / FIGURE_FILENAMES["bucket"]
    save_pdf(fig, path)
    return path


def write_table_outputs(summary: pd.DataFrame, marker_lookup: dict[tuple[str, str, str, str], str], out_dir: Path) -> None:
    rows = []
    for model in MODEL_ORDER:
        for method in TABLE_METHOD_ORDER:
            method_rows = summary[(summary["Model"] == model) & (summary["Method"] == method)]
            if method_rows.empty:
                continue
            record = {"Model": model, "Method": method}
            for language in LANGUAGE_ORDER:
                lang_row = method_rows[method_rows["Language"] == language]
                if lang_row.empty:
                    continue
                for metric in ("OPT@1 (%)", "OPT@8 (%)"):
                    value = float(lang_row.iloc[0][metric])
                    marker = marker_lookup.get((model, language, method, metric), "")
                    col = f"{language} {metric}"
                    record[col] = format_display_value(value, marker, tex=False)
            rows.append(record)

    table_csv = pd.DataFrame(rows)
    table_csv.to_csv(out_dir / "table1_rq1.csv", index=False)

    lines = [
        r"\begin{tabular}{llcccc}",
        r"\toprule",
        r"Model & Method & Python OPT@1 (\%) & Python OPT@8 (\%) & C++ OPT@1 (\%) & C++ OPT@8 (\%) \\",
        r"\midrule",
    ]
    for model in MODEL_ORDER:
        model_rows = summary[summary["Model"] == model]
        methods = [m for m in TABLE_METHOD_ORDER if m in set(model_rows["Method"].astype(str))]
        for idx, method in enumerate(methods):
            method_rows = model_rows[model_rows["Method"] == method]
            row = [model if idx == 0 else "", method]
            for language in LANGUAGE_ORDER:
                lang_row = method_rows[method_rows["Language"] == language]
                for metric in ("OPT@1 (%)", "OPT@8 (%)"):
                    value = float(lang_row.iloc[0][metric])
                    marker = marker_lookup.get((model, language, method, metric), "")
                    row.append(format_display_value(value, marker, tex=True))
            lines.append(" & ".join(row) + r" \\")
        if model != MODEL_ORDER[-1]:
            lines.append(r"\midrule")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (out_dir / "table1_rq1.tex").write_text("\n".join(lines) + "\n")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reproduce the paper-facing RQ1 outputs.")
    parser.add_argument("--output-dir", type=Path, default=outputs_root() / "rq1")
    parser.add_argument("--bootstrap-reps", type=int, default=10000)
    return parser


def run(output_dir: Path) -> None:
    configure_style()
    output_dir.mkdir(parents=True, exist_ok=True)
    eval_dir = rq1_eval_dir()
    master = build_master_task_frame(eval_dir)
    summary, marker_lookup, significance = compute_opt_summary(master)
    topk_summary = summarize_topk(master)
    mean_speedup = summarize_mean_speedup(master)
    best_baseline_gaps = summarize_best_baseline_gaps(mean_speedup)
    family_deltas = summarize_family_level_deltas(master)
    bucket_summary = summarize_buckets(master, ratio_col="top8_ratio")
    win_loss = pairwise_task_compare(master, metric_col="top8_ratio")
    write_table_outputs(summary, marker_lookup, output_dir)
    significance.to_csv(output_dir / "table5_significance.csv", index=False)
    topk_summary.pivot_table(index=["Language", "Model", "Method"], columns="k", values="OPT (%)", observed=True).round(2).to_csv(output_dir / "table6_opt_at_k.csv")
    summarize_terminal_outcomes(master).to_csv(output_dir / "table7_terminal_outcomes.csv", index=False)
    bins = bucket_summary.pivot_table(index=["Language", "Model", "Method"], columns="Bucket", values="Tasks (%)", observed=True)
    bins = bins[list(dict.fromkeys(bucket_summary["Bucket"]))].round(2)
    bins.columns = ["= 1.00", "(1.00, 1.10)", "[1.10, 1.25)", "[1.25, 1.50)", ">= 1.50"]
    bins.to_csv(output_dir / "table8_speedup_bins.csv")
    summarize_speedup_geomean(master).round(3).to_csv(output_dir / "speedup_geomean.csv", index=False)
    mean_speedup.to_csv(output_dir / "mean_speedup_summary.csv", index=False)
    best_baseline_gaps.to_csv(output_dir / "mean_speedup_best_baseline_gaps.csv", index=False)
    family_deltas.to_csv(output_dir / "mean_speedup_family_deltas.csv", index=False)
    plot_topk_growth_pdf(topk_summary, output_dir)
    plot_win_loss_pdf(win_loss, output_dir)
    plot_bucket_pdf(bucket_summary, output_dir)


def main(argv: list[str] | None = None) -> None:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    run(args.output_dir)


if __name__ == "__main__":
    main()
