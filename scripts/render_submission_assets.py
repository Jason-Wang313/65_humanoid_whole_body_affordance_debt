"""Render Paper 65 CSV evidence into LaTeX assets and audit summaries."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PAPER = ROOT / "paper"
GENERATED = PAPER / "generated"
DOCS = ROOT / "docs"


METHOD_ORDER = [
    "random_posture",
    "arm_only_reach",
    "greedy_reach_mpc",
    "comfort_regularized_mpc",
    "robust_balance_mpc",
    "current_target_only_greedy",
    "future_distribution_mpc",
    "learned_linear_debt_proxy",
    "bar_mpc_v5",
    "bar_mpc_no_online",
    "oracle_two_step_mpc",
]

SELECTED_METHODS = [
    "greedy_reach_mpc",
    "robust_balance_mpc",
    "future_distribution_mpc",
    "learned_linear_debt_proxy",
    "bar_mpc_v5",
    "oracle_two_step_mpc",
]

HOSTILE_SPLITS = ["combined_shift", "opposite_side_sequence", "support_reversal", "high_lateral_payload"]

LABELS = {
    "random_posture": "Random",
    "arm_only_reach": "Arm only",
    "greedy_reach_mpc": "Greedy reach",
    "comfort_regularized_mpc": "Comfort MPC",
    "robust_balance_mpc": "Robust balance",
    "current_target_only_greedy": "Current-only",
    "future_distribution_mpc": "Future dist.",
    "learned_linear_debt_proxy": "Linear debt",
    "bar_mpc_v5": "BAR-MPC",
    "bar_mpc_no_online": "BAR no-online",
    "oracle_two_step_mpc": "Oracle",
    "no_future_debt": "No future debt",
    "no_tail_debt": "No tail debt",
    "no_balance_margin": "No balance margin",
    "no_recovery_cost": "No recovery cost",
    "no_hand_switch_cost": "No hand-switch cost",
    "no_torque_comfort": "No torque comfort",
    "mean_future_only": "Mean future only",
    "small_future_sample": "Small future sample",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def f3(value: object) -> str:
    return f"{float(value):.3f}"


def f2(value: object) -> str:
    return f"{float(value):.2f}"


def pct(value: object) -> str:
    return f"{100.0 * float(value):.1f}"


def esc(text: object) -> str:
    out = str(text)
    return (
        out.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


def method_rank(method: str) -> int:
    return METHOD_ORDER.index(method) if method in METHOD_ORDER else len(METHOD_ORDER)


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def aggregate_by_method(metrics: list[dict[str, str]]) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in metrics:
        groups[row["method"]].append(row)
    out = []
    for method, rows in groups.items():
        out.append(
            {
                "method": method,
                "splits": len(rows),
                "episodes": sum(int(float(row["episodes"])) for row in rows),
                "seq": mean(float(row["sequential_success"]) for row in rows),
                "energy": mean(float(row["combined_energy_mean"]) for row in rows),
                "margin": mean(float(row["future_support_margin_mean"]) for row in rows),
                "failure": mean(float(row["balance_failure_rate"]) for row in rows),
                "unique": mean(float(row["unique_first_postures"]) for row in rows),
            }
        )
    return sorted(out, key=lambda row: method_rank(str(row["method"])))


def render_aggregate(metrics: list[dict[str, str]]) -> str:
    rows = aggregate_by_method(metrics)
    body = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Aggregate frozen results across all ten splits. Success and balance failure are rates; energy is lower-is-better.}",
        "\\label{tab:aggregate-main}",
        "\\small",
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "Method & Episodes & Seq. success & Energy & Margin & Bal. fail & Unique first \\\\",
        "\\midrule",
    ]
    for row in rows:
        body.append(
            f"{esc(LABELS.get(str(row['method']), row['method']))} & {row['episodes']} & {f3(row['seq'])} & "
            f"{f3(row['energy'])} & {f3(row['margin'])} & {f3(row['failure'])} & {f2(row['unique'])} \\\\"
        )
    body += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(body)


def render_selected_split_table(metrics: list[dict[str, str]]) -> str:
    by_key = {(row["split"], row["method"]): row for row in metrics}
    splits = sorted({row["split"] for row in metrics})
    body = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Split-level sequential success for strong baselines, BAR-MPC, and the oracle. The BAR column does not separate from robust or future-distribution planning.}",
        "\\label{tab:selected-splits}",
        "\\scriptsize",
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "Split & Greedy & Robust & Future & Linear & BAR & Oracle \\\\",
        "\\midrule",
    ]
    for split in splits:
        vals = [f3(by_key[(split, method)]["sequential_success"]) for method in SELECTED_METHODS]
        body.append(f"{esc(split)} & " + " & ".join(vals) + " \\\\")
    body += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(body)


def render_ablation(ablation: list[dict[str, str]]) -> str:
    rows = sorted(ablation, key=lambda row: (row["split"], method_rank(row["method"]), row["method"]))
    body = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Frozen ablation results on the two pre-registered hostile splits. Ablations matching BAR-MPC are mechanism-level failures, not cosmetic ties.}",
        "\\label{tab:ablation}",
        "\\scriptsize",
        "\\begin{tabular}{llrrrrr}",
        "\\toprule",
        "Split & Method & Episodes & Seq. & Energy & Tail debt & Unique first \\\\",
        "\\midrule",
    ]
    for row in rows:
        body.append(
            f"{esc(row['split'])} & {esc(LABELS.get(row['method'], row['method']))} & {int(float(row['episodes']))} & "
            f"{f3(row['sequential_success'])} & {f3(row['combined_energy_mean'])} & "
            f"{f3(row['tail_future_debt_mean'])} & {f3(row['unique_first_postures'])} \\\\"
        )
    body += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(body)


def render_pairwise(pairwise: list[dict[str, str]]) -> str:
    keep = {
        "greedy_reach_mpc",
        "comfort_regularized_mpc",
        "robust_balance_mpc",
        "future_distribution_mpc",
        "learned_linear_debt_proxy",
        "bar_mpc_no_online",
        "oracle_two_step_mpc",
    }
    rows = [
        row
        for row in pairwise
        if row["split"] in HOSTILE_SPLITS and row["baseline"] in keep
    ]
    rows.sort(key=lambda row: (HOSTILE_SPLITS.index(row["split"]), method_rank(row["baseline"])))
    body = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Paired BAR-MPC deltas on hostile splits. Positive success delta and positive energy improvement favor BAR-MPC.}",
        "\\label{tab:hostile-pairwise}",
        "\\scriptsize",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Split & Baseline & $\\Delta$ success & Energy impr. & $\\Delta$ margin & First-choice diff. \\\\",
        "\\midrule",
    ]
    for row in rows:
        body.append(
            f"{esc(row['split'])} & {esc(LABELS.get(row['baseline'], row['baseline']))} & "
            f"{f3(row['success_delta_mean'])} & {f3(row['energy_improvement_mean'])} & "
            f"{f3(row['future_margin_delta_mean'])} & {pct(row['first_choice_diff_rate'])}\\% \\\\"
        )
    body += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(body)


def render_full_metrics(metrics: list[dict[str, str]]) -> str:
    rows = sorted(metrics, key=lambda row: (row["split"], method_rank(row["method"])))
    body = [
        "\\begin{longtable}{llrrrrr}",
        "\\caption{Complete frozen split-method metric table used for the terminal decision.}\\label{tab:full-metrics}\\\\",
        "\\toprule",
        "Split & Method & Episodes & Seq. & Energy & Margin & Bal. fail \\\\",
        "\\midrule",
        "\\endfirsthead",
        "\\toprule",
        "Split & Method & Episodes & Seq. & Energy & Margin & Bal. fail \\\\",
        "\\midrule",
        "\\endhead",
    ]
    for row in rows:
        body.append(
            f"{esc(row['split'])} & {esc(LABELS.get(row['method'], row['method']))} & {int(float(row['episodes']))} & "
            f"{f3(row['sequential_success'])} & {f3(row['combined_energy_mean'])} & "
            f"{f3(row['future_support_margin_mean'])} & {f3(row['balance_failure_rate'])} \\\\"
        )
    body += ["\\bottomrule", "\\end{longtable}", ""]
    return "\n".join(body)


def render_full_pairwise(pairwise: list[dict[str, str]]) -> str:
    rows = sorted(pairwise, key=lambda row: (row["split"], method_rank(row["baseline"])))
    body = [
        "\\begin{longtable}{llrrrrr}",
        "\\caption{Complete paired BAR-MPC comparison table.}\\label{tab:full-pairwise}\\\\",
        "\\toprule",
        "Split & Baseline & Pairs & $\\Delta$ succ. & Energy impr. & $\\Delta$ margin & Diff. \\\\",
        "\\midrule",
        "\\endfirsthead",
        "\\toprule",
        "Split & Baseline & Pairs & $\\Delta$ succ. & Energy impr. & $\\Delta$ margin & Diff. \\\\",
        "\\midrule",
        "\\endhead",
    ]
    for row in rows:
        body.append(
            f"{esc(row['split'])} & {esc(LABELS.get(row['baseline'], row['baseline']))} & {int(float(row['paired_episodes']))} & "
            f"{f3(row['success_delta_mean'])} & {f3(row['energy_improvement_mean'])} & "
            f"{f3(row['future_margin_delta_mean'])} & {pct(row['first_choice_diff_rate'])}\\% \\\\"
        )
    body += ["\\bottomrule", "\\end{longtable}", ""]
    return "\n".join(body)


def render_seed_metrics(seed_metrics: list[dict[str, str]]) -> str:
    keep = set(SELECTED_METHODS)
    rows = [
        row
        for row in seed_metrics
        if row["method"] in keep
    ]
    rows.sort(key=lambda row: (row["split"], int(float(row["seed"])), method_rank(row["method"])))
    body = [
        "\\begin{longtable}{llrrrrr}",
        "\\caption{Seed-level robustness table for selected strong baselines, BAR-MPC, and the oracle.}\\label{tab:seed-metrics}\\\\",
        "\\toprule",
        "Split & Method & Seed & Episodes & Seq. & Energy & Margin \\\\",
        "\\midrule",
        "\\endfirsthead",
        "\\toprule",
        "Split & Method & Seed & Episodes & Seq. & Energy & Margin \\\\",
        "\\midrule",
        "\\endhead",
    ]
    for row in rows:
        body.append(
            f"{esc(row['split'])} & {esc(LABELS.get(row['method'], row['method']))} & {int(float(row['seed']))} & "
            f"{int(float(row['episodes']))} & {f3(row['sequential_success'])} & "
            f"{f3(row['combined_energy_mean'])} & {f3(row['future_support_margin_mean'])} \\\\"
        )
    body += ["\\bottomrule", "\\end{longtable}", ""]
    return "\n".join(body)


def render_failure_cases(cases: list[dict[str, str]]) -> str:
    body = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Pre-registered limitations and negative cases.}",
        "\\label{tab:negative-cases}",
        "\\small",
        "\\begin{tabular}{p{0.28\\linewidth}p{0.48\\linewidth}p{0.16\\linewidth}}",
        "\\toprule",
        "Case & Observed limitation & Status \\\\",
        "\\midrule",
    ]
    for row in cases:
        body.append(f"{esc(row['case'])} & {esc(row['observed'])} & {esc(row['paper_status'])} \\\\")
    body += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(body)


def render_gate_table(metrics: list[dict[str, str]], ablation: list[dict[str, str]]) -> tuple[str, str]:
    aggregates = {str(row["method"]): row for row in aggregate_by_method(metrics)}
    bar = aggregates["bar_mpc_v5"]
    weak_ok = (
        float(bar["seq"]) > float(aggregates["random_posture"]["seq"])
        and float(bar["seq"]) > float(aggregates["arm_only_reach"]["seq"])
        and float(bar["energy"]) < float(aggregates["random_posture"]["energy"])
        and float(bar["energy"]) < float(aggregates["arm_only_reach"]["energy"])
    )
    strong_baselines = [
        "greedy_reach_mpc",
        "comfort_regularized_mpc",
        "robust_balance_mpc",
        "future_distribution_mpc",
        "learned_linear_debt_proxy",
    ]
    strong_failures = []
    for method in strong_baselines:
        other = aggregates[method]
        if float(bar["seq"]) + 1e-9 < float(other["seq"]) or float(bar["energy"]) > float(other["energy"]) + 1e-9:
            strong_failures.append(LABELS[method])
    ab_by_key = {(row["split"], row["method"]): row for row in ablation}
    mechanism_failures = []
    for split in ["combined_shift", "opposite_side_sequence"]:
        bar_row = ab_by_key[(split, "bar_mpc_v5")]
        for method in ["bar_mpc_no_online", "no_future_debt", "no_tail_debt", "mean_future_only", "small_future_sample"]:
            other = ab_by_key[(split, method)]
            if float(other["sequential_success"]) >= float(bar_row["sequential_success"]) - 1e-9:
                mechanism_failures.append(f"{LABELS[method]} on {split}")
    decision = "KILL_ARCHIVE"
    rows = [
        ("Weak baseline gate", "PASS" if weak_ok else "FAIL", "BAR-MPC beats random and arm-only baselines in aggregate."),
        (
            "Strong baseline gate",
            "FAIL" if strong_failures else "PASS",
            "Matched or beaten by " + ", ".join(strong_failures[:5]) if strong_failures else "No aggregate strong-baseline failure.",
        ),
        (
            "Mechanism ablation gate",
            "FAIL" if mechanism_failures else "PASS",
            "Non-identifying ablations: " + "; ".join(mechanism_failures[:6]) if mechanism_failures else "Debt terms are causally separated.",
        ),
        ("Terminal decision", decision, "Archive rather than submit: evidence does not support an ICLR-main mechanism claim."),
    ]
    body = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Frozen decision gates. The failure is methodological, not formatting-related.}",
        "\\label{tab:gates}",
        "\\small",
        "\\begin{tabular}{p{0.22\\linewidth}p{0.13\\linewidth}p{0.55\\linewidth}}",
        "\\toprule",
        "Gate & Status & Evidence \\\\",
        "\\midrule",
    ]
    for gate, status, evidence in rows:
        body.append(f"{esc(gate)} & \\textbf{{{esc(status)}}} & {esc(evidence)} \\\\")
    body += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(body), decision


def render_macros(metrics: list[dict[str, str]], ablation: list[dict[str, str]], pairwise: list[dict[str, str]], decision: str) -> str:
    aggregates = {str(row["method"]): row for row in aggregate_by_method(metrics)}
    bar = aggregates["bar_mpc_v5"]
    greedy = aggregates["greedy_reach_mpc"]
    robust = aggregates["robust_balance_mpc"]
    future = aggregates["future_distribution_mpc"]
    oracle = aggregates["oracle_two_step_mpc"]
    raw_rows = count_rows(RESULTS / "affordance_debt_raw.csv")
    ablation_raw_rows = count_rows(RESULTS / "affordance_debt_ablation_raw.csv")
    return "\n".join(
        [
            "% Auto-generated by scripts/render_submission_assets.py",
            f"\\newcommand{{\\PaperDecision}}{{\\textsc{{{decision.replace('_', '-')}}}}}",
            f"\\newcommand{{\\MainRows}}{{{raw_rows:,}}}",
            f"\\newcommand{{\\AblationRows}}{{{ablation_raw_rows:,}}}",
            f"\\newcommand{{\\MetricRows}}{{{len(metrics)}}}",
            f"\\newcommand{{\\PairwiseRows}}{{{len(pairwise)}}}",
            f"\\newcommand{{\\AblationSummaryRows}}{{{len(ablation)}}}",
            f"\\newcommand{{\\BARAggregateSuccess}}{{{f3(bar['seq'])}}}",
            f"\\newcommand{{\\GreedyAggregateSuccess}}{{{f3(greedy['seq'])}}}",
            f"\\newcommand{{\\RobustAggregateSuccess}}{{{f3(robust['seq'])}}}",
            f"\\newcommand{{\\FutureAggregateSuccess}}{{{f3(future['seq'])}}}",
            f"\\newcommand{{\\OracleAggregateSuccess}}{{{f3(oracle['seq'])}}}",
            f"\\newcommand{{\\BARAggregateEnergy}}{{{f3(bar['energy'])}}}",
            f"\\newcommand{{\\GreedyAggregateEnergy}}{{{f3(greedy['energy'])}}}",
            f"\\newcommand{{\\RobustAggregateEnergy}}{{{f3(robust['energy'])}}}",
            f"\\newcommand{{\\FutureAggregateEnergy}}{{{f3(future['energy'])}}}",
            f"\\newcommand{{\\OracleAggregateEnergy}}{{{f3(oracle['energy'])}}}",
            "",
        ]
    )


def write_decision_markdown(metrics: list[dict[str, str]], ablation: list[dict[str, str]], pairwise: list[dict[str, str]], decision: str) -> None:
    aggregates = {str(row["method"]): row for row in aggregate_by_method(metrics)}
    bar = aggregates["bar_mpc_v5"]
    lines = [
        "# Paper 65 Expanded-Standard Terminal Decision",
        "",
        f"Date: 2026-06-20",
        "",
        f"Decision: `{decision}`",
        "",
        "## Evidence Scale",
        "",
        f"- Main raw rows: {count_rows(RESULTS / 'affordance_debt_raw.csv'):,}.",
        f"- Ablation raw rows: {count_rows(RESULTS / 'affordance_debt_ablation_raw.csv'):,}.",
        f"- Main split-method summaries: {len(metrics)}.",
        f"- Seed-level summaries: {count_rows(RESULTS / 'affordance_debt_seed_metrics.csv'):,}.",
        f"- Paired comparisons: {len(pairwise)}.",
        "",
        "## Aggregate Result",
        "",
        f"- BAR-MPC aggregate sequential success: {f3(bar['seq'])}.",
        f"- BAR-MPC aggregate energy: {f3(bar['energy'])}.",
        f"- BAR-MPC is not cleanly separated from greedy, robust balance, future-distribution, or learned-linear debt baselines.",
        "",
        "## Why This Is Not ICLR-Main Ready",
        "",
        "- The strong-baseline gate fails.",
        "- The no-online variant is identical to BAR-MPC in the frozen implementation.",
        "- Future-debt and tail-debt ablations match BAR-MPC on at least one hostile split.",
        "- Hostile splits expose first-choice differences but not a reliable outcome advantage.",
        "",
        "## Artifact Rule",
        "",
        "- The final PDF must remain `C:\\Users\\wangz\\Downloads\\65.pdf` only.",
        "- No PDF should be placed on the visible Desktop.",
        "",
    ]
    write(DOCS / "paper65_expanded_terminal_decision_20260620.md", "\n".join(lines))


def main() -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    metrics = read_csv(RESULTS / "affordance_debt_metrics.csv")
    seed_metrics = read_csv(RESULTS / "affordance_debt_seed_metrics.csv")
    ablation = read_csv(RESULTS / "affordance_debt_ablation.csv")
    pairwise = read_csv(RESULTS / "affordance_debt_pairwise.csv")
    cases = read_csv(RESULTS / "negative_cases.csv")
    gate_table, decision = render_gate_table(metrics, ablation)
    write(GENERATED / "aggregate_metrics_table.tex", render_aggregate(metrics))
    write(GENERATED / "selected_split_table.tex", render_selected_split_table(metrics))
    write(GENERATED / "ablation_table.tex", render_ablation(ablation))
    write(GENERATED / "hostile_pairwise_table.tex", render_pairwise(pairwise))
    write(GENERATED / "full_metrics_longtable.tex", render_full_metrics(metrics))
    write(GENERATED / "full_pairwise_longtable.tex", render_full_pairwise(pairwise))
    write(GENERATED / "seed_metrics_selected_longtable.tex", render_seed_metrics(seed_metrics))
    write(GENERATED / "negative_cases_table.tex", render_failure_cases(cases))
    write(GENERATED / "gate_table.tex", gate_table)
    write(GENERATED / "result_macros.tex", render_macros(metrics, ablation, pairwise, decision))
    write_decision_markdown(metrics, ablation, pairwise, decision)
    print(f"Rendered Paper 65 submission assets with decision={decision}")


if __name__ == "__main__":
    main()
