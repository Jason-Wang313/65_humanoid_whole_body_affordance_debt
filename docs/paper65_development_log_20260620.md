# Paper 65 Development Log

Date: 2026-06-20

This log records pre-freeze development for Paper 65, "Humanoid Whole-Body Affordance Debt." These runs are not final evidence. They were used to expose implementation issues and method weaknesses before freezing the final protocol.

## Starting Point

The v4 benchmark was a real MuJoCo articulated whole-body reaching setup with 2,940 main rows and 420 ablation rows. It reached `KILL_ARCHIVE` because `affordance_debt_mpc` was effectively matched by greedy reach, comfort-regularized MPC, robust balance MPC, and no-debt ablations.

## Pre-Edit Smoke

Command:

```powershell
python src\run_experiment.py --seeds 1 --episodes 1 --splits nominal --workers 1
```

Outcome:

- The old runner compiled.
- The old runner crashed in plotting because it assumed `combined_shift` existed in every run.
- This was treated as a recoverable implementation issue. The v5 runner adds output-directory arguments and plot logic that works for small split subsets.

## v5 Changes Implemented Before Freeze

- Added 10-split default protocol with three debt-identification splits:
- `opposite_side_sequence`
- `support_reversal`
- `high_lateral_payload`
- Expanded the posture library with reserve, hand-switch-ready, counterlean, cross-body, deep-forward, and wide-support templates.
- Added mean and tail future-debt estimates.
- Added hand-switch and lateral-commitment penalties to future-debt proxies.
- Added stronger baselines:
- `future_distribution_mpc`
- `learned_linear_debt_proxy`
- `current_target_only_greedy`
- Added first-choice difference diagnostics in pairwise stats.
- Added output-dir and ablation-split CLI arguments.

## v5 Smoke Run

Command:

```powershell
python src\run_experiment.py --seeds 1 --episodes 1 --splits nominal --ablation-splits nominal --workers 1 --results-dir results\dev_smoke_v5 --figures-dir figures\dev_smoke_v5
```

Outcome:

- Completed successfully.
- Produced 11 main rows and 13 ablation rows.
- Verified v5 I/O, plotting, and small-run behavior.

## Medium Development Run

Command:

```powershell
python src\run_experiment.py --seeds 2 --episodes 6 --splits nominal combined_shift opposite_side_sequence support_reversal --ablation-splits combined_shift opposite_side_sequence --workers 4 --chunksize 1 --results-dir results\dev_medium_v5 --figures-dir figures\dev_medium_v5
```

Outcome:

- Completed successfully.
- BAR-MPC changed first choices relative to greedy in:
- combined_shift: 2/12 episodes.
- opposite_side_sequence: 2/12 episodes.
- support_reversal: 5/12 episodes.
- BAR-MPC improved over greedy on support_reversal by +0.0833 sequential success and 0.0038 energy improvement.
- BAR-MPC remained tied with robust balance MPC on most key metrics.
- BAR-MPC and `bar_mpc_no_online` were identical because no online adaptation was implemented after the optional-online check.
- Ablations remained dangerous: `no_future_debt`, `no_tail_debt`, and related variants often matched the full method.

Interpretation:

- The new stress splits create some first-choice differences, especially support reversal.
- The mechanism is still weak and likely remains archive unless final scale reveals robust separation.

## Failed Tail-Risk Repair

Change attempted:

- Increased BAR-MPC tail-debt weight.
- Reduced balance and comfort weights.

Command:

```powershell
python src\run_experiment.py --seeds 2 --episodes 6 --splits nominal combined_shift opposite_side_sequence support_reversal --ablation-splits combined_shift opposite_side_sequence --workers 4 --chunksize 1 --results-dir results\dev_medium_v5_tail --figures-dir figures\dev_medium_v5_tail
```

Outcome:

- Completed successfully.
- Tail-heavy scoring worsened support_reversal relative to the previous medium run.
- Opposite-side first-choice diversity collapsed from 2/12 to 0/12.
- The change was reverted before freeze.

## Pre-Freeze Decision

Freeze the v5 scorer from `dev_medium_v5`, not the failed tail-heavy variant.

Prior expectation for the frozen full run remains `KILL_ARCHIVE`, because:

- BAR-MPC is still tied with robust balance on most dev metrics.
- The no-online ablation is identical.
- Future-debt ablations often match the full method.

The final run must report these facts honestly.

