# Paper 65 Frozen Protocol

Date frozen: 2026-06-20

This document freezes the final expanded-standard evidence protocol for Paper 65. No method tuning is allowed after this point.

## Primary Method

Primary method: `bar_mpc_v5`

Manuscript name: Balance-Aware Affordance Reservation MPC (BAR-MPC)

BAR-MPC scores first-stage humanoid postures using:

- immediate MuJoCo reach cost;
- future target distribution debt;
- tail future debt;
- support-margin risk;
- recovery effort proxy;
- hand-switch and lateral-commitment penalties;
- comfort/effort regularization.

## Final Command

```powershell
python src\run_experiment.py --seeds 8 --episodes 24 --splits nominal narrow_support high_reach lateral_reach weak_actuation payload_shift combined_shift opposite_side_sequence support_reversal high_lateral_payload --ablation-splits combined_shift opposite_side_sequence --workers 4 --chunksize 1 --results-dir results --figures-dir figures
```

## Frozen Scale

- Seeds: 8.
- Episodes per seed/split: 24.
- Main splits: 10.
- Main methods: 11.
- Expected main rows: 21,120.
- Ablation splits: 2.
- Ablation methods: 13.
- Expected ablation rows: 4,992.
- Raw ablation rows must be persisted in `results/affordance_debt_ablation_raw.csv`.
- CPU-only execution.
- RAM-light execution: compact posture libraries, cached MuJoCo models, no GPU, no large neural training.

## Main Splits

- `nominal`
- `narrow_support`
- `high_reach`
- `lateral_reach`
- `weak_actuation`
- `payload_shift`
- `combined_shift`
- `opposite_side_sequence`
- `support_reversal`
- `high_lateral_payload`

## Main Methods

- `random_posture`
- `arm_only_reach`
- `greedy_reach_mpc`
- `comfort_regularized_mpc`
- `robust_balance_mpc`
- `current_target_only_greedy`
- `future_distribution_mpc`
- `learned_linear_debt_proxy`
- `bar_mpc_v5`
- `bar_mpc_no_online`
- `oracle_two_step_mpc`

## Ablation Methods

Frozen on `combined_shift` and `opposite_side_sequence`:

- `bar_mpc_v5`
- `bar_mpc_no_online`
- `no_future_debt`
- `no_tail_debt`
- `no_balance_margin`
- `no_recovery_cost`
- `no_hand_switch_cost`
- `no_torque_comfort`
- `mean_future_only`
- `small_future_sample`
- `current_target_only_greedy`
- `robust_balance_mpc`
- `oracle_two_step_mpc`

## Metrics

Primary:

- Sequential success.
- Combined energy.
- Energy regret against the oracle second-stage action.
- Future support margin.
- Balance failure rate.

Mechanism diagnostics:

- First-choice difference rate versus baselines.
- Unique first-posture count.
- Mean future debt.
- Tail future debt.
- Ablation sensitivity.

## Decision Gates

Weak gate:

- BAR-MPC must beat random and arm-only baselines in aggregate success and energy.

Strong gate:

- BAR-MPC must beat or tie greedy reach, comfort-regularized MPC, robust balance MPC, future-distribution MPC, and learned linear debt proxy in aggregate success and energy.

Mechanism gate:

- BAR-MPC must change first choices relative to greedy/no-debt in a nontrivial fraction of hostile episodes.
- `no_future_debt`, `no_tail_debt`, and `mean_future_only` should be worse on pre-registered hostile splits.
- `bar_mpc_no_online` is expected to match BAR-MPC because online adaptation was not retained after development; this must be reported as a limitation.

Terminal decision:

- `STRONG_REVISE` only if weak and strong gates pass but external validation or ablation limitations remain.
- `KILL_ARCHIVE` if strong baselines or ablations match or beat BAR-MPC, or if future-debt terms remain non-identifiable.

Prior expectation from development is `KILL_ARCHIVE`.

## Artifact Rules

- Final PDF must be `C:\Users\wangz\Downloads\65.pdf`.
- No PDF may be copied to visible Desktop.
- Manuscript must be at least 25 pages.
- Manuscript must use bright boxed clickable citations.
- Public GitHub repo must be pushed after validation.
