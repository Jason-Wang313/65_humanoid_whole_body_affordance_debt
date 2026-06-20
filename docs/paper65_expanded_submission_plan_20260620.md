# Paper 65 Expanded-Standard Execution Plan

Date: 2026-06-20

Paper: `65_humanoid_whole_body_affordance_debt`

Target standard: 25+ page ICLR-style manuscript, CPU-only/RAM-light execution, bright boxed clickable citations, numbered PDF in Downloads only, public GitHub repository updated, and honest terminal decision.

## Current State

The v4 artifact is a real MuJoCo articulated whole-body reaching benchmark, but it is too small for the expanded standard:

- 2,940 main rows.
- 420 ablation rows.
- 5 seeds.
- 12 episodes per seed/split.
- 7 stress splits.
- 7 main methods.
- Short manuscript.
- Terminal decision: `KILL_ARCHIVE`.

The old negative result is strong: `affordance_debt_mpc` is effectively tied with `greedy_reach_mpc`, `comfort_regularized_mpc`, `robust_balance_mpc`, and no-debt ablations. The v5 pass must not hide this. It must either produce a genuinely better mechanism under pre-freeze development or preserve the archive decision with stronger evidence.

## Core Failure To Attack

The old benchmark does not create enough cases where the first posture has competing current and future consequences. Greedy, robust, comfort, and debt objectives frequently select the same first candidate. As a result, the debt term is not causally identified.

The v5 rebuild will test a stronger mechanism and a harsher benchmark:

- Expand the first-posture library with explicit commitment, reserve, cross-body, crouched, counterbalance, and hand-switching templates.
- Expand future target distributions to include paired opposite-side, high-lateral, and support-margin reversal sequences.
- Add stress splits that make current target success and future reachability conflict.
- Add first-choice diversity diagnostics so we can see whether debt actually changes action selection.
- Add robust/no-debt/current-target/learned-debt baselines to prevent easy wins.

## Proposed v5 Method

Working method name: Balance-Aware Affordance Reservation MPC (BAR-MPC).

BAR-MPC keeps the original idea but makes it sharper:

1. Immediate reach cost from MuJoCo rollout.
2. Support-margin risk penalty under support polygon shrinkage.
3. Counterfactual future reachability over a pre-registered future-target distribution.
4. Recovery effort from first posture to best future posture.
5. Hand-switch cost and lateral commitment penalty.
6. Tail-risk debt term over the worst future samples, not only mean future debt.
7. Optional light online calibration of future-debt residual by split/target-side family, only if it changes rankings in development.

This is still CPU/RAM light: no neural training, no GPU, no large state, and all scoring uses compact candidate libraries plus MuJoCo rollouts.

## Baselines

Main methods for the frozen run should include:

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

The learned linear proxy must be trained only on source/fitting samples generated before evaluation and must remain CPU-light.

## Ablations

Ablations should run on at least `combined_shift` and `opposite_side_sequence`.

Required ablations:

- `bar_mpc_v5`
- `bar_mpc_no_online`
- `no_future_debt`
- `no_tail_debt`
- `no_balance_margin`
- `no_recovery_cost`
- `no_hand_switch_cost`
- `mean_future_only`
- `small_future_sample`
- `current_target_only_greedy`
- `robust_balance_mpc`
- `oracle_two_step_mpc`

## Stress Splits

The frozen run should include 10 splits:

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

The last three are specifically designed to test affordance debt rather than generic reaching.

## Pre-Freeze Development Protocol

1. Compile the current runner.
2. Run a tiny smoke test with 1 seed, 1 episode, and 1 or 2 splits.
3. Implement v5 benchmark/method changes.
4. Run a tiny smoke test again.
5. Run a medium development run:
   - 2 seeds.
   - 6 episodes.
   - splits: `nominal`, `combined_shift`, `opposite_side_sequence`, `support_reversal`.
   - ablation splits: `combined_shift`, `opposite_side_sequence`.
6. Inspect:
   - whether `bar_mpc_v5` changes first choices relative to greedy/robust/no-debt;
   - whether it improves sequential success or energy;
   - whether it avoids increasing balance failures;
   - whether ablations reveal a necessary debt term.
7. Repair recoverable implementation/design failures before freeze.
8. Write a development log.
9. Freeze the final protocol.

No tuning after the final protocol is frozen.

## Frozen Target Scale

Target full run:

- Seeds: 8.
- Episodes per seed/split: 24.
- Splits: 10.
- Main methods: 11.
- Expected main rows: 21,120.
- Ablation splits: 2.
- Ablation methods: 12.
- Expected ablation rows: 4,608.
- Candidate library: compact enough for CPU-only execution, but expanded enough to expose first-posture tradeoffs.

If runtime becomes unreasonable, reduce episodes only before protocol freeze and document the reason. Do not reduce baselines or ablations to make results look better.

## Decision Gates

Weak gate:

- v5 method must beat random, arm-only, and CEFV-era weak selectors by meaningful aggregate sequential success or energy.

Strong gate:

- v5 method must beat or tie `greedy_reach_mpc`, `comfort_regularized_mpc`, `robust_balance_mpc`, `future_distribution_mpc`, and `learned_linear_debt_proxy` in aggregate success and energy.

Mechanism gate:

- v5 method must change first-posture choices relative to greedy/no-debt in a nontrivial fraction of hostile episodes.
- Removing future debt or tail debt must hurt on the pre-registered hostile splits.
- Removing balance or recovery terms must expose the claimed tradeoff without making the method safer only by refusing difficult reaches.

Terminal decision:

- `ACCEPTABLE_SUBMISSION_CANDIDATE`: all gates pass, validation passes, and the manuscript is genuinely submission-grade.
- `STRONG_REVISE`: weak/strong evidence is promising but mechanism or external-validation gaps remain.
- `KILL_ARCHIVE`: strong baselines or ablations still match/beat the method, or the debt mechanism remains non-identifiable.

Given the v4 evidence, the prior expectation is `KILL_ARCHIVE` unless v5 creates a real, frozen, ablation-supported separation.

## Manuscript Requirements

The final paper must be 25+ pages and contain:

- Formal problem setup for two-stage humanoid whole-body reach under future affordance uncertainty.
- Theory explaining when affordance debt can and cannot help.
- Analysis of identifiability: when debt, comfort, and robust balance produce the same ranking.
- Full frozen protocol.
- Generated tables from CSVs.
- Main, ablation, pairwise, seed, stress, and failure analyses.
- First-choice diversity diagnostics.
- Honest limitations and terminal decision.
- Bright boxed clickable citations.

## Validation Requirements

The final pass must verify:

- `python -m py_compile src\run_experiment.py`.
- Frozen row counts.
- Expected result CSVs and figures exist.
- Manuscript compiles.
- Downloads-only `C:\Users\wangz\Downloads\65.pdf`.
- PDF is 25+ pages.
- No `C:\Users\wangz\Desktop\65.pdf`.
- Public GitHub repo is updated and remains public.
- Root ledgers are updated.

