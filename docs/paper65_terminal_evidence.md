# Paper 65 Terminal Evidence

Date: 2026-06-13

Decision: KILL_ARCHIVE.

ICLR main ready: no.

## What Changed

The synthetic v3 scaffold was replaced with a real MuJoCo articulated whole-body reaching benchmark. The benchmark tests whether selecting an initial posture with lower estimated future affordance debt improves a two-step humanoid-style reach task.

## Run Configuration

- Main rows: 2,940.
- Ablation rows: 420.
- Seeds: 5.
- Episodes: 12 per seed/split/method.
- Splits: nominal, narrow_support, high_reach, lateral_reach, weak_actuation, payload_shift, combined_shift.
- Main methods: random_posture, arm_only_reach, greedy_reach_mpc, comfort_regularized_mpc, robust_balance_mpc, affordance_debt_mpc, oracle_two_step_mpc.

## Key Results

- Combined shift: affordance_debt_mpc success 0.733 +/- 0.113, energy 0.306 +/- 0.026; greedy_reach_mpc success 0.733, energy 0.307; robust_balance_mpc success 0.733, energy 0.307; oracle success 0.767, energy 0.302.
- High reach: affordance_debt_mpc, greedy, comfort, robust, and oracle all reach 0.967 sequential success.
- Lateral reach: affordance_debt_mpc success 0.400, greedy success 0.400, robust success 0.400, oracle success 0.417.
- Nominal: affordance_debt_mpc success 0.467, greedy success 0.467, robust success 0.467, oracle success 0.483.
- Payload shift: affordance_debt_mpc, greedy, and robust all reach 0.483 sequential success.

## Ablation Result

Combined-shift ablations are fatal to the mechanism:

- no_balance_margin: success 0.733, energy 0.306.
- affordance_debt_mpc: success 0.733, energy 0.306.
- no_future_debt: success 0.733, energy 0.307.
- current_target_only_greedy: success 0.733, energy 0.307.

The full debt mechanism does not create a meaningful performance gap.

## Terminal Judgment

This is a real negative result, not a synthetic archive. The mechanism does not survive the evidence because simpler first-posture selectors match it across stress splits, and the ablations show the future-debt term is not necessary.

Final status: KILL_ARCHIVE.
