# 65 Humanoid Whole-Body Affordance Debt

Expanded-standard status: `KILL_ARCHIVE` for ICLR-main submission.

This repository contains the Paper 65 v5 rebuild: a CPU-only MuJoCo humanoid whole-body reaching falsifier for the hypothesis that explicit future affordance debt improves first-posture selection.

The final result is negative. Balance-Aware Affordance Reservation MPC (`bar_mpc_v5`, BAR-MPC) beats random and arm-only weak baselines, but it does not separate from greedy reach, comfort-regularized MPC, robust-balance MPC, future-distribution MPC, learned linear debt, or no-online/no-debt ablations.

## Frozen Evidence Scale

- Main rows: 21,120.
- Ablation raw rows: 4,992.
- Seeds: 8.
- Episodes per seed/split: 24.
- Main splits: 10.
- Main methods: 11.
- Ablation splits: `combined_shift`, `opposite_side_sequence`.
- Ablation methods: 13.
- Final PDF target: `C:\Users\wangz\Downloads\65.pdf`.
- Desktop PDF: forbidden.

## Reproduce Benchmark

```powershell
python src\run_experiment.py --seeds 8 --episodes 24 --splits nominal narrow_support high_reach lateral_reach weak_actuation payload_shift combined_shift opposite_side_sequence support_reversal high_lateral_payload --ablation-splits combined_shift opposite_side_sequence --workers 4 --chunksize 1 --results-dir results --figures-dir figures
```

## Build Paper

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_submission_pdf.ps1
```

This renders generated tables, compiles the ICLR-style manuscript, and copies the final numbered PDF to Downloads only.

## Validate

```powershell
python scripts\validate_submission_artifacts.py
```

The validator checks Python compilation, frozen row counts, figures, bright boxed clickable citation setup, `Downloads\65.pdf` page count, and absence of `Desktop\65.pdf`.

## Key Files

- `docs/paper65_expanded_submission_plan_20260620.md`: plan created before v5 edits.
- `docs/paper65_development_log_20260620.md`: pre-freeze development and failed repair log.
- `docs/paper65_protocol_freeze_20260620.md`: frozen final command and decision gates.
- `docs/paper65_expanded_terminal_decision_20260620.md`: generated terminal decision summary.
- `paper/main.tex`: 25+ page ICLR-style negative result manuscript.
- `scripts/render_submission_assets.py`: table/macro renderer from CSV evidence.
- `scripts/validate_submission_artifacts.py`: final artifact validator.
